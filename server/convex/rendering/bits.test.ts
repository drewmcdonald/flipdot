import { describe, it, expect } from "vitest";
import { packBitsLittleEndian, bitsToBase64, base64ToBits } from "./bits";

describe("packBitsLittleEndian", () => {
  it("returns empty output for empty input", () => {
    const packed = packBitsLittleEndian([]);
    expect(packed).toEqual(new Uint8Array([]));
    expect(packed.length).toBe(0);
  });

  it("packs all zeros (8 bits)", () => {
    const bits = Array(8).fill(0);
    const packed = packBitsLittleEndian(bits);
    expect(packed).toEqual(new Uint8Array([0x00]));
  });

  it("packs all zeros (16 bits)", () => {
    const bits = Array(16).fill(0);
    const packed = packBitsLittleEndian(bits);
    expect(packed).toEqual(new Uint8Array([0x00, 0x00]));
  });

  it("packs all ones (8 bits)", () => {
    const bits = Array(8).fill(1);
    const packed = packBitsLittleEndian(bits);
    expect(packed).toEqual(new Uint8Array([0xff]));
  });

  it("packs all ones (16 bits)", () => {
    const bits = Array(16).fill(1);
    const packed = packBitsLittleEndian(bits);
    expect(packed).toEqual(new Uint8Array([0xff, 0xff]));
  });

  it("packs alternating pattern 10101010", () => {
    const bits = [1, 0, 1, 0, 1, 0, 1, 0];
    const packed = packBitsLittleEndian(bits);
    // Little-endian: bit 0 is LSB, so 10101010 -> 0x55 (01010101)
    expect(packed).toEqual(new Uint8Array([0x55]));
  });

  it("packs alternating pattern 01010101", () => {
    const bits = [0, 1, 0, 1, 0, 1, 0, 1];
    const packed = packBitsLittleEndian(bits);
    // Little-endian: 01010101 -> 0xAA (10101010)
    expect(packed).toEqual(new Uint8Array([0xaa]));
  });

  it("packs a single 0 bit", () => {
    expect(packBitsLittleEndian([0])).toEqual(new Uint8Array([0x00]));
  });

  it("packs a single 1 bit", () => {
    expect(packBitsLittleEndian([1])).toEqual(new Uint8Array([0x01]));
  });

  it("packs partial bytes with correct zero-padding", () => {
    for (let length = 1; length < 8; length++) {
      const bits = Array(length).fill(1);
      const packed = packBitsLittleEndian(bits);
      const expected = (1 << length) - 1;
      expect(packed).toEqual(new Uint8Array([expected]));
    }
  });

  it("packs multiple complete bytes", () => {
    const bits = [
      ...Array(8).fill(1),
      ...Array(8).fill(0),
      ...Array(8).fill(1),
    ];
    const packed = packBitsLittleEndian(bits);
    expect(packed).toEqual(new Uint8Array([0xff, 0x00, 0xff]));
  });

  it("handles specific bit pattern revealing endianness (first bit set)", () => {
    // bit[0]=1, rest 0 -> LSB is set -> 0x01
    const bits = [1, 0, 0, 0, 0, 0, 0, 0];
    const packed = packBitsLittleEndian(bits);
    expect(packed).toEqual(new Uint8Array([0x01]));
  });

  it("handles specific bit pattern revealing endianness (last bit set)", () => {
    // bit[7]=1, rest 0 -> MSB is set -> 0x80
    const bits = [0, 0, 0, 0, 0, 0, 0, 1];
    const packed = packBitsLittleEndian(bits);
    expect(packed).toEqual(new Uint8Array([0x80]));
  });

  it("handles large arrays", () => {
    const size = 1024;
    const bits = Array.from({ length: size }, (_, i) => i % 2);
    const packed = packBitsLittleEndian(bits);
    expect(packed.length).toBe(size / 8);
    // Each byte should be 0xAA (alternating starting with 0 at LSB)
    for (let i = 0; i < packed.length; i++) {
      expect(packed[i]).toBe(0xaa);
    }
  });
});

