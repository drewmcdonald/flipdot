/**
 * Compositor: reads display_config + content_sources, picks the active source,
 * and writes to the displays table. Runs on a cron.
 */

import { internalMutation } from "./_generated/server";
import { getActiveRotationSource, getActiveOverride } from "./lib/rotation";

/** Main compositor: picks active source and writes to displays */
export const compose = internalMutation({
  args: {},
  handler: async (ctx) => {
    // 1. Read display config for "main"
    const config = await ctx.db
      .query("display_config")
      .withIndex("by_display_name", (q) => q.eq("display_name", "main"))
      .first();

    if (!config) {
      // Auto-seed default config
      await ctx.db.insert("display_config", {
        display_name: "main",
        rotation: [{ source_id: "clock", duration_s: 60 }],
        overrides: [],
      });
      return;
    }

    // 2. Gather all content sources
    const allSources = await ctx.db.query("content_sources").collect();
    const sourceMap = new Map(allSources.map((s) => [s.source_id, s]));
    const availableSourceIds = new Set(sourceMap.keys());

    // 3. Check for active overrides (highest priority wins)
    let activeSourceId = getActiveOverride(
      config.overrides,
      availableSourceIds
    );

    // 4. If no override, calculate rotation position
    if (!activeSourceId) {
      activeSourceId = getActiveRotationSource(config.rotation, Date.now());
    }

    if (!activeSourceId) return;

    // 5. Get the source content
    const source = sourceMap.get(activeSourceId);
    if (!source) {
      // Source is in rotation but hasn't written content yet — skip
      return;
    }

    // 6. Compare with current display content — skip write if unchanged
    const currentDisplay = await ctx.db
      .query("displays")
      .withIndex("by_name", (q) => q.eq("name", "main"))
      .first();

    if (currentDisplay?.content.content_id === source.content.content_id) {
      // Content hasn't changed — no need to write
      return;
    }

    // 7. Write to displays table
    const now = Date.now();
    if (currentDisplay) {
      await ctx.db.patch(currentDisplay._id, {
        content: source.content,
        updatedAt: now,
      });
    } else {
      await ctx.db.insert("displays", {
        name: "main",
        content: source.content,
        updatedAt: now,
      });
    }
  },
});
