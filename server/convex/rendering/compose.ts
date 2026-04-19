/**
 * Bit composition utilities for frame overlays
 * Used by composite sources that combine content from multiple sources.
 */

type ComposeMode = "or" | "xor" | "and";

/**
 * Compose two equal-length bit arrays using the specified bitwise operation.
 *
 * @param a First bit array (0s and 1s)
 * @param b Second bit array (0s and 1s)
 * @param mode Bitwise operation: "or" (union), "xor" (toggle), "and" (intersection)
 * @returns New bit array with the result
 */
export function composeBits(
  a: number[],
  b: number[],
  mode: ComposeMode
): number[] {
  if (a.length !== b.length) {
    throw new Error(
      `Bit arrays must be the same length: got ${a.length} and ${b.length}`
    );
  }

  switch (mode) {
    case "or":
      return a.map((bit, i) => bit | b[i]);
    case "xor":
      return a.map((bit, i) => bit ^ b[i]);
    case "and":
      return a.map((bit, i) => bit & b[i]);
  }
}
