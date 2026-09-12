/**
 * Bit unpacking utilities for FlipDot frame rendering
 * Client-side version of convex/rendering/bits.ts
 */

/**
 * Unpack base64 string back to bit array
 *
 * @param base64 Base64-encoded packed bits (little-endian)
 * @param expectedLength Expected number of bits (width * height)
 * @returns Array of 0s and 1s
 */
export function base64ToBits(base64: string, expectedLength: number): number[] {
  const decoded = atob(base64);
  const bytes = new Uint8Array(decoded.length);
  for (let i = 0; i < decoded.length; i++) {
    bytes[i] = decoded.charCodeAt(i);
  }

  const bits: number[] = [];
  for (let i = 0; i < expectedLength; i++) {
    const byteIndex = Math.floor(i / 8);
    const bitIndex = i % 8;
    const bit = (bytes[byteIndex] >> bitIndex) & 1;
    bits.push(bit);
  }

  return bits;
}
