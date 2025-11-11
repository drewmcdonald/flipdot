/**
 * Clock content generator
 * Displays current time in HH:MM format
 */

import type { Content } from "../../shared/types.ts";
import type { ContentSource } from "./types.ts";
import {
  createFrame,
  DISPLAY_HEIGHT,
  DISPLAY_WIDTH,
} from "../rendering/frame.ts";
import { getFontName, renderText } from "../rendering/font.ts";

// Clock configuration
const CLOCK_PRIORITY = 10;
const CLOCK_TTL_MS = 60000; // 1 minute
const CLOCK_INTERRUPTIBLE = true;

/**
 * Generate content ID for clock based on current time
 */
function getClockContentId(hour: number, minute: number): string {
  const fontName = getFontName();
  const hourStr = hour.toString().padStart(2, "0");
  const minuteStr = minute.toString().padStart(2, "0");
  return `clock:${fontName}:${hourStr}:${minuteStr}`;
}

/**
 * Get cache key for clock content
 */
export function getClockCacheKey(hour: number, minute: number): string {
  const fontName = getFontName();
  const hourStr = hour.toString().padStart(2, "0");
  const minuteStr = minute.toString().padStart(2, "0");
  return `flipdot:clock:${fontName}:${hourStr}:${minuteStr}`;
}

/**
 * Generate clock content
 */
export async function generateClockContent(): Promise<Content> {
  const now = new Date();
  const hour = now.getHours();
  const minute = now.getMinutes();

  // Format time as "HH:MM"
  const hourStr = hour.toString().padStart(2, "0");
  const minuteStr = minute.toString().padStart(2, "0");
  const timeText = `${hourStr}:${minuteStr}`;

  // Render text to bits
  const bits = renderText(timeText, DISPLAY_WIDTH, DISPLAY_HEIGHT);

  // Create frame
  const frame = createFrame(bits);

  return {
    content_id: getClockContentId(hour, minute),
    frames: [frame],
    playback: {
      loop: false,
    },
    metadata: {
      type: "clock",
      time: timeText,
      timestamp: now.toISOString(),
    },
  };
}

/**
 * Create clock content source
 */
export function createClockSource(): ContentSource {
  return {
    id: "clock",
    type: "clock",
    priority: CLOCK_PRIORITY,
    interruptible: CLOCK_INTERRUPTIBLE,
    ttl_ms: CLOCK_TTL_MS,
    generate: generateClockContent,
  };
}
