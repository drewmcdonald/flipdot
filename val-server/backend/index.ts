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
import { AVAILABLE_FONTS, DEFAULT_FONT } from "./rendering/font-loader.ts";
import { PatternStorage } from "./patterns/content.ts";
import type { PatternConfig, TransitionConfig } from "./patterns/types.ts";
import { createBlankFrame, renderTransition } from "./patterns/render.ts";
import type { Content } from "../shared/types.ts";
import { serveFile } from "https://esm.town/v/std/utils@85-main/index.ts";

// Initialize Hono app
const app = new Hono<{ Variables: { authenticated: boolean } }>();

// Initialize content router
const router = new ContentRouter();

// Initialize pattern storage
const patternStorage = new PatternStorage();

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

    // Calculate optimal poll interval based on next expiration
    const poll_interval_ms = router.getOptimalPollInterval(
      DEFAULT_POLL_INTERVAL_MS,
    );

    if (playlist.length === 0) {
      // No content available - return "clear" status
      const response: ContentResponse = {
        status: "clear",
        playlist: [],
        poll_interval_ms: DEFAULT_POLL_INTERVAL_MS, // Use default when no content
      };
      return c.json(response);
    }

    // Return complete playlist with dynamic poll interval
    const response: ContentResponse = {
      status: "updated",
      playlist: playlist,
      poll_interval_ms: poll_interval_ms, // Tell driver when to check back
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

    // Validate font if provided
    if (body.font && !AVAILABLE_FONTS.includes(body.font)) {
      return c.json(
        {
          error: `Invalid font. Available fonts: ${AVAILABLE_FONTS.join(", ")}`,
        },
        400,
      );
    }

    // Create custom text source with provided options
    const ttl_ms = body.ttl_ms ?? 60000; // Default 1 minute
    const options: CustomTextOptions = {
      text: body.text.toUpperCase(),
      priority: body.priority ?? 20, // Default higher than clock
      ttl_ms: ttl_ms,
      interruptible: body.interruptible ?? true,
      scroll: body.scroll ?? false,
      frame_delay_ms: body.frame_delay_ms ?? 100,
      font: body.font ?? DEFAULT_FONT,
    };

    // Validate priority range
    if (options.priority! < 0 || options.priority! > 99) {
      return c.json({ error: "Priority must be between 0 and 99" }, 400);
    }

    // Validate TTL range
    if (ttl_ms < 1000 || ttl_ms > 3600000) {
      return c.json(
        { error: "TTL must be between 1000ms and 3600000ms" },
        400,
      );
    }

    // Create and register the source
    // Set expiration time = now + ttl_ms
    const expires_at = Date.now() + ttl_ms;
    const source = createCustomTextSource(options, expires_at);
    router.registerSource(source);

    return c.json({
      success: true,
      message: "Text message registered",
      source_id: source.id,
      type: source.type,
      priority: source.priority,
      ttl_ms: source.ttl_ms,
      font: options.font,
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
 * POST /api/flipdot/pattern
 * Submit a pattern animation
 */
app.post("/api/flipdot/pattern", bearerAuthMiddleware, async (c) => {
  try {
    const body = await c.req.json();

    // Validate pattern type
    if (!body.type || typeof body.type !== "string") {
      return c.json({ error: "Missing or invalid 'type' field" }, 400);
    }

    // Valid pattern types
    const validTypes = [
      "wave",
      "rain",
      "spiral",
      "checkerboard",
      "random",
      "expand",
      "gameoflife",
      "matrix",
      "sparkle",
      "pulse",
      "scan",
      "fire",
      "snake",
    ];

    if (!validTypes.includes(body.type)) {
      return c.json({
        error: `Invalid pattern type. Valid types: ${validTypes.join(", ")}`,
      }, 400);
    }

    // Build pattern config
    const config: PatternConfig = {
      type: body.type,
      duration_ms: body.duration_ms ?? 3000,
      frame_delay_ms: body.frame_delay_ms ?? 100,
      options: body.options ?? {},
    };

    // Validate durations
    if (config.duration_ms! < 100 || config.duration_ms! > 60000) {
      return c.json(
        { error: "duration_ms must be between 100ms and 60000ms" },
        400,
      );
    }

    if (config.frame_delay_ms! < 20 || config.frame_delay_ms! > 1000) {
      return c.json(
        { error: "frame_delay_ms must be between 20ms and 1000ms" },
        400,
      );
    }

    // Create pattern source
    const priority = body.priority ?? 15;
    const ttl_ms = body.ttl_ms ?? 30000;
    const interruptible = body.interruptible ?? true;

    // Validate priority range
    if (priority < 0 || priority > 99) {
      return c.json({ error: "Priority must be between 0 and 99" }, 400);
    }

    // Validate TTL range
    if (ttl_ms < 1000 || ttl_ms > 3600000) {
      return c.json(
        { error: "TTL must be between 1000ms and 3600000ms" },
        400,
      );
    }

    const source = patternStorage.set(config, {
      priority,
      ttl_ms,
      interruptible,
    });
    router.registerSource(source);

    return c.json({
      success: true,
      message: "Pattern registered",
      source_id: source.id,
      type: source.type,
      pattern_type: config.type,
      priority: source.priority,
      ttl_ms: source.ttl_ms,
      expires_at: new Date(Date.now() + source.ttl_ms).toISOString(),
    });
  } catch (error) {
    console.error("Error handling pattern submission:", error);
    return c.json({ error: "Internal server error" }, 500);
  }
});

/**
 * POST /api/flipdot/pattern/clear
 * Clear all patterns
 */
app.post("/api/flipdot/pattern/clear", bearerAuthMiddleware, (c) => {
  try {
    // Get all pattern sources
    const sources = router.getSources();
    const patternSources = sources.filter((s) => s.type === "pattern");

    // Clear each pattern source
    for (const source of patternSources) {
      router.unregisterSource(source.id);
    }

    // Clear pattern storage
    patternStorage.clear();

    return c.json({
      success: true,
      message: "All patterns cleared",
      cleared_count: patternSources.length,
    });
  } catch (error) {
    console.error("Error clearing patterns:", error);
    return c.json({ error: "Internal server error" }, 500);
  }
});

/**
 * GET /api/flipdot/patterns/list
 * List available pattern types
 */
app.get("/api/flipdot/patterns/list", bearerAuthMiddleware, (c) => {
  const patterns = [
    {
      type: "wave",
      description: "Horizontal or vertical sine wave",
      options: {
        vertical: "boolean",
        amplitude: "number",
        frequency: "number",
        speed: "number",
      },
    },
    {
      type: "rain",
      description: "Falling dots",
      options: { density: "number (0-1)", speed: "number" },
    },
    {
      type: "spiral",
      description: "Spiral from center",
      options: { speed: "number", arms: "number" },
    },
    {
      type: "checkerboard",
      description: "Animated checkerboard",
      options: { size: "number" },
    },
    {
      type: "random",
      description: "Random noise",
      options: { density: "number (0-1)" },
    },
    {
      type: "expand",
      description: "Expanding circles or squares",
      options: { speed: "number", shape: "'circle' | 'square'" },
    },
    {
      type: "gameoflife",
      description: "Conway's Game of Life",
      options: { density: "number (0-1)", seed: "number" },
    },
    {
      type: "matrix",
      description: "Matrix-style falling characters",
      options: { density: "number (0-1)", speed: "number" },
    },
    {
      type: "sparkle",
      description: "Random sparkles",
      options: { density: "number (0-1)" },
    },
    {
      type: "pulse",
      description: "Pulsing effect from center",
      options: { speed: "number" },
    },
    {
      type: "scan",
      description: "Scanner effect (back and forth)",
      options: { vertical: "boolean", speed: "number" },
    },
    {
      type: "fire",
      description: "Fire effect from bottom",
      options: { intensity: "number (0-1)" },
    },
    {
      type: "snake",
      description: "Snake/worm moving around",
      options: { length: "number", speed: "number" },
    },
  ];

  return c.json({
    patterns,
    active_patterns: patternStorage.size,
  });
});

/**
 * GET /api/flipdot/transitions/list
 * List available transition types
 */
app.get("/api/flipdot/transitions/list", bearerAuthMiddleware, (c) => {
  const transitions = [
    {
      type: "wipe",
      description: "Wipe from one direction",
      options: { direction: "'left' | 'right' | 'up' | 'down'" },
    },
    { type: "fade", description: "Dithered fade for binary display" },
    {
      type: "dissolve",
      description: "Random pixel dissolve",
      options: { seed: "number" },
    },
    {
      type: "slide",
      description: "Slide in from direction",
      options: { direction: "'left' | 'right' | 'up' | 'down'" },
    },
    {
      type: "checkerboard",
      description: "Checkerboard pattern reveal",
      options: { size: "number" },
    },
    {
      type: "blinds",
      description: "Venetian blinds effect",
      options: { vertical: "boolean", blindSize: "number" },
    },
    { type: "center_out", description: "Expand from center" },
    { type: "corners", description: "Reveal from corners" },
    { type: "spiral", description: "Spiral transition from center" },
  ];

  return c.json({
    transitions,
  });
});

/**
 * POST /api/flipdot/transition
 * Create a transition animation between two states
 * This can be used as a standalone content item or to preview transitions
 */
app.post("/api/flipdot/transition", bearerAuthMiddleware, async (c) => {
  try {
    const body = await c.req.json();

    // Validate transition type
    if (!body.type || typeof body.type !== "string") {
      return c.json({ error: "Missing or invalid 'type' field" }, 400);
    }

    // Valid transition types
    const validTypes = [
      "wipe",
      "fade",
      "dissolve",
      "slide",
      "checkerboard",
      "blinds",
      "center_out",
      "corners",
      "spiral",
    ];

    if (!validTypes.includes(body.type)) {
      return c.json({
        error: `Invalid transition type. Valid types: ${validTypes.join(", ")}`,
      }, 400);
    }

    // Build transition config
    const config: TransitionConfig = {
      type: body.type,
      duration_ms: body.duration_ms ?? 1000,
      frame_delay_ms: body.frame_delay_ms ?? 50,
      direction: body.direction,
    };

    // Validate durations
    if (config.duration_ms! < 100 || config.duration_ms! > 10000) {
      return c.json(
        { error: "duration_ms must be between 100ms and 10000ms" },
        400,
      );
    }

    if (config.frame_delay_ms! < 20 || config.frame_delay_ms! > 500) {
      return c.json(
        { error: "frame_delay_ms must be between 20ms and 500ms" },
        400,
      );
    }

    // For now, create a transition from blank to filled
    // In the future, could accept fromFrame and toFrame in the request
    const fromFrame = createBlankFrame();
    const toFrame = createBlankFrame();

    // Create a simple pattern for toFrame (all on)
    const bits = new Array(28 * 14).fill(1);
    const packed = new Uint8Array(Math.ceil(bits.length / 8));
    for (let i = 0; i < bits.length; i++) {
      if (bits[i]) {
        const byteIndex = Math.floor(i / 8);
        const bitIndex = i % 8;
        packed[byteIndex] |= 1 << bitIndex;
      }
    }
    toFrame.data_b64 = btoa(String.fromCharCode(...packed));

    const result = renderTransition(fromFrame, toFrame, config);

    // Return as a content response (not registered as a source)
    const content: Content = {
      content_id: `transition:${config.type}:${Date.now()}`,
      frames: result.frames,
      playback: {
        loop: false,
      },
      metadata: {
        type: "transition",
        transition_type: config.type,
        config,
      },
    };

    return c.json({
      success: true,
      message: "Transition animation created",
      content,
      frame_count: result.frames.length,
    });
  } catch (error) {
    console.error("Error handling transition request:", error);
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
 * GET /api/flipdot/fonts
 * List available fonts (no auth required)
 */
app.get("/api/flipdot/fonts", (c) => {
  return c.json({
    default: DEFAULT_FONT,
    available: AVAILABLE_FONTS,
  });
});

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
      version: "2.1",
      endpoints: [
        {
          path: "/api/flipdot/content",
          method: "GET",
          auth: "required",
          description: "Get current content playlist",
        },
        {
          path: "/api/flipdot/text",
          method: "POST",
          auth: "required",
          description: "Submit text message",
        },
        {
          path: "/api/flipdot/clear",
          method: "POST",
          auth: "required",
          description: "Clear all custom content",
        },
        {
          path: "/api/flipdot/pattern",
          method: "POST",
          auth: "required",
          description: "Submit pattern animation",
        },
        {
          path: "/api/flipdot/pattern/clear",
          method: "POST",
          auth: "required",
          description: "Clear all patterns",
        },
        {
          path: "/api/flipdot/patterns/list",
          method: "GET",
          auth: "required",
          description: "List available patterns",
        },
        {
          path: "/api/flipdot/transition",
          method: "POST",
          auth: "required",
          description: "Create transition animation",
        },
        {
          path: "/api/flipdot/transitions/list",
          method: "GET",
          auth: "required",
          description: "List available transitions",
        },
        {
          path: "/health",
          method: "GET",
          auth: "none",
          description: "Health check",
        },
      ],
    });
  }
});

// Export Hono app for Val Town
export default app;
