import { MessagingMenu } from "@mail/core/public_web/messaging_menu";
import { browser } from "@web/core/browser/browser";
import { InstallScopedApp } from "@web/core/install_scoped_app/install_scoped_app";
import { click } from "@odoo/hoot-dom";
import { beforeEach, describe, expect, test } from "@odoo/hoot";
import { animationFrame } from "@odoo/hoot-mock";
import { Component, xml } from "@odoo/owl";
import {
    makeMockEnv,
    mountWithCleanup,
    onRpc,
    patchWithCleanup,
} from "@web/../tests/web_test_helpers";

import "@trucalc_branding/js/messaging_branding";

describe.current.tags("headless");

beforeEach(async () => {
    await makeMockEnv();
    const manifestLink = document.createElement("link");
    manifestLink.rel = "manifest";
    manifestLink.href = "/web/manifest.scoped_app_manifest";
    document.head.append(manifestLink);
});

test("install UI uses TruCalc attribution and preserves install callback", async () => {
    const beforeInstallPromptEvent = new CustomEvent("beforeinstallprompt");
    beforeInstallPromptEvent.preventDefault = () => {};
    beforeInstallPromptEvent.prompt = async () => {
        expect.step("install prompted");
        return { outcome: "accepted" };
    };
    browser.BeforeInstallPromptEvent = beforeInstallPromptEvent;
    patchWithCleanup(browser.location, {
        replace(url) {
            expect.step(`opened:${url}`);
        },
    });
    onRpc("/*", () => ({
        icons: [{ src: "/trucalc_branding/static/src/img/trucalc-icon-192x192.png" }],
        name: "TruCalc",
        scope: "/odoo",
        start_url: "/odoo",
    }));

    class Parent extends Component {
        static components = { InstallScopedApp };
        static props = ["*"];
        static template = xml`<InstallScopedApp/>`;
    }

    await mountWithCleanup(Parent);
    await animationFrame();
    expect(".o_install_scoped_app h1").toHaveText("TruCalc");
    expect(".o_install_scoped_app span.text-primary").toHaveText("TruCalc");
    expect(".o_install_scoped_app").not.toHaveText(/Odoo S\.A\./);
    browser.dispatchEvent(beforeInstallPromptEvent);
    await animationFrame();
    expect("button.btn-primary").toHaveText("Install");
    await click("button.btn-primary");
    await animationFrame();
    expect.verifySteps(["install prompted", "opened:/odoo"]);
});

test("Discuss PWA prompt uses TruCalc text and preserves its action", () => {
    const menu = Object.create(MessagingMenu.prototype);
    menu.pwa = {
        canPromptToInstall: true,
        show() {
            expect.step("install action");
        },
    };
    menu.store = {
        discuss: { activeTab: "notification" },
        odoobot: { avatarUrl: "/avatar.png" },
    };

    const request = menu.installationRequest;
    expect(String(request.displayName)).toBe("Install TruCalc");
    expect(String(request.body)).toBe("Come here often? Install the app for quick and easy access!");
    expect(request.isShown).toBe(true);
    request.onClick();
    expect.verifySteps(["install action"]);
});
