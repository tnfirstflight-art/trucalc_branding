from odoo import api, models


class MailTemplate(models.Model):
    _inherit = "mail.template"

    _TRUCALC_AUTH_TEMPLATE_XMLIDS = (
        "auth_signup.set_password_email",
        "auth_signup.mail_template_user_signup_account_created",
        "auth_signup.portal_set_password_email",
    )

    @api.model
    def apply_trucalc_auth_mail_branding(self):
        """Debrand stock noupdate auth templates once per addon install/upgrade."""
        for xmlid in self._TRUCALC_AUTH_TEMPLATE_XMLIDS:
            template = self.env.ref(xmlid, raise_if_not_found=False)
            if not template:
                continue
            template = template.sudo()
            body_translations = (
                template._fields["body_html"]._get_stored_translations(template) or {}
            )
            branded_bodies = {
                lang: self._trucalc_brand_auth_body(xmlid, body)
                for lang, body in body_translations.items()
            }
            if branded_bodies != body_translations:
                template.update_field_translations("body_html", branded_bodies)

            if xmlid == "auth_signup.set_password_email":
                subject_translations = (
                    template._fields["subject"]._get_stored_translations(template) or {}
                )
                branded_subjects = {
                    lang: subject.replace("Odoo", "TruCalc")
                    for lang, subject in subject_translations.items()
                }
                if branded_subjects != subject_translations:
                    template.update_field_translations("subject", branded_subjects)
        return True

    @api.model
    def _trucalc_brand_auth_body(self, xmlid, body):
        branded = body.replace("#875A7B", "#022f5b")
        branded = self._trucalc_remove_powered_by_block(branded)
        if xmlid != "auth_signup.set_password_email":
            return branded

        branded = branded.replace("Welcome to Odoo", "Welcome to TruCalc")
        branded = branded.replace(">OdooBot</t>", ">Administrator</t>")
        branded = branded.replace("to connect on Odoo.", "to connect to TruCalc.")
        branded = branded.replace(
            "Your Odoo domain is:", "Your TruCalc sign-in site is:"
        )
        branded = branded.replace(
            ">http://yourcompany.odoo.com</a>", ">https://example.com</a>"
        )
        promo_start = branded.find("Never heard of Odoo?")
        promo_end = branded.find("Enjoy Odoo!", promo_start)
        if promo_start >= 0 and promo_end >= 0:
            branded = (
                branded[:promo_start]
                + "Welcome to TruCalc!"
                + branded[promo_end + len("Enjoy Odoo!") :]
            )
        return branded

    @api.model
    def _trucalc_remove_powered_by_block(self, body):
        marker = "<!-- POWERED BY -->"
        marker_at = body.rfind(marker)
        outer_table_close = body.rfind("</table>")
        if marker_at >= 0 and outer_table_close > marker_at:
            return body[:marker_at] + body[outer_table_close:]
        return body
