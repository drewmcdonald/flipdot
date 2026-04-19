import { useState } from "react";
import { useMutation } from "convex/react";
import { api } from "../../convex/_generated/api";

interface Override {
  source_id: string;
  priority: number;
}

interface OverrideManagerProps {
  config: {
    rotation: { source_id: string; duration_s: number }[];
    overrides: Override[];
  } | null | undefined;
  sources: { source_id: string }[] | undefined;
  displayName: string;
}

export function OverrideManager({
  config,
  sources,
  displayName,
}: OverrideManagerProps) {
  const updateConfig = useMutation(api.display_config.updateConfig);
  const removeSource = useMutation(api.content.adhoc.removeSource);
  const [newSourceId, setNewSourceId] = useState("");
  const [newPriority, setNewPriority] = useState(50);

  if (!config) return null;

  const sorted = [...config.overrides].sort((a, b) => b.priority - a.priority);

  const overrideSourceIds = new Set(config.overrides.map((o) => o.source_id));
  const availableSources = (sources ?? [])
    .map((s) => s.source_id)
    .filter((id) => !overrideSourceIds.has(id));

  const handleClear = async (sourceId: string) => {
    const newOverrides = config.overrides.filter(
      (o) => o.source_id !== sourceId
    );
    await updateConfig({
      display_name: displayName,
      rotation: config.rotation,
      overrides: newOverrides,
    });
    // If it's an adhoc source, also clean up the content
    if (sourceId.startsWith("adhoc:")) {
      await removeSource({ source_id: sourceId });
    }
  };

  const handleAdd = async () => {
    if (!newSourceId) return;
    await updateConfig({
      display_name: displayName,
      rotation: config.rotation,
      overrides: [
        ...config.overrides,
        { source_id: newSourceId, priority: newPriority },
      ],
    });
    setNewSourceId("");
    setNewPriority(50);
  };

  return (
    <section className="panel">
      <h2>Overrides</h2>
      {sorted.length === 0 ? (
        <p className="label">No active overrides</p>
      ) : (
        <div className="override-list">
          {sorted.map((o) => (
            <div key={o.source_id} className="override-item">
              <span>{o.source_id}</span>
              <span className="label">priority: {o.priority}</span>
              <button
                className="btn-icon btn-danger"
                onClick={() => handleClear(o.source_id)}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}
      {availableSources.length > 0 && (
        <div className="add-slot-row">
          <select
            value={newSourceId}
            onChange={(e) => setNewSourceId(e.target.value)}
            className="input-sm"
          >
            <option value="">Add override...</option>
            {availableSources.map((id) => (
              <option key={id} value={id}>
                {id}
              </option>
            ))}
          </select>
          <input
            type="number"
            min={0}
            value={newPriority}
            onChange={(e) => setNewPriority(parseInt(e.target.value) || 0)}
            className="input-sm"
            style={{ width: "60px" }}
          />
          <span className="label">priority</span>
          <button
            className="btn-sm"
            onClick={handleAdd}
            disabled={!newSourceId}
          >
            Add
          </button>
        </div>
      )}
    </section>
  );
}
