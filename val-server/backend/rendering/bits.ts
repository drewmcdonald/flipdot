/**
 * Bit packing utilities for FlipDot frame data
 * Implements little-endian packed bit format per CONTENT_SERVER_SPEC.md Section 4
 */

/**
 * Pack bits into bytes using little-endian format
 * LSB (least significant bit) is first in the bit array
 *
 * Example: [1,0,1,0, 1,1,0,0] -> 0b00110101 = 0x35
 *
 * @param bits Array of 0s and 1s representing pixel data
 * @returns Uint8Array of packed bytes
 */
export function packBitsLittleEndian(bits: number[]): Uint8Array {
  const byteArray = new Uint8Array(Math.ceil(bits.length / 8));

  for (let i = 0; i < bits.length; i++) {
    if (bits[i]) {
      const byteIndex = Math.floor(i / 8);
      const bitIndex = i % 8;
      byteArray[byteIndex] |= 1 << bitIndex;
    }
  }

  return byteArray;
}

/**
 * Convert packed bytes to base64 string
 *
 * @param bits Array of 0s and 1s
 * @returns Base64-encoded string
 */
export function bitsToBase64(bits: number[]): string {
  const packed = packBitsLittleEndian(bits);
  return btoa(String.fromCharCode(...packed));
}

/**
 * Unpack base64 string back to bit array (for testing/debugging)
 *
 * @param base64 Base64-encoded packed bits
 * @param expectedLength Expected number of bits
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
