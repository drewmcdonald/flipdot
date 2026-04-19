import { useState, useEffect } from "react";
import { useMutation } from "convex/react";
import { api } from "../../convex/_generated/api";
import { getActiveRotationSource } from "../../convex/lib/rotation";

interface RotationSlot {
  source_id: string;
  duration_s: number;
}

interface RotationEditorProps {
  config: {
    rotation: RotationSlot[];
    overrides: { source_id: string; priority: number }[];
  } | null | undefined;
  sources: { source_id: string }[] | undefined;
  displayName: string;
}

export function RotationEditor({
  config,
  sources,
  displayName,
}: RotationEditorProps) {
  const updateConfig = useMutation(api.display_config.updateConfig);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState<RotationSlot[]>([]);
  const [newSourceId, setNewSourceId] = useState("");
  const [newDuration, setNewDuration] = useState(60);
  const [now, setNow] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, []);

  if (!config) return null;

  const cycleDuration = config.rotation.reduce(
    (sum, r) => sum + r.duration_s,
    0
  );
  const positionInCycle =
    cycleDuration > 0 ? (now / 1000) % cycleDuration : 0;
  const activeSource = getActiveRotationSource(config.rotation, now);

  const availableSourceIds = (sources ?? []).map((s) => s.source_id);
  const usedSourceIds = new Set(
    (editing ? draft : config.rotation).map((r) => r.source_id)
  );
  const unusedSources = availableSourceIds.filter(
    (id) => !usedSourceIds.has(id)
  );

  const startEditing = () => {
    setDraft([...config.rotation]);
    setEditing(true);
  };

  const handleSave = async () => {
    await updateConfig({
      display_name: displayName,
      rotation: draft,
      overrides: config.overrides,
    });
    setEditing(false);
  };

  const moveSlot = (index: number, direction: -1 | 1) => {
    const target = index + direction;
    if (target < 0 || target >= draft.length) return;
    const next = [...draft];
    [next[index], next[target]] = [next[target], next[index]];
    setDraft(next);
  };

  const removeSlot = (index: number) => {
    setDraft(draft.filter((_, i) => i !== index));
  };

  const updateDuration = (index: number, duration_s: number) => {
    const next = [...draft];
    next[index] = { ...next[index], duration_s };
    setDraft(next);
  };

  const addSlot = () => {
    if (!newSourceId) return;
    setDraft([...draft, { source_id: newSourceId, duration_s: newDuration }]);
    setNewSourceId("");
    setNewDuration(60);
  };

  // Pre-compute slot start positions for read-only view
  const slotStarts = config.rotation.reduce<number[]>((acc, _, i) => {
    acc.push(i === 0 ? 0 : acc[i - 1] + config.rotation[i - 1].duration_s);
    return acc;
  }, []);

  // Read-only view
  if (!editing) {
    return (
      <section className="panel">
        <div className="panel-header">
          <h2>Rotation</h2>
          <button className="btn-sm" onClick={startEditing}>
            Edit
          </button>
        </div>
        <div className="rotation-slots">
          {config.rotation.map((slot, i) => {
            const slotStart = slotStarts[i];
            const slotEnd = slotStart + slot.duration_s;
            const isActive = slot.source_id === activeSource &&
              positionInCycle >= slotStart &&
              positionInCycle < slotEnd;
            return (
              <div
                key={i}
                className={`rotation-slot ${isActive ? "active" : ""}`}
              >
                <span>{slot.source_id}</span>
                <span className="label">{slot.duration_s}s</span>
              </div>
            );
          })}
        </div>
        {cycleDuration > 0 && (
          <div className="label" style={{ marginTop: "0.5rem" }}>
            Cycle: {cycleDuration}s | Position:{" "}
            {Math.floor(positionInCycle)}s
          </div>
        )}
      </section>
    );
  }

  // Edit view
  return (
    <section className="panel">
      <div className="panel-header">
        <h2>Rotation</h2>
        <div className="btn-group">
          <button className="btn-sm" onClick={() => setEditing(false)}>
            Cancel
          </button>
          <button className="btn-sm btn-primary" onClick={handleSave}>
            Save
          </button>
        </div>
      </div>
      <div className="rotation-slots">
        {draft.map((slot, i) => (
          <div key={i} className="rotation-slot editing">
            <span>{slot.source_id}</span>
            <div className="slot-controls">
              <input
                type="number"
                min={1}
                value={slot.duration_s}
                onChange={(e) =>
                  updateDuration(i, parseInt(e.target.value) || 1)
                }
                className="input-sm"
                style={{ width: "60px" }}
              />
              <span className="label">s</span>
              <button
                className="btn-icon"
                onClick={() => moveSlot(i, -1)}
                disabled={i === 0}
              >
                ↑
              </button>
              <button
                className="btn-icon"
                onClick={() => moveSlot(i, 1)}
                disabled={i === draft.length - 1}
              >
                ↓
              </button>
              <button className="btn-icon btn-danger" onClick={() => removeSlot(i)}>
                ×
              </button>
            </div>
          </div>
        ))}
      </div>
      {unusedSources.length > 0 && (
        <div className="add-slot-row">
          <select
            value={newSourceId}
            onChange={(e) => setNewSourceId(e.target.value)}
            className="input-sm"
          >
            <option value="">Add source...</option>
            {unusedSources.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
          <input
            type="number"
            min={1}
            value={newDuration}
            onChange={(e) => setNewDuration(parseInt(e.target.value) || 1)}
            className="input-sm"
            style={{ width: "60px" }}
          />
          <span className="label">s</span>
          <button
            className="btn-sm"
            onClick={addSlot}
            disabled={!newSourceId}
          >
            Add
          </button>
        </div>
      )}
    </section>
  );
}
