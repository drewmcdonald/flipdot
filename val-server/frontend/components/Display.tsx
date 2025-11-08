/** @jsxImportSource https://esm.sh/react@18.2.0 */
import React from "https://esm.sh/react@18.2.0";

interface DisplayProps {
  bits: number[];
  isPolling: boolean;
}

export function Display({ bits, isPolling }: DisplayProps) {
  const DISPLAY_WIDTH = 28;
  const DISPLAY_HEIGHT = 14;

  return (
    <div
      style={{
        background: "white",
        borderRadius: "8px",
        padding: "1.5rem",
        boxShadow: "0 1px 3px rgba(0,0,0,0.1)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: "1rem",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "0.5rem",
          fontSize: "0.875rem",
          color: "#6b7280",
        }}
      >
        <div
          style={{
            width: "8px",
            height: "8px",
            borderRadius: "50%",
            backgroundColor: isPolling ? "#10b981" : "#ef4444",
            animation: isPolling ? "pulse 2s infinite" : "none",
          }}
        />
        {isPolling ? "Live (polling every 2s)" : "Paused"}
      </div>

      <div
        style={{
          display: "inline-grid",
          gridTemplateColumns: `repeat(${DISPLAY_WIDTH}, 12px)`,
          gridTemplateRows: `repeat(${DISPLAY_HEIGHT}, 12px)`,
          gap: "2px",
          padding: "1rem",
          backgroundColor: "#1f2937",
          borderRadius: "4px",
          border: "3px solid #374151",
        }}
      >
        {bits.map((bit, idx) => (
          <div
            key={idx}
            style={{
              width: "12px",
              height: "12px",
              backgroundColor: bit ? "#fbbf24" : "#374151",
              borderRadius: "50%",
            }}
          />
        ))}
      </div>

      <style>
        {`
          @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
          }

          @media (max-width: 768px) {
            .display-grid {
              grid-template-columns: repeat(28, 8px) !important;
              grid-template-rows: repeat(14, 8px) !important;
            }
            .display-grid > div {
              width: 8px !important;
              height: 8px !important;
            }
          }
        `}
      </style>
    </div>
  );
}
