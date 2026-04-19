use anyhow::{Context, Result};
use clap::Parser;
use flipdot_driver::driver::FlipDotDriver;
use flipdot_driver::models::DriverConfig;
use std::path::PathBuf;
use tokio::signal::unix::{signal, SignalKind};
use tokio::sync::watch;
use tracing::{error, info};
use tracing_subscriber::{fmt, EnvFilter};

#[derive(Parser)]
#[command(
    name = "flipdot",
    about = "FlipDot display driver",
    version = env!("CARGO_PKG_VERSION"),
)]
struct Cli {
    #[arg(long, value_name = "PATH")]
    config: PathBuf,
}

fn init_logging(level: &str) {
    let default_filter = EnvFilter::try_new(format!(
        "flipdot={level},flipdot_driver={level},warn",
        level = level.to_lowercase()
    ))
    .unwrap_or_else(|_| EnvFilter::new("info"));
    let filter = EnvFilter::try_from_default_env().unwrap_or(default_filter);
    fmt().with_env_filter(filter).with_target(true).init();
}

fn load_config(path: &PathBuf) -> Result<DriverConfig> {
    let text = std::fs::read_to_string(path)
        .with_context(|| format!("reading config file {}", path.display()))?;
    let cfg: DriverConfig = serde_json::from_str(&text)
        .with_context(|| format!("parsing config file {}", path.display()))?;
    Ok(cfg)
}

#[tokio::main]
async fn main() -> Result<()> {
    let cli = Cli::parse();
    let config = load_config(&cli.config)?;
    init_logging(&config.log_level);

    // rustls 0.23 requires an explicit crypto provider; convex's
    // rustls-tls-webpki-roots feature doesn't pick one.
    rustls::crypto::ring::default_provider()
        .install_default()
        .map_err(|_| anyhow::anyhow!("failed to install rustls crypto provider"))?;

    info!(
        version = env!("CARGO_PKG_VERSION"),
        "starting flipdot driver"
    );

    let (shutdown_tx, shutdown_rx) = watch::channel(false);

    // Forward SIGTERM and SIGINT to the shutdown channel.
    let signal_tx = shutdown_tx.clone();
    tokio::spawn(async move {
        let mut term = match signal(SignalKind::terminate()) {
            Ok(s) => s,
            Err(e) => {
                error!(error = %e, "failed to install SIGTERM handler");
                return;
            }
        };
        let mut int = match signal(SignalKind::interrupt()) {
            Ok(s) => s,
            Err(e) => {
                error!(error = %e, "failed to install SIGINT handler");
                return;
            }
        };
        tokio::select! {
            _ = term.recv() => info!("received SIGTERM"),
            _ = int.recv() => info!("received SIGINT"),
        }
        let _ = signal_tx.send(true);
    });

    let driver = FlipDotDriver::new(config).await?;
    driver.run(shutdown_rx).await?;

    Ok(())
}
