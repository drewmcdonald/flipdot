use base64::{engine::general_purpose::STANDARD as B64, Engine as _};
use serde::{de::Error as _, Deserialize, Deserializer, Serialize};
use thiserror::Error;

#[derive(Debug, Error)]
pub enum DecodeError {
    #[error("invalid base64 data: {0}")]
    InvalidBase64(#[from] base64::DecodeError),
}

// Convex exports numeric fields as f64 (Float64), so `14` arrives as `14.0`.
// Accept any JSON number and coerce to u32 if it's a non-negative integer value.
fn deser_u32_lenient<'de, D: Deserializer<'de>>(d: D) -> Result<u32, D::Error> {
    let n = serde_json::Number::deserialize(d)?;
    number_to_u32::<D>(&n)
}

fn deser_opt_u32_lenient<'de, D: Deserializer<'de>>(d: D) -> Result<Option<u32>, D::Error> {
    let n: Option<serde_json::Number> = Option::deserialize(d)?;
    n.map(|n| number_to_u32::<D>(&n)).transpose()
}

fn number_to_u32<'de, D: Deserializer<'de>>(n: &serde_json::Number) -> Result<u32, D::Error> {
    if let Some(i) = n.as_u64() {
        u32::try_from(i).map_err(|_| D::Error::custom(format!("{i} exceeds u32 range")))
    } else if let Some(f) = n.as_f64() {
        if f.is_finite() && f >= 0.0 && f <= u32::MAX as f64 && f.fract() == 0.0 {
            Ok(f as u32)
        } else {
            Err(D::Error::custom(format!(
                "expected non-negative integer, got {f}"
            )))
        }
    } else {
        Err(D::Error::custom(format!(
            "expected non-negative integer, got {n}"
        )))
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct Frame {
    pub data_b64: String,
    #[serde(deserialize_with = "deser_u32_lenient")]
    pub width: u32,
    #[serde(deserialize_with = "deser_u32_lenient")]
    pub height: u32,
    #[serde(default, deserialize_with = "deser_opt_u32_lenient")]
    pub duration_ms: Option<u32>,
    #[serde(default)]
    pub metadata: Option<serde_json::Value>,
}

impl Frame {
    pub fn decode_data(&self) -> Result<Vec<u8>, DecodeError> {
        Ok(B64.decode(self.data_b64.as_bytes())?)
    }

    pub fn to_bit_array(&self) -> Result<Vec<Vec<u8>>, DecodeError> {
        let data = self.decode_data()?;
        let mut rows = Vec::with_capacity(self.height as usize);
        let mut bit_idx = 0usize;
        for _ in 0..self.height {
            let mut row = Vec::with_capacity(self.width as usize);
            for _ in 0..self.width {
                let byte_idx = bit_idx / 8;
                let bit_pos = bit_idx % 8;
                let bit = if byte_idx < data.len() {
                    (data[byte_idx] >> bit_pos) & 1
                } else {
                    0
                };
                row.push(bit);
                bit_idx += 1;
            }
            rows.push(row);
        }
        Ok(rows)
    }
}

#[derive(Debug, Clone, Default, Serialize, PartialEq, Eq)]
pub struct PlaybackMode {
    #[serde(rename = "loop")]
    pub looping: bool,
    pub loop_count: Option<u32>,
}

impl<'de> Deserialize<'de> for PlaybackMode {
    fn deserialize<D: Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
        #[derive(Deserialize)]
        struct Raw {
            #[serde(default, rename = "loop")]
            looping: bool,
            #[serde(default, deserialize_with = "deser_opt_u32_lenient")]
            loop_count: Option<u32>,
        }
        let raw = Raw::deserialize(d)?;
        if let Some(n) = raw.loop_count {
            if n == 0 {
                return Err(D::Error::custom("loop_count must be >= 1"));
            }
            if !raw.looping {
                return Err(D::Error::custom(
                    "loop_count can only be set when loop=true",
                ));
            }
        }
        Ok(PlaybackMode {
            looping: raw.looping,
            loop_count: raw.loop_count,
        })
    }
}

pub const MAX_FRAMES_PER_CONTENT: usize = 1000;
pub const MAX_TOTAL_BYTES: usize = 5 * 1024 * 1024;
pub const MAX_METADATA_BYTES: usize = 10 * 1024;

#[derive(Debug, Error)]
pub enum ContentError {
    #[error("content {content_id} has frame dimensions {actual_w}x{actual_h}, but display is {expected_w}x{expected_h}")]
    DimensionMismatch {
        content_id: String,
        actual_w: u32,
        actual_h: u32,
        expected_w: u32,
        expected_h: u32,
    },
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct Content {
    pub content_id: String,
    pub frames: Vec<Frame>,
    pub playback: PlaybackMode,
    pub metadata: Option<serde_json::Value>,
}

impl<'de> Deserialize<'de> for Content {
    fn deserialize<D: Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
        #[derive(Deserialize)]
        struct Raw {
            content_id: String,
            frames: Vec<Frame>,
            #[serde(default)]
            playback: PlaybackMode,
            #[serde(default)]
            metadata: Option<serde_json::Value>,
        }
        let raw = Raw::deserialize(d)?;

        if raw.frames.is_empty() {
            return Err(D::Error::custom("at least one frame is required"));
        }
        if raw.frames.len() > MAX_FRAMES_PER_CONTENT {
            return Err(D::Error::custom(format!(
                "too many frames: {} exceeds limit of {MAX_FRAMES_PER_CONTENT}",
                raw.frames.len()
            )));
        }

        let first = &raw.frames[0];
        let (w, h) = (first.width, first.height);
        let mut total_bytes = 0usize;
        for (i, frame) in raw.frames.iter().enumerate() {
            if i > 0 && (frame.width != w || frame.height != h) {
                return Err(D::Error::custom(format!(
                    "frame {i} has dimensions {}x{}, but frame 0 has {w}x{h}",
                    frame.width, frame.height
                )));
            }
            let data = frame
                .decode_data()
                .map_err(|e| D::Error::custom(format!("frame {i}: {e}")))?;
            total_bytes += data.len();
            if let Some(md) = &frame.metadata {
                let md_bytes = serde_json::to_vec(md).map_err(D::Error::custom)?.len();
                if md_bytes > MAX_METADATA_BYTES {
                    return Err(D::Error::custom(format!(
                        "frame {i} metadata too large: {md_bytes} bytes exceeds limit of {MAX_METADATA_BYTES}"
                    )));
                }
                total_bytes += md_bytes;
            }
        }
        if total_bytes > MAX_TOTAL_BYTES {
            return Err(D::Error::custom(format!(
                "content too large: {total_bytes} bytes exceeds limit of {MAX_TOTAL_BYTES}"
            )));
        }

        if let Some(md) = &raw.metadata {
            let md_bytes = serde_json::to_vec(md).map_err(D::Error::custom)?.len();
            if md_bytes > MAX_METADATA_BYTES {
                return Err(D::Error::custom(format!(
                    "content metadata too large: {md_bytes} bytes exceeds limit of {MAX_METADATA_BYTES}"
                )));
            }
        }

        Ok(Content {
            content_id: raw.content_id,
            frames: raw.frames,
            playback: raw.playback,
            metadata: raw.metadata,
        })
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
pub struct DriverConfig {
    pub convex_url: String,
    #[serde(default = "default_display_name")]
    pub display_name: String,
    #[serde(default)]
    pub serial_device: Option<String>,
    #[serde(default = "default_serial_baudrate")]
    pub serial_baudrate: u32,
    #[serde(default = "default_module_layout")]
    pub module_layout: Vec<Vec<u32>>,
    #[serde(default = "default_module_width")]
    pub module_width: u32,
    #[serde(default = "default_module_height")]
    pub module_height: u32,
    #[serde(default)]
    pub dev_mode: bool,
    #[serde(default = "default_log_level")]
    pub log_level: String,
}

fn default_display_name() -> String {
    "main".to_string()
}
fn default_serial_baudrate() -> u32 {
    57600
}
fn default_module_layout() -> Vec<Vec<u32>> {
    vec![vec![1], vec![2]]
}
fn default_module_width() -> u32 {
    28
}
fn default_module_height() -> u32 {
    7
}
fn default_log_level() -> String {
    "INFO".to_string()
}

#[derive(Debug, Clone, Copy, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum ResponseStatus {
    Updated,
    Clear,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
pub struct ContentResponse {
    pub status: ResponseStatus,
    pub playlist: Vec<Content>,
    pub poll_interval_ms: u32,
}

impl<'de> Deserialize<'de> for ContentResponse {
    fn deserialize<D: Deserializer<'de>>(d: D) -> Result<Self, D::Error> {
        #[derive(Deserialize)]
        struct Raw {
            status: ResponseStatus,
            #[serde(default)]
            playlist: Vec<Content>,
            #[serde(default = "default_poll_interval", deserialize_with = "deser_u32_lenient")]
            poll_interval_ms: u32,
        }
        fn default_poll_interval() -> u32 {
            30000
        }
        let raw = Raw::deserialize(d)?;
        if raw.poll_interval_ms < 1000 {
            return Err(D::Error::custom("poll_interval_ms must be >= 1000"));
        }
        if raw.status == ResponseStatus::Updated && raw.playlist.is_empty() {
            return Err(D::Error::custom(
                "playlist must be non-empty when status is 'updated'",
            ));
        }
        Ok(ContentResponse {
            status: raw.status,
            playlist: raw.playlist,
            poll_interval_ms: raw.poll_interval_ms,
        })
    }
}

impl Content {
    pub fn validate_display_dimensions(
        &self,
        display_width: u32,
        display_height: u32,
    ) -> Result<(), ContentError> {
        if let Some(frame) = self.frames.first() {
            if frame.width != display_width || frame.height != display_height {
                return Err(ContentError::DimensionMismatch {
                    content_id: self.content_id.clone(),
                    actual_w: frame.width,
                    actual_h: frame.height,
                    expected_w: display_width,
                    expected_h: display_height,
                });
            }
        }
        Ok(())
    }
}
