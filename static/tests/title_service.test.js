import { beforeEach, describe, expect, test } from "@odoo/hoot";
import { getService, makeMockEnv } from "@web/../tests/web_test_helpers";

import "@trucalc_branding/js/title_service";

describe.current.tags("headless");

let title;

beforeEach(async () => {
    document.title = "TruCalc";
    await makeMockEnv();
    title = getService("title");
});

test("uses the TruCalc fallback when all title parts are cleared", () => {
    title.setParts({ action: "Orders" });
    expect(title.current).toBe("Orders");
    title.setParts({ action: null });
    expect(title.current).toBe("TruCalc");
});

test("preserves specific title parts", () => {
    title.setParts({ app: "Orders", view: "Open" });
    expect(title.current).toBe("Orders - Open");
});

test("preserves counters with the TruCalc fallback", () => {
    title.setCounters({ notifications: 2 });
    expect(title.current).toBe("(2) TruCalc");
});
