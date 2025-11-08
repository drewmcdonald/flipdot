/** @jsxImportSource https://esm.sh/react@18.2.0 */
import React, { useEffect } from "https://esm.sh/react@18.2.0";

interface StatusMessageProps {
  type: "success" | "error" | "info";
  text: string;
  onDismiss: () => void;
}

export function StatusMessage({ type, text, onDismiss }: StatusMessageProps) {
  useEffect(() => {
    const timer = setTimeout(onDismiss, 5000);
    return () => clearTimeout(timer);
  }, [onDismiss]);

  const colors = {
    success: { bg: "#d1fae5", border: "#10b981", text: "#065f46" },
    error: { bg: "#fee2e2", border: "#ef4444", text: "#991b1b" },
    info: { bg: "#dbeafe", border: "#3b82f6", text: "#1e40af" },
  };

  const color = colors[type];

  return (
    <div
      style={{
        marginTop: "1rem",
        padding: "1rem",
        backgroundColor: color.bg,
        border: `1px solid ${color.border}`,
        borderRadius: "4px",
        color: color.text,
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
      }}
    >
      <span>{text}</span>
      <button
        onClick={onDismiss}
        style={{
          background: "none",
          border: "none",
          color: color.text,
          cursor: "pointer",
          fontSize: "1.25rem",
          padding: "0 0.5rem",
        }}
      >
        ×
      </button>
    </div>
  );
}
