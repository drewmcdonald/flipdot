use crate::limits::SerialLimits;
use std::io;
use std::time::{Duration, Instant};
use tracing::{debug, error, info, warn};

pub trait SerialPort: Send {
    fn write(&mut self, data: &[u8]) -> io::Result<usize>;
}

pub type ReconnectFactory = Box<dyn FnMut() -> io::Result<Box<dyn SerialPort>> + Send>;

pub struct SerialConnection {
    dev_mode: bool,
    port: Option<Box<dyn SerialPort>>,
    limits: SerialLimits,
    reconnect: Option<ReconnectFactory>,
    consecutive_failures: u32,
    last_reconnect_attempt: Option<Instant>,
    reconnect_backoff_ms: u32,
}

impl SerialConnection {
    pub fn dev_mode() -> Self {
        Self {
            dev_mode: true,
            port: None,
            limits: SerialLimits::default(),
            reconnect: None,
            consecutive_failures: 0,
            last_reconnect_attempt: None,
            reconnect_backoff_ms: SerialLimits::default().initial_reconnect_backoff_ms,
        }
    }

    pub fn with_port(port: Box<dyn SerialPort>, limits: SerialLimits) -> Self {
        let backoff = limits.initial_reconnect_backoff_ms;
        Self {
            dev_mode: false,
            port: Some(port),
            limits,
            reconnect: None,
            consecutive_failures: 0,
            last_reconnect_attempt: None,
            reconnect_backoff_ms: backoff,
        }
    }

    pub fn without_port(limits: SerialLimits) -> Self {
        let backoff = limits.initial_reconnect_backoff_ms;
        Self {
            dev_mode: false,
            port: None,
            limits,
            reconnect: None,
            consecutive_failures: 0,
            last_reconnect_attempt: None,
            reconnect_backoff_ms: backoff,
        }
    }

    pub fn set_reconnect_factory(&mut self, factory: ReconnectFactory) {
        self.reconnect = Some(factory);
    }

    pub fn consecutive_failures(&self) -> u32 {
        self.consecutive_failures
    }

    pub fn write(&mut self, data: &[u8], now: Instant) -> bool {
        if self.dev_mode {
            debug!(target: "flipdot::serial", bytes = data.len(), "[dev] would write to serial");
            return true;
        }

        if self.port.is_none() && !self.try_reconnect(now) {
            self.consecutive_failures += 1;
            if self.consecutive_failures >= self.limits.max_consecutive_failures {
                error!(
                    failures = self.consecutive_failures,
                    "serial device unavailable; check hardware connection"
                );
            }
            return false;
        }

        let Some(port) = self.port.as_mut() else {
            return false;
        };
        match port.write(data) {
            Ok(n) if n == data.len() => {
                if self.consecutive_failures > 0 {
                    info!("serial communication recovered");
                }
                self.consecutive_failures = 0;
                self.reconnect_backoff_ms = self.limits.initial_reconnect_backoff_ms;
                true
            }
            Ok(n) => {
                self.consecutive_failures += 1;
                error!(
                    written = n,
                    expected = data.len(),
                    "serial write incomplete"
                );
                false
            }
            Err(e) => {
                self.consecutive_failures += 1;
                error!(error = %e, failures = self.consecutive_failures, "serial write failed");
                self.port = None;
                false
            }
        }
    }

    fn should_attempt_reconnect(&self, now: Instant) -> bool {
        match self.last_reconnect_attempt {
            None => true,
            Some(t) => {
                now.saturating_duration_since(t)
                    >= Duration::from_millis(self.reconnect_backoff_ms as u64)
            }
        }
    }

    fn try_reconnect(&mut self, now: Instant) -> bool {
        if !self.should_attempt_reconnect(now) {
            return false;
        }
        self.last_reconnect_attempt = Some(now);
        let Some(factory) = self.reconnect.as_mut() else {
            return false;
        };
        info!(
            failures = self.consecutive_failures,
            "attempting serial reconnection"
        );
        match factory() {
            Ok(port) => {
                self.port = Some(port);
                self.consecutive_failures = 0;
                self.reconnect_backoff_ms = self.limits.initial_reconnect_backoff_ms;
                info!("serial reconnection succeeded");
                true
            }
            Err(e) => {
                self.reconnect_backoff_ms =
                    (self.reconnect_backoff_ms * 2).min(self.limits.max_reconnect_backoff_ms);
                warn!(error = %e, next_backoff_ms = self.reconnect_backoff_ms,
                      "reconnection failed");
                false
            }
        }
    }
}

/// Adapter so `serialport::SerialPort` implementations satisfy our trait.
#[cfg(feature = "hardware")]
pub struct RealPort(pub Box<dyn serialport::SerialPort>);

#[cfg(feature = "hardware")]
impl SerialPort for RealPort {
    fn write(&mut self, data: &[u8]) -> io::Result<usize> {
        use std::io::Write as _;
        self.0.write(data)
    }
}

#[cfg(feature = "hardware")]
pub fn open_serial(device: &str, baudrate: u32) -> io::Result<Box<dyn SerialPort>> {
    let port = serialport::new(device, baudrate)
        .timeout(Duration::from_secs(1))
        .open()
        .map_err(|e| io::Error::other(e.to_string()))?;
    Ok(Box::new(RealPort(port)))
}
