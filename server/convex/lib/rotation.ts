/**
 * Pure functions for rotation/override source selection.
 * Shared between compositor (server-side) and control panel (client-side).
 */

/**
 * Given a rotation config and the current time, determine which source_id
 * should be active based on time-based slot calculation.
 */
export function getActiveRotationSource(
  rotation: { source_id: string; duration_s: number }[],
  nowMs: number
): string | null {
  if (rotation.length === 0) return null;
  if (rotation.length === 1) return rotation[0].source_id;

  const cycleDuration = rotation.reduce((sum, r) => sum + r.duration_s, 0);
  if (cycleDuration <= 0) return null;

  const positionInCycle = (nowMs / 1000) % cycleDuration;

  let elapsed = 0;
  for (const slot of rotation) {
    elapsed += slot.duration_s;
    if (positionInCycle < elapsed) {
      return slot.source_id;
    }
  }

  // Fallback (shouldn't happen due to modular arithmetic)
  return rotation[0].source_id;
}

/**
 * Given override config and available source_ids, determine
 * the highest-priority active override.
 */
export function getActiveOverride(
  overrides: { source_id: string; priority: number }[],
  availableSourceIds: Set<string>
): string | null {
  if (overrides.length === 0) return null;

  // Sort by priority descending, pick the first one that has content
  const sorted = [...overrides].sort((a, b) => b.priority - a.priority);
  for (const override of sorted) {
    if (availableSourceIds.has(override.source_id)) {
      return override.source_id;
    }
  }

  return null;
}
