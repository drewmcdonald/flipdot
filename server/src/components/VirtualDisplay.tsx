import { useEffect, useRef } from "react";
import { useQuery } from "convex/react";
import { api } from "../../convex/_generated/api";
import { base64ToBits } from "../lib/frameRenderer";
import "./VirtualDisplay.css";

const DOT_SIZE = 20;
const DOT_GAP = 2;
const DOT_RADIUS = 8;

const COLOR_OFF = "#1a1a1a";
const COLOR_ON = "#ffffff";

interface VirtualDisplayProps {
  displayName?: string;
}

function drawFrame(
  canvas: HTMLCanvasElement,
  frame: { data_b64: string; width: number; height: number } | undefined
) {
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  let width = 28;
  let height = 14;
  let bits: number[] = [];

  if (frame) {
    width = frame.width;
    height = frame.height;
    bits = base64ToBits(frame.data_b64, width * height);
  }

  const canvasWidth = width * DOT_SIZE + (width - 1) * DOT_GAP;
  const canvasHeight = height * DOT_SIZE + (height - 1) * DOT_GAP;
  canvas.width = canvasWidth;
  canvas.height = canvasHeight;

  ctx.fillStyle = "#0a0a0a";
  ctx.fillRect(0, 0, canvasWidth, canvasHeight);

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const bitIndex = y * width + x;
      const isOn = bits[bitIndex] === 1;
      const dotX = x * (DOT_SIZE + DOT_GAP) + DOT_SIZE / 2;
      const dotY = y * (DOT_SIZE + DOT_GAP) + DOT_SIZE / 2;
      ctx.beginPath();
      ctx.arc(dotX, dotY, DOT_RADIUS, 0, Math.PI * 2);
      ctx.fillStyle = isOn ? COLOR_ON : COLOR_OFF;
      ctx.fill();
    }
  }
}

export function VirtualDisplay({ displayName = "main" }: VirtualDisplayProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const display = useQuery(api.displays.getCurrentDisplay, {
    name: displayName,
  });

  const frames = display?.content?.frames;
  const contentId = display?.content?.content_id;
  const shouldLoop = display?.content?.playback?.loop ?? false;

  // Single effect handles drawing + animation loop imperatively
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    if (!frames || frames.length === 0) {
      drawFrame(canvas, undefined);
      return;
    }

    // Single frame — just draw it
    if (frames.length === 1) {
      drawFrame(canvas, frames[0]);
      return;
    }

    // Multi-frame animation loop
    let currentIndex = 0;
    let timeoutId: ReturnType<typeof setTimeout>;
    let cancelled = false;

    function tick() {
      if (cancelled || !canvas) return;
      drawFrame(canvas, frames![currentIndex]);

      const duration = frames![currentIndex].duration_ms;
      if (!duration || duration <= 0) return;

      const isLast = currentIndex >= frames!.length - 1;
      if (isLast && !shouldLoop) return;

      timeoutId = setTimeout(() => {
        currentIndex = (currentIndex + 1) % frames!.length;
        tick();
      }, duration);
    }

    tick();

    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [contentId, frames, shouldLoop]);

  const isLoading = display === undefined;
  const isEmpty = display === null;

  return (
    <div className="virtual-display-container">
      <div className="virtual-display-frame">
        <canvas ref={canvasRef} className="virtual-display-canvas" />
      </div>
      <div className="virtual-display-status">
        {isLoading && <span className="status-loading">Connecting...</span>}
        {isEmpty && <span className="status-empty">No display content</span>}
        {display && (
          <span className="status-connected">
            Display: {displayName} | Content: {display.content.content_id}
          </span>
        )}
      </div>
    </div>
  );
}
