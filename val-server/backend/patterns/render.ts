/**
 * Pattern Rendering
 *
 * Converts pattern/transition output to flipdot frames.
 */

import type { Frame } from "../../shared/types.ts";
import type { PatternConfig, PatternResult, TransitionConfig } from "./types.ts";
import { patterns } from "./generators.ts";
import { transitions } from "./transitions.ts";
import { bitsToBase64 } from "../rendering/bits.ts";

// Display dimensions
const DISPLAY_WIDTH = 28;
const DISPLAY_HEIGHT = 14;

/**
 * Convert 2D boolean array to bit array (row-major order)
 */
function frame2DToBits(frame: boolean[][]): number[] {
  const bits: number[] = [];
  for (let y = 0; y < frame.length; y++) {
    for (let x = 0; x < frame[y].length; x++) {
      bits.push(frame[y][x] ? 1 : 0);
    }
  }
  return bits;
}

/**
 * Convert 2D boolean array to Frame object
 */
export function booleanArrayToFrame(
  frame: boolean[][],
  duration_ms?: number | null
): Frame {
  const bits = frame2DToBits(frame);
  const data_b64 = bitsToBase64(bits);

  return {
    data_b64,
    width: DISPLAY_WIDTH,
    height: DISPLAY_HEIGHT,
    duration_ms: duration_ms ?? null,
  };
}

/**
 * Render a pattern animation
 */
export function renderPattern(config: PatternConfig): PatternResult {
  const generator = patterns[config.type];
  if (!generator) {
    throw new Error(`Unknown pattern type: ${config.type}`);
  }

  const duration_ms = config.duration_ms ?? 3000;
  const frame_delay_ms = config.frame_delay_ms ?? 100;
  const numFrames = Math.floor(duration_ms / frame_delay_ms);
  const frames: Frame[] = [];

  for (let i = 0; i < numFrames; i++) {
    const frame2D = generator(
      DISPLAY_WIDTH,
      DISPLAY_HEIGHT,
      i,
      config.options
    );
    frames.push(booleanArrayToFrame(frame2D, frame_delay_ms));
  }

  return {
    frames,
    loop: true, // Patterns typically loop
  };
}

/**
 * Render a transition between two frames
 */
export function renderTransition(
  fromFrame: Frame,
  toFrame: Frame,
  config: TransitionConfig
): PatternResult {
  const transitionFn = transitions[config.type];
  if (!transitionFn) {
    throw new Error(`Unknown transition type: ${config.type}`);
  }

  // Convert frames from base64 back to 2D boolean arrays
  const from2D = frameTo2DArray(fromFrame);
  const to2D = frameTo2DArray(toFrame);

  const duration_ms = config.duration_ms ?? 1000;
  const frame_delay_ms = config.frame_delay_ms ?? 50;
  const numFrames = Math.floor(duration_ms / frame_delay_ms);
  const frames: Frame[] = [];

  const options = {
    direction: config.direction,
  };

  for (let i = 0; i < numFrames; i++) {
    const progress = (i + 1) / numFrames;
    const frame2D = transitionFn(from2D, to2D, progress, options);
    frames.push(booleanArrayToFrame(frame2D, frame_delay_ms));
  }

  return {
    frames,
    loop: false, // Transitions don't loop
  };
}

/**
 * Convert a Frame back to 2D boolean array (for transitions)
 */
function frameTo2DArray(frame: Frame): boolean[][] {
  // Decode base64 to bits
  const decoded = atob(frame.data_b64);
  const bytes = new Uint8Array(decoded.length);
  for (let i = 0; i < decoded.length; i++) {
    bytes[i] = decoded.charCodeAt(i);
  }

  // Extract bits (little-endian)
  const totalBits = frame.width * frame.height;
  const bits: boolean[] = [];
  for (let i = 0; i < totalBits; i++) {
    const byteIndex = Math.floor(i / 8);
    const bitIndex = i % 8;
    const bit = (bytes[byteIndex] >> bitIndex) & 1;
    bits.push(bit === 1);
  }

  // Convert to 2D array (row-major order)
  const result: boolean[][] = [];
  for (let y = 0; y < frame.height; y++) {
    const row: boolean[] = [];
    for (let x = 0; x < frame.width; x++) {
      row.push(bits[y * frame.width + x]);
    }
    result.push(row);
  }

  return result;
}

/**
 * Create a blank frame
 */
export function createBlankFrame(): Frame {
  const bits = new Array(DISPLAY_WIDTH * DISPLAY_HEIGHT).fill(0);
  const data_b64 = bitsToBase64(bits);

  return {
    data_b64,
    width: DISPLAY_WIDTH,
    height: DISPLAY_HEIGHT,
    duration_ms: null,
  };
}

/**
 * Create a filled frame (all pixels on)
 */
export function createFilledFrame(): Frame {
  const bits = new Array(DISPLAY_WIDTH * DISPLAY_HEIGHT).fill(1);
  const data_b64 = bitsToBase64(bits);

  return {
    data_b64,
    width: DISPLAY_WIDTH,
    height: DISPLAY_HEIGHT,
    duration_ms: null,
  };
}
