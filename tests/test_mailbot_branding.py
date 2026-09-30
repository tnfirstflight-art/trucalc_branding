from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged(
    "post_install",
    "-at_install",
    "trucalc_branding",
    "trucalc_mailbot_branding",
)
class TestTruCalcMailBotBranding(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.assistant = cls.env.ref("base.partner_root")
        cls.internal_user = new_test_user(
            cls.env,
            "mailbot-internal@example.test",
            groups="base.group_user",
            context={"no_reset_password": True},
            name="MailBot Internal Test",
        )
        cls.portal_user = new_test_user(
            cls.env,
            "mailbot-portal@example.test",
            groups="base.group_portal",
            context={"no_reset_password": True},
            name="MailBot Portal Test",
        )

    def _assert_debranded(self, content):
        lowered = str(content).lower()
        self.assertNotIn("odoobot", lowered)
        self.assertNotIn("odoo.com", lowered)
        self.assertNotIn("exploring odoo", lowered)

    def _assistant_chat_count(self, user):
        return self.env["discuss.channel"].search_count([
            ("channel_type", "=", "chat"),
            ("channel_member_ids.partner_id", "=", self.assistant.id),
            ("channel_member_ids.partner_id", "=", user.partner_id.id),
        ])

    def test_assistant_uses_neutral_trucalc_identity(self):
        self.assertEqual(self.assistant.name, "TruCalc Assistant")
        self.assertFalse(self.assistant.active)

    def test_assistant_identity_update_is_idempotent(self):
        self.env["res.partner"].apply_trucalc_assistant_identity()
        self.env["res.partner"].apply_trucalc_assistant_identity()
        self.assertEqual(self.assistant.name, "TruCalc Assistant")

    def test_new_internal_user_gets_one_debranded_welcome(self):
        self.internal_user.sudo().odoobot_state = "not_initialized"
        channel = self.internal_user.with_user(self.internal_user)._init_odoobot()

        self.assertEqual(self.internal_user.odoobot_state, "idle")
        self.assertEqual(channel.channel_type, "chat")
        self.assertEqual(
            set(channel.channel_member_ids.partner_id.ids),
            {self.assistant.id, self.internal_user.partner_id.id},
        )
        welcome = self.env["mail.message"].search([
            ("model", "=", "discuss.channel"),
            ("res_id", "=", channel.id),
            ("author_id", "=", self.assistant.id),
        ], order="id desc", limit=1)
        self.assertTrue(welcome)
        self.assertIn("Welcome to TruCalc", welcome.body)
        self.assertIn("automated assistant", welcome.body)
        self._assert_debranded(welcome.body)

        message_count = channel.message_count
        self.internal_user.with_user(self.internal_user)._on_webclient_bootstrap()
        self.assertEqual(channel.message_count, message_count)
        self.assertEqual(self._assistant_chat_count(self.internal_user), 1)

    def test_future_bot_reply_is_debranded_and_ends_legacy_tour(self):
        self.internal_user.sudo().odoobot_state = "onboarding_ping"
        channel = self.internal_user.with_user(self.internal_user)._init_odoobot()
        self.internal_user.sudo().odoobot_state = "onboarding_ping"
        answer = self.env["mail.bot"].with_user(self.internal_user)._get_answer(
            channel,
            "help",
            {"author_id": self.internal_user.partner_id.id},
        )
        self.assertEqual(self.internal_user.odoobot_state, "idle")
        self.assertIn("TruCalc Assistant", answer)
        self.assertIn("automated assistant", answer)
        self._assert_debranded(answer)

    def test_portal_bootstrap_does_not_create_assistant_chat(self):
        self.portal_user.sudo().odoobot_state = False
        count_before = self._assistant_chat_count(self.portal_user)
        self.portal_user.with_user(self.portal_user)._on_webclient_bootstrap()
        self.assertFalse(self.portal_user.odoobot_state)
        self.assertEqual(self._assistant_chat_count(self.portal_user), count_before)
