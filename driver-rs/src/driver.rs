//! Driver orchestration. Ported from the legacy Python driver implementation.

use crate::convex_client::{ContentMessage, ConvexContentClient};
use crate::hardware::Panel;
use crate::limits::DriverLimits;
use crate::models::DriverConfig;
use crate::queue::ContentQueue;
use crate::serial::SerialConnection;
use anyhow::Result;
use std::time::{Duration, Instant};
use tokio::sync::watch;
use tracing::{debug, error, info, warn};

pub struct FlipDotDriver {
    limits: DriverLimits,
    panel: Panel,
    serial: SerialConnection,
    queue: ContentQueue,
    convex: ConvexContentClient,
}

impl FlipDotDriver {
    pub async fn new(config: DriverConfig) -> Result<Self> {
        let limits = DriverLimits::default();
        info!("initializing hardware");
        let panel = Panel::new(
            &config.module_layout,
            config.module_width,
            config.module_height,
        )?;
        let (ph, pw) = panel.dimensions();
        info!(width = pw, height = ph, "display dimensions");

        let serial = if config.dev_mode {
            info!("serial running in dev mode");
            SerialConnection::dev_mode()
        } else {
            build_serial(&config, limits)?
        };

        let queue = ContentQueue::new();
        let convex =
            ConvexContentClient::start(config.convex_url.clone(), config.display_name.clone())
                .await?;
        Ok(Self {
            limits,
            panel,
            serial,
            queue,
            convex,
        })
    }

    /// Run the main loop until `shutdown` is signalled.
    pub async fn run(mut self, mut shutdown: watch::Receiver<bool>) -> Result<()> {
        info!("starting driver loop");
        let sleep = Duration::from_millis(self.limits.loop_timing.sleep_interval_ms);
        loop {
            if *shutdown.borrow_and_update() {
                break;
            }
            tokio::select! {
                biased;
                _ = shutdown.changed() => {
                    if *shutdown.borrow() { break; }
                }
                msg = self.convex.recv_timeout(sleep) => {
                    if let Some(msg) = msg {
                        self.apply_message(msg);
                    }
                }
            }
            self.render_frame();
        }
        self.stop().await;
        Ok(())
    }

    fn apply_message(&mut self, msg: ContentMessage) {
        let now = Instant::now();
        match msg {
            ContentMessage::Updated(playlist) => {
                let (ph, pw) = self.panel.dimensions();
                for content in &playlist {
                    if let Err(e) = content.validate_display_dimensions(pw, ph) {
                        error!(error = %e, "rejecting playlist due to dimension mismatch");
                        return;
                    }
                }
                self.queue.set_playlist(playlist, now);
            }
            ContentMessage::Clear => {
                info!("server requested display clear");
                self.queue.clear();
                self.clear_display();
            }
        }
    }

    fn render_frame(&mut self) {
        let now = Instant::now();
        let Some(frame) = self.queue.update(now) else {
            return;
        };
        let data = match frame.decode_data() {
            Ok(d) => d,
            Err(e) => {
                error!(error = %e, "failed to decode frame data");
                return;
            }
        };
        match self
            .panel
            .set_content_from_frame(&data, frame.width, frame.height)
        {
            Ok(bytes) => {
                if !self.serial.write(&bytes, now) {
                    warn!("serial write failed; will retry next loop iteration");
                }
            }
            Err(e) => error!(error = %e, "failed to build serial command for frame"),
        }
    }

    fn clear_display(&mut self) {
        let (h, w) = self.panel.dimensions();
        let blank: Vec<Vec<u8>> = (0..h).map(|_| vec![0u8; w as usize]).collect();
        match self.panel.set_content(&blank) {
            Ok(bytes) => {
                if !self.serial.write(&bytes, Instant::now()) {
                    warn!("serial write failed during display clear");
                }
            }
            Err(e) => error!(error = %e, "failed to build blank frame"),
        }
    }

    async fn stop(mut self) {
        info!("stopping driver; clearing display");
        self.clear_display();
        self.convex.shutdown().await;
        info!("driver stopped");
    }
}

#[cfg(feature = "hardware")]
fn build_serial(config: &DriverConfig, limits: DriverLimits) -> Result<SerialConnection> {
    use crate::serial::SerialPort;
    let Some(device) = config.serial_device.clone() else {
        anyhow::bail!("serial_device required unless dev_mode is true");
    };
    let baudrate = config.serial_baudrate;
    let mut conn = SerialConnection::without_port(limits.serial);
    let factory_device = device.clone();
    conn.set_reconnect_factory(Box::new(move || -> std::io::Result<Box<dyn SerialPort>> {
        crate::serial::open_serial(&factory_device, baudrate)
    }));
    // Eagerly try once at startup so we log success/failure up front.
    let _ = conn.write(&[], std::time::Instant::now());
    debug!(device, baudrate, "serial factory installed");
    let _ = device;
    Ok(conn)
}

#[cfg(not(feature = "hardware"))]
fn build_serial(config: &DriverConfig, _limits: DriverLimits) -> Result<SerialConnection> {
    anyhow::bail!("driver was built without the `hardware` feature; set dev_mode=true to run")
}
