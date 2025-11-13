/**
 * Transition Effects
 *
 * Functions to create smooth transitions between frames on the flipdot display.
 */

import type { TransitionGenerator } from "./types.ts";
import { createEmptyFrame } from "./generators.ts";

/**
 * Wipe transition - reveals new frame from a direction
 */
export const wipeTransition: TransitionGenerator = (
  fromFrame,
  toFrame,
  progress,
  options = {}
) => {
  const height = fromFrame.length;
  const width = fromFrame[0]?.length ?? 0;
  const direction = (options.direction as string) ?? "left";

  const result = fromFrame.map(row => [...row]);

  if (direction === "left") {
    const wipeX = Math.floor(progress * width);
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < wipeX; x++) {
        result[y][x] = toFrame[y][x];
      }
    }
  } else if (direction === "right") {
    const wipeX = Math.floor((1 - progress) * width);
    for (let y = 0; y < height; y++) {
      for (let x = wipeX; x < width; x++) {
        result[y][x] = toFrame[y][x];
      }
    }
  } else if (direction === "up") {
    const wipeY = Math.floor(progress * height);
    for (let y = 0; y < wipeY; y++) {
      for (let x = 0; x < width; x++) {
        result[y][x] = toFrame[y][x];
      }
    }
  } else if (direction === "down") {
    const wipeY = Math.floor((1 - progress) * height);
    for (let y = wipeY; y < height; y++) {
      for (let x = 0; x < width; x++) {
        result[y][x] = toFrame[y][x];
      }
    }
  }

  return result;
};

/**
 * Fade transition - dithered fade for binary display
 * Uses a Bayer matrix for ordered dithering
 */
export const fadeTransition: TransitionGenerator = (
  fromFrame,
  toFrame,
  progress,
  options = {}
) => {
  const height = fromFrame.length;
  const width = fromFrame[0]?.length ?? 0;
  const result = createEmptyFrame(width, height);

  // 4x4 Bayer matrix for ordered dithering
  const bayerMatrix = [
    [0, 8, 2, 10],
    [12, 4, 14, 6],
    [3, 11, 1, 9],
    [15, 7, 13, 5]
  ];

  const threshold = progress * 16; // 0 to 16

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const bayerValue = bayerMatrix[y % 4][x % 4];
      const from = fromFrame[y][x];
      const to = toFrame[y][x];

      // If pixels are the same, use that value
      if (from === to) {
        result[y][x] = from;
      } else if (from && !to) {
        // Transitioning from on to off
        result[y][x] = bayerValue >= threshold;
      } else {
        // Transitioning from off to on
        result[y][x] = bayerValue < threshold;
      }
    }
  }

  return result;
};

/**
 * Dissolve transition - random pixel reveal
 */
export const dissolveTransition: TransitionGenerator = (
  fromFrame,
  toFrame,
  progress,
  options = {}
) => {
  const height = fromFrame.length;
  const width = fromFrame[0]?.length ?? 0;
  const result = fromFrame.map(row => [...row]);
  const seed = (options.seed as number) ?? 42;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      // Deterministic pseudo-random value for this pixel
      const hash = Math.sin(seed + x * 12.9898 + y * 78.233) * 43758.5453;
      const pixelThreshold = hash - Math.floor(hash);

      if (progress > pixelThreshold) {
        result[y][x] = toFrame[y][x];
      }
    }
  }

  return result;
};

/**
 * Slide transition - slide in from direction
 */
export const slideTransition: TransitionGenerator = (
  fromFrame,
  toFrame,
  progress,
  options = {}
) => {
  const height = fromFrame.length;
  const width = fromFrame[0]?.length ?? 0;
  const direction = (options.direction as string) ?? "left";
  const result = createEmptyFrame(width, height);

  if (direction === "left") {
    const offset = Math.floor(progress * width);
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        if (x < offset) {
          result[y][x] = toFrame[y][x];
        } else {
          const fromX = x - offset;
          result[y][x] = fromFrame[y][fromX] ?? false;
        }
      }
    }
  } else if (direction === "right") {
    const offset = Math.floor(progress * width);
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        if (x >= width - offset) {
          result[y][x] = toFrame[y][x];
        } else {
          const fromX = x + offset;
          result[y][x] = fromX < width ? fromFrame[y][fromX] : false;
        }
      }
    }
  } else if (direction === "up") {
    const offset = Math.floor(progress * height);
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        if (y < offset) {
          result[y][x] = toFrame[y][x];
        } else {
          const fromY = y - offset;
          result[y][x] = fromFrame[fromY]?.[x] ?? false;
        }
      }
    }
  } else if (direction === "down") {
    const offset = Math.floor(progress * height);
    for (let y = 0; y < height; y++) {
      for (let x = 0; x < width; x++) {
        if (y >= height - offset) {
          result[y][x] = toFrame[y][x];
        } else {
          const fromY = y + offset;
          result[y][x] = fromY < height ? fromFrame[fromY][x] : false;
        }
      }
    }
  }

  return result;
};

/**
 * Checkerboard transition - alternating checkerboard reveal
 */
