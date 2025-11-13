/**
 * Pattern Generators
 *
 * Functions to generate various animated patterns for the flipdot display.
 */

import type { PatternGenerator } from "./types.ts";

/**
 * Create an empty frame (all pixels off)
 */
export function createEmptyFrame(width: number, height: number): boolean[][] {
  return Array(height).fill(null).map(() => Array(width).fill(false));
}

/**
 * Wave pattern - horizontal or vertical sine wave
 */
export const wavePattern: PatternGenerator = (
  width,
  height,
  frameIndex,
  options = {}
) => {
  const frame = createEmptyFrame(width, height);
  const vertical = options.vertical === true;
  const amplitude = (options.amplitude as number) ?? (vertical ? width / 4 : height / 4);
  const frequency = (options.frequency as number) ?? 0.5;
  const speed = (options.speed as number) ?? 0.3;

  if (vertical) {
    // Vertical wave (left to right)
    for (let y = 0; y < height; y++) {
      const x = Math.floor(
        width / 2 + amplitude * Math.sin(frequency * y + speed * frameIndex)
      );
      if (x >= 0 && x < width) {
        frame[y][x] = true;
      }
    }
  } else {
    // Horizontal wave (top to bottom)
    for (let x = 0; x < width; x++) {
      const y = Math.floor(
        height / 2 + amplitude * Math.sin(frequency * x + speed * frameIndex)
      );
      if (y >= 0 && y < height) {
        frame[y][x] = true;
      }
    }
  }

  return frame;
};

/**
 * Rain pattern - falling dots
 */
export const rainPattern: PatternGenerator = (
  width,
  height,
  frameIndex,
  options = {}
) => {
  const frame = createEmptyFrame(width, height);
  const density = (options.density as number) ?? 0.3;
  const speed = (options.speed as number) ?? 1;

  // Use frameIndex as seed for pseudo-random but deterministic rain
  const seed = frameIndex * 12345;

  for (let x = 0; x < width; x++) {
    // Each column has a pseudo-random pattern
    const columnSeed = seed + x * 67890;
    const hash = Math.sin(columnSeed) * 10000;
    const shouldRain = (hash - Math.floor(hash)) < density;

    if (shouldRain) {
      const y = Math.floor((frameIndex * speed + x * 3) % (height + 5)) - 2;
      if (y >= 0 && y < height) {
        frame[y][x] = true;
        // Add tail
        if (y > 0) frame[y - 1][x] = true;
      }
    }
  }

  return frame;
};

/**
 * Spiral pattern - spiral from center
 */
export const spiralPattern: PatternGenerator = (
  width,
  height,
  frameIndex,
  options = {}
) => {
  const frame = createEmptyFrame(width, height);
  const centerX = width / 2;
  const centerY = height / 2;
  const speed = (options.speed as number) ?? 0.5;
  const arms = (options.arms as number) ?? 3;
  const maxRadius = Math.sqrt(centerX * centerX + centerY * centerY);

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const dx = x - centerX;
      const dy = y - centerY;
      const r = Math.sqrt(dx * dx + dy * dy);
      const angle = Math.atan2(dy, dx);

      const spiralAngle = angle + r * 0.3 - frameIndex * speed * 0.1;
      const armValue = Math.sin(spiralAngle * arms);

      if (armValue > 0.7 && r < maxRadius) {
        frame[y][x] = true;
      }
    }
  }

  return frame;
};

/**
 * Checkerboard pattern - animated checkerboard
 */
export const checkerboardPattern: PatternGenerator = (
  width,
  height,
  frameIndex,
  options = {}
) => {
  const frame = createEmptyFrame(width, height);
  const size = (options.size as number) ?? 2;
  const invert = Math.floor(frameIndex / 5) % 2 === 0;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const checkX = Math.floor(x / size);
      const checkY = Math.floor(y / size);
      let isOn = (checkX + checkY) % 2 === 0;
      if (invert) isOn = !isOn;
      frame[y][x] = isOn;
    }
  }

  return frame;
};

/**
 * Random/noise pattern
 */
