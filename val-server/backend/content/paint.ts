import { Content, ContentSource } from "./types.ts";
import { createFrame } from "../rendering/frame.ts";
import { storage } from "../storage.ts";

const DISPLAY_WIDTH = 28;
const DISPLAY_HEIGHT = 14;
const PAINT_PRIORITY = 50; // Higher than text, lower than alerts
const PAINT_TTL_MS = 5 * 60 * 1000; // 5 minutes
const INACTIVITY_TIMEOUT_MS = 2 * 60 * 1000; // 2 minutes of inactivity

interface PaintBuffer {
  bits: number[];
  lastUpdate: number; // timestamp
}

const STORAGE_KEY = "flipdot:paint:buffer";

/**
 * Get the current paint buffer from storage
 */
export async function getPaintBuffer(): Promise<PaintBuffer | null> {
  try {
    const buffer = await storage.getJSON<PaintBuffer>(STORAGE_KEY);
    if (!buffer) return null;

    // Check if buffer has expired due to inactivity
    const now = Date.now();
    if (now - buffer.lastUpdate > INACTIVITY_TIMEOUT_MS) {
      // Clear expired buffer
      await clearPaintBuffer();
      return null;
    }

    return buffer;
  } catch (error) {
    console.error("Error reading paint buffer:", error);
    return null;
  }
}

/**
 * Set the paint buffer in storage
 */
export async function setPaintBuffer(bits: number[]): Promise<void> {
  const buffer: PaintBuffer = {
    bits,
    lastUpdate: Date.now(),
  };
  await storage.setJSON(STORAGE_KEY, buffer);
}

/**
 * Clear the paint buffer from storage
 */
export async function clearPaintBuffer(): Promise<void> {
  await storage.delete(STORAGE_KEY);
}

/**
 * Generate paint content from the current buffer
 */
async function generatePaintContent(): Promise<Content | null> {
  const buffer = await getPaintBuffer();
  if (!buffer) return null;

  const frame = createFrame(buffer.bits);

  return {
    content_id: "paint:canvas",
    frames: [frame],
    playback: { loop: false },
    metadata: {
      type: "paint",
      timestamp: new Date(buffer.lastUpdate).toISOString(),
    },
  };
}

/**
 * Create a paint content source
 */
export function createPaintSource(): ContentSource {
  return {
    id: "paint",
    type: "paint",
    priority: PAINT_PRIORITY,
    interruptible: true,
    ttl_ms: PAINT_TTL_MS,
    generate: async () => {
      const content = await generatePaintContent();
      if (!content) {
        throw new Error("No paint buffer available");
      }
      return content;
    },
  };
}

/**
 * Update paint buffer with new pixel data
 * @param bits Array of 392 bits (28x14) representing pixel states
 */
export async function updatePaintBuffer(bits: number[]): Promise<void> {
  if (bits.length !== DISPLAY_WIDTH * DISPLAY_HEIGHT) {
    throw new Error(
      `Invalid bits array length: expected ${DISPLAY_WIDTH * DISPLAY_HEIGHT}, got ${bits.length}`,
    );
  }

  // Validate bits are 0 or 1
  if (!bits.every((bit) => bit === 0 || bit === 1)) {
    throw new Error("Invalid bits: all values must be 0 or 1");
  }

  await setPaintBuffer(bits);
}
