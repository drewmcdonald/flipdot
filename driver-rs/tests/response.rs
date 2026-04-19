use flipdot_driver::models::{ContentResponse, ResponseStatus};

const FIXTURE_UPDATED: &str = include_str!("fixtures/response_updated.json");
const FIXTURE_CLEAR: &str = include_str!("fixtures/response_clear.json");

#[test]
fn deserializes_updated_response() {
    let r: ContentResponse = serde_json::from_str(FIXTURE_UPDATED).unwrap();
    assert_eq!(r.status, ResponseStatus::Updated);
    assert_eq!(r.playlist.len(), 1);
    assert_eq!(r.poll_interval_ms, 30000);
}

#[test]
fn deserializes_clear_response() {
    let r: ContentResponse = serde_json::from_str(FIXTURE_CLEAR).unwrap();
    assert_eq!(r.status, ResponseStatus::Clear);
    assert!(r.playlist.is_empty());
}

#[test]
fn round_trip_preserves_fixtures() {
    for fixture in [FIXTURE_UPDATED, FIXTURE_CLEAR] {
        let r: ContentResponse = serde_json::from_str(fixture).unwrap();
        let reserialized = serde_json::to_value(&r).unwrap();
        let original: serde_json::Value = serde_json::from_str(fixture).unwrap();
        assert_eq!(reserialized, original);
    }
}

#[test]
fn rejects_updated_with_empty_playlist() {
    let bad = serde_json::json!({
        "status": "updated",
        "playlist": [],
        "poll_interval_ms": 30000,
    });
    let result: Result<ContentResponse, _> = serde_json::from_value(bad);
    assert!(result.is_err(), "expected error for updated+empty playlist");
}

#[test]
fn rejects_too_small_poll_interval() {
    // Pydantic: poll_interval_ms ge=1000.
    let bad = serde_json::json!({
        "status": "clear",
        "playlist": [],
        "poll_interval_ms": 500,
    });
    let result: Result<ContentResponse, _> = serde_json::from_value(bad);
    assert!(result.is_err(), "expected error for poll_interval_ms < 1000");
}
