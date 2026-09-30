import { browser } from "@web/core/browser/browser";
import {
    ClientErrorDialog,
    ErrorDialog,
    NetworkErrorDialog,
    RedirectWarningDialog,
    RPCErrorDialog,
    SessionExpiredDialog,
    WarningDialog,
} from "@web/core/errors/error_dialogs";
import { registry } from "@web/core/registry";
import { defineMailModels } from "@mail/../tests/mail_test_helpers";
import { click, queryAllTexts } from "@odoo/hoot-dom";
import { beforeEach, describe, expect, test } from "@odoo/hoot";
import { animationFrame } from "@odoo/hoot-mock";
import {
    makeMockEnv,
    mockService,
    mountWithCleanup,
    patchWithCleanup,
} from "@web/../tests/web_test_helpers";

import "@trucalc_branding/js/error_dialogs";
import "@trucalc_branding/js/public_error_notifications";
import "@trucalc_branding/js/user_menu_items";

describe.current.tags("headless");

defineMailModels();

let env;

beforeEach(async () => {
    env = await makeMockEnv({
        dialogData: {
            close: () => {},
            isActive: true,
            scrollToOrigin: () => {},
        },
    });
});

test("removes only the Odoo support and account user-menu entries", () => {
    const userMenuItems = registry.category("user_menuitems");

    expect(userMenuItems.contains("support")).toBe(false);
    expect(userMenuItems.contains("odoo_account")).toBe(false);
    expect(userMenuItems.contains("shortcuts")).toBe(true);
    expect(userMenuItems.contains("separator")).toBe(true);
    expect(userMenuItems.contains("preferences")).toBe(true);
    expect(userMenuItems.contains("install_pwa")).toBe(true);
    expect(userMenuItems.contains("log_out")).toBe(true);
});

test("uses neutral generic, client, and network error titles", () => {
    expect(String(ErrorDialog.title)).toBe("Error");
    expect(String(ClientErrorDialog.title)).toBe("Client Error");
    expect(String(NetworkErrorDialog.title)).toBe("Network Error");
});

test("uses a neutral RPC fallback while preserving error details", async () => {
    await mountWithCleanup(RPCErrorDialog, {
        env,
        props: {
            type: "server",
            name: "SERVER_FAILURE",
            message: "The operation failed",
            traceback: "client traceback",
            data: { debug: "server traceback" },
            close() {},
        },
    });

    await click("main button");
    await animationFrame();
    expect("main .o_error_detail b").toHaveText("Server Error");
    expect("main .o_error_detail code").toHaveText("SERVER_FAILURE");
    expect("main .o_error_detail pre").toHaveText(
        "server traceback\nThe above server error caused the following client error:\nclient traceback"
    );
    expect(queryAllTexts("footer button")).toEqual(["Close"]);
});

test("neutralizes only the default warning title", async () => {
    await mountWithCleanup(WarningDialog, {
        env,
        props: {
            message: "A generic warning",
            close() {},
        },
    });
    expect("header .modal-title").toHaveText("Warning");
    expect("main").toHaveText("A generic warning");
    expect("footer button").toHaveText("Close");
});

test("preserves specific warning titles", async () => {
    await mountWithCleanup(WarningDialog, {
        env,
        props: {
            exceptionName: "odoo.exceptions.ValidationError",
            message: "A validation warning",
            close() {},
        },
    });
    expect("header .modal-title").toHaveText("Validation Error");
    expect("main").toHaveText("A validation warning");
});

test("preserves redirect-warning action behavior with a neutral fallback title", async () => {
    mockService("action", {
        doAction(actionId, options) {
            expect.step(`action:${actionId}:${options.forceLeave}`);
        },
    });
    await mountWithCleanup(RedirectWarningDialog, {
        env,
        props: {
            data: { arguments: ["Continue to settings", "settings_action", "Open settings"] },
            close() {
                expect.step("closed");
            },
        },
    });

    expect("header .modal-title").toHaveText("Warning");
    expect("main").toHaveText("Continue to settings");
    expect(queryAllTexts("footer button")).toEqual(["Open settings", "Close"]);
    await click("footer button:first-child");
    await animationFrame();
    expect.verifySteps(["action:settings_action:true", "closed"]);
});

test("uses neutral internal session-expired copy and preserves reload behavior", async () => {
    patchWithCleanup(browser.location, {
        reload() {
            expect.step("reloaded");
        },
    });
    await mountWithCleanup(SessionExpiredDialog, { env, props: { close() {} } });

    expect("header .modal-title").toHaveText("Session Expired");
    expect("main p").toHaveText("Your session has expired. Please sign in again.");
    expect("footer button").toHaveText("Close");
    await click("footer button");
    await animationFrame();
    expect.verifySteps(["reloaded"]);
});

test("uses neutral public session-expired notifications and preserves actions", () => {
    const errorNotifications = registry.category("error_notifications");
    for (const key of ["odoo.http.SessionExpiredException", "werkzeug.exceptions.Forbidden"]) {
        const notification = errorNotifications.get(key);
        expect(String(notification.title)).toBe("Session Expired");
        expect(String(notification.message)).toBe("Your session has expired. Please sign in again.");
        expect(notification.buttons).toHaveLength(1);
        expect(String(notification.buttons[0].text)).toBe("Ok");
        expect(notification.buttons[0].click).toBeOfType("function");
        expect(notification.buttons[0].close).toBe(true);
    }
});
