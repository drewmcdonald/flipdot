use base64::{engine::general_purpose::STANDARD as B64, Engine as _};
use flipdot_driver::models::{Content, Frame};
use flipdot_driver::queue::{ContentQueue, ContentState};
use std::time::{Duration, Instant};

fn frame(duration_ms: Option<u32>) -> Frame {
    // 1x1 pixel = 1 bit; ceil(1/8) = 1 byte.
    let data = B64.encode([0u8]);
    Frame {
        data_b64: data,
        width: 1,
        height: 1,
        duration_ms,
        metadata: None,
    }
}

fn content(id: &str, frames: Vec<Frame>, looping: bool, loop_count: Option<u32>) -> Content {
    serde_json::from_value(serde_json::json!({
        "content_id": id,
        "frames": frames.into_iter().map(|f| serde_json::json!({
            "data_b64": f.data_b64,
            "width": f.width,
            "height": f.height,
            "duration_ms": f.duration_ms,
            "metadata": null,
        })).collect::<Vec<_>>(),
        "playback": {"loop": looping, "loop_count": loop_count},
        "metadata": null,
    }))
    .expect("valid content")
}

#[test]
fn state_does_not_advance_before_duration_elapses() {
    let t0 = Instant::now();
    let c = content("c", vec![frame(Some(100)), frame(Some(100))], false, None);
    let mut s = ContentState::new(c, t0);
    assert!(!s.advance_frame(t0 + Duration::from_millis(50)));
    assert_eq!(s.frame_index(), 0);
}

#[test]
fn state_advances_after_duration_elapses() {
    let t0 = Instant::now();
    let c = content("c", vec![frame(Some(100)), frame(Some(100))], false, None);
    let mut s = ContentState::new(c, t0);
    assert!(s.advance_frame(t0 + Duration::from_millis(150)));
    assert_eq!(s.frame_index(), 1);
}

#[test]
fn state_with_indefinite_duration_never_advances() {
    let t0 = Instant::now();
    let c = content("c", vec![frame(None), frame(Some(100))], false, None);
    let mut s = ContentState::new(c, t0);
    assert!(!s.advance_frame(t0 + Duration::from_secs(60)));
    assert_eq!(s.frame_index(), 0);
}

#[test]
fn state_with_zero_duration_never_advances() {
    // Python: duration_ms=0 also means indefinite.
    let t0 = Instant::now();
    let c = content("c", vec![frame(Some(0)), frame(Some(100))], false, None);
    let mut s = ContentState::new(c, t0);
    assert!(!s.advance_frame(t0 + Duration::from_secs(60)));
    assert_eq!(s.frame_index(), 0);
}

#[test]
fn state_loops_back_to_frame_zero_when_looping() {
    let t0 = Instant::now();
    let c = content("c", vec![frame(Some(100)), frame(Some(100))], true, None);
    let mut s = ContentState::new(c, t0);
    s.advance_frame(t0 + Duration::from_millis(150));
    assert_eq!(s.frame_index(), 1);
    s.advance_frame(t0 + Duration::from_millis(300));
    assert_eq!(s.frame_index(), 0);
    assert_eq!(s.loop_count(), 1);
}

#[test]
fn state_stays_on_last_frame_when_not_looping() {
    let t0 = Instant::now();
    let c = content("c", vec![frame(Some(100)), frame(Some(100))], false, None);
    let mut s = ContentState::new(c, t0);
    s.advance_frame(t0 + Duration::from_millis(150));
    assert_eq!(s.frame_index(), 1);
    // After last frame's duration, stays on last frame (so is_complete can detect).
    s.advance_frame(t0 + Duration::from_millis(400));
    assert_eq!(s.frame_index(), 1);
}

#[test]
fn is_complete_true_after_last_frame_duration_without_loop() {
    let t0 = Instant::now();
    let c = content("c", vec![frame(Some(100))], false, None);
    let s = ContentState::new(c, t0);
    assert!(!s.is_complete(t0 + Duration::from_millis(50)));
    assert!(s.is_complete(t0 + Duration::from_millis(150)));
}

