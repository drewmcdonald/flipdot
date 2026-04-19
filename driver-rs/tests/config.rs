use flipdot_driver::models::DriverConfig;

const FIXTURE: &str = include_str!("fixtures/driver_config.json");
const EXAMPLE_CONFIG: &str = include_str!("../../flipdot/config.example.json");

#[test]
fn deserializes_fixture() {
    let cfg: DriverConfig = serde_json::from_str(FIXTURE).unwrap();
    assert_eq!(cfg.convex_url, "https://your-deployment.convex.cloud");
    assert_eq!(cfg.display_name, "main");
    assert_eq!(cfg.serial_device.as_deref(), Some("/dev/ttyUSB0"));
    assert_eq!(cfg.serial_baudrate, 57600);
    assert_eq!(cfg.module_layout, vec![vec![1], vec![2]]);
    assert_eq!(cfg.module_width, 28);
    assert_eq!(cfg.module_height, 7);
    assert!(!cfg.dev_mode);
    assert_eq!(cfg.log_level, "INFO");
}

#[test]
fn deserializes_actual_example_config_from_python_package() {
    // Same file the Python driver ships — must parse identically.
    let cfg: DriverConfig = serde_json::from_str(EXAMPLE_CONFIG).unwrap();
    assert_eq!(cfg.serial_baudrate, 57600);
    assert_eq!(cfg.module_width, 28);
    assert_eq!(cfg.module_height, 7);
}

#[test]
fn minimal_config_uses_defaults() {
    let minimal = r#"{"convex_url":"https://x.convex.cloud"}"#;
    let cfg: DriverConfig = serde_json::from_str(minimal).unwrap();
    assert_eq!(cfg.display_name, "main");
    assert_eq!(cfg.serial_baudrate, 57600);
    assert_eq!(cfg.module_width, 28);
    assert_eq!(cfg.module_height, 7);
    assert_eq!(cfg.module_layout, vec![vec![1], vec![2]]);
    assert!(!cfg.dev_mode);
    assert_eq!(cfg.log_level, "INFO");
    assert!(cfg.serial_device.is_none());
}

#[test]
fn round_trip_preserves_fixture() {
    let cfg: DriverConfig = serde_json::from_str(FIXTURE).unwrap();
    let reserialized = serde_json::to_value(&cfg).unwrap();
    let original: serde_json::Value = serde_json::from_str(FIXTURE).unwrap();
    assert_eq!(reserialized, original);
}

#[test]
fn missing_convex_url_errors() {
    // convex_url is required (Pydantic ...).
    let bad = r#"{"display_name":"main"}"#;
    let result: Result<DriverConfig, _> = serde_json::from_str(bad);
    assert!(result.is_err());
}
