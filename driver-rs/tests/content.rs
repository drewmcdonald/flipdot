use flipdot_driver::models::Content;

const FIXTURE_TWO_FRAMES: &str = include_str!("fixtures/content_two_frames.json");

fn fixture_frame(width: u32, height: u32, duration_ms: Option<u32>) -> serde_json::Value {
    // 28x14 = 392 bits = 49 bytes, all zero -> 49 zero bytes base64'd.
    // For other sizes, generate ceil(w*h/8) zero bytes.
    let n_bytes = (width * height).div_ceil(8);
    let zero = vec![0u8; n_bytes as usize];
    let b64 = base64::Engine::encode(&base64::engine::general_purpose::STANDARD, &zero);
    serde_json::json!({
        "data_b64": b64,
        "width": width,
        "height": height,
        "duration_ms": duration_ms,
        "metadata": null,
    })
}

#[test]
fn deserializes_two_frame_fixture() {
    let c: Content = serde_json::from_str(FIXTURE_TWO_FRAMES).unwrap();
    assert_eq!(c.content_id, "test-content-1");
    assert_eq!(c.frames.len(), 2);
    assert!(c.playback.looping);
    assert_eq!(c.playback.loop_count, Some(2));
    assert!(c.metadata.is_some());
}

#[test]
fn round_trip_preserves_two_frame_fixture() {
    let c: Content = serde_json::from_str(FIXTURE_TWO_FRAMES).unwrap();
    let reserialized = serde_json::to_value(&c).unwrap();
    let original: serde_json::Value = serde_json::from_str(FIXTURE_TWO_FRAMES).unwrap();
    assert_eq!(reserialized, original);
}

#[test]
fn rejects_empty_frames() {
    let bad = serde_json::json!({
        "content_id": "empty",
        "frames": [],
        "playback": {"loop": false, "loop_count": null},
        "metadata": null,
    });
    let result: Result<Content, _> = serde_json::from_value(bad);
    assert!(
        result.is_err(),
        "expected error for empty frames, got {result:?}"
    );
}

#[test]
fn rejects_mismatched_frame_dimensions() {
    let bad = serde_json::json!({
        "content_id": "mixed",
        "frames": [fixture_frame(28, 14, Some(100)), fixture_frame(28, 7, Some(100))],
        "playback": {"loop": false, "loop_count": null},
        "metadata": null,
    });
    let result: Result<Content, _> = serde_json::from_value(bad);
    assert!(
        result.is_err(),
        "expected error for mismatched dims, got {result:?}"
    );
}

#[test]
fn rejects_too_many_frames() {
    // MAX_FRAMES_PER_CONTENT = 1000. 1001 frames -> error.
    let frames: Vec<_> = (0..1001).map(|_| fixture_frame(1, 1, Some(10))).collect();
    let bad = serde_json::json!({
        "content_id": "huge",
        "frames": frames,
        "playback": {"loop": false, "loop_count": null},
        "metadata": null,
    });
    let result: Result<Content, _> = serde_json::from_value(bad);
    assert!(result.is_err(), "expected error for >1000 frames, got Ok");
}

#[test]
fn validate_display_dimensions_matches() {
    let c: Content = serde_json::from_str(FIXTURE_TWO_FRAMES).unwrap();
    assert!(c.validate_display_dimensions(28, 14).is_ok());
    assert!(c.validate_display_dimensions(28, 7).is_err());
}
