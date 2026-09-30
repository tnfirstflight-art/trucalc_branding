from markupsafe import Markup

from odoo import _, models


class ResUsers(models.Model):
    _inherit = "res.users"

    def _init_odoobot(self):
        """Create the standard bot chat with concise TruCalc onboarding."""
        self.ensure_one()
        assistant = self.env.ref("base.partner_root")
        channel = self.env["discuss.channel"]._get_or_create_chat([
            assistant.id,
            self.partner_id.id,
        ])
        message = Markup("%s<br/>%s") % (
            _("Welcome to TruCalc."),
            _(
                "I'm TruCalc Assistant, an automated assistant. Use Discuss to "
                "communicate with teammates and share files."
            ),
        )
        channel.sudo().message_post(
            author_id=assistant.id,
            body=message,
            message_type="comment",
            silent=True,
            subtype_xmlid="mail.mt_comment",
        )
        self.sudo().odoobot_state = "idle"
        return channel
