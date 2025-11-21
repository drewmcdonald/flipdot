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
import { getFont, renderText, DEFAULT_FONT } from "../rendering/font-loader.ts";

// Clock configuration
const CLOCK_PRIORITY = 10;
const CLOCK_TTL_MS = 60000; // 1 minute
const CLOCK_INTERRUPTIBLE = true;

/**
 * Generate content ID for clock based on current time
 */
function getClockContentId(hour: number, minute: number, fontName: string): string {
  const hourStr = hour.toString().padStart(2, "0");
  const minuteStr = minute.toString().padStart(2, "0");
  return `clock:${fontName}:${hourStr}:${minuteStr}`;
}

/**
 * Get cache key for clock content
 */
export function getClockCacheKey(hour: number, minute: number, fontName: string): string {
  const hourStr = hour.toString().padStart(2, "0");
  const minuteStr = minute.toString().padStart(2, "0");
  return `flipdot:clock:${fontName}:${hourStr}:${minuteStr}`;
}

/**
 * Generate clock content
 */
export async function generateClockContent(fontName: string = DEFAULT_FONT): Promise<Content> {
  const now = new Date();

  // Get Eastern time (America/New_York - handles EST/EDT automatically)
  const easternTime = new Date(now.toLocaleString("en-US", { timeZone: "America/New_York" }));
  const hour = easternTime.getHours();
  const minute = easternTime.getMinutes();

  // Format time as "HH:MM"
  const hourStr = hour.toString().padStart(2, "0");
  const minuteStr = minute.toString().padStart(2, "0");
  const timeText = `${hourStr}:${minuteStr}`;

  // Load the font
  const font = await getFont(fontName);

  // Render text to bits
  const bits = renderText(font, timeText, DISPLAY_WIDTH, DISPLAY_HEIGHT);

  // Create frame
  const frame = createFrame(bits);

  return {
    content_id: getClockContentId(hour, minute, fontName),
    frames: [frame],
    playback: {
      loop: false,
    },
    metadata: {
      type: "clock",
      time: timeText,
      font: fontName,
      timestamp: now.toISOString(),
    },
  };
}

/**
 * Create clock content source
 */
export function createClockSource(fontName: string = DEFAULT_FONT): ContentSource {
  return {
    id: "clock",
    type: "clock",
    priority: CLOCK_PRIORITY,
    interruptible: CLOCK_INTERRUPTIBLE,
    ttl_ms: CLOCK_TTL_MS,
    generate: () => generateClockContent(fontName),
  };
}
