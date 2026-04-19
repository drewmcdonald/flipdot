/**
 * Ad-hoc text content: send arbitrary text messages to the display.
 */

import { mutation } from "../_generated/server";
import { v } from "convex/values";
import { getFont, renderText, renderScrollingText } from "../rendering/fontLoader";
import { createFrame, DISPLAY_WIDTH, DISPLAY_HEIGHT } from "../rendering/frame";

/** Send a text message to the display */
export const sendText = mutation({
  args: {
    text: v.string(),
    font: v.optional(v.string()),
    display_name: v.optional(v.string()),
    as_override: v.optional(v.boolean()),
    scroll: v.optional(v.boolean()),
  },
  handler: async (ctx, args) => {
    const displayName = args.display_name ?? "main";
    const fontName = args.font ?? "axion_6x7";
    const font = getFont(fontName);
    const sourceId = `adhoc:${Date.now().toString(36)}`;

    let frames;
    if (args.scroll) {
      const scrollFrames = renderScrollingText(
        font,
        args.text,
        DISPLAY_WIDTH,
        DISPLAY_HEIGHT,
        80
      );
      frames = scrollFrames.map((f) => createFrame(f.bits, f.duration_ms));
    } else {
      frames = [createFrame(renderText(font, args.text, DISPLAY_WIDTH, DISPLAY_HEIGHT))];
    }

    const content = {
      content_id: `adhoc:${args.text.slice(0, 20)}:${Date.now()}`,
      frames: frames.map((f) => ({
        data_b64: f.data_b64,
        width: f.width,
        height: f.height,
        duration_ms: f.duration_ms ?? null,
      })),
      playback: args.scroll ? { loop: true } : undefined,
      metadata: { type: "adhoc", text: args.text, font: fontName },
    };

    // Write to content_sources
    await ctx.db.insert("content_sources", {
      source_id: sourceId,
      content,
      updatedAt: Date.now(),
    });

    // Optionally add as override
    if (args.as_override) {
      const config = await ctx.db
        .query("display_config")
        .withIndex("by_display_name", (q) =>
          q.eq("display_name", displayName)
        )
        .first();

      if (config) {
        await ctx.db.patch(config._id, {
          overrides: [...config.overrides, { source_id: sourceId, priority: 50 }],
        });
      }
    }

    return { source_id: sourceId };
  },
});

/** Remove an ad-hoc source and clean up config references */
export const removeSource = mutation({
  args: { source_id: v.string() },
  handler: async (ctx, args) => {
    // Remove from content_sources
    const source = await ctx.db
      .query("content_sources")
      .withIndex("by_source_id", (q) => q.eq("source_id", args.source_id))
      .first();
    if (source) {
      await ctx.db.delete(source._id);
    }

    // Remove from any display_config overrides/rotation that reference it
    const configs = await ctx.db.query("display_config").collect();
    for (const config of configs) {
      const filteredOverrides = config.overrides.filter(
        (o) => o.source_id !== args.source_id
      );
      const filteredRotation = config.rotation.filter(
        (r) => r.source_id !== args.source_id
      );
      if (
        filteredOverrides.length !== config.overrides.length ||
        filteredRotation.length !== config.rotation.length
      ) {
        await ctx.db.patch(config._id, {
          overrides: filteredOverrides,
          rotation: filteredRotation,
        });
      }
    }
  },
});