export const randomPattern: PatternGenerator = (
  width,
  height,
  frameIndex,
  options = {}
) => {
  const frame = createEmptyFrame(width, height);
  const density = (options.density as number) ?? 0.5;

  // Pseudo-random but deterministic based on frameIndex
  const seed = frameIndex * 9876;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const hash = Math.sin(seed + x * 12.9898 + y * 78.233) * 43758.5453;
      frame[y][x] = (hash - Math.floor(hash)) < density;
    }
  }

  return frame;
};

/**
 * Expanding pattern - expanding circles or squares
 */
export const expandPattern: PatternGenerator = (
  width,
  height,
  frameIndex,
  options = {}
) => {
  const frame = createEmptyFrame(width, height);
  const centerX = width / 2;
  const centerY = height / 2;
  const speed = (options.speed as number) ?? 0.5;
  const shape = (options.shape as string) ?? "circle"; // "circle" or "square"
  const maxRadius = Math.sqrt(centerX * centerX + centerY * centerY);

  const radius = (frameIndex * speed) % (maxRadius + 5);
  const thickness = 1.5;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const dx = x - centerX;
      const dy = y - centerY;

      let distance: number;
      if (shape === "square") {
        distance = Math.max(Math.abs(dx), Math.abs(dy));
      } else {
        distance = Math.sqrt(dx * dx + dy * dy);
      }

      if (Math.abs(distance - radius) < thickness) {
        frame[y][x] = true;
      }
    }
  }

  return frame;
};

/**
 * Conway's Game of Life
 */
export const gameOfLifePattern: PatternGenerator = (
  width,
  height,
  frameIndex,
  options = {}
) => {
  // Initialize or get previous state
  const initialDensity = (options.density as number) ?? 0.3;

  // For first frame, create random initial state
  if (frameIndex === 0) {
    const frame = createEmptyFrame(width, height);
    const seed = (options.seed as number) ?? 42;
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        const hash = Math.sin(seed + x * 12.9898 + y * 78.233) * 43758.5453;
        frame[y][x] = (hash - Math.floor(hash)) < initialDensity;
      }
    }
    return frame;
  }

  // Note: In practice, we'd need to pass previous state or use a closure
  // For now, just create a deterministic pattern
  const frame = createEmptyFrame(width, height);
  const seed = frameIndex * 1234;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const hash = Math.sin(seed + x * 12.9898 + y * 78.233) * 43758.5453;
      frame[y][x] = (hash - Math.floor(hash)) < initialDensity;
    }
  }

  return frame;
};

/**
 * Matrix-style falling characters
 */
export const matrixPattern: PatternGenerator = (
  width,
  height,
  frameIndex,
  options = {}
) => {
  const frame = createEmptyFrame(width, height);
  const density = (options.density as number) ?? 0.2;
  const speed = (options.speed as number) ?? 1;

  for (let x = 0; x < width; x++) {
    const columnSeed = x * 54321;
    const hash = Math.sin(columnSeed) * 10000;
    const shouldHaveTrail = (hash - Math.floor(hash)) < density;

    if (shouldHaveTrail) {
      const trailLength = 5 + Math.floor((hash - Math.floor(hash)) * 5);
      const headY = Math.floor((frameIndex * speed + x * 2) % (height + trailLength));

      for (let i = 0; i < trailLength; i++) {
        const y = headY - i;
        if (y >= 0 && y < height) {
          // Fade out the trail (just on/off for binary display)
          frame[y][x] = i < 3; // Only first 3 pixels of trail
        }
      }
    }
  }

  return frame;
};

/**
 * Sparkle pattern - random sparkles
 */
export const sparklePattern: PatternGenerator = (
  width,
  height,
  frameIndex,
  options = {}
) => {
  const frame = createEmptyFrame(width, height);
  const density = (options.density as number) ?? 0.15;
  const seed = frameIndex * 11111;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const hash = Math.sin(seed + x * 12.9898 + y * 78.233) * 43758.5453;
      const value = hash - Math.floor(hash);

      // Quick sparkle (only on for 1-2 frames)
      const isSparkle = value < density;
      const age = Math.floor(value * 1000) % 3;
      frame[y][x] = isSparkle && age < 1;
    }
  }

  return frame;
};

