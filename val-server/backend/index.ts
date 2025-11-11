/**
 * FlipDot Content Server
 * Main HTTP endpoint implementing CONTENT_SERVER_SPEC.md v2.0
 */

import { Context, Hono } from "npm:hono";
import type { ContentResponse } from "../shared/types.ts";
import {
  authHandlers,
  bearerAuthMiddleware,
  optionalAuthMiddleware,
} from "./auth.ts";
import { ContentRouter } from "./content/router.ts";
import { createClockSource } from "./content/clock.ts";
import {
  createCustomTextSource,
  type CustomTextOptions,
} from "./content/text.ts";
import { serveFile } from "https://esm.town/v/std/utils@85-main/index.ts";

// Initialize Hono app
const app = new Hono<{ Variables: { authenticated: boolean } }>();

// Initialize content router
const router = new ContentRouter();

// Register default content sources
router.registerSource(createClockSource());

// Default polling interval (30 seconds)
const DEFAULT_POLL_INTERVAL_MS = 30000;

/**
 * GET /api/flipdot/content
 * Main polling endpoint - returns complete playlist
 */
app.get("/api/flipdot/content", bearerAuthMiddleware, async (c) => {
  try {
    // Generate playlist from all sources (ordered by priority)
    const playlist = await router.generatePlaylist();

    if (playlist.length === 0) {
      // No content available - return "clear" status
      const response: ContentResponse = {
        status: "clear",
        playlist: [],
        poll_interval_ms: DEFAULT_POLL_INTERVAL_MS,
      };
      return c.json(response);
    }

    // Return complete playlist
    const response: ContentResponse = {
      status: "updated",
      playlist: playlist,
      poll_interval_ms: DEFAULT_POLL_INTERVAL_MS,
    };

    return c.json(response);
  } catch (error) {
    console.error("Error handling content request:", error);
    return c.json({ error: "Internal server error" }, 500);
  }
});

/**
 * POST /api/flipdot/text
 * Submit custom text message
 */
app.post("/api/flipdot/text", bearerAuthMiddleware, async (c) => {
  try {
    const body = await c.req.json();

    // Validate input
    if (!body.text || typeof body.text !== "string") {
      return c.json({ error: "Missing or invalid 'text' field" }, 400);
    }

    if (body.text.length === 0) {
      return c.json({ error: "Text cannot be empty" }, 400);
    }

    if (body.text.length > 50) {
      return c.json(
        { error: "Text too long (max 50 characters)" },
        400,
      );
    }

    // Create custom text source with provided options
    const options: CustomTextOptions = {
      text: body.text.toUpperCase(),
      priority: body.priority ?? 20, // Default higher than clock
      ttl_ms: body.ttl_ms ?? 60000, // Default 1 minute
      interruptible: body.interruptible ?? true,
      scroll: body.scroll ?? false,
      frame_delay_ms: body.frame_delay_ms ?? 100,
    };

    // Validate priority range
    if (options.priority! < 0 || options.priority! > 99) {
      return c.json({ error: "Priority must be between 0 and 99" }, 400);
    }

    // Validate TTL range
    if (options.ttl_ms! < 1000 || options.ttl_ms! > 3600000) {
      return c.json(
        { error: "TTL must be between 1000ms and 3600000ms" },
        400,
      );
    }

    // Create and register the source
    const source = createCustomTextSource(options);
    router.registerSource(source);

    return c.json({
      success: true,
      message: "Text message registered",
      source_id: source.id,
      type: source.type,
      priority: source.priority,
      ttl_ms: source.ttl_ms,
      expires_at: new Date(Date.now() + source.ttl_ms).toISOString(),
    });
  } catch (error) {
    console.error("Error handling text submission:", error);
    return c.json({ error: "Internal server error" }, 500);
  }
});

/**
 * POST /api/flipdot/clear
 * Clear all custom text messages (keeps clock running)
 */
app.post("/api/flipdot/clear", bearerAuthMiddleware, (c) => {
  try {
    // Get all sources except clock
    const sources = router.getSources();
    const customSources = sources.filter((s) => s.type !== "clock");

    // Clear each custom source
    for (const source of customSources) {
      router.unregisterSource(source.id);
    }

    return c.json({
      success: true,
      message: "All custom messages cleared",
      cleared_count: customSources.length,
    });
  } catch (error) {
    console.error("Error clearing messages:", error);
    return c.json({ error: "Internal server error" }, 500);
  }
});

/**
 * POST /api/auth/login
 * Login with password
 */
app.post("/api/auth/login", authHandlers.login);

/**
 * POST /api/auth/logout
 * Logout (clears auth cookie)
 */
app.post("/api/auth/logout", authHandlers.logout);

/**
 * GET /api/auth/check
 * Check if user is authenticated
 */
app.get(
  "/api/auth/check",
  optionalAuthMiddleware,
  (c) => {
    const authenticated = c.get("authenticated");
    return c.json({ authenticated: !!authenticated });
  },
);

/**
 * GET /health
 * Health check endpoint (no auth required)
 */
app.get("/health", (c) => {
  return c.json({
    status: "ok",
    timestamp: new Date().toISOString(),
    sources: router.getSources().map((s) => ({
      id: s.id,
      type: s.type,
      priority: s.priority,
    })),
  });
});

/**
 * Serve frontend and shared files (React TSX components, types, etc.)
 * Uses Val Town's serveFile utility which handles TSX transpilation
 */
app.get("/frontend/*", (c) => serveFile(c.req.path, import.meta.url));
app.get("/shared/*", (c) => serveFile(c.req.path, import.meta.url));

/**
 * GET /
 * Serve web UI
 */
app.get("/", async (c) => {
  try {
    // Read frontend HTML file
    return serveFile("/frontend/index.html", import.meta.url);
  } catch (error) {
    console.error("Error serving frontend:", error);
    // Fallback to JSON API info
    return c.json({
      name: "FlipDot Content Server",
      version: "2.0",
      endpoints: [
        { path: "/api/flipdot/content", method: "GET", auth: "required" },
        { path: "/api/flipdot/text", method: "POST", auth: "required" },
        { path: "/health", method: "GET", auth: "none" },
      ],
    });
  }
});

// Export Hono app for Val Town
export default app;
