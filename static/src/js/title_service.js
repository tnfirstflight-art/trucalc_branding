import { titleService } from "@web/core/browser/title_service";
import { patch } from "@web/core/utils/patch";

const ODOO_FALLBACK_TITLE = /^(\(\d+\) )?Odoo$/;

patch(titleService, {
    start() {
        const service = super.start(...arguments);
        const setParts = service.setParts;
        const setCounters = service.setCounters;

        function applyTruCalcFallback() {
            if (ODOO_FALLBACK_TITLE.test(service.current)) {
                document.title = service.current.replace(/Odoo$/, "TruCalc");
            }
        }

        service.setParts = (parts) => {
            setParts(parts);
            applyTruCalcFallback();
        };
        service.setCounters = (counters) => {
            setCounters(counters);
            applyTruCalcFallback();
        };
        applyTruCalcFallback();
        return service;
    },
});
