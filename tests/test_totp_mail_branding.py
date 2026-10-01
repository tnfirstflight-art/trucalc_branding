import re
from urllib.parse import urlparse

from lxml import html

from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged(
    "post_install",
    "-at_install",
    "trucalc_branding",
    "trucalc_totp_mail_branding",
)
class TestTOTPBranding(TransactionCase):
    blue = "#022f5b"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_user = new_test_user(
            cls.env,
            "totp-branding@example.test",
            groups="base.group_user",
            context={"no_reset_password": True},
            name="TOTP Branding Recipient",
        )

    def _render(self, template, field_name):
        return str(
            template._render_field(field_name, self.test_user.ids)[
                self.test_user.id
            ]
        )

    def _action_paths(self, tree):
        return [
            urlparse(url).path
            for url in tree.xpath("//a[contains(normalize-space(), 'Activate')]/@href")
        ]

    def test_totp_invitation_subject_and_action_remain_functional(self):
        template = self.env.ref("auth_totp_mail.mail_template_totp_invite")
        mail_count = self.env["mail.mail"].search_count([])

        subject = self._render(template, "subject")
        body = self._render(template, "body_html")
        tree = html.fromstring(body)

        self.assertEqual(
            subject,
            "Invitation to activate two-factor authentication on your TruCalc account",
        )
        self.assertNotIn("Odoo account", subject)
        self.assertIn(self.test_user.name, body)
        self.assertEqual(
            self._action_paths(tree),
            ["/odoo/action-auth_totp_mail.action_activate_two_factor_authentication"],
        )
        self.assertTrue(template.use_default_to)
        self.assertEqual(template.model, "res.users")
        self.assertEqual(self.env["mail.mail"].search_count([]), mail_count)

    def test_totp_code_mail_uses_trucalc_blue_without_changing_content(self):
        template = self.env.ref("auth_totp_mail.mail_template_totp_mail_code")
        mail_count = self.env["mail.mail"].search_count([])

        subject = self._render(template, "subject")
        body = self._render(template, "body_html")
        tree = html.fromstring(body)

        self.assertEqual(subject, "Your two-factor authentication code")
        self.assertNotIn("#875a7b", body.lower())
        self.assertGreaterEqual(body.lower().count(self.blue), 2)
        self.assertRegex(tree.text_content(), re.compile(r"\b\d{6}\b"))
        self.assertIn("expires in", tree.text_content())
        self.assertEqual(
            self._action_paths(tree),
            ["/odoo/action-auth_totp_mail.action_activate_two_factor_authentication"],
        )
        self.assertTrue(template.use_default_to)
        self.assertEqual(template.model, "res.users")
        self.assertEqual(self.env["mail.mail"].search_count([]), mail_count)