describe("bitsToBase64", () => {
  it("converts empty bits to empty base64", () => {
    const b64 = bitsToBase64([]);
    expect(b64).toBe("");
  });

  it("converts all zeros to correct base64", () => {
    const bits = Array(8).fill(0);
    const b64 = bitsToBase64(bits);
    // 0x00 -> base64 "AA=="
    expect(b64).toBe(btoa(String.fromCharCode(0x00)));
  });

  it("converts all ones to correct base64", () => {
    const bits = Array(8).fill(1);
    const b64 = bitsToBase64(bits);
    // 0xFF -> base64 "/w=="
    expect(b64).toBe(btoa(String.fromCharCode(0xff)));
  });
});

describe("base64ToBits", () => {
  it("decodes base64 back to bits for all zeros", () => {
    const b64 = btoa(String.fromCharCode(0x00));
    const bits = base64ToBits(b64, 8);
    expect(bits).toEqual(Array(8).fill(0));
  });

  it("decodes base64 back to bits for all ones", () => {
    const b64 = btoa(String.fromCharCode(0xff));
    const bits = base64ToBits(b64, 8);
    expect(bits).toEqual(Array(8).fill(1));
  });

  it("respects expectedLength to truncate padding bits", () => {
    // Pack 5 ones -> byte = 0x1F, base64 encode
    const b64 = bitsToBase64([1, 1, 1, 1, 1]);
    const bits = base64ToBits(b64, 5);
    expect(bits).toEqual([1, 1, 1, 1, 1]);
    expect(bits.length).toBe(5);
  });
});

describe("bitsToBase64 / base64ToBits round-trip", () => {
  it("round-trips all zeros", () => {
    const original = Array(8).fill(0);
    const b64 = bitsToBase64(original);
    const result = base64ToBits(b64, original.length);
    expect(result).toEqual(original);
  });

  it("round-trips all ones", () => {
    const original = Array(8).fill(1);
    const b64 = bitsToBase64(original);
    const result = base64ToBits(b64, original.length);
    expect(result).toEqual(original);
  });

  it("round-trips alternating pattern", () => {
    const original = [1, 0, 1, 0, 1, 0, 1, 0];
    const b64 = bitsToBase64(original);
    const result = base64ToBits(b64, original.length);
    expect(result).toEqual(original);
  });

  it("round-trips partial byte (not divisible by 8)", () => {
    const original = [1, 0, 1, 1, 0];
    const b64 = bitsToBase64(original);
    const result = base64ToBits(b64, original.length);
    expect(result).toEqual(original);
  });

  it("round-trips single bit 0", () => {
    const original = [0];
    const b64 = bitsToBase64(original);
    const result = base64ToBits(b64, original.length);
    expect(result).toEqual(original);
  });

  it("round-trips single bit 1", () => {
    const original = [1];
    const b64 = bitsToBase64(original);
    const result = base64ToBits(b64, original.length);
    expect(result).toEqual(original);
  });

  it("round-trips multiple bytes", () => {
    const original = [
      1, 0, 1, 0, 1, 0, 1, 0, 0, 1, 0, 1, 0, 1, 0, 1, 1, 1, 1, 1, 0, 0, 0,
      0,
    ];
    const b64 = bitsToBase64(original);
    const result = base64ToBits(b64, original.length);
    expect(result).toEqual(original);
  });

  it("round-trips large array", () => {
    const original = Array.from({ length: 1000 }, (_, i) => i % 2);
    const b64 = bitsToBase64(original);
    const result = base64ToBits(b64, original.length);
    expect(result).toEqual(original);
  });

  it("round-trips random-like pattern", () => {
    // Deterministic pseudo-random pattern
    const original = Array.from(
      { length: 256 },
      (_, i) => ((i * 7 + 3) % 11) % 2,
    );
    const b64 = bitsToBase64(original);
    const result = base64ToBits(b64, original.length);
    expect(result).toEqual(original);
  });
});
