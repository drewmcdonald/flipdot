use flipdot_driver::limits::SerialLimits;
use flipdot_driver::serial::{SerialConnection, SerialPort};
use std::io;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};

type Writes = Arc<Mutex<Vec<Vec<u8>>>>;
type FailFlag = Arc<Mutex<bool>>;

#[derive(Default)]
struct FakePort {
    writes: Writes,
    fail_next: FailFlag,
}

impl FakePort {
    fn new() -> (Writes, FailFlag, Self) {
        let writes = Arc::new(Mutex::new(Vec::new()));
        let fail = Arc::new(Mutex::new(false));
        let port = FakePort {
            writes: writes.clone(),
            fail_next: fail.clone(),
        };
        (writes, fail, port)
    }
}

impl SerialPort for FakePort {
    fn write(&mut self, data: &[u8]) -> io::Result<usize> {
        if *self.fail_next.lock().unwrap() {
            return Err(io::Error::new(io::ErrorKind::BrokenPipe, "simulated"));
        }
        self.writes.lock().unwrap().push(data.to_vec());
        Ok(data.len())
    }
}

#[test]
fn dev_mode_writes_succeed_without_port() {
    let mut conn = SerialConnection::dev_mode();
    assert!(conn.write(b"hello", Instant::now()));
    assert_eq!(conn.consecutive_failures(), 0);
}

#[test]
fn writes_pass_through_to_port() {
    let (writes, _fail, port) = FakePort::new();
    let mut conn = SerialConnection::with_port(Box::new(port), SerialLimits::default());
    assert!(conn.write(b"payload", Instant::now()));
    assert_eq!(writes.lock().unwrap().as_slice(), &[b"payload".to_vec()]);
    assert_eq!(conn.consecutive_failures(), 0);
}

#[test]
fn failures_increment_counter_and_drop_port() {
    let (_writes, fail, port) = FakePort::new();
    *fail.lock().unwrap() = true;
    let mut conn = SerialConnection::with_port(Box::new(port), SerialLimits::default());
    let now = Instant::now();
    assert!(!conn.write(b"x", now));
    assert_eq!(conn.consecutive_failures(), 1);
    // Port dropped after failure -> no reconnect factory means retry also counts.
    assert!(!conn.write(b"x", now + Duration::from_millis(2_000)));
    assert_eq!(conn.consecutive_failures(), 2);
}

#[test]
fn success_resets_failure_counter() {
    let (_writes, fail, port) = FakePort::new();
    *fail.lock().unwrap() = true;
    let mut conn = SerialConnection::with_port(Box::new(port), SerialLimits::default());
    let now = Instant::now();
    conn.write(b"x", now);
    conn.write(b"x", now);
    assert_eq!(conn.consecutive_failures(), 2);
    // Recover by making future writes succeed — but the port has been dropped.
    // The reconnect factory (injected) produces a fresh fake port that succeeds.
    let fresh_writes: Arc<Mutex<Vec<Vec<u8>>>> = Arc::new(Mutex::new(Vec::new()));
    let shared = fresh_writes.clone();
    conn.set_reconnect_factory(Box::new(move || {
        let w = shared.clone();
        Ok(Box::new(EverSucceedingPort { writes: w }) as Box<dyn SerialPort>)
    }));
    // After backoff elapses reconnect succeeds and the write goes through.
    assert!(conn.write(b"good", now + Duration::from_millis(2_000)));
    assert_eq!(conn.consecutive_failures(), 0);
    assert_eq!(fresh_writes.lock().unwrap().as_slice(), &[b"good".to_vec()]);
}

#[test]
fn reconnect_respects_backoff_before_retrying() {
    // Port absent, factory would succeed, but backoff hasn't elapsed yet.
    let conn_limits = SerialLimits {
        initial_reconnect_backoff_ms: 5_000,
        ..SerialLimits::default()
    };
    let mut conn = SerialConnection::without_port(conn_limits);
    let attempts = Arc::new(Mutex::new(0u32));
    let seen = attempts.clone();
    conn.set_reconnect_factory(Box::new(move || {
        *seen.lock().unwrap() += 1;
        Err(io::Error::new(io::ErrorKind::NotFound, "no device"))
    }));
    let t0 = Instant::now();
    // First call attempts reconnect (attempts=1), fails.
    assert!(!conn.write(b"x", t0));
    assert_eq!(*attempts.lock().unwrap(), 1);
    // Backoff not elapsed -> no additional reconnect attempt.
    assert!(!conn.write(b"x", t0 + Duration::from_millis(100)));
    assert_eq!(*attempts.lock().unwrap(), 1);
    // Backoff doubled to 10s after the first failure; 5.5s isn't enough.
    assert!(!conn.write(b"x", t0 + Duration::from_millis(5_500)));
    assert_eq!(*attempts.lock().unwrap(), 1);
    // 11s exceeds the 10s doubled backoff -> second retry.
    assert!(!conn.write(b"x", t0 + Duration::from_millis(11_000)));
    assert_eq!(*attempts.lock().unwrap(), 2);
}

struct EverSucceedingPort {
    writes: Arc<Mutex<Vec<Vec<u8>>>>,
}
impl SerialPort for EverSucceedingPort {
    fn write(&mut self, data: &[u8]) -> io::Result<usize> {
        self.writes.lock().unwrap().push(data.to_vec());
        Ok(data.len())
    }
}
