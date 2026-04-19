//! Driver limits and tuning constants (port of flipdot/config.py).

#[derive(Debug, Clone, Copy)]
pub struct SerialLimits {
    pub max_consecutive_failures: u32,
    pub initial_reconnect_backoff_ms: u32,
    pub max_reconnect_backoff_ms: u32,
}

impl Default for SerialLimits {
    fn default() -> Self {
        Self {
            max_consecutive_failures: 10,
            initial_reconnect_backoff_ms: 1_000,
            max_reconnect_backoff_ms: 60_000,
        }
    }
}

#[derive(Debug, Clone, Copy)]
pub struct LoopTiming {
    pub sleep_interval_ms: u64,
}

impl Default for LoopTiming {
    fn default() -> Self {
        Self {
            sleep_interval_ms: 20,
        }
    }
}

#[derive(Debug, Clone, Copy, Default)]
pub struct DriverLimits {
    pub serial: SerialLimits,
    pub loop_timing: LoopTiming,
}