/**
 * Pulse pattern - pulsing effect from center
 */
export const pulsePattern: PatternGenerator = (
  width,
  height,
  frameIndex,
  options = {}
) => {
  const frame = createEmptyFrame(width, height);
  const centerX = width / 2;
  const centerY = height / 2;
  const speed = (options.speed as number) ?? 0.3;
  const maxRadius = Math.sqrt(centerX * centerX + centerY * centerY);

  const pulseValue = Math.sin(frameIndex * speed * 0.2);
  const threshold = (pulseValue + 1) / 2; // 0 to 1

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const dx = x - centerX;
      const dy = y - centerY;
      const distance = Math.sqrt(dx * dx + dy * dy);
      const normalizedDistance = distance / maxRadius;

      frame[y][x] = normalizedDistance < threshold;
    }
  }

  return frame;
};

/**
 * Scanner pattern - back and forth scanner
 */
export const scanPattern: PatternGenerator = (
  width,
  height,
  frameIndex,
  options = {}
) => {
  const frame = createEmptyFrame(width, height);
  const vertical = options.vertical === true;
  const speed = (options.speed as number) ?? 0.5;

  if (vertical) {
    // Scan up and down
    const totalFrames = height * 2;
    const pos = Math.floor((frameIndex * speed) % totalFrames);
    const y = pos < height ? pos : totalFrames - pos - 1;

    for (let x = 0; x < width; x++) {
      frame[y][x] = true;
      // Add fade trail
      if (y > 0) frame[y - 1][x] = true;
      if (y < height - 1) frame[y + 1][x] = true;
    }
  } else {
    // Scan left and right
    const totalFrames = width * 2;
    const pos = Math.floor((frameIndex * speed) % totalFrames);
    const x = pos < width ? pos : totalFrames - pos - 1;

    for (let y = 0; y < height; y++) {
      frame[y][x] = true;
      // Add fade trail
      if (x > 0) frame[y][x - 1] = true;
      if (x < width - 1) frame[y][x + 1] = true;
    }
  }

  return frame;
};

/**
 * Fire pattern - fire effect from bottom
 */
export const firePattern: PatternGenerator = (
  width,
  height,
  frameIndex,
  options = {}
) => {
  const frame = createEmptyFrame(width, height);
  const intensity = (options.intensity as number) ?? 0.7;
  const seed = frameIndex * 8888;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      // Fire is hotter at bottom
      const heatFactor = 1 - y / height;
      const hash = Math.sin(seed + x * 12.9898 + y * 78.233 + frameIndex * 0.5) * 43758.5453;
      const value = hash - Math.floor(hash);

      frame[y][x] = value < intensity * heatFactor;
    }
  }

  return frame;
};

/**
 * Snake pattern - snake/worm moving around
 */
export const snakePattern: PatternGenerator = (
  width,
  height,
  frameIndex,
  options = {}
) => {
  const frame = createEmptyFrame(width, height);
  const length = (options.length as number) ?? 10;
  const speed = (options.speed as number) ?? 0.5;

  // Parametric snake path (figure-8 or circular)
  const t = frameIndex * speed * 0.1;

  for (let i = 0; i < length; i++) {
    const offset = i * 0.3;
    const x = Math.floor(width / 2 + (width / 3) * Math.sin(t - offset));
    const y = Math.floor(height / 2 + (height / 3) * Math.cos(2 * (t - offset)));

    if (x >= 0 && x < width && y >= 0 && y < height) {
      frame[y][x] = true;
    }
  }

  return frame;
};

/**
 * Pattern registry
 */
export const patterns: Record<string, PatternGenerator> = {
  wave: wavePattern,
  rain: rainPattern,
  spiral: spiralPattern,
  checkerboard: checkerboardPattern,
  random: randomPattern,
  expand: expandPattern,
  gameoflife: gameOfLifePattern,
  matrix: matrixPattern,
  sparkle: sparklePattern,
  pulse: pulsePattern,
  scan: scanPattern,
  fire: firePattern,
  snake: snakePattern,
};
