/** @jsxImportSource https://esm.sh/react@18.2.0 */
import React, { useState } from "https://esm.sh/react@18.2.0";

interface ControlPanelProps {
  onSendMessage: (formData: {
    text: string;
    priority: number;
    duration: number;
    scroll: boolean;
    font: string;
  }) => void;
  onClearAll: () => void;
  onTogglePolling: () => void;
  isPolling: boolean;
}

export function ControlPanel({
  onSendMessage,
  onClearAll,
  onTogglePolling,
  isPolling,
}: ControlPanelProps) {
  const [text, setText] = useState("");
  const [priority, setPriority] = useState(30);
  const [duration, setDuration] = useState(60);
  const [scroll, setScroll] = useState(false);
  const [font, setFont] = useState("axion_6x7");

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!text.trim()) return;

    onSendMessage({
      text: text.trim(),
      priority,
      duration,
      scroll,
      font,
    });

    // Reset form
    setText("");
    setScroll(false);
  };

  return (
    <div
      style={{
        background: "white",
        borderRadius: "8px",
        padding: "1.5rem",
        boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
      }}
    >
      <h2 style={{ marginTop: 0, fontSize: "1.25rem", marginBottom: "1.5rem" }}>
        Send Message
      </h2>

      <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "1.25rem" }}>
        <div>
          <label
            htmlFor="messageText"
            style={{
              display: "block",
              marginBottom: "0.5rem",
              fontWeight: "500",
              fontSize: "0.875rem",
            }}
          >
            Message Text:
          </label>
          <input
            type="text"
            id="messageText"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="HELLO WORLD"
            maxLength={100}
            required
            style={{
              width: "100%",
              padding: "0.5rem",
              border: "1px solid #d1d5db",
              borderRadius: "4px",
              fontSize: "1rem",
            }}
          />
          <small style={{ color: "#9ca3af", fontSize: "0.8rem" }}>
            Text longer than display width will auto-scroll
          </small>
        </div>

        <div>
          <label
            htmlFor="messageFont"
            style={{
              display: "block",
              marginBottom: "0.5rem",
              fontWeight: "500",
              fontSize: "0.875rem",
            }}
          >
            Font:
          </label>
          <select
            id="messageFont"
            value={font}
            onChange={(e) => setFont(e.target.value)}
            style={{
              width: "100%",
              padding: "0.5rem",
              border: "1px solid #d1d5db",
              borderRadius: "4px",
              fontSize: "1rem",
              backgroundColor: "white",
            }}
          >
            <option value="axion_6x7">Axion 6x7 (default)</option>
            <option value="cg_pixel_4x5">CG Pixel 4x5</option>
            <option value="hanover_6x13m">Hanover 6x13m</option>
          </select>
        </div>

        <div>
          <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
            <input
              type="checkbox"
              checked={scroll}
              onChange={(e) => setScroll(e.target.checked)}
              style={{ width: "auto" }}
            />
            <span style={{ fontSize: "0.875rem" }}>
              Force scrolling (even for short text)
            </span>
          </label>
        </div>

        <div>
          <label
            htmlFor="messagePriority"
            style={{
              display: "block",
              marginBottom: "0.5rem",
              fontWeight: "500",
              fontSize: "0.875rem",
            }}
          >
            Priority: {priority}
          </label>
          <input
            type="range"
            id="messagePriority"
            value={priority}
            onChange={(e) => setPriority(Number(e.target.value))}
            min="0"
            max="100"
            style={{ width: "100%" }}
          />
          <small style={{ color: "#9ca3af", fontSize: "0.8rem" }}>
            Higher priority messages override lower priority (Clock is 10)
          </small>
        </div>

        <div>
          <label
            htmlFor="messageDuration"
            style={{
              display: "block",
              marginBottom: "0.5rem",
              fontWeight: "500",
              fontSize: "0.875rem",
            }}
          >
            Duration: {duration}s
          </label>
          <input
            type="range"
            id="messageDuration"
            value={duration}
            onChange={(e) => setDuration(Number(e.target.value))}
            min="10"
            max="300"
            step="10"
            style={{ width: "100%" }}
          />
        </div>

        <div style={{ display: "flex", gap: "0.75rem" }}>
          <button
            type="submit"
            style={{
              flex: 1,
              padding: "0.625rem 1.25rem",
              backgroundColor: "#3b82f6",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontWeight: "500",
            }}
          >
            Send Message
          </button>

          <button
            type="button"
            onClick={onTogglePolling}
            style={{
              padding: "0.625rem 1.25rem",
              backgroundColor: isPolling ? "#ef4444" : "#10b981",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontWeight: "500",
            }}
          >
            {isPolling ? "Pause" : "Resume"}
          </button>

          <button
            type="button"
            onClick={onClearAll}
            style={{
              padding: "0.625rem 1.25rem",
              backgroundColor: "#6b7280",
              color: "white",
              border: "none",
              borderRadius: "4px",
              cursor: "pointer",
              fontWeight: "500",
            }}
          >
            Clear All
          </button>
        </div>
      </form>

      <div
        style={{
          marginTop: "1.5rem",
          padding: "1rem",
          backgroundColor: "#f9fafb",
          borderRadius: "4px",
          fontSize: "0.875rem",
        }}
      >
        <h3 style={{ marginTop: 0, fontSize: "1rem", marginBottom: "0.5rem" }}>
          Priority Guide:
        </h3>
        <ul style={{ margin: 0, paddingLeft: "1.25rem" }}>
          <li>Clock: 10 (default, always visible)</li>
          <li>Text messages: 20-40 (temporary override)</li>
          <li>Alerts: 50-100 (high priority)</li>
        </ul>
      </div>
    </div>
  );
}