export const checkerboardTransition: TransitionGenerator = (
  fromFrame,
  toFrame,
  progress,
  options = {}
) => {
  const height = fromFrame.length;
  const width = fromFrame[0]?.length ?? 0;
  const result = fromFrame.map(row => [...row]);
  const size = (options.size as number) ?? 2;

  // First half: reveal checkerboard pattern 1
  // Second half: reveal checkerboard pattern 2
  const phase = progress < 0.5 ? 0 : 1;
  const phaseProgress = (progress % 0.5) * 2;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const checkX = Math.floor(x / size);
      const checkY = Math.floor(y / size);
      const isPattern = ((checkX + checkY) % 2) === phase;

      if (isPattern && progress > 0.25) {
        result[y][x] = toFrame[y][x];
      } else if (!isPattern && progress > 0.75) {
        result[y][x] = toFrame[y][x];
      }
    }
  }

  return result;
};

/**
 * Blinds transition - venetian blinds effect
 */
export const blindsTransition: TransitionGenerator = (
  fromFrame,
  toFrame,
  progress,
  options = {}
) => {
  const height = fromFrame.length;
  const width = fromFrame[0]?.length ?? 0;
  const result = fromFrame.map(row => [...row]);
  const vertical = options.vertical === true;
  const blindSize = (options.blindSize as number) ?? 3;

  if (vertical) {
    for (let x = 0; x < width; x++) {
      const blindIndex = Math.floor(x / blindSize);
      const blindProgress = (progress - (blindIndex % 5) * 0.1) * 1.4;

      if (blindProgress > 0) {
        const revealHeight = Math.floor(blindProgress * height);
        for (let y = 0; y < revealHeight && y < height; y++) {
          result[y][x] = toFrame[y][x];
        }
      }
    }
  } else {
    for (let y = 0; y < height; y++) {
      const blindIndex = Math.floor(y / blindSize);
      const blindProgress = (progress - (blindIndex % 5) * 0.1) * 1.4;

      if (blindProgress > 0) {
        const revealWidth = Math.floor(blindProgress * width);
        for (let x = 0; x < revealWidth && x < width; x++) {
          result[y][x] = toFrame[y][x];
        }
      }
    }
  }

  return result;
};

/**
 * Center out transition - expand from center
 */
export const centerOutTransition: TransitionGenerator = (
  fromFrame,
  toFrame,
  progress,
  options = {}
) => {
  const height = fromFrame.length;
  const width = fromFrame[0]?.length ?? 0;
  const result = fromFrame.map(row => [...row]);
  const centerX = width / 2;
  const centerY = height / 2;
  const maxRadius = Math.sqrt(centerX * centerX + centerY * centerY);
  const currentRadius = progress * maxRadius;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const dx = x - centerX;
      const dy = y - centerY;
      const distance = Math.sqrt(dx * dx + dy * dy);

      if (distance <= currentRadius) {
        result[y][x] = toFrame[y][x];
      }
    }
  }

  return result;
};

/**
 * Corners transition - reveal from corners
 */
export const cornersTransition: TransitionGenerator = (
  fromFrame,
  toFrame,
  progress,
  options = {}
) => {
  const height = fromFrame.length;
  const width = fromFrame[0]?.length ?? 0;
  const result = fromFrame.map(row => [...row]);

  // Four corners expand simultaneously
  const corners = [
    { x: 0, y: 0 },
    { x: width - 1, y: 0 },
    { x: 0, y: height - 1 },
    { x: width - 1, y: height - 1 }
  ];

  const maxDist = Math.sqrt(width * width + height * height) / 2;
  const currentRadius = progress * maxDist;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      // Check distance to nearest corner
      const minDistance = Math.min(
        ...corners.map(corner => {
          const dx = x - corner.x;
          const dy = y - corner.y;
          return Math.sqrt(dx * dx + dy * dy);
        })
      );

      if (minDistance <= currentRadius) {
        result[y][x] = toFrame[y][x];
      }
    }
  }

  return result;
};

/**
 * Spiral transition - spiral from center
 */
export const spiralTransition: TransitionGenerator = (
  fromFrame,
  toFrame,
  progress,
  options = {}
) => {
  const height = fromFrame.length;
  const width = fromFrame[0]?.length ?? 0;
  const result = fromFrame.map(row => [...row]);
  const centerX = width / 2;
  const centerY = height / 2;

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const dx = x - centerX;
      const dy = y - centerY;
      const angle = Math.atan2(dy, dx);
      const distance = Math.sqrt(dx * dx + dy * dy);
      const maxDist = Math.sqrt(centerX * centerX + centerY * centerY);

      // Combine angle and distance for spiral effect
      const spiralValue = (angle / (2 * Math.PI) + 0.5 + distance / maxDist) / 2;

      if (spiralValue <= progress) {
        result[y][x] = toFrame[y][x];
      }
    }
  }

  return result;
};

/**
 * Transition registry
 */
export const transitions: Record<string, TransitionGenerator> = {
  wipe: wipeTransition,
  fade: fadeTransition,
  dissolve: dissolveTransition,
  slide: slideTransition,
  checkerboard: checkerboardTransition,
  blinds: blindsTransition,
  center_out: centerOutTransition,
  corners: cornersTransition,
  spiral: spiralTransition,
};
