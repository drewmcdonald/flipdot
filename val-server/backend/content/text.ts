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
  getFont,
  measureText,
  renderScrollingText,
  renderText,
  DEFAULT_FONT,
} from "../rendering/font-loader.ts";

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
function getTextContentId(text: string, fontName: string): string {
  const hash = hashText(text);
  return `text:${fontName}:${hash}`;
}

/**
 * Get cache key for text content
 */
export function getTextCacheKey(text: string, fontName: string): string {
  const hash = hashText(text);
  return `flipdot:text:${fontName}:${hash}`;
}

/**
 * Generate static text content
 * Note: priority and interruptible are kept as parameters for server-side use
 * but are NOT included in the Content playback (driver manages queue now)
 */
export async function generateTextContent(
  text: string,
  priority: number = TEXT_PRIORITY,
  interruptible: boolean = TEXT_INTERRUPTIBLE,
  fontName: string = DEFAULT_FONT,
): Promise<Content> {
  // Load the font
  const font = await getFont(fontName);

  // Render text to bits
  const bits = renderText(font, text, DISPLAY_WIDTH, DISPLAY_HEIGHT);

  // Create frame
  const frame = createFrame(bits);

  return {
    content_id: getTextContentId(text, fontName),
    frames: [frame],
    playback: {
      loop: false,
    },
    metadata: {
      type: "text",
      text: text,
      font: fontName,
      timestamp: new Date().toISOString(),
    },
  };
}

/**
 * Generate scrolling text content
 * Note: priority and interruptible are kept as parameters for server-side use
 * but are NOT included in the Content playback (driver manages queue now)
 */
export async function generateScrollingTextContent(
  text: string,
  priority: number = TEXT_PRIORITY,
  interruptible: boolean = TEXT_INTERRUPTIBLE,
  frameDelayMs: number = 100,
  fontName: string = DEFAULT_FONT,
): Promise<Content> {
  // Load the font
  const font = await getFont(fontName);

  // Generate scrolling frames
  const scrollFrames = renderScrollingText(
    font,
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
    content_id: `scroll:${getTextContentId(text, fontName)}`,
    frames,
    playback: {
      loop: true, // Loop the scrolling animation
    },
    metadata: {
      type: "scrolling_text",
      text: text,
      font: fontName,
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
  font?: string;
}

export function createCustomTextSource(
  options: CustomTextOptions,
  expires_at?: number,
): ContentSource {
  const {
    text,
    priority = TEXT_PRIORITY,
    ttl_ms = TEXT_TTL_MS,
    interruptible = TEXT_INTERRUPTIBLE,
    scroll = false,
    frame_delay_ms = 100,
    font = DEFAULT_FONT,
  } = options;

  return {
    id: `custom_text:${hashText(text)}:${Date.now()}`,
    type: scroll ? "scrolling_text" : "custom_text",
    priority,
    interruptible,
    ttl_ms,
    expires_at, // Set expiration timestamp (undefined means no expiration)
    generate: async () => {
      // Load the font to measure text (async)
      const fontData = await getFont(font);

      // Determine if text needs to scroll
      const textWidth = measureText(fontData, text);
      const shouldScroll = scroll || textWidth > DISPLAY_WIDTH;

      return shouldScroll
        ? generateScrollingTextContent(
          text,
          priority,
          interruptible,
          frame_delay_ms,
          font,
        )
        : generateTextContent(text, priority, interruptible, font);
    },
  };
}
