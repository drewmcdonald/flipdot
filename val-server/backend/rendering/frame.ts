/**
 * Frame creation utilities for FlipDot content server
 */

import type { Frame } from "../../shared/types.ts";
import { bitsToBase64 } from "./bits.ts";

// Display specifications
// Two 28×7 modules stacked vertically = 28 wide × 14 tall
export const DISPLAY_WIDTH = 28;
export const DISPLAY_HEIGHT = 14;
export const DISPLAY_BITS = DISPLAY_WIDTH * DISPLAY_HEIGHT; // 392 bits

/**
 * Create a frame from bit array
 *
 * @param bits Array of 0s and 1s (must be 392 bits for 28×14 display)
 * @param duration_ms Duration to display frame (null = static frame)
 * @returns Frame object with base64-encoded data
 */
export function createFrame(
  bits: number[],
  duration_ms?: number | null,
): Frame {
  // Validate bit count
  if (bits.length !== DISPLAY_BITS) {
    throw new Error(
      `Invalid bit count: expected ${DISPLAY_BITS}, got ${bits.length}`,
    );
  }

  // Validate all values are 0 or 1
  for (let i = 0; i < bits.length; i++) {
    if (bits[i] !== 0 && bits[i] !== 1) {
      throw new Error(`Invalid bit value at index ${i}: ${bits[i]}`);
    }
  }

  return {
    data_b64: bitsToBase64(bits),
    width: DISPLAY_WIDTH,
    height: DISPLAY_HEIGHT,
    duration_ms: duration_ms ?? null,
  };
}

/**
 * Create a blank frame (all pixels off)
 */
export function createBlankFrame(): Frame {
  const bits = new Array(DISPLAY_BITS).fill(0);
  return createFrame(bits);
}

/**
 * Create a test pattern frame (all pixels on)
 */
export function createTestPattern(): Frame {
  const bits = new Array(DISPLAY_BITS).fill(1);
  return createFrame(bits);
}

/**
 * Create a checkerboard pattern for testing
 */
export function createCheckerboard(): Frame {
  const bits = new Array(DISPLAY_BITS);
  for (let y = 0; y < DISPLAY_HEIGHT; y++) {
    for (let x = 0; x < DISPLAY_WIDTH; x++) {
      const index = y * DISPLAY_WIDTH + x;
      bits[index] = (x + y) % 2;
    }
  }
  return createFrame(bits);
}