#[test]
fn is_complete_false_indefinite_last_frame() {
    let t0 = Instant::now();
    let c = content("c", vec![frame(None)], false, None);
    let s = ContentState::new(c, t0);
    assert!(!s.is_complete(t0 + Duration::from_secs(3600)));
}

#[test]
fn is_complete_respects_loop_count_limit() {
    let t0 = Instant::now();
    let c = content("c", vec![frame(Some(100))], true, Some(2));
    let mut s = ContentState::new(c, t0);
    // loop_count starts at 0; advance twice to complete two full loops.
    s.advance_frame(t0 + Duration::from_millis(150)); // loops back, loop_count=1
    assert_eq!(s.loop_count(), 1);
    assert!(!s.is_complete(t0 + Duration::from_millis(150)));
    s.advance_frame(t0 + Duration::from_millis(300)); // loops back, loop_count=2
    assert_eq!(s.loop_count(), 2);
    assert!(s.is_complete(t0 + Duration::from_millis(300)));
}

#[test]
fn queue_update_returns_current_frame() {
    let t0 = Instant::now();
    let mut q = ContentQueue::new();
    let c = content("a", vec![frame(Some(100))], false, None);
    q.set_playlist(vec![c], t0);
    let f = q.update(t0).expect("expected a frame");
    assert_eq!(f.width, 1);
}

#[test]
fn queue_advances_to_next_content_when_current_completes() {
    let t0 = Instant::now();
    let mut q = ContentQueue::new();
    q.set_playlist(
        vec![
            content("a", vec![frame(Some(100))], false, None),
            content("b", vec![frame(None)], false, None),
        ],
        t0,
    );
    assert_eq!(q.current_content_id(), Some("a"));
    let _ = q.update(t0 + Duration::from_millis(150));
    assert_eq!(q.current_content_id(), Some("b"));
}

#[test]
fn queue_returns_none_when_playlist_exhausted() {
    let t0 = Instant::now();
    let mut q = ContentQueue::new();
    q.set_playlist(vec![content("a", vec![frame(Some(100))], false, None)], t0);
    let _ = q.update(t0 + Duration::from_millis(150));
    assert_eq!(q.current_content_id(), None);
    assert!(q.update(t0 + Duration::from_millis(150)).is_none());
}

#[test]
fn set_playlist_preserves_state_when_first_id_matches() {
    let t0 = Instant::now();
    let mut q = ContentQueue::new();
    q.set_playlist(
        vec![content(
            "a",
            vec![frame(Some(100)), frame(Some(100))],
            false,
            None,
        )],
        t0,
    );
    // Advance to frame 1.
    let _ = q.update(t0 + Duration::from_millis(150));
    // Now push a new playlist with the same content_id at position 0.
    q.set_playlist(
        vec![content(
            "a",
            vec![frame(Some(100)), frame(Some(100))],
            false,
            None,
        )],
        t0 + Duration::from_millis(150),
    );
    // Frame index should be preserved (still 1).
    assert_eq!(q.current_frame_index(), Some(1));
}

#[test]
fn set_playlist_resets_state_when_first_id_differs() {
    let t0 = Instant::now();
    let mut q = ContentQueue::new();
    q.set_playlist(
        vec![content(
            "a",
            vec![frame(Some(100)), frame(Some(100))],
            false,
            None,
        )],
        t0,
    );
    let _ = q.update(t0 + Duration::from_millis(150));
    // New playlist with a different first content_id.
    q.set_playlist(
        vec![content(
            "b",
            vec![frame(Some(100)), frame(Some(100))],
            false,
            None,
        )],
        t0 + Duration::from_millis(150),
    );
    assert_eq!(q.current_content_id(), Some("b"));
    assert_eq!(q.current_frame_index(), Some(0));
}

#[test]
fn set_playlist_with_empty_clears() {
    let t0 = Instant::now();
    let mut q = ContentQueue::new();
    q.set_playlist(vec![content("a", vec![frame(None)], false, None)], t0);
    q.set_playlist(vec![], t0);
    assert!(q.current_content_id().is_none());
}
