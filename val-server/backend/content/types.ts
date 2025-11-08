/**
 * Content source types for priority queue system
 */

import type { Content } from "../../shared/types.ts";

/**
 * Content source configuration
 * Each source represents a type of content that can be displayed
 */
export interface ContentSource {
  /** Unique identifier for this source */
  id: string;

  /** Content type (e.g., "clock", "text", "weather") */
  type: string;

  /** Priority level (0-99, higher = more important) */
  priority: number;

  /** Whether this content can be interrupted by higher priority content */
  interruptible: boolean;

  /** Time-to-live in milliseconds (how long to cache) */
  ttl_ms: number;

  /** Function to generate content */
  generate: () => Promise<Content>;
}

/**
 * Cached content entry
 */
export interface CachedContent {
  /** The content */
  content: Content;

  /** Timestamp when cached */
  cached_at: number;

  /** TTL in milliseconds */
  ttl_ms: number;
}

/**
 * Check if cached content is still valid
 */
export function isCacheValid(cached: CachedContent, now: number): boolean {
  return now - cached.cached_at < cached.ttl_ms;
}
