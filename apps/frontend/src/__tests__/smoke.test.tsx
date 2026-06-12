/**
 * Smoke test — verifies the Vitest + jsdom harness is wired correctly.
 * Does NOT render the full app (that requires a running backend).
 * Real component tests will be added in 3.x.
 */
import { describe, it, expect } from "vitest";

describe("Frontend test harness", () => {
    it("vitest + jsdom can run a basic assertion", () => {
        expect(1 + 1).toBe(2);
    });

    it("document is available in jsdom", () => {
        expect(document).toBeDefined();
        expect(document.createElement("div")).toBeTruthy();
    });
});
