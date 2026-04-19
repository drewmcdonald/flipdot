use crate::models::{Content, Frame};
use std::collections::VecDeque;
use std::time::{Duration, Instant};

/// Per-content playback tracking. Time is injected via `now: Instant` so
/// tests stay deterministic without hitting the system clock.
pub struct ContentState {
    content: Content,
    frame_index: usize,
    loop_count: u32,
    frame_start_time: Instant,
}

impl ContentState {
    pub fn new(content: Content, now: Instant) -> Self {
        Self {
            content,
            frame_index: 0,
            loop_count: 0,
            frame_start_time: now,
        }
    }

    pub fn frame_index(&self) -> usize {
        self.frame_index
    }
    pub fn loop_count(&self) -> u32 {
        self.loop_count
    }
    pub fn content_id(&self) -> &str {
        &self.content.content_id
    }
    pub fn current_frame(&self) -> &Frame {
        &self.content.frames[self.frame_index]
    }

    pub fn advance_frame(&mut self, now: Instant) -> bool {
        let Some(duration_ms) = self.current_frame().duration_ms else {
            return false;
        };
        if duration_ms == 0 {
            return false;
        }
        let elapsed = now.saturating_duration_since(self.frame_start_time);
        if elapsed < Duration::from_millis(duration_ms as u64) {
            return false;
        }

        self.frame_index += 1;
        let n = self.content.frames.len();
        if self.frame_index >= n {
            if self.content.playback.looping {
                self.frame_index = 0;
                self.loop_count += 1;
                self.frame_start_time = now;
            } else {
                // Clamp to last frame; is_complete() detects end-of-content.
                self.frame_index = n - 1;
            }
        } else {
            self.frame_start_time = now;
        }
        true
    }

    pub fn is_complete(&self, now: Instant) -> bool {
        let n = self.content.frames.len();
        let playback = &self.content.playback;
        if self.frame_index >= n - 1 {
            if !playback.looping {
                if let Some(d) = self.current_frame().duration_ms {
                    if d == 0 {
                        return false;
                    }
                    let elapsed = now.saturating_duration_since(self.frame_start_time);
                    return elapsed >= Duration::from_millis(d as u64);
                }
                return false;
            }
            if let Some(limit) = playback.loop_count {
                if self.loop_count >= limit {
                    return true;
                }
            }
        }
        false
    }

    /// Swap the underlying Content (when a new playlist shares content_id at
    /// position 0) while preserving playback timing. Resets if frame index
    /// is no longer valid for the new frame count.
    fn replace_content(&mut self, new_content: Content, now: Instant) {
        self.content = new_content;
        if self.frame_index >= self.content.frames.len() {
            self.frame_index = 0;
            self.loop_count = 0;
            self.frame_start_time = now;
        }
    }
}

pub struct ContentQueue {
    current: Option<ContentState>,
    queue: VecDeque<ContentState>,
}

impl Default for ContentQueue {
    fn default() -> Self {
        Self::new()
    }
}

impl ContentQueue {
    pub fn new() -> Self {
        Self {
            current: None,
            queue: VecDeque::new(),
        }
    }

    pub fn set_playlist(&mut self, playlist: Vec<Content>, now: Instant) {
        if playlist.is_empty() {
            self.clear();
            return;
        }
        let mut iter = playlist.into_iter();
        let first = iter.next().expect("non-empty above");

        // Preserve state when first content_id matches current.
        match self.current.take() {
            Some(mut s) if s.content_id() == first.content_id => {
                s.replace_content(first, now);
                self.current = Some(s);
            }
            _ => {
                self.current = Some(ContentState::new(first, now));
            }
        }

        self.queue.clear();
        for c in iter {
            self.queue.push_back(ContentState::new(c, now));
        }
    }

    /// Advance the queue and return the frame to render (or None).
    pub fn update(&mut self, now: Instant) -> Option<Frame> {
        let current = self.current.as_mut()?;
        let _ = current.advance_frame(now);
        if current.is_complete(now) {
            self.current = self.queue.pop_front();
        }
        self.current.as_ref().map(|s| s.current_frame().clone())
    }

    pub fn clear(&mut self) {
        self.current = None;
        self.queue.clear();
    }

    pub fn current_content_id(&self) -> Option<&str> {
        self.current.as_ref().map(|s| s.content_id())
    }

    pub fn current_frame_index(&self) -> Option<usize> {
        self.current.as_ref().map(|s| s.frame_index())
    }

    pub fn has_content(&self) -> bool {
        self.current.is_some()
    }
}
