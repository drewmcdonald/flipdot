//! Convex subscription client. Ported from the legacy Python implementation.
//!
//! Runs a background tokio task that subscribes to `displays:getCurrentDisplay`
//! and forwards updates to the main driver loop via an mpsc channel.

use crate::models::Content;
use anyhow::Result;
use convex::{ConvexClient, FunctionResult, Value};
use futures::StreamExt;
use std::collections::BTreeMap;
use tokio::sync::{mpsc, oneshot};
use tokio::task::JoinHandle;
use tracing::{debug, error, info, warn};

#[derive(Debug, Clone)]
pub enum ContentMessage {
    Updated(Vec<Content>),
    Clear,
}

pub struct ConvexContentClient {
    rx: mpsc::Receiver<ContentMessage>,
    shutdown: Option<oneshot::Sender<()>>,
    handle: Option<JoinHandle<()>>,
}

impl ConvexContentClient {
    pub async fn start(convex_url: String, display_name: String) -> Result<Self> {
        let (tx, rx) = mpsc::channel(16);
        let (shutdown_tx, shutdown_rx) = oneshot::channel::<()>();

        let handle = tokio::spawn(async move {
            if let Err(e) = run_subscription(convex_url, display_name, tx, shutdown_rx).await {
                error!(error = ?e, "convex subscription task exited with error");
            }
        });

        Ok(Self {
            rx,
            shutdown: Some(shutdown_tx),
            handle: Some(handle),
        })
    }

    /// Non-blocking try_recv. Used by the main loop when it wants to drain
    /// pending updates without blocking.
    pub fn try_recv(&mut self) -> Option<ContentMessage> {
        self.rx.try_recv().ok()
    }

    /// Wait for the next message or the timeout.
    pub async fn recv_timeout(&mut self, timeout: std::time::Duration) -> Option<ContentMessage> {
        tokio::time::timeout(timeout, self.rx.recv())
            .await
            .ok()
            .flatten()
    }

    pub async fn shutdown(mut self) {
        if let Some(tx) = self.shutdown.take() {
            let _ = tx.send(());
        }
        if let Some(handle) = self.handle.take() {
            let _ = handle.await;
        }
    }
}

async fn run_subscription(
    convex_url: String,
    display_name: String,
    tx: mpsc::Sender<ContentMessage>,
    mut shutdown: oneshot::Receiver<()>,
) -> Result<()> {
    info!(%convex_url, %display_name, "starting convex subscription");
    let mut client = ConvexClient::new(&convex_url).await?;
    let mut args: BTreeMap<String, Value> = BTreeMap::new();
    args.insert("name".to_string(), Value::String(display_name.clone()));
    let mut subscription = client.subscribe("displays:getCurrentDisplay", args).await?;

    let mut last_sent_id: Option<String> = None;

    loop {
        tokio::select! {
            biased;
            _ = &mut shutdown => {
                info!("convex subscription received shutdown signal");
                return Ok(());
            }
            next = subscription.next() => {
                match next {
                    None => {
                        warn!("convex subscription stream ended unexpectedly");
                        return Ok(());
                    }
                    Some(FunctionResult::Value(v)) => {
                        let json: serde_json::Value = v.export();
                        handle_value(&json, &tx, &mut last_sent_id).await;
                    }
                    Some(FunctionResult::ErrorMessage(msg)) => {
                        error!(error = %msg, "convex query returned an error");
                    }
                    Some(FunctionResult::ConvexError(e)) => {
                        error!(error = ?e, "convex query returned ConvexError");
                    }
                }
            }
        }
    }
}

async fn handle_value(
    json: &serde_json::Value,
    tx: &mpsc::Sender<ContentMessage>,
    last_sent_id: &mut Option<String>,
) {
    let content_field = json.get("content");
    match content_field {
        None | Some(serde_json::Value::Null) => {
            if last_sent_id.is_some() {
                *last_sent_id = None;
                if tx.send(ContentMessage::Clear).await.is_err() {
                    warn!("driver receiver dropped; exiting subscription handler");
                }
            }
        }
        Some(content_value) => match serde_json::from_value::<Content>(content_value.clone()) {
            Ok(content) => {
                let new_id = content.content_id.clone();
                if last_sent_id.as_deref() == Some(new_id.as_str()) {
                    debug!(content_id = %new_id, "ignoring duplicate content update");
                    return;
                }
                *last_sent_id = Some(new_id.clone());
                let _ = tx.send(ContentMessage::Updated(vec![content])).await;
            }
            Err(e) => {
                error!(error = %e, "failed to parse Content from convex result");
            }
        },
    }
}
