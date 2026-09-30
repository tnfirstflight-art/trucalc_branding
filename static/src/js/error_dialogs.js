import {
    ClientErrorDialog,
    ErrorDialog,
    NetworkErrorDialog,
    RedirectWarningDialog,
    RPCErrorDialog,
    WarningDialog,
} from "@web/core/errors/error_dialogs";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

function neutralizeTitle(title, brandedTitle, neutralTitle) {
    return String(title) === String(brandedTitle) ? neutralTitle : title;
}

patch(ErrorDialog, {
    title: _t("Error"),
});

patch(ClientErrorDialog, {
    title: _t("Client Error"),
});

patch(NetworkErrorDialog, {
    title: _t("Network Error"),
});

patch(RPCErrorDialog.prototype, {
    inferTitle() {
        super.inferTitle(...arguments);
        this.title = neutralizeTitle(this.title, _t("Odoo Server Error"), _t("Server Error"));
        this.title = neutralizeTitle(this.title, _t("Odoo Client Error"), _t("Client Error"));
        this.title = neutralizeTitle(this.title, _t("Odoo Network Error"), _t("Network Error"));
    },
});

patch(WarningDialog.prototype, {
    inferTitle() {
        const title = super.inferTitle(...arguments);
        return neutralizeTitle(title, _t("Odoo Warning"), _t("Warning"));
    },
});

patch(RedirectWarningDialog.prototype, {
    setup() {
        super.setup(...arguments);
        this.title = neutralizeTitle(this.title, _t("Odoo Warning"), _t("Warning"));
    },
});
