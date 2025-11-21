/** @jsxImportSource https://esm.sh/react@18.2.0 */
import React, { useState, useEffect } from "https://esm.sh/react@18.2.0";
import type {
  PlaylistItem,
  PatternInfo,
  TransitionInfo,
} from "../types/playlist.ts";

interface AddItemModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (item: PlaylistItem) => void;
  editItem?: PlaylistItem | null;
}

export function AddItemModal({
  isOpen,
  onClose,
  onAdd,
  editItem,
}: AddItemModalProps) {
  const [itemType, setItemType] = useState<"text" | "pattern" | "transition">(
    "text"
  );
  const [patterns, setPatterns] = useState<PatternInfo[]>([]);
  const [transitions, setTransitions] = useState<TransitionInfo[]>([]);

  // Text fields
  const [text, setText] = useState("");
  const [scroll, setScroll] = useState(false);
  const [textFrameDelay, setTextFrameDelay] = useState(100);

  // Pattern fields
  const [patternType, setPatternType] = useState("wave");
  const [patternDuration, setPatternDuration] = useState(3000);
  const [patternFrameDelay, setPatternFrameDelay] = useState(100);
  const [patternOptions, setPatternOptions] = useState<Record<string, any>>({});

  // Transition fields
  const [transitionType, setTransitionType] = useState("wipe");
  const [transitionDuration, setTransitionDuration] = useState(1000);
  const [transitionFrameDelay, setTransitionFrameDelay] = useState(50);
  const [transitionDirection, setTransitionDirection] = useState("left");

  // Common fields
  const [priority, setPriority] = useState(20);
  const [ttl, setTtl] = useState(60);

  // Load patterns and transitions on mount
  useEffect(() => {
    const loadOptions = async () => {
      try {
        const patternsRes = await fetch("/api/flipdot/patterns/list", {
          headers: { "X-API-Key": "local-dev-key" },
        });
        if (patternsRes.ok) {
          const data = await patternsRes.json();
          setPatterns(data.patterns || []);
        }

        const transitionsRes = await fetch("/api/flipdot/transitions/list", {
          headers: { "X-API-Key": "local-dev-key" },
        });
        if (transitionsRes.ok) {
          const data = await transitionsRes.json();
          setTransitions(data.transitions || []);
        }
      } catch (error) {
        console.error("Failed to load patterns/transitions:", error);
      }
    };

    if (isOpen) {
      loadOptions();
    }
  }, [isOpen]);

  // Populate form when editing
  useEffect(() => {
    if (editItem) {
      setItemType(editItem.type);
      setPriority(editItem.priority);
      setTtl((editItem.ttl_ms || 60000) / 1000);

      if (editItem.type === "text") {
        setText(editItem.config.text);
        setScroll(editItem.config.scroll || false);
        setTextFrameDelay(editItem.config.frame_delay_ms || 100);
      } else if (editItem.type === "pattern") {
        setPatternType(editItem.config.pattern_type);
        setPatternDuration(editItem.config.duration_ms || 3000);
        setPatternFrameDelay(editItem.config.frame_delay_ms || 100);
        setPatternOptions(editItem.config.options || {});
      } else if (editItem.type === "transition") {
        setTransitionType(editItem.config.transition_type);
        setTransitionDuration(editItem.config.duration_ms || 1000);
        setTransitionFrameDelay(editItem.config.frame_delay_ms || 50);
        setTransitionDirection(editItem.config.direction || "left");
      }
    }
  }, [editItem]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    const baseItem = {
      id: editItem?.id || crypto.randomUUID(),
      priority,
      ttl_ms: ttl * 1000,
    };

    let item: PlaylistItem;

    if (itemType === "text") {
      item = {
        ...baseItem,
        type: "text",
        config: {
          text: text.toUpperCase(),
          scroll,
          frame_delay_ms: textFrameDelay,
        },
      };
    } else if (itemType === "pattern") {
      item = {
        ...baseItem,
        type: "pattern",
        config: {
          pattern_type: patternType,
          duration_ms: patternDuration,
          frame_delay_ms: patternFrameDelay,
          options: patternOptions,
        },
      };
    } else {
      item = {
        ...baseItem,
        type: "transition",
        config: {
          transition_type: transitionType,
          duration_ms: transitionDuration,
          frame_delay_ms: transitionFrameDelay,
          direction: transitionDirection,
        },
      };
    }

    onAdd(item);
    handleClose();
  };

  const handleClose = () => {
    // Reset form
    setText("");
    setScroll(false);
    setTextFrameDelay(100);
    setPatternType("wave");
    setPatternDuration(3000);
    setPatternFrameDelay(100);
    setPatternOptions({});
    setTransitionType("wipe");
    setTransitionDuration(1000);
    setTransitionFrameDelay(50);
    setTransitionDirection("left");
    setPriority(20);
    setTtl(60);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: "rgba(0, 0, 0, 0.5)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
      onClick={handleClose}
    >
      <div
        style={{
          backgroundColor: "white",
          borderRadius: "8px",
          padding: "2rem",
          maxWidth: "600px",
          width: "90%",
          maxHeight: "90vh",
          overflow: "auto",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 style={{ marginTop: 0, marginBottom: "1.5rem" }}>
          {editItem ? "Edit" : "Add"} Playlist Item
        </h2>

        <form onSubmit={handleSubmit}>
          {/* Item Type Selector */}
          <div style={{ marginBottom: "1.5rem" }}>
            <label
              style={{
                display: "block",
                marginBottom: "0.5rem",
                fontWeight: "500",
              }}
            >
              Item Type:
            </label>
            <div style={{ display: "flex", gap: "1rem" }}>
              {(["text", "pattern", "transition"] as const).map((type) => (
                <label key={type} style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <input
                    type="radio"
                    value={type}
                    checked={itemType === type}
                    onChange={(e) =>
                      setItemType(e.target.value as typeof itemType)
                    }
                    disabled={!!editItem}
                  />
                  <span style={{ textTransform: "capitalize" }}>{type}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Text Configuration */}
          {itemType === "text" && (
            <>
              <div style={{ marginBottom: "1rem" }}>
                <label
                  style={{
                    display: "block",
                    marginBottom: "0.5rem",
                    fontWeight: "500",
                  }}
                >
                  Text:
                </label>
                <input
                  type="text"
                  value={text}
                  onChange={(e) => setText(e.target.value)}
                  required
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    border: "1px solid #d1d5db",
                    borderRadius: "4px",
                  }}
                />
              </div>

              <div style={{ marginBottom: "1rem" }}>
                <label style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                  <input
                    type="checkbox"
                    checked={scroll}
                    onChange={(e) => setScroll(e.target.checked)}
                  />
                  <span>Force scrolling</span>
                </label>
              </div>

              <div style={{ marginBottom: "1rem" }}>
                <label
                  style={{
                    display: "block",
                    marginBottom: "0.5rem",
                    fontWeight: "500",
                  }}
                >
                  Frame Delay: {textFrameDelay}ms
                </label>
                <input
                  type="range"
                  value={textFrameDelay}
                  onChange={(e) => setTextFrameDelay(Number(e.target.value))}
                  min="50"
                  max="300"
                  step="10"
                  style={{ width: "100%" }}
                />
              </div>
            </>
          )}

          {/* Pattern Configuration */}
          {itemType === "pattern" && (
            <>
              <div style={{ marginBottom: "1rem" }}>
                <label
                  style={{
                    display: "block",
                    marginBottom: "0.5rem",
                    fontWeight: "500",
                  }}
                >
                  Pattern Type:
                </label>
                <select
                  value={patternType}
                  onChange={(e) => setPatternType(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    border: "1px solid #d1d5db",
                    borderRadius: "4px",
                  }}
                >
                  {patterns.map((p) => (
                    <option key={p.type} value={p.type}>
                      {p.type} - {p.description}
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ marginBottom: "1rem" }}>
                <label
                  style={{
                    display: "block",
                    marginBottom: "0.5rem",
                    fontWeight: "500",
                  }}
                >
                  Duration: {patternDuration}ms
                </label>
                <input
                  type="range"
                  value={patternDuration}
                  onChange={(e) => setPatternDuration(Number(e.target.value))}
                  min="1000"
                  max="10000"
                  step="100"
                  style={{ width: "100%" }}
                />
              </div>

              <div style={{ marginBottom: "1rem" }}>
                <label
                  style={{
                    display: "block",
                    marginBottom: "0.5rem",
                    fontWeight: "500",
                  }}
                >
                  Frame Delay: {patternFrameDelay}ms
                </label>
                <input
                  type="range"
                  value={patternFrameDelay}
                  onChange={(e) => setPatternFrameDelay(Number(e.target.value))}
                  min="20"
                  max="200"
                  step="10"
                  style={{ width: "100%" }}
                />
              </div>
            </>
          )}

          {/* Transition Configuration */}
          {itemType === "transition" && (
            <>
              <div style={{ marginBottom: "1rem" }}>
                <label
                  style={{
                    display: "block",
                    marginBottom: "0.5rem",
                    fontWeight: "500",
                  }}
                >
                  Transition Type:
                </label>
                <select
                  value={transitionType}
                  onChange={(e) => setTransitionType(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    border: "1px solid #d1d5db",
                    borderRadius: "4px",
                  }}
                >
                  {transitions.map((t) => (
                    <option key={t.type} value={t.type}>
                      {t.type} - {t.description}
                    </option>
                  ))}
                </select>
              </div>

              <div style={{ marginBottom: "1rem" }}>
                <label
                  style={{
                    display: "block",
                    marginBottom: "0.5rem",
                    fontWeight: "500",
                  }}
                >
                  Duration: {transitionDuration}ms
                </label>
                <input
                  type="range"
                  value={transitionDuration}
                  onChange={(e) => setTransitionDuration(Number(e.target.value))}
                  min="200"
                  max="3000"
                  step="100"
                  style={{ width: "100%" }}
                />
              </div>

              <div style={{ marginBottom: "1rem" }}>
                <label
                  style={{
                    display: "block",
                    marginBottom: "0.5rem",
                    fontWeight: "500",
                  }}
                >
                  Direction:
                </label>
                <select
                  value={transitionDirection}
                  onChange={(e) => setTransitionDirection(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "0.5rem",
                    border: "1px solid #d1d5db",
                    borderRadius: "4px",
                  }}
                >
                  <option value="left">Left</option>
                  <option value="right">Right</option>
                  <option value="up">Up</option>
                  <option value="down">Down</option>
                </select>
              </div>
            </>
          )}

          {/* Common Configuration */}
          <div style={{ marginBottom: "1rem" }}>
            <label
              style={{
                display: "block",
                marginBottom: "0.5rem",
                fontWeight: "500",
              }}
            >
              Priority: {priority}
            </label>
            <input
              type="range"
              value={priority}
              onChange={(e) => setPriority(Number(e.target.value))}
              min="0"
              max="99"
              style={{ width: "100%" }}
            />
            <small style={{ color: "#6b7280" }}>
              Higher priority items display first
            </small>
          </div>

          <div style={{ marginBottom: "1.5rem" }}>
            <label
              style={{
                display: "block",
                marginBottom: "0.5rem",
                fontWeight: "500",
              }}
            >
              Display Time: {ttl}s
            </label>
            <input
              type="range"
              value={ttl}
              onChange={(e) => setTtl(Number(e.target.value))}
              min="5"
              max="300"
              step="5"
              style={{ width: "100%" }}
            />
          </div>

          {/* Action Buttons */}
          <div style={{ display: "flex", gap: "0.75rem", justifyContent: "flex-end" }}>
            <button
              type="button"
              onClick={handleClose}
              style={{
                padding: "0.5rem 1rem",
                backgroundColor: "#e5e7eb",
                color: "#374151",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              Cancel
            </button>
            <button
              type="submit"
              style={{
                padding: "0.5rem 1rem",
                backgroundColor: "#3b82f6",
                color: "white",
                border: "none",
                borderRadius: "4px",
                cursor: "pointer",
              }}
            >
              {editItem ? "Update" : "Add"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
