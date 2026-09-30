from odoo import api, models


class Digest(models.Model):
    _inherit = "digest.digest"

    @api.model
    def apply_trucalc_default_digest_branding(self):
        """Rename only the upstream default digest, preserving its configuration."""
        digest = self.env.ref("digest.digest_digest_default", raise_if_not_found=False)
        if not digest:
            return True
        digest = digest.sudo()
        translations = digest._fields["name"]._get_stored_translations(digest) or {}
        branded = {
            lang: value.replace("Odoo", "TruCalc")
            for lang, value in translations.items()
        }
        if branded != translations:
            digest.update_field_translations("name", branded)
        return True
