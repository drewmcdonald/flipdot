/**
 * Clock content generator
 * Displays current time in HH:MM format
 */

import { internalAction } from "../_generated/server";
import { internal } from "../_generated/api";
import type { Content } from "../types";
import { createFrame, DISPLAY_HEIGHT, DISPLAY_WIDTH } from "../rendering/frame";
import { DEFAULT_FONT, getFont, renderText } from "../rendering/fontLoader";

/**
 * Generate content ID for clock based on current time
 */
function getClockContentId(
  hour: number,
  minute: number,
  fontName: string
): string {
  const hourStr = hour.toString().padStart(2, "0");
  const minuteStr = minute.toString().padStart(2, "0");
  return `clock:${fontName}:${hourStr}:${minuteStr}`;
}

/**
 * Generate clock content for the current time
 */
function generateClockContent(fontName: string = DEFAULT_FONT): Content {
  const now = new Date();

  // Get Eastern time (America/New_York - handles EST/EDT automatically)
  const easternTime = new Date(
    now.toLocaleString("en-US", { timeZone: "America/New_York" })
  );
  const hour = easternTime.getHours();
  const minute = easternTime.getMinutes();

  // Format time as "HH:MM"
  const hourStr = hour.toString().padStart(2, "0");
  const minuteStr = minute.toString().padStart(2, "0");
  const timeText = `${hourStr}:${minuteStr}`;

  // Load the font
  const font = getFont(fontName);

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
 * Internal action to generate and update the clock display
 * Called by cron job every minute
 */
export const generateClock = internalAction({
  args: {},
  handler: async (ctx) => {
    // Generate clock content
    const content = generateClockContent(DEFAULT_FONT);

    // Update the main display
    await ctx.runMutation(internal.displays.updateDisplay, {
      name: "main",
      content: {
        content_id: content.content_id,
        frames: content.frames.map((f) => ({
          data_b64: f.data_b64,
          width: f.width,
          height: f.height,
          duration_ms: f.duration_ms ?? null,
          metadata: f.metadata,
        })),
        playback: content.playback,
        metadata: content.metadata,
      },
    });

    console.log(`Clock updated: ${content.metadata?.time}`);
  },
});
