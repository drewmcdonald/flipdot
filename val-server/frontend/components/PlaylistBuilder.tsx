/** @jsxImportSource https://esm.sh/react@18.2.0 */
import React, { useState } from "https://esm.sh/react@18.2.0";
import type { PlaylistItem } from "../types/playlist.ts";
import { AddItemModal } from "./AddItemModal.tsx";

interface PlaylistBuilderProps {
  onSubmitPlaylist: (items: PlaylistItem[]) => void;
}

export function PlaylistBuilder({ onSubmitPlaylist }: PlaylistBuilderProps) {
  const [items, setItems] = useState<PlaylistItem[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<PlaylistItem | null>(null);
  const [expandedItems, setExpandedItems] = useState<Set<string>>(new Set());

  const handleAddItem = (item: PlaylistItem) => {
    if (editingItem) {
      // Update existing item
      setItems(items.map((i) => (i.id === item.id ? item : i)));
      setEditingItem(null);
    } else {
      // Add new item
      setItems([...items, item]);
    }
  };

  const handleEditItem = (item: PlaylistItem) => {
    setEditingItem(item);
    setIsModalOpen(true);
  };

  const handleDeleteItem = (id: string) => {
    setItems(items.filter((item) => item.id !== id));
  };

  const handleMoveUp = (index: number) => {
    if (index === 0) return;
    const newItems = [...items];
    [newItems[index - 1], newItems[index]] = [newItems[index], newItems[index - 1]];
    setItems(newItems);
  };

  const handleMoveDown = (index: number) => {
    if (index === items.length - 1) return;
    const newItems = [...items];
    [newItems[index], newItems[index + 1]] = [newItems[index + 1], newItems[index]];
    setItems(newItems);
  };

  const toggleExpanded = (id: string) => {
    const newExpanded = new Set(expandedItems);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedItems(newExpanded);
  };

  const handleSubmit = () => {
    if (items.length === 0) {
      alert("Please add at least one item to the playlist");
      return;
    }
    onSubmitPlaylist(items);
  };

  const handleClear = () => {
    if (confirm("Are you sure you want to clear the playlist?")) {
      setItems([]);
    }
  };

  const getItemSummary = (item: PlaylistItem): string => {
    if (item.type === "text") {
      return item.config.text.substring(0, 30) + (item.config.text.length > 30 ? "..." : "");
    } else if (item.type === "pattern") {
      return `${item.config.pattern_type} (${item.config.duration_ms}ms)`;
    } else {
      return `${item.config.transition_type} ${item.config.direction || ""}`.trim();
    }
  };

  const getItemTypeColor = (type: string): string => {
    switch (type) {
      case "text": return "#3b82f6";
      case "pattern": return "#8b5cf6";
      case "transition": return "#10b981";
      default: return "#6b7280";
    }
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
      <div style={{ marginBottom: "1.5rem" }}>
        <h2 style={{ marginTop: 0, fontSize: "1.25rem", marginBottom: "0.5rem" }}>
          Playlist Builder
        </h2>
        <p style={{ margin: 0, color: "#6b7280", fontSize: "0.875rem" }}>
          Create a sequence of content items to display on the FlipDot
        </p>
      </div>

      {/* Playlist Items */}
      <div style={{ marginBottom: "1.5rem" }}>
        {items.length === 0 ? (
          <div
            style={{
              padding: "2rem",
              textAlign: "center",
              backgroundColor: "#f9fafb",
              borderRadius: "4px",
              color: "#6b7280",
            }}
          >
            No items in playlist. Click "Add Item" to get started.
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
            {items.map((item, index) => (
              <div
                key={item.id}
                style={{
                  border: "1px solid #e5e7eb",
                  borderRadius: "4px",
                  overflow: "hidden",
                }}
              >
                {/* Item Header */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    padding: "0.75rem",
                    backgroundColor: "#f9fafb",
                    gap: "0.75rem",
                  }}
                >
                  {/* Order Number */}
                  <div
                    style={{
                      width: "24px",
                      height: "24px",
                      borderRadius: "50%",
                      backgroundColor: "#e5e7eb",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      fontSize: "0.75rem",
                      fontWeight: "600",
                    }}
                  >
                    {index + 1}
                  </div>

                  {/* Type Badge */}
                  <div
                    style={{
                      padding: "0.25rem 0.5rem",
                      borderRadius: "4px",
                      backgroundColor: getItemTypeColor(item.type),
                      color: "white",
                      fontSize: "0.75rem",
                      fontWeight: "500",
                      textTransform: "uppercase",
                    }}
                  >
                    {item.type}
                  </div>

                  {/* Summary */}
                  <div style={{ flex: 1, fontSize: "0.875rem" }}>
                    {getItemSummary(item)}
                  </div>

                  {/* Priority Badge */}
                  <div
                    style={{
                      padding: "0.25rem 0.5rem",
                      borderRadius: "4px",
                      backgroundColor: "#f3f4f6",
                      fontSize: "0.75rem",
                    }}
                  >
                    P: {item.priority}
                  </div>

                  {/* Action Buttons */}
                  <div style={{ display: "flex", gap: "0.25rem" }}>
                    <button
                      onClick={() => toggleExpanded(item.id)}
                      style={{
                        padding: "0.25rem 0.5rem",
                        border: "none",
                        background: "transparent",
                        cursor: "pointer",
                        fontSize: "0.875rem",
                      }}
                      title="Toggle details"
                    >
                      {expandedItems.has(item.id) ? "▼" : "▶"}
                    </button>
                    <button
                      onClick={() => handleMoveUp(index)}
                      disabled={index === 0}
                      style={{
                        padding: "0.25rem 0.5rem",
                        border: "1px solid #d1d5db",
                        borderRadius: "4px",
                        background: "white",
                        cursor: index === 0 ? "not-allowed" : "pointer",
                        opacity: index === 0 ? 0.5 : 1,
                      }}
                      title="Move up"
                    >
                      ↑
                    </button>
                    <button
                      onClick={() => handleMoveDown(index)}
                      disabled={index === items.length - 1}
                      style={{
                        padding: "0.25rem 0.5rem",
                        border: "1px solid #d1d5db",
                        borderRadius: "4px",
                        background: "white",
                        cursor: index === items.length - 1 ? "not-allowed" : "pointer",
                        opacity: index === items.length - 1 ? 0.5 : 1,
                      }}
                      title="Move down"
                    >
                      ↓
                    </button>
                    <button
                      onClick={() => handleEditItem(item)}
                      style={{
                        padding: "0.25rem 0.5rem",
                        border: "1px solid #d1d5db",
                        borderRadius: "4px",
                        background: "white",
                        cursor: "pointer",
                      }}
                      title="Edit"
                    >
                      ✎
                    </button>
                    <button
                      onClick={() => handleDeleteItem(item.id)}
                      style={{
                        padding: "0.25rem 0.5rem",
                        border: "1px solid #ef4444",
                        borderRadius: "4px",
                        background: "white",
                        color: "#ef4444",
                        cursor: "pointer",
                      }}
                      title="Delete"
                    >
                      ✕
                    </button>
                  </div>
                </div>

                {/* Expanded Details */}
                {expandedItems.has(item.id) && (
                  <div
                    style={{
                      padding: "0.75rem",
                      backgroundColor: "white",
                      borderTop: "1px solid #e5e7eb",
                      fontSize: "0.875rem",
                    }}
                  >
                    {item.type === "text" && (
                      <div>
                        <div><strong>Text:</strong> {item.config.text}</div>
                        <div><strong>Scroll:</strong> {item.config.scroll ? "Yes" : "No"}</div>
                        <div><strong>Frame Delay:</strong> {item.config.frame_delay_ms}ms</div>
                      </div>
                    )}
                    {item.type === "pattern" && (
                      <div>
                        <div><strong>Pattern:</strong> {item.config.pattern_type}</div>
                        <div><strong>Duration:</strong> {item.config.duration_ms}ms</div>
                        <div><strong>Frame Delay:</strong> {item.config.frame_delay_ms}ms</div>
                      </div>
                    )}
                    {item.type === "transition" && (
                      <div>
                        <div><strong>Transition:</strong> {item.config.transition_type}</div>
                        <div><strong>Direction:</strong> {item.config.direction || "N/A"}</div>
                        <div><strong>Duration:</strong> {item.config.duration_ms}ms</div>
                      </div>
                    )}
                    <div style={{ marginTop: "0.5rem", paddingTop: "0.5rem", borderTop: "1px solid #e5e7eb" }}>
                      <strong>Display Time:</strong> {(item.ttl_ms || 0) / 1000}s
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Action Buttons */}
      <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
        <button
          onClick={() => {
            setEditingItem(null);
            setIsModalOpen(true);
          }}
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
          + Add Item
        </button>

        <button
          onClick={handleSubmit}
          disabled={items.length === 0}
          style={{
            flex: 1,
            padding: "0.625rem 1.25rem",
            backgroundColor: items.length === 0 ? "#d1d5db" : "#10b981",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: items.length === 0 ? "not-allowed" : "pointer",
            fontWeight: "500",
          }}
        >
          Send Playlist ({items.length})
        </button>

        <button
          onClick={handleClear}
          disabled={items.length === 0}
          style={{
            padding: "0.625rem 1.25rem",
            backgroundColor: items.length === 0 ? "#e5e7eb" : "#6b7280",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: items.length === 0 ? "not-allowed" : "pointer",
            fontWeight: "500",
          }}
        >
          Clear All
        </button>
      </div>

      {/* Info Box */}
      <div
        style={{
          marginTop: "1.5rem",
          padding: "1rem",
          backgroundColor: "#eff6ff",
          borderRadius: "4px",
          fontSize: "0.875rem",
          color: "#1e40af",
        }}
      >
        <strong>💡 Tip:</strong> Items will play in the order shown. Higher priority
        items display first when the playlist is sent to the server. Use transitions
        between content for smooth visual effects.
      </div>

      {/* Add Item Modal */}
      <AddItemModal
        isOpen={isModalOpen}
        onClose={() => {
          setIsModalOpen(false);
          setEditingItem(null);
        }}
        onAdd={handleAddItem}
        editItem={editingItem}
      />
    </div>
  );
}
