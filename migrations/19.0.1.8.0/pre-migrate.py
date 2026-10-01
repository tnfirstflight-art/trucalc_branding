from odoo.addons.trucalc_branding.hooks import migrate_main_company_email_color


def migrate(cr, version):
    migrate_main_company_email_color(cr)
