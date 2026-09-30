import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

const sessionExpired = {
    title: _t("Session Expired"),
    message: _t("Your session has expired. Please sign in again."),
    buttons: [
        {
            text: _t("Ok"),
            click: () => window.location.reload(true),
            close: true,
        },
    ],
};

registry
    .category("error_notifications")
    .add("odoo.http.SessionExpiredException", sessionExpired, { force: true })
    .add("werkzeug.exceptions.Forbidden", sessionExpired, { force: true });
