use flipdot_driver::models::Frame;

const FIXTURE_SINGLE: &str = include_str!("fixtures/frame_single_pixel.json");
const FIXTURE_ALL_ON: &str = include_str!("fixtures/frame_all_on_indefinite.json");

#[test]
fn deserializes_single_pixel_frame_fixture() {
    let frame: Frame = serde_json::from_str(FIXTURE_SINGLE).expect("valid Frame JSON");
    assert_eq!(frame.width, 28);
    assert_eq!(frame.height, 14);
    assert_eq!(frame.duration_ms, Some(500));
    // Bit 0 of byte 0 set -> the (0,0) pixel. Decoded data should be 49 bytes
    // (ceil(28*14 / 8)) with byte 0 == 0x01 and the rest zero.
    let data = frame.decode_data().expect("valid base64");
    assert_eq!(data.len(), 49);
    assert_eq!(data[0], 0x01);
    assert!(data[1..].iter().all(|&b| b == 0));
}

#[test]
fn deserializes_indefinite_duration_as_none() {
    let frame: Frame = serde_json::from_str(FIXTURE_ALL_ON).expect("valid Frame JSON");
    assert_eq!(frame.duration_ms, None);
    let data = frame.decode_data().expect("valid base64");
    assert!(data.iter().all(|&b| b == 0xFF));
}

#[test]
fn rejects_invalid_base64() {
    let bad =
        r#"{"data_b64":"not*base64!","width":28,"height":14,"duration_ms":null,"metadata":null}"#;
    let frame: Frame = serde_json::from_str(bad).expect("structural JSON still parses");
    assert!(frame.decode_data().is_err());
}

#[test]
fn to_bit_array_unpacks_little_endian_row_major() {
    let frame: Frame = serde_json::from_str(FIXTURE_SINGLE).unwrap();
    let bits = frame.to_bit_array().unwrap();
    assert_eq!(bits.len(), 14);
    assert_eq!(bits[0].len(), 28);
    // Only pixel (0,0) should be on.
    assert_eq!(bits[0][0], 1);
    for (r, row) in bits.iter().enumerate() {
        for (c, bit) in row.iter().enumerate() {
            if (r, c) == (0, 0) {
                continue;
            }
            assert_eq!(*bit, 0u8, "unexpected set pixel at ({r},{c})");
        }
    }
}

#[test]
fn round_trip_serialization_preserves_fixture() {
    let frame: Frame = serde_json::from_str(FIXTURE_SINGLE).unwrap();
    let reserialized = serde_json::to_value(&frame).unwrap();
    let fixture: serde_json::Value = serde_json::from_str(FIXTURE_SINGLE).unwrap();
    assert_eq!(reserialized, fixture);
}
