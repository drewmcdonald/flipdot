import React, { useState, useRef, useEffect } from "react";

const DISPLAY_WIDTH = 28;
const DISPLAY_HEIGHT = 14;
const PIXEL_SIZE = 20; // Size of each pixel in the canvas
const PIXEL_GAP = 2; // Gap between pixels

interface PaintCanvasProps {
  initialBits?: number[];
  onPaint: (bits: number[]) => void;
  disabled?: boolean;
}

export function PaintCanvas({ initialBits, onPaint, disabled = false }: PaintCanvasProps) {
  const [bits, setBits] = useState<number[]>(
    initialBits || new Array(DISPLAY_WIDTH * DISPLAY_HEIGHT).fill(0),
  );
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawMode, setDrawMode] = useState<"set" | "clear">("set"); // "set" = draw, "clear" = erase
  const canvasRef = useRef<HTMLDivElement>(null);

  // Update bits when initialBits changes
  useEffect(() => {
    if (initialBits) {
      setBits(initialBits);
    }
  }, [initialBits]);

  const getPixelIndex = (x: number, y: number): number => {
    return y * DISPLAY_WIDTH + x;
  };

  const togglePixel = (x: number, y: number) => {
    if (x < 0 || x >= DISPLAY_WIDTH || y < 0 || y >= DISPLAY_HEIGHT) {
      return;
    }

    const index = getPixelIndex(x, y);
    const newBits = [...bits];
    newBits[index] = drawMode === "set" ? 1 : 0;
    setBits(newBits);
    onPaint(newBits);
  };

  const handleMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (disabled) return;

    e.preventDefault();
    setIsDrawing(true);

    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = Math.floor((e.clientX - rect.left) / (PIXEL_SIZE + PIXEL_GAP));
    const y = Math.floor((e.clientY - rect.top) / (PIXEL_SIZE + PIXEL_GAP));

    // Determine draw mode based on current pixel state
    const index = getPixelIndex(x, y);
    setDrawMode(bits[index] === 1 ? "clear" : "set");

    togglePixel(x, y);
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLDivElement>) => {
    if (!isDrawing || disabled) return;

    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;

    const x = Math.floor((e.clientX - rect.left) / (PIXEL_SIZE + PIXEL_GAP));
    const y = Math.floor((e.clientY - rect.top) / (PIXEL_SIZE + PIXEL_GAP));

    togglePixel(x, y);
  };

  const handleMouseUp = () => {
    setIsDrawing(false);
  };

  const handleMouseLeave = () => {
    setIsDrawing(false);
  };

  const clearCanvas = () => {
    const newBits = new Array(DISPLAY_WIDTH * DISPLAY_HEIGHT).fill(0);
    setBits(newBits);
    onPaint(newBits);
  };

  const fillCanvas = () => {
    const newBits = new Array(DISPLAY_WIDTH * DISPLAY_HEIGHT).fill(1);
    setBits(newBits);
    onPaint(newBits);
  };

  return (
    <div className="paint-canvas-container">
      <div
        ref={canvasRef}
        className={`paint-canvas ${disabled ? "disabled" : ""}`}
        style={{
          display: "inline-grid",
          gridTemplateColumns: `repeat(${DISPLAY_WIDTH}, ${PIXEL_SIZE}px)`,
          gridTemplateRows: `repeat(${DISPLAY_HEIGHT}, ${PIXEL_SIZE}px)`,
          gap: `${PIXEL_GAP}px`,
          backgroundColor: "#1a1a1a",
          padding: "10px",
          borderRadius: "8px",
          cursor: disabled ? "not-allowed" : "crosshair",
          userSelect: "none",
          opacity: disabled ? 0.5 : 1,
        }}
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseLeave}
      >
        {bits.map((bit, index) => {
          const x = index % DISPLAY_WIDTH;
          const y = Math.floor(index / DISPLAY_WIDTH);
          return (
            <div
              key={`${x}-${y}`}
              className="pixel"
              style={{
                width: `${PIXEL_SIZE}px`,
                height: `${PIXEL_SIZE}px`,
                backgroundColor: bit === 1 ? "#fbbf24" : "#374151",
                borderRadius: "2px",
                transition: "background-color 0.1s",
              }}
            />
          );
        })}
      </div>

      <div className="paint-controls" style={{ marginTop: "10px" }}>
        <button
          onClick={clearCanvas}
          disabled={disabled}
          style={{
            padding: "8px 16px",
            marginRight: "8px",
            backgroundColor: "#ef4444",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: disabled ? "not-allowed" : "pointer",
            opacity: disabled ? 0.5 : 1,
          }}
        >
          Clear Canvas
        </button>
        <button
          onClick={fillCanvas}
          disabled={disabled}
          style={{
            padding: "8px 16px",
            backgroundColor: "#3b82f6",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: disabled ? "not-allowed" : "pointer",
            opacity: disabled ? 0.5 : 1,
          }}
        >
          Fill Canvas
        </button>
      </div>

      <div className="paint-info" style={{ marginTop: "10px", fontSize: "12px", color: "#9ca3af" }}>
        <p>Click and drag to paint. Click on a pixel to toggle between set/erase mode.</p>
        <p>Changes are sent automatically with low latency.</p>
      </div>
    </div>
  );
}
