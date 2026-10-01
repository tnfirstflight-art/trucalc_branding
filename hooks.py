LEGACY_ODOO_PURPLE = "#875A7B"
TRUCALC_BLUE = "#022f5b"


def _main_company(cr):
    cr.execute(
        """
        SELECT data.id, data.res_id, company.email_secondary_color
          FROM ir_model_data data
          JOIN res_company company ON company.id = data.res_id
         WHERE data.module = 'base'
           AND data.name = 'main_company'
           AND data.model = 'res.company'
        """
    )
    rows = cr.fetchall()
    if len(rows) != 1:
        raise RuntimeError(
            "TruCalc company email color migration aborted: "
            "base.main_company is missing or ambiguous"
        )
    return rows[0]


def migrate_main_company_email_color(cr):
    external_id, company_id, current_color = _main_company(cr)
    if current_color not in (None, "", LEGACY_ODOO_PURPLE, TRUCALC_BLUE):
        raise RuntimeError(
            "TruCalc company email color migration aborted: "
            "base.main_company has unexpected email_secondary_color %r"
            % current_color
        )

    if current_color != TRUCALC_BLUE:
        cr.execute(
            """
            UPDATE res_company
               SET email_secondary_color = %s
             WHERE id = %s
               AND email_secondary_color IS NOT DISTINCT FROM %s
            """,
            (TRUCALC_BLUE, company_id, current_color),
        )
        if cr.rowcount != 1:
            raise RuntimeError(
                "TruCalc company email color migration aborted: "
                "base.main_company changed concurrently"
            )

    verified_external_id, verified_company_id, verified_color = _main_company(cr)
    if (
        verified_external_id != external_id
        or verified_company_id != company_id
        or verified_color != TRUCALC_BLUE
    ):
        raise RuntimeError(
            "TruCalc company email color migration aborted: "
            "target identity or color verification failed"
        )


def post_init_hook(env):
    migrate_main_company_email_color(env.cr)
