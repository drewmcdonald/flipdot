/** @jsxImportSource https://esm.sh/react@18.2.0 */
import React, { useEffect, useState, useRef, useCallback } from "https://esm.sh/react@18.2.0";
import { Display } from "./components/Display.tsx";
import { ControlPanel } from "./components/ControlPanel.tsx";
import { StatusMessage } from "./components/StatusMessage.tsx";
import { LoginForm } from "./components/LoginForm.tsx";
import { PaintCanvas } from "./components/PaintCanvas.tsx";
import { useAuthCheck } from "./hooks/useAuth.ts";

export function App() {
  const { data: authenticated, isLoading, refetch } = useAuthCheck();

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div
        style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          backgroundColor: "#f9fafb",
        }}
      >
        <div style={{ fontSize: "1.125rem", color: "#374151" }}>
          Loading...
        </div>
      </div>
    );
  }

  // Show login form if not authenticated
  if (!authenticated) {
    return <LoginForm onLogin={() => refetch()} />;
  }

  // User is authenticated, show the main app
  return <AuthenticatedApp />;
}

function AuthenticatedApp() {
  const [displayBits, setDisplayBits] = useState<number[]>(
    new Array(28 * 14).fill(0),
  );
  const [statusMessage, setStatusMessage] = useState<
    {
      type: "success" | "error" | "info";
      text: string;
    } | null
  >(null);
  const [isPolling, setIsPolling] = useState(false);
  const [currentContent, setCurrentContent] = useState<any>(null);
  const [isPaintMode, setIsPaintMode] = useState(false);
  const [paintBits, setPaintBits] = useState<number[]>(
    new Array(28 * 14).fill(0),
  );
  const [isPageVisible, setIsPageVisible] = useState(true);
  const [lastPaintActivity, setLastPaintActivity] = useState<number>(Date.now());

  // Refs for debouncing and polling
  const paintDebounceRef = useRef<number | null>(null);
  const activityTimeoutRef = useRef<number | null>(null);
  const pollIntervalRef = useRef<number | null>(null);

  // Helper function to decode a frame
  const decodeFrame = (frame: any): number[] => {
    const decoded = atob(frame.data_b64);
    const bytes = new Uint8Array(decoded.length);
    for (let i = 0; i < decoded.length; i++) {
      bytes[i] = decoded.charCodeAt(i);
    }

    // Unpack bits (little-endian)
    const bits: number[] = [];
    for (let byteIdx = 0; byteIdx < bytes.length; byteIdx++) {
      for (let bitIdx = 0; bitIdx < 8; bitIdx++) {
        if (bits.length < 28 * 14) {
          bits.push((bytes[byteIdx] >> bitIdx) & 1);
        }
      }
    }
    return bits;
  };

  // Page Visibility API - detect when tab is visible/hidden
  useEffect(() => {
    const handleVisibilityChange = () => {
      setIsPageVisible(!document.hidden);
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, []);

  // Debounced paint handler with activity tracking
  const handlePaint = useCallback((bits: number[]) => {
    setPaintBits(bits);
    setLastPaintActivity(Date.now());

    // Clear existing debounce timer
    if (paintDebounceRef.current) {
      clearTimeout(paintDebounceRef.current);
    }

    // Debounce API call - send after 150ms of no changes (low latency while painting)
    paintDebounceRef.current = globalThis.setTimeout(async () => {
      try {
        const response = await fetch("/api/flipdot/paint", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-API-Key": "local-dev-key",
          },
          body: JSON.stringify({ bits }),
        });

        if (!response.ok) {
          const result = await response.json();
          setStatusMessage({
            type: "error",
            text: result.error || "Failed to update paint",
          });
        }
      } catch (error) {
        console.error("Error sending paint data:", error);
      }
    }, 150); // 150ms debounce for low latency

    // Set activity timeout - stop rapid polling after 10 seconds of inactivity
    if (activityTimeoutRef.current) {
      clearTimeout(activityTimeoutRef.current);
    }
  }, []);

  // Animate through frames
  useEffect(() => {
    if (
      !currentContent || !currentContent.frames ||
      currentContent.frames.length === 0
    ) {
      return;
    }

    const frames = currentContent.frames;
    const playback = currentContent.playback || {};
    const shouldLoop = playback.loop !== false; // Default to true

    let currentFrameIndex = 0;
    let animationTimeout: number;

    const showNextFrame = () => {
      if (currentFrameIndex >= frames.length) {
        if (shouldLoop) {
          currentFrameIndex = 0; // Loop back to start
        } else {
          return; // Stop animation
        }
      }

      const frame = frames[currentFrameIndex];
      const bits = decodeFrame(frame);
      setDisplayBits(bits);

      const duration = frame.duration_ms || 100; // Default 100ms per frame
      currentFrameIndex++;

      animationTimeout = globalThis.setTimeout(showNextFrame, duration);
    };

    // Start animation
    showNextFrame();

    return () => {
      if (animationTimeout) clearTimeout(animationTimeout);
    };
  }, [currentContent]);

  // Adaptive polling with presence detection and paint mode awareness
  useEffect(() => {
    if (!isPolling) return;

    const pollContent = async () => {
      try {
        const response = await fetch("/api/flipdot/content", {
          headers: {
            "X-API-Key": "local-dev-key",
          },
        });

        if (response.ok) {
          const data = await response.json();

          if (data.status === "updated" && data.playlist && data.playlist.length > 0) {
            // Use first item from playlist
            setCurrentContent(data.playlist[0]);
          } else if (data.status === "clear" || (data.status === "updated" && (!data.playlist || data.playlist.length === 0))) {
            setCurrentContent(null);
            setDisplayBits(new Array(28 * 14).fill(0));
          }
        }
      } catch (error) {
        console.error("Error polling content:", error);
      }
    };

    // Determine polling interval based on mode and activity
    const getPollingInterval = () => {
      // Don't poll if page is not visible (presence detection)
      if (!isPageVisible) {
        return 30000; // 30s when tab is hidden
      }

      // Fast polling in paint mode with recent activity
      if (isPaintMode) {
        const timeSinceActivity = Date.now() - lastPaintActivity;
        if (timeSinceActivity < 10000) {
          // Active painting - 500ms for low latency
          return 500;
        } else if (timeSinceActivity < 30000) {
          // Recent activity - 2s
          return 2000;
        }
      }

      // Default polling for normal mode
      return 2000; // 2s default
    };

    const schedulePoll = () => {
      const interval = getPollingInterval();
      pollIntervalRef.current = globalThis.setTimeout(() => {
        pollContent().then(() => {
          // Schedule next poll if still polling
          if (isPolling) {
            schedulePoll();
          }
        });
      }, interval);
    };

    // Start polling
    pollContent(); // Initial poll
    schedulePoll();

    return () => {
      if (pollIntervalRef.current) {
        clearTimeout(pollIntervalRef.current);
      }
    };
  }, [isPolling, isPaintMode, lastPaintActivity, isPageVisible]);

  // Auto-start polling
  useEffect(() => {
    setIsPolling(true);
  }, []);

  const handleSendMessage = async (formData: {
    text: string;
    priority: number;
    duration: number;
    scroll: boolean;
  }) => {
    try {
      const response = await fetch("/api/flipdot/text", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": "local-dev-key",
        },
        body: JSON.stringify({
          text: formData.text.toUpperCase(),
          priority: formData.priority,
          ttl_ms: formData.duration * 1000,
          scroll: formData.scroll,
        }),
      });

      const result = await response.json();

      if (response.ok) {
        const typeMsg = result.type === "scrolling_text" ? " (Scrolling)" : "";
        setStatusMessage({
          type: "success",
          text: `Message sent! Priority: ${formData.priority}${typeMsg}`,
        });
      } else {
        setStatusMessage({
          type: "error",
          text: result.error || "Failed to send message",
        });
      }
    } catch (error) {
      setStatusMessage({
        type: "error",
        text: "Network error: " + (error as Error).message,
      });
    }
  };

  const handleClearAll = async () => {
    try {
      const response = await fetch("/api/flipdot/clear", {
        method: "POST",
        headers: {
          "X-API-Key": "local-dev-key",
        },
      });

      if (response.ok) {
        setStatusMessage({
          type: "success",
          text: "All messages cleared",
        });
        setDisplayBits(new Array(28 * 14).fill(0));
      } else {
        const result = await response.json();
        setStatusMessage({
          type: "error",
          text: result.error || "Failed to clear messages",
        });
      }
    } catch (error) {
      setStatusMessage({
        type: "error",
        text: "Network error: " + (error as Error).message,
      });
    }
  };

  const handleTogglePaintMode = async () => {
    if (isPaintMode) {
      // Exiting paint mode - clear paint buffer
      try {
        await fetch("/api/flipdot/paint/clear", {
          method: "POST",
          headers: {
            "X-API-Key": "local-dev-key",
          },
        });
        setStatusMessage({
          type: "info",
          text: "Paint mode disabled",
        });
      } catch (error) {
        console.error("Error clearing paint:", error);
      }
    } else {
      // Entering paint mode
      setStatusMessage({
        type: "info",
        text: "Paint mode enabled - draw on the canvas!",
      });
      // Load existing paint buffer if any
      try {
        const response = await fetch("/api/flipdot/paint", {
          headers: {
            "X-API-Key": "local-dev-key",
          },
        });
        if (response.ok) {
          const data = await response.json();
          if (data.active && data.bits) {
            setPaintBits(data.bits);
          }
        }
      } catch (error) {
        console.error("Error loading paint buffer:", error);
      }
    }
    setIsPaintMode(!isPaintMode);
  };

  const handleClearPaint = async () => {
    try {
      const response = await fetch("/api/flipdot/paint/clear", {
        method: "POST",
        headers: {
          "X-API-Key": "local-dev-key",
        },
      });

      if (response.ok) {
        setPaintBits(new Array(28 * 14).fill(0));
        setStatusMessage({
          type: "success",
          text: "Paint canvas cleared",
        });
      } else {
        const result = await response.json();
        setStatusMessage({
          type: "error",
          text: result.error || "Failed to clear paint",
        });
      }
    } catch (error) {
      setStatusMessage({
        type: "error",
        text: "Network error: " + (error as Error).message,
      });
    }
  };

  return (
    <div style={{ padding: "2rem", maxWidth: "1200px", margin: "0 auto" }}>
      <header style={{ textAlign: "center", marginBottom: "2rem" }}>
        <h1 style={{ margin: "0 0 0.5rem 0", fontSize: "2rem" }}>
          FlipDot Display Control
        </h1>
        <p style={{ color: "#6b7280", margin: 0 }}>
          28×14 Pixel Display Simulator
        </p>
      </header>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "1fr",
          gap: "2rem",
          // @ts-ignore
          "@media (min-width: 768px)": {
            gridTemplateColumns: "auto 1fr",
          },
        }}
      >
        <div>
          <Display bits={displayBits} isPolling={isPolling} />
          {isPaintMode && (
            <div style={{ marginTop: "2rem" }}>
              <h2 style={{ fontSize: "1.25rem", marginBottom: "1rem" }}>
                Paint Canvas
              </h2>
              <PaintCanvas
                initialBits={paintBits}
                onPaint={handlePaint}
                disabled={!isPageVisible}
              />
              {!isPageVisible && (
                <div
                  style={{
                    marginTop: "1rem",
                    padding: "0.75rem",
                    backgroundColor: "#fef3c7",
                    borderRadius: "4px",
                    fontSize: "0.875rem",
                    color: "#92400e",
                  }}
                >
                  Tab is hidden - painting disabled, polling slowed
                </div>
              )}
            </div>
          )}
        </div>
        <div>
          <ControlPanel
            onSendMessage={handleSendMessage}
            onClearAll={handleClearAll}
            onTogglePolling={() => setIsPolling(!isPolling)}
            isPolling={isPolling}
            onTogglePaintMode={handleTogglePaintMode}
            isPaintMode={isPaintMode}
          />
          {statusMessage && (
            <StatusMessage
              type={statusMessage.type}
              text={statusMessage.text}
              onDismiss={() => setStatusMessage(null)}
            />
          )}
        </div>
      </div>

      <footer
        style={{
          marginTop: "3rem",
          paddingTop: "2rem",
          borderTop: "1px solid #e5e7eb",
          textAlign: "center",
          color: "#6b7280",
          fontSize: "0.875rem",
        }}
      >
        <p>
          Content Server v2.0 |{" "}
          <a
            href="/api/flipdot/content"
            style={{ color: "#3b82f6", textDecoration: "none" }}
          >
            View API
          </a>
        </p>
      </footer>
    </div>
  );
}
