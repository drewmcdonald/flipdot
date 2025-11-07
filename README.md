# FlipDot Driver v2.0

A lightweight driver for flipdot displays that fetches pre-rendered content from a remote server.

## Architecture Overview

The new architecture separates the **driver** (runs on Raspberry Pi) from the **content server** (runs anywhere). This separation allows:

- Faster startup times on the Pi (no NumPy, minimal dependencies)
- Heavy lifting (rendering, fonts, animations) happens on a powerful server
- Easier development and testing
- Better scalability

```
┌─────────────────────────────────┐
│  CONTENT SERVER (anywhere)      │
│  - Render frames                │
│  - Generate animations          │
│  - Return structured JSON       │
└────────────┬────────────────────┘
             │ HTTP/JSON
             ▼
┌─────────────────────────────────┐
│  DRIVER (Raspberry Pi)          │
│  - Poll for content             │
│  - Accept push notifications    │
│  - Manage frame queue           │
│  - Send to hardware             │
└────────────┬────────────────────┘
             │ Serial
             ▼
┌─────────────────────────────────┐
│  FLIPDOT HARDWARE               │
└─────────────────────────────────┘
```

## Quick Start

### 1. Install Dependencies

The driver has minimal dependencies:

```bash
pip install pydantic pyserial
```

### 2. Create Configuration

Copy the example configuration:

```bash
cp config.example.json config.json
```

Edit `config.json` with your settings:

```json
{
  "poll_endpoint": "https://your-server.com/api/flipdot/content",
  "auth": {
    "type": "api_key",
    "key": "your-secret-key"
  },
  "serial_device": "/dev/ttyUSB0",
  "module_layout": [[1], [2]]
}
```

### 3. Run the Driver

```bash
python -m flipdot.driver.main --config config.json
```

For development (no hardware):

```bash
python -m flipdot.driver.main --config config.dev.json
```

## Data Structures

### Frame

A single image to display:

```json
{
  "data_b64": "AQIDBAUGBwgJ...",
  "width": 56,
  "height": 14,
  "duration_ms": 1000
}
```

- `data_b64`: Base64-encoded packed bits (little-endian)
- `width`, `height`: Dimensions in pixels
- `duration_ms`: How long to display (null = indefinite)

### Content

A sequence of frames with playback instructions:

```json
{
  "content_id": "clock-12:00",
  "frames": [
    /* array of Frame objects */
  ],
  "playback": {
    "loop": true,
    "loop_count": null,
    "priority": 0,
    "interruptible": true
  }
}
```

- `content_id`: Unique identifier
- `frames`: Array of Frame objects
- `playback.loop`: Whether to loop frames
- `playback.loop_count`: How many times to loop (null = infinite)
- `playback.priority`: Priority level (0=normal, 10=notification, 99=urgent)
- `playback.interruptible`: Can be interrupted by higher priority?

### ContentResponse

What the server returns:

```json
{
  "status": "updated",
  "content": {
    /* Content object */
  },
  "poll_interval_ms": 30000
}
```

- `status`: "updated", "no_change", or "clear"
- `content`: Content object (only if status="updated")
- `poll_interval_ms`: How long to wait before next poll

## Server API

The driver expects a server endpoint that returns `ContentResponse` JSON.

### Polling Endpoint

**GET** `/api/flipdot/content`

Returns the current content to display.

**Headers:**

- `X-API-Key: your-secret-key` (or `Authorization: Bearer token`)

**Response:**

```json
{
  "status": "updated",
  "content": {
    "content_id": "clock-12:00",
    "frames": [...],
    "playback": {...}
  },
  "poll_interval_ms": 30000
}
```

### Push Notifications (Optional)

If `enable_push: true` in config, the driver runs a simple HTTP server:

**POST** `http://pi-address:8080/`

Push high-priority content immediately.

**Headers:**

- `X-API-Key: your-secret-key`
- `Content-Type: application/json`

**Body:**

```json
{
  "content_id": "notification",
  "frames": [...],
  "playback": {
    "priority": 10,
    "interruptible": false
  }
}
```

## Configuration Reference

```json
{
  // Server settings
  "poll_endpoint": "https://example.com/api/content",
  "poll_interval_ms": 30000,

  // Push server (optional)
  "enable_push": false,
  "push_port": 8080,
  "push_host": "0.0.0.0",

  // Authentication
  "auth": {
    "type": "api_key", // or "bearer"
    "key": "secret-key",
    "header_name": "X-API-Key"
  },

  // Hardware
  "serial_device": "/dev/ttyUSB0",
  "serial_baudrate": 57600,
  "module_layout": [[1], [2]],
  "module_width": 28,
  "module_height": 7,

  // Behavior
  "error_fallback": "keep_last", // "keep_last", "blank", or "error_message"
  "dev_mode": false,
  "log_level": "INFO"
}
```

## Content Queue & Priorities

The driver maintains a priority queue:

- **Priority 0-9**: Normal content (clock, weather, etc.)
- **Priority 10-98**: Notifications
- **Priority 99**: Urgent alerts

Higher priority content **interrupts** lower priority if marked as `interruptible`.

Example flow:

1. Clock is displaying (priority 0)
2. Notification arrives (priority 10)
3. Clock pauses, notification plays
4. Notification completes
5. Clock resumes from where it left off

## Generating Content

See `examples/generate_content.py` for examples of creating frames:

```python
from flipdot.hardware import pack_bits_little_endian
import base64

# Create a 2x2 frame
bits = [1, 0, 1, 0]  # Row-major order
packed = pack_bits_little_endian(bits)
b64 = base64.b64encode(packed).decode()

frame = {
    "data_b64": b64,
    "width": 2,
    "height": 2,
    "duration_ms": 1000
}
```

## Testing

Run tests:

```bash
pytest tests/test_driver.py
```

Generate example content:

```bash
cd examples
python generate_content.py
```

## Development Mode

Use `dev_mode: true` to test without hardware:

```bash
python -m flipdot.driver.main --config config.dev.json
```

The driver will print serial data to the console instead of sending to hardware.

## Migration from v1.0

**Key changes:**

1. **Driver is now minimal**: Only handles display logic, no rendering
2. **NumPy removed**: Faster startup on Pi
3. **Server provides frames**: All rendering happens server-side
4. **New data format**: Base64-encoded packed bits instead of live rendering
5. **Priority queue**: Better support for notifications

**What was removed from the Pi:**

- FastAPI web server
- React frontend
- Display modes (Clock, ScrollText, Weather, etc.)
- NumPy dependency

**What moved to the content server:**

- All rendering logic
- Font handling
- Animation generation
- Display mode implementations

## Troubleshooting

### Driver can't connect to server

Check:

- `poll_endpoint` is correct
- Authentication credentials match
- Server is running and accessible

### Serial device not found

Check:

- Device path is correct (`/dev/ttyUSB0`, `/dev/ttyACM0`, etc.)
- User has permission to access serial port
- Run: `sudo usermod -a -G dialout $USER`

### Frames not displaying

Check:

- Frame dimensions match display dimensions
- `data_b64` is valid base64
- Driver logs for errors (`log_level: "DEBUG"`)

## Next Steps

This is Phase 1 and 2 of the refactor. Still TODO:

- **Phase 3**: Build the content server
  - Migrate existing mode logic
  - Create API endpoints
  - Handle rendering server-side
- **Phase 4**: Advanced features
  - Content caching
  - Compression
  - Transition effects
