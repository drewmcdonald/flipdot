import { defineSchema, defineTable } from "convex/server";
import { v } from "convex/values";

/**
 * Convex schema for FlipDot display server
 */
export default defineSchema({
  /**
   * Displays table - stores current content for each named display
   */
  displays: defineTable({
    /** Display name (e.g., "main") */
    name: v.string(),
    /** Current content being displayed */
    content: v.object({
      /** Unique identifier for this content */
      content_id: v.string(),
      /** Array of frames to display */
      frames: v.array(
        v.object({
          /** Base64-encoded packed bit data (little-endian) */
          data_b64: v.string(),
          /** Frame width in pixels */
          width: v.number(),
          /** Frame height in pixels */
          height: v.number(),
          /** Duration to display frame in milliseconds (null = static) */
          duration_ms: v.union(v.number(), v.null()),
          /** Optional metadata for debugging/logging */
          metadata: v.optional(v.any()),
        })
      ),
      /** Playback configuration */
      playback: v.optional(
        v.object({
          /** Whether to loop the animation */
          loop: v.optional(v.boolean()),
          /** Number of times to loop (null = infinite) */
          loop_count: v.optional(v.union(v.number(), v.null())),
        })
      ),
      /** Optional metadata */
      metadata: v.optional(v.any()),
    }),
    /** Last update timestamp */
    updatedAt: v.number(),
  }).index("by_name", ["name"]),
});
