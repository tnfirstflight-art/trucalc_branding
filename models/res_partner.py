from odoo import api, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    @api.model
    def apply_trucalc_assistant_identity(self):
        """Apply the identity override for the protected stock bot partner."""
        assistant = self.env.ref("base.partner_root")
        if assistant.name != "TruCalc Assistant":
            assistant.write({"name": "TruCalc Assistant"})
