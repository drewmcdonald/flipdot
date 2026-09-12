/// <reference types="vite/client" />
import { describe, it, expect, vi } from "vitest";
import { convexTest } from "convex-test";
import schema from "./schema";

vi.mock("./staticAssets.generated", () => ({
  staticAssets: {
    "/index.html": {
      contentType: "text/html; charset=utf-8",
      base64: Buffer.from("<html>flipdot</html>").toString("base64"),
    },
    "/assets/index-abc123.js": {
      contentType: "text/javascript; charset=utf-8",
      base64: Buffer.from("console.log('hi')").toString("base64"),
    },
  },
}));

const modules = import.meta.glob("./**/*.ts");

describe("http static asset serving", () => {
  it("serves index.html at /", async () => {
    const t = convexTest(schema, modules);
    const response = await t.fetch("/");
    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toBe("text/html; charset=utf-8");
    expect(response.headers.get("Cache-Control")).toBe("no-cache");
    expect(await response.text()).toBe("<html>flipdot</html>");
  });

  it("serves hashed files under /assets/ with an immutable cache header", async () => {
    const t = convexTest(schema, modules);
    const response = await t.fetch("/assets/index-abc123.js");
    expect(response.status).toBe(200);
    expect(response.headers.get("Content-Type")).toBe(
      "text/javascript; charset=utf-8"
    );
    expect(response.headers.get("Cache-Control")).toBe(
      "public, max-age=31536000, immutable"
    );
    expect(await response.text()).toBe("console.log('hi')");
  });

  it("404s for unknown assets", async () => {
    const t = convexTest(schema, modules);
    const response = await t.fetch("/assets/does-not-exist.js");
    expect(response.status).toBe(404);
  });
});
