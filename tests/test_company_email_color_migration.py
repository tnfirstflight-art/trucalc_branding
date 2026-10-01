from lxml import html
from markupsafe import Markup

from odoo.addons.trucalc_branding.hooks import (
    LEGACY_ODOO_PURPLE,
    TRUCALC_BLUE,
    migrate_main_company_email_color,
    post_init_hook,
)
from odoo.tests import TransactionCase, tagged


@tagged(
    "post_install",
    "-at_install",
    "trucalc_branding",
    "trucalc_company_email_color",
)
class TestCompanyEmailColorMigration(TransactionCase):
    protected_queries = {
        "target_company_except_color": """
            SELECT count(*), md5(COALESCE(string_agg(
                (to_jsonb(record) - 'email_secondary_color')::text,
                E'\n' ORDER BY id
            ), ''))
              FROM res_company record
             WHERE id = %s
        """,
        "other_companies": """
            SELECT count(*), md5(COALESCE(string_agg(
                to_jsonb(record)::text, E'\n' ORDER BY id
            ), ''))
              FROM res_company record
             WHERE id <> %s
        """,
        "company_user_links": """
            SELECT count(*), md5(COALESCE(string_agg(
                concat_ws('|', cid, user_id), E'\n' ORDER BY cid, user_id
            ), ''))
              FROM res_company_users_rel
        """,
        "orders": """
            SELECT count(*), md5(COALESCE(string_agg(
                to_jsonb(record)::text, E'\n' ORDER BY id
            ), ''))
              FROM trucalc_order record
        """,
        "invoices": """
            SELECT count(*), md5(COALESCE(string_agg(
                to_jsonb(record)::text, E'\n' ORDER BY id
            ), ''))
              FROM trucalc_bank_invoice record
        """,
        "documents": """
            SELECT count(*), md5(COALESCE(string_agg(
                to_jsonb(record)::text, E'\n' ORDER BY id
            ), ''))
              FROM trucalc_document record
        """,
        "lifecycle_events": """
            SELECT count(*), md5(COALESCE(string_agg(
                to_jsonb(record)::text, E'\n' ORDER BY id
            ), ''))
              FROM trucalc_order_lifecycle_event record
        """,
        "messages": """
            SELECT count(*), md5(COALESCE(string_agg(
                to_jsonb(record)::text, E'\n' ORDER BY id
            ), ''))
              FROM mail_message record
        """,
        "mail_queue": """
            SELECT count(*), md5(COALESCE(string_agg(
                to_jsonb(record)::text, E'\n' ORDER BY id
            ), ''))
              FROM mail_mail record
        """,
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.ref("base.main_company")

    def _set_color(self, color):
        self.env.cr.execute(
            "UPDATE res_company SET email_secondary_color = %s WHERE id = %s",
            (color, self.company.id),
        )
        self.env.invalidate_all()

    def _identity(self):
        self.env.cr.execute(
            """
            SELECT data.id, data.res_id, company.name,
                   company.email_primary_color
              FROM ir_model_data data
              JOIN res_company company ON company.id = data.res_id
             WHERE data.module = 'base'
               AND data.name = 'main_company'
               AND data.model = 'res.company'
            """
        )
        return self.env.cr.fetchone()

    def _protected_state(self):
        state = {}
        for key, query in self.protected_queries.items():
            table_name = {
                "orders": "trucalc_order",
                "invoices": "trucalc_bank_invoice",
                "documents": "trucalc_document",
                "lifecycle_events": "trucalc_order_lifecycle_event",
            }.get(key)
            if table_name:
                self.env.cr.execute("SELECT to_regclass(%s)", (table_name,))
                if not self.env.cr.fetchone()[0]:
                    continue
            params = (self.company.id,) if "%s" in query else ()
            self.env.cr.execute(query, params)
            state[key] = self.env.cr.fetchone()
        return state

    def _render_notification(self):
        return str(self.env["mail.render.mixin"]._render_encapsulate(
            "mail.mail_notification_layout",
            Markup("<p>TruCalc production-like notification body</p>"),
            add_context={
                "company": self.company,
                "author_user": self.env.user,
                "button_access": {"url": "/odoo", "title": "Open record"},
                "has_button_access": True,
                "show_unfollow": True,
                "email_notification_force_footer": True,
            },
            context_record=self.env.user,
        ))

    def test_legacy_purple_migrates_and_notification_renders_blue(self):
        self._set_color(LEGACY_ODOO_PURPLE)
        identity_before = self._identity()
        protected_before = self._protected_state()
        mail_count_before = self.env["mail.mail"].search_count([])

        migrate_main_company_email_color(self.env.cr)
        self.env.invalidate_all()

        self.assertEqual(self.company.email_secondary_color, TRUCALC_BLUE)
        self.assertEqual(self._identity(), identity_before)
        self.assertEqual(self._protected_state(), protected_before)
        rendered = self._render_notification()
        tree = html.fromstring(rendered)
        button_cells = tree.xpath(
            "//a[normalize-space()='Open record']/parent::td"
        )
        self.assertEqual(len(button_cells), 1)
        self.assertIn(TRUCALC_BLUE, button_cells[0].get("style", "").lower())
        self.assertNotIn(LEGACY_ODOO_PURPLE.lower(), rendered.lower())
        self.assertIn("TruCalc production-like notification body", rendered)
        self.assertIn(self.company.name, rendered)
        self.assertIn("/mail/unfollow", rendered)
        self.assertEqual(self.env["mail.mail"].search_count([]), mail_count_before)

    def test_already_correct_color_is_noop(self):
        self._set_color(TRUCALC_BLUE)
        self.env.cr.execute(
            "SELECT to_jsonb(record) FROM res_company record WHERE id = %s",
            (self.company.id,),
        )
        before = self.env.cr.fetchone()[0]
        migrate_main_company_email_color(self.env.cr)
        self.env.cr.execute(
            "SELECT to_jsonb(record) FROM res_company record WHERE id = %s",
            (self.company.id,),
        )
        self.assertEqual(self.env.cr.fetchone()[0], before)

    def test_empty_color_uses_authoritative_trucalc_blue(self):
        for empty_color in (None, ""):
            with self.subTest(empty_color=empty_color):
                self._set_color(empty_color)
                post_init_hook(self.env)
                self.env.invalidate_all()
                self.assertEqual(
                    self.company.email_secondary_color,
                    TRUCALC_BLUE,
                )

    def test_unexpected_color_blocks_without_mutation(self):
        unexpected = "#123456"
        self._set_color(unexpected)
        identity_before = self._identity()
        protected_before = self._protected_state()
        with self.assertRaisesRegex(RuntimeError, "unexpected email_secondary_color"):
            migrate_main_company_email_color(self.env.cr)
        self.env.invalidate_all()
        self.assertEqual(self.company.email_secondary_color, unexpected)
        self.assertEqual(self._identity(), identity_before)
        self.assertEqual(self._protected_state(), protected_before)
