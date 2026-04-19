use flipdot_driver::models::PlaybackMode;

const FIXTURE_DEFAULT: &str = include_str!("fixtures/playback_default.json");
const FIXTURE_INFINITE: &str = include_str!("fixtures/playback_loop_infinite.json");
const FIXTURE_COUNT: &str = include_str!("fixtures/playback_loop_count.json");

#[test]
fn default_is_no_loop() {
    let pb: PlaybackMode = serde_json::from_str(FIXTURE_DEFAULT).unwrap();
    assert!(!pb.looping);
    assert_eq!(pb.loop_count, None);
}

#[test]
fn infinite_loop_has_no_count() {
    let pb: PlaybackMode = serde_json::from_str(FIXTURE_INFINITE).unwrap();
    assert!(pb.looping);
    assert_eq!(pb.loop_count, None);
}

#[test]
fn bounded_loop_has_count() {
    let pb: PlaybackMode = serde_json::from_str(FIXTURE_COUNT).unwrap();
    assert!(pb.looping);
    assert_eq!(pb.loop_count, Some(3));
}

#[test]
fn round_trip_preserves_fixture_shape() {
    for fixture in [FIXTURE_DEFAULT, FIXTURE_INFINITE, FIXTURE_COUNT] {
        let pb: PlaybackMode = serde_json::from_str(fixture).unwrap();
        let reserialized = serde_json::to_value(&pb).unwrap();
        let original: serde_json::Value = serde_json::from_str(fixture).unwrap();
        assert_eq!(
            reserialized, original,
            "round-trip mismatch for:\n{fixture}"
        );
    }
}

#[test]
fn rejects_loop_count_without_loop() {
    // Python Pydantic validator rejects loop_count set when loop=false.
    // Rust side must validate equivalently.
    let bad = r#"{"loop":false,"loop_count":5}"#;
    let result: Result<PlaybackMode, _> = serde_json::from_str(bad);
    assert!(
        result.is_err(),
        "expected validation error, got: {result:?}"
    );
}

#[test]
fn rejects_zero_loop_count() {
    // Pydantic: loop_count: ge=1 (>= 1). 0 is invalid.
    let bad = r#"{"loop":true,"loop_count":0}"#;
    let result: Result<PlaybackMode, _> = serde_json::from_str(bad);
    assert!(
        result.is_err(),
        "expected validation error, got: {result:?}"
    );
}
