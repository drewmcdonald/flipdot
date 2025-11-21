/**
 * Pattern Content Sources
 *
 * Integrates patterns and transitions into the content system.
 */

import type { Content } from "../../shared/types.ts";
import type { ContentSource } from "../content/types.ts";
import type { PatternConfig } from "./types.ts";
import { renderPattern } from "./render.ts";
import { createHash } from "node:crypto";

/**
 * Create a content source for a pattern
 */
export function createPatternSource(
  config: PatternConfig,
  options: {
    priority?: number;
    ttl_ms?: number;
    interruptible?: boolean;
  } = {}
): ContentSource {
  // Generate unique ID based on pattern config
  const configStr = JSON.stringify(config);
  const hash = createHash("md5").update(configStr).digest("hex").substring(0, 8);
  const id = `pattern:${config.type}:${hash}`;

  return {
    id,
    type: "pattern",
    priority: options.priority ?? 15,
    interruptible: options.interruptible ?? true,
    ttl_ms: options.ttl_ms ?? 60000,

    generate: async () => {
      const result = renderPattern(config);

      return {
        content_id: id,
        frames: result.frames,
        playback: {
          loop: result.loop ?? false,
        },
        metadata: {
          type: "pattern",
          pattern_type: config.type,
          config,
        },
      };
    },
  };
}

/**
 * Pattern storage for managing active patterns
 */
export class PatternStorage {
  private patterns = new Map<string, ContentSource>();

  /**
   * Add or update a pattern
   */
  set(config: PatternConfig, options?: {
    priority?: number;
    ttl_ms?: number;
    interruptible?: boolean;
  }): ContentSource {
    const source = createPatternSource(config, options);
    this.patterns.set(source.id, source);
    return source;
  }

  /**
   * Get a pattern by ID
   */
  get(id: string): ContentSource | undefined {
    return this.patterns.get(id);
  }

  /**
   * Get all patterns
   */
  getAll(): ContentSource[] {
    return Array.from(this.patterns.values());
  }

  /**
   * Remove a pattern
   */
  remove(id: string): boolean {
    return this.patterns.delete(id);
  }

  /**
   * Clear all patterns
   */
  clear(): void {
    this.patterns.clear();
  }

  /**
   * Get pattern count
   */
  get size(): number {
    return this.patterns.size;
  }
}
