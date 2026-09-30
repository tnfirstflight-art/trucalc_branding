from odoo import api, models


class Digest(models.Model):
    _inherit = "digest.digest"

    @api.model
    def apply_trucalc_default_digest_branding(self):
        """Brand upstream digest data that has no safe QWeb inheritance point."""
        layout = self.env.ref("digest.digest_mail_layout", raise_if_not_found=False)
        if layout:
            layout = layout.sudo().with_context(lang="en_US")
            if "#714B67" in layout.arch_db:
                layout.arch_db = layout.arch_db.replace("#714B67", "#022f5b")

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
