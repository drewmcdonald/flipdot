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

  /**
   * Content sources table - each content generator writes here
   * The compositor reads from this table to decide what to show
   */
  content_sources: defineTable({
    /** Source identifier (e.g., "clock", "weather", "pomodoro") */
    source_id: v.string(),
    /** Content package (same shape as displays.content) */
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
    /** Last update timestamp */
    updatedAt: v.number(),
  }).index("by_source_id", ["source_id"]),

  /**
   * Display configuration - controls which sources are shown and when
   */
  display_config: defineTable({
    /** Display name (e.g., "main") */
    display_name: v.string(),
    /** Ordered rotation of sources with durations */
    rotation: v.array(
      v.object({
        source_id: v.string(),
        duration_s: v.number(),
      })
    ),
    /** Override sources that take priority over rotation */
    overrides: v.array(
      v.object({
        source_id: v.string(),
        priority: v.number(),
      })
    ),
    /** Per-generator settings (timezone, font, etc.) */
    generator_settings: v.optional(
      v.object({
        clock: v.optional(
          v.object({
            timezone: v.optional(v.string()),
            font: v.optional(v.string()),
          })
        ),
      })
    ),
  }).index("by_display_name", ["display_name"]),
});
