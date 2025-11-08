#!/usr/bin/env -S deno run --allow-net --allow-read --allow-write --allow-env --allow-import

/**
 * Local development server
 * Run with: deno run --allow-net --allow-read --allow-write --allow-env --allow-import dev.ts
 * Or: chmod +x dev.ts && ./dev.ts
 */

import { load } from "https://deno.land/std@0.224.0/dotenv/mod.ts";
import app from "./backend/index.ts";

// Load .env file from parent directory
const env = await load({ envPath: "../.env", export: true });

const PORT = 8000;

// Get the fetch handler from the Hono app
const handler = app.fetch.bind(app);

console.log(`
╔═══════════════════════════════════════════════════════════════╗
║  FlipDot Content Server - Local Development                  ║
╚═══════════════════════════════════════════════════════════════╝

Server running at: http://localhost:${PORT}

Endpoints:
  GET  /                         - Server info
  GET  /health                   - Health check (no auth)
  GET  /api/flipdot/content      - Content endpoint (requires auth)

Environment:
  Storage: Local filesystem (./.local-storage/)
  Auth: Set FLIPDOT_API_KEY env variable

Test commands:
  curl http://localhost:${PORT}/health
  curl -H "X-API-Key: test" http://localhost:${PORT}/api/flipdot/content

Press Ctrl+C to stop
═══════════════════════════════════════════════════════════════
`);

// Set default API key for local dev if not set
if (!Deno.env.get("FLIPDOT_API_KEY")) {
  console.error("⚠️  No FLIPDOT_API_KEY set");
}

Deno.serve({ port: PORT }, handler);
