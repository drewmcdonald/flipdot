import { httpRouter } from "convex/server";
import { httpAction } from "./_generated/server";
import { auth } from "./auth";
import { staticAssets } from "./staticAssets.generated";

const http = httpRouter();

auth.addHttpRoutes(http);

/**
 * Serves the built web app (React virtual display + control panel) directly
 * from this Convex deployment's HTTP Actions, so there's no separate static
 * host. Asset content is embedded at build time by
 * scripts/generate-static-assets.mjs into staticAssets.generated.ts.
 */
function serveStaticAsset(path: string): Response {
  const asset = staticAssets[path];
  if (!asset) {
    return new Response("Not found", { status: 404 });
  }
  const bytes = Uint8Array.from(atob(asset.base64), (c) => c.charCodeAt(0));
  return new Response(bytes, {
    headers: {
      "Content-Type": asset.contentType,
      // Vite content-hashes files under /assets/, so those are safe to cache
      // forever; index.html (and anything else) must always be revalidated.
      "Cache-Control": path.startsWith("/assets/")
        ? "public, max-age=31536000, immutable"
        : "no-cache",
    },
  });
}

http.route({
  path: "/",
  method: "GET",
  handler: httpAction(async () => serveStaticAsset("/index.html")),
});

http.route({
  pathPrefix: "/assets/",
  method: "GET",
  handler: httpAction(async (_ctx, request) => {
    const { pathname } = new URL(request.url);
    return serveStaticAsset(pathname);
  }),
});

http.route({
  path: "/vite.svg",
  method: "GET",
  handler: httpAction(async () => serveStaticAsset("/vite.svg")),
});

export default http;
