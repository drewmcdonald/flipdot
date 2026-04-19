import { describe, it, expect } from "vitest";
import { composeBits } from "./compose";

describe("composeBits", () => {
  it("OR combines two bit arrays", () => {
    const a = [1, 0, 1, 0];
    const b = [0, 1, 1, 0];
    expect(composeBits(a, b, "or")).toEqual([1, 1, 1, 0]);
  });

  it("XOR toggles bits", () => {
    const a = [1, 0, 1, 0];
    const b = [0, 1, 1, 0];
    expect(composeBits(a, b, "xor")).toEqual([1, 1, 0, 0]);
  });

  it("AND intersects bit arrays", () => {
    const a = [1, 0, 1, 0];
    const b = [0, 1, 1, 0];
    expect(composeBits(a, b, "and")).toEqual([0, 0, 1, 0]);
  });

  it("throws on mismatched lengths", () => {
    expect(() => composeBits([1, 0], [1], "or")).toThrow(
      "Bit arrays must be the same length: got 2 and 1"
    );
  });

  it("handles empty arrays", () => {
    expect(composeBits([], [], "or")).toEqual([]);
  });

  it("handles all-zeros", () => {
    const zeros = [0, 0, 0, 0];
    expect(composeBits(zeros, zeros, "or")).toEqual([0, 0, 0, 0]);
    expect(composeBits(zeros, zeros, "xor")).toEqual([0, 0, 0, 0]);
    expect(composeBits(zeros, zeros, "and")).toEqual([0, 0, 0, 0]);
  });

  it("handles all-ones", () => {
    const ones = [1, 1, 1, 1];
    expect(composeBits(ones, ones, "or")).toEqual([1, 1, 1, 1]);
    expect(composeBits(ones, ones, "xor")).toEqual([0, 0, 0, 0]);
    expect(composeBits(ones, ones, "and")).toEqual([1, 1, 1, 1]);
  });
});
