/**
 * Content sources CRUD
 * Each content generator writes to this table; the compositor reads from it.
 */

import {
  internalMutation,
  internalQuery,
  query,
} from "./_generated/server";
import { v } from "convex/values";

const contentValidator = v.object({
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
});

/** Upsert a content source by source_id */
export const updateSource = internalMutation({
  args: {
    source_id: v.string(),
    content: contentValidator,
  },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("content_sources")
      .withIndex("by_source_id", (q) => q.eq("source_id", args.source_id))
      .first();

    const now = Date.now();

    if (existing) {
      await ctx.db.patch(existing._id, {
        content: args.content,
        updatedAt: now,
      });
    } else {
      await ctx.db.insert("content_sources", {
        source_id: args.source_id,
        content: args.content,
        updatedAt: now,
      });
    }
  },
});

/** Read a single source by source_id */
export const getSource = internalQuery({
  args: { source_id: v.string() },
  handler: async (ctx, args) => {
    return await ctx.db
      .query("content_sources")
      .withIndex("by_source_id", (q) => q.eq("source_id", args.source_id))
      .first();
  },
});

/** List all sources (for debugging/admin) */
export const listSources = query({
  args: {},
  handler: async (ctx) => {
    const sources = await ctx.db.query("content_sources").collect();
    return sources.map((s) => ({
      source_id: s.source_id,
      content_id: s.content.content_id,
      frameCount: s.content.frames.length,
      updatedAt: s.updatedAt,
    }));
  },
});

/** Remove a source (used by ephemeral sources when they're done) */
export const clearSource = internalMutation({
  args: { source_id: v.string() },
  handler: async (ctx, args) => {
    const existing = await ctx.db
      .query("content_sources")
      .withIndex("by_source_id", (q) => q.eq("source_id", args.source_id))
      .first();

    if (existing) {
      await ctx.db.delete(existing._id);
    }
  },
});
