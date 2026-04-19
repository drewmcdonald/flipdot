import { useState, useEffect } from "react";
import {
  getActiveRotationSource,
  getActiveOverride,
} from "../../convex/lib/rotation";

interface StatusPanelProps {
  display: {
    content: { content_id: string };
    updatedAt: number;
  } | null | undefined;
  config: {
    rotation: { source_id: string; duration_s: number }[];
    overrides: { source_id: string; priority: number }[];
  } | null | undefined;
  sources: { source_id: string }[] | undefined;
}

export function StatusPanel({ display, config, sources }: StatusPanelProps) {
  const [now, setNow] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => setNow(Date.now()), 1000);
    return () => clearInterval(interval);
  }, []);

  const availableIds = new Set((sources ?? []).map((s) => s.source_id));
  const activeOverride = config
    ? getActiveOverride(config.overrides, availableIds)
    : null;
  const activeRotation = config
    ? getActiveRotationSource(config.rotation, now)
    : null;
  const activeSource = activeOverride ?? activeRotation;

  return (
    <section className="panel">
      <h2>Status</h2>
      <div className="status-row">
        <span className="label">Active Source:</span>
        <span className="value">{activeSource ?? "none"}</span>
        {activeOverride && <span className="badge-override">override</span>}
      </div>
      <div className="status-row">
        <span className="label">Content ID:</span>
        <span className="value mono">
          {display?.content?.content_id ?? "---"}
        </span>
      </div>
      <div className="status-row">
        <span className="label">Updated:</span>
        <span className="value">
          {display
            ? new Date(display.updatedAt).toLocaleTimeString()
            : "---"}
        </span>
      </div>
    </section>
  );
}
