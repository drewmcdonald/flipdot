import { describe, it, expect } from "vitest";
import { getActiveRotationSource, getActiveOverride } from "./lib/rotation";

describe("getActiveRotationSource", () => {
  it("returns null for empty rotation", () => {
    expect(getActiveRotationSource([], 0)).toBeNull();
  });

  it("returns the only source for single-item rotation", () => {
    const rotation = [{ source_id: "clock", duration_s: 60 }];
    expect(getActiveRotationSource(rotation, 0)).toBe("clock");
    expect(getActiveRotationSource(rotation, 999999)).toBe("clock");
  });

  it("cycles through sources based on time", () => {
    const rotation = [
      { source_id: "clock", duration_s: 50 },
      { source_id: "weather", duration_s: 10 },
    ];
    // Cycle is 60s total. Position = (time_ms / 1000) % 60

    // t=0s → clock (position 0, within [0, 50))
    expect(getActiveRotationSource(rotation, 0)).toBe("clock");

    // t=25s → clock (position 25, within [0, 50))
    expect(getActiveRotationSource(rotation, 25_000)).toBe("clock");

    // t=49s → clock (position 49, within [0, 50))
    expect(getActiveRotationSource(rotation, 49_000)).toBe("clock");

    // t=50s → weather (position 50, within [50, 60))
    expect(getActiveRotationSource(rotation, 50_000)).toBe("weather");

    // t=55s → weather (position 55, within [50, 60))
    expect(getActiveRotationSource(rotation, 55_000)).toBe("weather");

    // t=60s → clock again (position 0, cycle wraps)
    expect(getActiveRotationSource(rotation, 60_000)).toBe("clock");

    // t=110s → weather (position 50)
    expect(getActiveRotationSource(rotation, 110_000)).toBe("weather");
  });

  it("handles three sources", () => {
    const rotation = [
      { source_id: "a", duration_s: 10 },
      { source_id: "b", duration_s: 20 },
      { source_id: "c", duration_s: 30 },
    ];
    // Cycle = 60s

    expect(getActiveRotationSource(rotation, 0)).toBe("a"); // position 0
    expect(getActiveRotationSource(rotation, 5_000)).toBe("a"); // position 5
    expect(getActiveRotationSource(rotation, 10_000)).toBe("b"); // position 10
    expect(getActiveRotationSource(rotation, 29_000)).toBe("b"); // position 29
    expect(getActiveRotationSource(rotation, 30_000)).toBe("c"); // position 30
    expect(getActiveRotationSource(rotation, 59_000)).toBe("c"); // position 59
    expect(getActiveRotationSource(rotation, 60_000)).toBe("a"); // wraps
  });

  it("returns null for zero total duration", () => {
    const rotation = [
      { source_id: "a", duration_s: 0 },
      { source_id: "b", duration_s: 0 },
    ];
    expect(getActiveRotationSource(rotation, 1000)).toBeNull();
  });

  it("is deterministic — same time always gives same result", () => {
    const rotation = [
      { source_id: "clock", duration_s: 30 },
      { source_id: "weather", duration_s: 30 },
    ];
    const t = 45_000;
    const result1 = getActiveRotationSource(rotation, t);
    const result2 = getActiveRotationSource(rotation, t);
    expect(result1).toBe(result2);
    expect(result1).toBe("weather");
  });
});

describe("getActiveOverride", () => {
  it("returns null when no overrides configured", () => {
    expect(getActiveOverride([], new Set(["clock"]))).toBeNull();
  });

  it("returns null when override source has no content", () => {
    const overrides = [{ source_id: "pomodoro", priority: 100 }];
    expect(getActiveOverride(overrides, new Set(["clock"]))).toBeNull();
  });

  it("returns override source when it has content", () => {
    const overrides = [{ source_id: "pomodoro", priority: 100 }];
    expect(
      getActiveOverride(overrides, new Set(["clock", "pomodoro"]))
    ).toBe("pomodoro");
  });

  it("returns highest priority override when multiple are active", () => {
    const overrides = [
      { source_id: "alert", priority: 200 },
      { source_id: "pomodoro", priority: 100 },
    ];
    expect(
      getActiveOverride(overrides, new Set(["clock", "pomodoro", "alert"]))
    ).toBe("alert");
  });

  it("skips inactive overrides and returns next active one", () => {
    const overrides = [
      { source_id: "alert", priority: 200 },
      { source_id: "pomodoro", priority: 100 },
    ];
    // alert has no content, only pomodoro does
    expect(
      getActiveOverride(overrides, new Set(["clock", "pomodoro"]))
    ).toBe("pomodoro");
  });

  it("handles priority ties deterministically", () => {
    const overrides = [
      { source_id: "a", priority: 100 },
      { source_id: "b", priority: 100 },
    ];
    const result = getActiveOverride(overrides, new Set(["a", "b"]));
    // Sort is stable for equal priorities, so first in the array wins
    expect(result).toBe("a");
  });
});
