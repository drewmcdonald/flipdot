/**
 * Display configuration CRUD
 * Controls which content sources are shown on each display and when.
 */

import { internalMutation, internalQuery, mutation, query } from "./_generated/server";
import { v } from "convex/values";

/** Read config for a display */
export const getConfig = internalQuery({
  args: { display_name: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("display_config")
      .withIndex("by_display_name", (q) =>
        q.eq("display_name", args.display_name)
      )
      .first();
  },
});

/** Update rotation/overrides for a display */
export const updateConfig = mutation({
  args: {
    display_name: v.string(),
    rotation: v.array(
      v.object({
        source_id: v.string(),
        duration_s: v.number(),
      })
    ),
    overrides: v.array(
      v.object({
        source_id: v.string(),
        priority: v.number(),
      })
    ),
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("display_config")
      .withIndex("by_display_name", (q) =>
        q.eq("display_name", args.display_name)
      )
      .first();

    if (existing) {
      await ctx.db.patch(existing._id, {
        rotation: args.rotation,
        overrides: args.overrides,
      });
    } else {
      await ctx.db.insert("display_config", {
        display_name: args.display_name,
        rotation: args.rotation,
        overrides: args.overrides,
      });
    }
  },
});

/** Read config for a display (public) */
export const getConfigPublic = query({
  args: { display_name: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("display_config")
      .withIndex("by_display_name", (q) =>
        q.eq("display_name", args.display_name)
      )
      .first();
  },
});

/** Update generator-specific settings (timezone, font, etc.) */
export const updateGeneratorSettings = mutation({
  args: {
    display_name: v.string(),
    source_id: v.string(),
    settings: v.object({
      timezone: v.optional(v.string()),
      font: v.optional(v.string()),
    }),
  },
  handler: async (ctx, args) => {
    const config = await ctx.db
      .query("display_config")
      .withIndex("by_display_name", (q) =>
        q.eq("display_name", args.display_name)
      )
      .first();

    if (!config) return;

    // Currently only "clock" settings are supported
    if (args.source_id === "clock") {
      await ctx.db.patch(config._id, {
        generator_settings: {
          ...config.generator_settings,
          clock: args.settings,
        },
      });
    }
  },
});

/** Create initial config on first run (idempotent) */
export const seedDefaultConfig = internalMutation({
  args: {},
  handler: async (ctx) => {
    const existing = await ctx.db
      .query("display_config")
      .withIndex("by_display_name", (q) => q.eq("display_name", "main"))
      .first();

    if (!existing) {
      await ctx.db.insert("display_config", {
        display_name: "main",
        rotation: [{ source_id: "clock", duration_s: 60 }],
        overrides: [],
      });
    }
  },
});
