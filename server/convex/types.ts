/**
 * FlipDot Content Server API Types
 * Implements types from CONTENT_SERVER_SPEC.md
 */

/**
 * A single frame of display content
 */
export interface Frame {
  /** Base64-encoded packed bit data (little-endian) */
  data_b64: string;
  /** Frame width in pixels */
  width: number;
  /** Frame height in pixels */
  height: number;
  /** Duration to display frame in milliseconds (null = static) */
  duration_ms?: number | null;
  /** Optional metadata for debugging/logging */
  metadata?: Record<string, unknown>;
}

/**
 * Playback mode configuration
 */
export interface PlaybackMode {
  /** Whether to loop the animation */
  loop?: boolean;
  /** Number of times to loop (null = infinite) */
  loop_count?: number | null;
}

/**
 * Content package with frames and playback configuration
 */
export interface Content {
  /** Unique identifier for this content */
  content_id: string;
  /** Array of frames to display */
  frames: Frame[];
  /** Playback configuration */
  playback?: PlaybackMode;
  /** Optional metadata */
  metadata?: Record<string, unknown>;
}

/**
 * Response status from content server
 */
export type ResponseStatus = "updated" | "clear";

/**
 * Top-level response from GET /api/flipdot/content
 * Server sends complete playlist - driver plays in order
 */
export interface ContentResponse {
  /** Status of the content update */
  status: ResponseStatus;
  /**
   * Complete ordered playlist to display.
   * First item plays immediately, rest queued in order.
   * Required when status="updated"
   */
  playlist: Content[];
  /** Polling interval in milliseconds (minimum 1000) */
  poll_interval_ms: number;
}
