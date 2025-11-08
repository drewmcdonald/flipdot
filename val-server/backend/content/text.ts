/**
 * Static text content generator
 * Displays arbitrary text messages
 */

import type { Content } from "../../shared/types.ts";
import type { ContentSource } from "./types.ts";
import {
  createFrame,
  DISPLAY_HEIGHT,
  DISPLAY_WIDTH,
} from "../rendering/frame.ts";
import {
  getFontName,
  measureText,
  renderScrollingText,
  renderText,
} from "../rendering/font.ts";

// Text configuration
const TEXT_PRIORITY = 15;
const TEXT_TTL_MS = 300000; // 5 minutes
const TEXT_INTERRUPTIBLE = true;

/**
 * Simple hash function for text content
 */
function hashText(text: string): string {
  let hash = 0;
  for (let i = 0; i < text.length; i++) {
    const char = text.charCodeAt(i);
    hash = (hash << 5) - hash + char;
    hash = hash & hash; // Convert to 32-bit integer
  }
  return Math.abs(hash).toString(36);
}

/**
 * Generate content ID for text
 */
function getTextContentId(text: string): string {
  const fontName = getFontName();
  const hash = hashText(text);
  return `text:${fontName}:${hash}`;
}

/**
 * Get cache key for text content
 */
export function getTextCacheKey(text: string): string {
  const fontName = getFontName();
  const hash = hashText(text);
  return `flipdot:text:${fontName}:${hash}`;
}

/**
 * Generate static text content
 */
export async function generateTextContent(
  text: string,
  priority: number = TEXT_PRIORITY,
  interruptible: boolean = TEXT_INTERRUPTIBLE,
): Promise<Content> {
  // Render text to bits
  const bits = renderText(text, DISPLAY_WIDTH, DISPLAY_HEIGHT);

  // Create frame
  const frame = createFrame(bits);

  return {
    content_id: getTextContentId(text),
    frames: [frame],
    playback: {
      priority,
      interruptible,
      loop: false,
    },
    metadata: {
      type: "text",
      text: text,
      timestamp: new Date().toISOString(),
    },
  };
}

/**
 * Generate scrolling text content
 */
export async function generateScrollingTextContent(
  text: string,
  priority: number = TEXT_PRIORITY,
  interruptible: boolean = TEXT_INTERRUPTIBLE,
  frameDelayMs: number = 100,
): Promise<Content> {
  // Generate scrolling frames
  const scrollFrames = renderScrollingText(
    text,
    DISPLAY_WIDTH,
    DISPLAY_HEIGHT,
    frameDelayMs,
  );

  // Convert to Frame objects
  const frames = scrollFrames.map((f) =>
    createFrame(f.bits, f.duration_ms)
  );

  return {
    content_id: `scroll:${getTextContentId(text)}`,
    frames,
    playback: {
      priority,
      interruptible,
      loop: true, // Loop the scrolling animation
    },
    metadata: {
      type: "scrolling_text",
      text: text,
      frame_delay_ms: frameDelayMs,
      frame_count: frames.length,
      timestamp: new Date().toISOString(),
    },
  };
}

/**
 * Create text content source
 */
export function createTextSource(text: string): ContentSource {
  return {
    id: `text:${hashText(text)}`,
    type: "text",
    priority: TEXT_PRIORITY,
    interruptible: TEXT_INTERRUPTIBLE,
    ttl_ms: TEXT_TTL_MS,
    generate: () => generateTextContent(text),
  };
}

/**
 * Create custom text content source with configurable priority and TTL
 */
export interface CustomTextOptions {
  text: string;
  priority?: number;
  ttl_ms?: number;
  interruptible?: boolean;
  scroll?: boolean;
  frame_delay_ms?: number;
}

export function createCustomTextSource(
  options: CustomTextOptions,
): ContentSource {
  const {
    text,
    priority = TEXT_PRIORITY,
    ttl_ms = TEXT_TTL_MS,
    interruptible = TEXT_INTERRUPTIBLE,
    scroll = false,
    frame_delay_ms = 100,
  } = options;

  // Determine if text needs to scroll
  const textWidth = measureText(text);
  const shouldScroll = scroll || textWidth > DISPLAY_WIDTH;

  return {
    id: `custom_text:${hashText(text)}:${Date.now()}`,
    type: shouldScroll ? "scrolling_text" : "custom_text",
    priority,
    interruptible,
    ttl_ms,
    generate: () =>
      shouldScroll
        ? generateScrollingTextContent(
          text,
          priority,
          interruptible,
          frame_delay_ms,
        )
        : generateTextContent(text, priority, interruptible),
  };
}
