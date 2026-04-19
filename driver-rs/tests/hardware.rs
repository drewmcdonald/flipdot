use flipdot_driver::hardware::{pack_bits_little_endian, Panel};
use serde::Deserialize;

const PACK_BITS_FIXTURES: &str = include_str!("fixtures/hardware_pack_bits_cases.json");
const PANEL_FIXTURES: &str = include_str!("fixtures/hardware_panel_cases.json");

#[derive(Deserialize)]
struct PackBitsCase {
    name: String,
    bits: Vec<u8>,
    expected_hex: String,
}

#[derive(Deserialize)]
struct PanelCase {
    name: String,
    layout: Vec<Vec<u32>>,
    module_width: u32,
    module_height: u32,
    matrix: Vec<Vec<u8>>,
    expected_hex: String,
}

fn hex_encode(bytes: &[u8]) -> String {
    let mut s = String::with_capacity(bytes.len() * 2);
    for b in bytes {
        s.push_str(&format!("{:02x}", b));
    }
    s
}

#[test]
fn pack_bits_matches_python_fixtures() {
    let cases: Vec<PackBitsCase> = serde_json::from_str(PACK_BITS_FIXTURES).unwrap();
    assert!(!cases.is_empty());
    for case in cases {
        let got = pack_bits_little_endian(&case.bits);
        assert_eq!(
            hex_encode(&got),
            case.expected_hex,
            "pack_bits case '{}' diverged from Python",
            case.name
        );
    }
}

#[test]
fn panel_set_content_matches_python_fixtures() {
    let cases: Vec<PanelCase> = serde_json::from_str(PANEL_FIXTURES).unwrap();
    assert!(cases.len() >= 4, "need coverage");
    for case in cases {
        let mut panel = Panel::new(&case.layout, case.module_width, case.module_height)
            .unwrap_or_else(|e| panic!("panel build failed for {}: {e}", case.name));
        let got = panel
            .set_content(&case.matrix)
            .unwrap_or_else(|e| panic!("set_content failed for {}: {e}", case.name));
        assert_eq!(
            hex_encode(&got),
            case.expected_hex,
            "panel case '{}' diverged from Python",
            case.name
        );
    }
}

#[test]
fn set_content_from_frame_equivalent_to_set_content() {
    // Unpacking a little-endian packed frame and calling set_content should
    // produce the same bytes as set_content_from_frame.
    let cases: Vec<PanelCase> = serde_json::from_str(PANEL_FIXTURES).unwrap();
    for case in cases {
        // Build the packed frame bytes from the matrix (row-major, LE).
        let h = case.matrix.len();
        let w = if h > 0 { case.matrix[0].len() } else { 0 };
        let mut bits: Vec<u8> = Vec::with_capacity(h * w);
        for row in &case.matrix {
            bits.extend_from_slice(row);
        }
        let packed = pack_bits_little_endian(&bits);

        let mut panel = Panel::new(&case.layout, case.module_width, case.module_height).unwrap();
        let got = panel
            .set_content_from_frame(&packed, w as u32, h as u32)
            .unwrap();
        assert_eq!(
            hex_encode(&got),
            case.expected_hex,
            "set_content_from_frame case '{}' diverged",
            case.name
        );
    }
}

#[test]
fn panel_rejects_wrong_matrix_dimensions() {
    let mut panel = Panel::new(&[vec![1], vec![2]], 28, 7).unwrap();
    // 28x13 is one row short of 28x14.
    let bad = vec![vec![0u8; 28]; 13];
    let result = panel.set_content(&bad);
    assert!(result.is_err());
}

#[test]
fn panel_rejects_non_rectangular_layout() {
    let result = Panel::new(&[vec![1, 2], vec![3]], 28, 7);
    assert!(result.is_err());
}

#[test]
fn panel_dimensions_property() {
    let panel = Panel::new(&[vec![1], vec![2]], 28, 7).unwrap();
    assert_eq!(panel.dimensions(), (14, 28));
    let panel2 = Panel::new(&[vec![1, 2]], 28, 7).unwrap();
    assert_eq!(panel2.dimensions(), (7, 56));
}
