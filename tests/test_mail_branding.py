from markupsafe import Markup
from urllib.parse import parse_qs, urlparse

from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged(
    "post_install",
    "-at_install",
    "trucalc_branding",
    "trucalc_mail_branding",
)
class TestTruCalcMailBranding(TransactionCase):
    blue = "#022f5b"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write({
            "name": "TruCalc Mail Test Company",
            "email_secondary_color": False,
        })
        cls.test_user = new_test_user(
            cls.env,
            "mail-branding@example.test",
            groups="base.group_portal",
            context={"no_reset_password": True},
            name="Mail Branding Recipient",
        )
        cls.test_user.partner_id.signup_prepare()

    def _render_layout(self, xmlid):
        return str(self.env["mail.render.mixin"]._render_encapsulate(
            xmlid,
            Markup("<p>TruCalc notification body</p>"),
            add_context={
                "company": self.company,
                "author_user": self.env.user,
                "button_access": {"url": "/odoo", "title": "Open record"},
                "has_button_access": True,
                "show_unfollow": True,
                "email_notification_force_footer": True,
            },
            context_record=self.test_user,
        ))

    def _render_template(self, xmlid):
        template = self.env.ref(xmlid)
        return str(template._render_field("body_html", self.test_user.ids)[self.test_user.id])

    def _assert_no_odoo_attribution(self, rendered):
        lowered = rendered.lower()
        self.assertNotIn("powered by odoo", lowered)
        self.assertNotIn("sent by odoo", lowered)
        self.assertNotIn("www.odoo.com", lowered)

    def _assert_valid_signup_link(self, rendered, expected_route):
        from lxml import html

        tree = html.fromstring(rendered)
        links = [
            href for href in tree.xpath("//a/@href")
            if expected_route in href and "token=" in href
        ]
        self.assertTrue(links, rendered)
        token = parse_qs(urlparse(links[0]).query)["token"][0]
        self.assertEqual(
            self.env["res.partner"]._get_partner_from_token(token),
            self.test_user.partner_id,
        )

    def test_standard_notification_layouts_preserve_content_and_unfollow(self):
        for xmlid in ("mail.mail_notification_layout", "mail.mail_notification_light"):
            with self.subTest(xmlid=xmlid):
                rendered = self._render_layout(xmlid)
                self._assert_no_odoo_attribution(rendered)
                self.assertIn("TruCalc notification body", rendered)
                self.assertIn(self.company.name, rendered)
                self.assertIn("/mail/unfollow", rendered)
                self.assertIn("/odoo", rendered)
                self.assertNotIn("#875a7b", rendered.lower())
                if xmlid == "mail.mail_notification_layout":
                    self.assertIn(self.blue, rendered.lower())

    def test_reset_password_view_preserves_signed_reset_link(self):
        self.test_user.partner_id.signup_prepare(signup_type="reset")
        rendered = str(self.env["mail.render.mixin"]._render_template(
            "auth_signup.reset_password_email",
            "res.users",
            self.test_user.ids,
            engine="qweb_view",
        )[self.test_user.id])
        self._assert_no_odoo_attribution(rendered)
        self.assertNotIn("#875a7b", rendered.lower())
        self.assertIn(self.blue, rendered.lower())
        self.assertIn(self.test_user.name, rendered)
        self.assertIn(self.company.name, rendered)
        self._assert_valid_signup_link(rendered, "/web/reset_password")

    def test_stock_auth_templates_render_without_attribution(self):
        self.test_user.partner_id.signup_prepare(signup_type="signup")
        token_templates = {
            "auth_signup.set_password_email": "/web/signup",
            "auth_signup.portal_set_password_email": "/web/signup",
        }
        xmlids = (
            "auth_signup.set_password_email",
            "auth_signup.mail_template_user_signup_account_created",
            "auth_signup.portal_set_password_email",
        )
        for xmlid in xmlids:
            with self.subTest(xmlid=xmlid):
                template = self.env.ref(xmlid)
                rendered = self._render_template(xmlid)
                self._assert_no_odoo_attribution(rendered)
                self.assertNotIn("#875a7b", template.body_html.lower())
                self.assertNotIn("#875a7b", rendered.lower())
                self.assertIn(self.test_user.name, rendered)
                self.assertIn(self.company.name, rendered)
                if xmlid in token_templates:
                    self._assert_valid_signup_link(rendered, token_templates[xmlid])
        subject = self.env.ref("auth_signup.set_password_email")._render_field(
            "subject", self.test_user.ids
        )[self.test_user.id]
        self.assertIn("TruCalc", subject)
        self.assertNotIn("connect to Odoo", subject)

    def test_stock_auth_branding_migration_is_idempotent(self):
        templates = {
            xmlid: (self.env.ref(xmlid).subject, self.env.ref(xmlid).body_html)
            for xmlid in self.env["mail.template"]._TRUCALC_AUTH_TEMPLATE_XMLIDS
        }
        self.env["mail.template"].apply_trucalc_auth_mail_branding()
        self.assertEqual(
            templates,
            {
                xmlid: (self.env.ref(xmlid).subject, self.env.ref(xmlid).body_html)
                for xmlid in templates
            },
        )

    def test_existing_trucalc_invitations_remain_authoritative(self):
        self.test_user.partner_id.signup_prepare(signup_type="signup")
        for xmlid in (
            "trucalc_orders.mail_template_bank_user_invitation",
            "trucalc_orders.mail_template_internal_user_invitation",
        ):
            template = self.env.ref(xmlid, raise_if_not_found=False)
            if not template:
                self.skipTest("trucalc_orders is not installed in this database")
            with self.subTest(xmlid=xmlid):
                rendered = str(template._render_field(
                    "body_html", self.test_user.ids
                )[self.test_user.id])
                self._assert_no_odoo_attribution(rendered)
                self.assertEqual(template.subject, "Set up your TruCalc account")
                self.assertIn("Welcome to TruCalc", rendered)
                self.assertIn(self.blue, rendered.lower())
                self._assert_valid_signup_link(rendered, "/web/signup")

    def test_digest_render_preserves_kpi_unsubscribe_and_schedule(self):
        digest = self.env.ref("digest.digest_digest_default")
        schedule_before = (digest.periodicity, digest.next_run_date, digest.state)
        mail_count_before = self.env["mail.mail"].search_count([])
        unsubscribe_token = digest._get_unsubscribe_token(self.env.user.id)
        rendered_body = self.env["mail.render.mixin"]._render_template(
            "digest.digest_mail_main",
            "digest.digest",
            digest.ids,
            engine="qweb_view",
            add_context={
                "title": digest.name,
                "sub_title": False,
                "top_button_label": "Connect",
                "top_button_url": digest.get_base_url(),
                "company": self.company,
                "user": self.env.user,
                "unsubscribe_token": unsubscribe_token,
                "formatted_date": "September 29, 2026",
                "display_mobile_banner": True,
                "kpi_data": [{
                    "kpi_name": "test_kpi",
                    "kpi_fullname": "Test KPI",
                    "kpi_action": False,
                    "kpi_col1": {"value": 42, "col_subtitle": "Completed"},
                    "kpi_col2": False,
                    "kpi_col3": False,
                }],
                "tips": [],
                "preferences": [],
            },
            options={"preserve_comments": True, "post_process": True},
        )[digest.id]
        rendered = str(self.env["mail.render.mixin"]._render_encapsulate(
            "digest.digest_mail_layout",
            rendered_body,
            add_context={"company": self.company, "user": self.env.user},
        ))
        self._assert_no_odoo_attribution(rendered)
        self.assertNotIn("Odoo Mobile", rendered)
        self.assertNotIn("play.google.com/store/apps/details?id=com.odoo.mobile", rendered)
        self.assertIn("TruCalc Periodic Digest", digest.name)
        self.assertIn("Test KPI", rendered)
        self.assertIn("Completed", rendered)
        self.assertIn("42", rendered)
        self.assertIn("Unsubscribe", rendered)
        self.assertIn(f"/digest/{digest.id}/unsubscribe", rendered)
        self.assertIn(self.blue, rendered.lower())
        self.assertNotIn("#714b67", rendered.lower())
        self.assertEqual(
            (digest.periodicity, digest.next_run_date, digest.state), schedule_before
        )
        self.assertEqual(self.env["mail.mail"].search_count([]), mail_count_before)
