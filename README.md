# FlipDot v2.0

Lightweight driver + content server for flipdot displays. 

The architecture consists of a Rust-based driver running on a Raspberry Pi and a Convex (TypeScript/React) backend for content generation and management.

## Project Structure

- `driver-rs/`: Rust driver that subscribes to Convex and drives the hardware via serial.
- `server/`: Convex backend + React virtual display.

## Architecture

```
[Convex Backend]  ──real-time subscription──>  [Rust Driver]  ──serial──>  [FlipDot Hardware]
       │                                              │
   cron: clock                                   ConvexClient
   rendering pipeline                            Driver
   displays table                                SerialConnection
       │
[React Virtual Display]  (dev/testing UI, subscribes to same query)
```

## Getting Started

### Driver (Rust)

The driver runs on a Raspberry Pi and communicates with the flipdot modules over serial.

```bash
cd driver-rs
cargo build --release
./target/release/flipdot --config config.json
```

See `driver-rs/config.example.json` for configuration options.

### Server (Convex + React)

The server manages display state and provides a virtual preview.

```bash
cd server
npm install
npm run dev
```

## Features

- **Real-time updates**: Subscribes to Convex for instant content changes.
- **Minimal footprint**: Rust driver is efficient and has minimal dependencies.
- **Virtual Display**: Web-based preview for development without hardware.
- **Flexible Layout**: Supports multiple modules in various configurations.

## License

MIT
