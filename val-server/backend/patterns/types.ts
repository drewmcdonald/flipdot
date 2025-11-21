/**
 * Pattern and Animation Types
 *
 * Defines the types and interfaces for flipdot patterns, animations, and transitions.
 */

import type { Frame } from "../../shared/types.ts";

/**
 * Pattern configuration for generating animated patterns
 */
export interface PatternConfig {
  /** Pattern type */
  type: PatternType;
  /** Duration in milliseconds for the entire pattern */
  duration_ms?: number;
  /** Frame delay in milliseconds (default: 100) */
  frame_delay_ms?: number;
  /** Pattern-specific options */
  options?: Record<string, unknown>;
}

/**
 * Available pattern types
 */
export type PatternType =
  | "wave"           // Horizontal or vertical wave
  | "rain"           // Falling dots
  | "spiral"         // Spiral from center
  | "checkerboard"   // Animated checkerboard
  | "random"         // Random noise
  | "expand"         // Expanding circles/squares
  | "gameoflife"     // Conway's Game of Life
  | "matrix"         // Matrix-style falling characters
  | "sparkle"        // Random sparkles
  | "pulse"          // Pulsing effect
  | "scan"           // Scanner effect (back and forth)
  | "fire"           // Fire effect
  | "snake";         // Snake/worm moving around

/**
 * Transition configuration for transitioning between frames
 */
export interface TransitionConfig {
  /** Transition type */
  type: TransitionType;
  /** Duration in milliseconds for the transition */
  duration_ms?: number;
  /** Frame delay in milliseconds (default: 50) */
  frame_delay_ms?: number;
  /** Direction for directional transitions */
  direction?: Direction;
}

/**
 * Available transition types
 */
export type TransitionType =
  | "wipe"          // Wipe from one direction
  | "fade"          // Dithered fade
  | "dissolve"      // Random pixel dissolve
  | "slide"         // Slide in from direction
  | "checkerboard"  // Checkerboard pattern reveal
  | "blinds"        // Venetian blinds effect
  | "center_out"    // Expand from center
  | "corners"       // Reveal from corners
  | "spiral";       // Spiral transition

/**
 * Direction for directional patterns and transitions
 */
export type Direction = "left" | "right" | "up" | "down";

/**
 * Pattern generator function type
 */
export type PatternGenerator = (
  width: number,
  height: number,
  frameIndex: number,
  options?: Record<string, unknown>
) => boolean[][];

/**
 * Transition generator function type
 */
export type TransitionGenerator = (
  fromFrame: boolean[][],
  toFrame: boolean[][],
  progress: number,
  options?: Record<string, unknown>
) => boolean[][];

/**
 * Pattern result containing generated frames
 */
export interface PatternResult {
  frames: Frame[];
  loop?: boolean;
}
