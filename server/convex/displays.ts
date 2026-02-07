import { query, mutation, internalMutation } from "./_generated/server";
import { v } from "convex/values";
import type { Content } from "./types";

/**
 * Get the current display content by name
 * This is a public query that clients can subscribe to for real-time updates
 */
export const getCurrentDisplay = query({
  args: { name: v.string() },
  handler: async (ctx, args) => {
    const display = await ctx.db
      .query("displays")
      .withIndex("by_name", (q) => q.eq("name", args.name))
      .first();

    if (!display) {
      return null;
    }

    return {
      name: display.name,
      content: display.content as Content,
      updatedAt: display.updatedAt,
    };
  },
});

/**
 * Update display content (internal mutation - called by actions/crons)
 */
export const updateDisplay = internalMutation({
  args: {
    name: v.string(),
    content: v.object({
      content_id: v.string(),
      frames: v.array(
        v.object({
          data_b64: v.string(),
          width: v.number(),
          height: v.number(),
          duration_ms: v.union(v.number(), v.null()),
          metadata: v.optional(v.any()),
        })
      ),
      playback: v.optional(
        v.object({
          loop: v.optional(v.boolean()),
          loop_count: v.optional(v.union(v.number(), v.null())),
        })
      ),
      metadata: v.optional(v.any()),
    }),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("displays")
      .withIndex("by_name", (q) => q.eq("name", args.name))
      .first();

    const now = Date.now();

    if (existing) {
      await ctx.db.patch(existing._id, {
        content: args.content,
        updatedAt: now,
      });
    } else {
      await ctx.db.insert("displays", {
        name: args.name,
        content: args.content,
        updatedAt: now,
      });
    }
  },
});

/**
 * Clear display content (internal mutation)
 */
export const clearDisplay = internalMutation({
  args: { name: v.string() },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("displays")
      .withIndex("by_name", (q) => q.eq("name", args.name))
      .first();

    if (existing) {
      await ctx.db.delete(existing._id);
    }
  },
});

/**
 * List all displays (for debugging/admin)
 */
export const listDisplays = query({
  args: {},
  handler: async (ctx) => {
    const displays = await ctx.db.query("displays").collect();
    return displays.map((d) => ({
      name: d.name,
      content_id: d.content.content_id,
      frameCount: d.content.frames.length,
      updatedAt: d.updatedAt,
    }));
  },
});
