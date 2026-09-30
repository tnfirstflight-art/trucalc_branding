from odoo import _, models


class MailBot(models.AbstractModel):
    _inherit = "mail.bot"

    def _get_answer(self, channel, body, values, command=False):
        """Keep direct bot replies useful without the generic product tour."""
        assistant = self.env.ref("base.partner_root")
        is_assistant_chat = (
            channel.channel_type == "chat"
            and assistant in channel.channel_member_ids.partner_id
        )
        if not is_assistant_chat:
            return super()._get_answer(channel, body, values, command=command)

        if self.env.user.odoobot_state != "idle":
            self.env.user.sudo().odoobot_state = "idle"
        return _(
            "I'm TruCalc Assistant, an automated assistant for Discuss. Use Discuss "
            "to message teammates and share files. For help with TruCalc workflows, "
            "contact your TruCalc administrator."
        )
