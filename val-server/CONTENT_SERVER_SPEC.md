# FlipDot Content Server API Specification v2.0

**Status:** Draft
**Last Updated:** 2025-11-05
**Protocol Version:** 2.0

## 1. Overview

### 1.1 Purpose

This document specifies the HTTP API that a content server must implement to provide content to the FlipDot driver. The driver is a lightweight client that polls for content and displays it on physical flipdot hardware.

### 1.2 Architecture

```
Content Server (Stateless)
    ↓ HTTP/JSON (Poll)
Driver (Raspberry Pi)
    ↓ Serial
FlipDot Hardware
```

The content server is responsible for:
- Rendering content into frames
- Responding to polling requests
- Optionally pushing high-priority content

The driver is responsible for:
- Polling the content server
- Managing the display queue and priorities
- Timing frame transitions
- Communicating with hardware

### 1.3 Design Principles

- **Stateless Server:** The server does not track driver state
- **Client-Driven Polling:** The driver controls polling frequency
- **Push Optional:** Server can optionally push urgent content
- **Pre-Rendered:** All rendering happens server-side
- **Binary Efficient:** Frames use packed bit format

## 2. API Endpoints

### 2.1 Content Polling Endpoint (Required)

**Endpoint:** `GET {poll_endpoint}`
**Purpose:** Driver polls this endpoint to fetch current content

#### 2.1.1 Request

**Method:** `GET`

**Headers:**
```
User-Agent: FlipDot-Driver/2.0
Content-Type: application/json
```

**Authentication Headers (choose one):**
```
Authorization: Bearer {token}
```
OR
```
{header_name}: {api_key}
```
(Default header_name: `X-API-Key`)

**Query Parameters:** None required

#### 2.1.2 Response

**Status Codes:**
- `200 OK` - Content returned successfully
- `401 Unauthorized` - Authentication failed
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Endpoint not found
- `500 Internal Server Error` - Server error

**Content-Type:** `application/json`

**Body:** ContentResponse object (see Section 3)

**Example:**
```json
{
  "status": "updated",
  "content": {
    "content_id": "clock-12:00:00",
    "frames": [
      {
        "data_b64": "AQIDBAUGBwgJ",
        "width": 56,
        "height": 14,
        "duration_ms": 1000
      }
    ],
    "playback": {
      "loop": false,
      "priority": 0,
      "interruptible": true
    }
  },
  "poll_interval_ms": 30000
}
```

#### 2.1.3 Timing Guarantees

- Server SHOULD respond within 10 seconds (driver default timeout)
- Server MAY use long-polling techniques
- Server SHOULD set appropriate `poll_interval_ms` based on content update frequency

### 2.2 Push Notification Endpoint (Optional)

**Endpoint:** `POST http://{driver_host}:{push_port}/`
**Purpose:** Server pushes high-priority content directly to driver

**Note:** This endpoint is implemented by the driver, not the server. The server acts as a client to push urgent content.

#### 2.2.1 Request

**Method:** `POST`

**Headers:**
```
Content-Type: application/json
```

**Authentication Headers (must match driver config):**
```
{header_name}: {api_key}
```
OR
```
Authorization: Bearer {token}
```

**Body:** Content object (see Section 3.3)

**Example:**
```json
{
  "content_id": "urgent-alert",
  "frames": [
    {
      "data_b64": "AQIDBAUGBwgJ",
      "width": 56,
      "height": 14,
      "duration_ms": 5000
    }
  ],
  "playback": {
    "priority": 99,
    "interruptible": false
  }
}
```

#### 2.2.2 Response

**Status Codes:**
- `200 OK` - Content accepted
- `401 Unauthorized` - Authentication failed
- `413 Payload Too Large` - Request exceeds max_request_size
- `400 Bad Request` - Invalid JSON or validation error
- `500 Internal Server Error` - Driver error

**Body:**
```json
{
  "status": "accepted"
}
```

#### 2.2.3 Health Check

**Endpoint:** `GET http://{driver_host}:{push_port}/health`
**Response:**
```json
{
  "status": "ok"
}
```

## 3. Data Models

### 3.1 ContentResponse

The top-level response from the polling endpoint.

```typescript
interface ContentResponse {
  status: "updated" | "no_change" | "clear";
  content?: Content;
  poll_interval_ms: number;
}
```

**Fields:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `status` | enum | Yes | See below | Response status code |
| `content` | Content | Conditional | Required if status="updated" | Content to display |
| `poll_interval_ms` | integer | Yes | >= 1000 | Milliseconds until next poll |

**Status Values:**

| Status | Meaning | Content Field |
|--------|---------|---------------|
| `updated` | New content available | Required |
| `no_change` | Keep displaying current content | Omit |
| `clear` | Clear the display | Omit |

**Validation Rules:**
- If `status` is `"updated"`, `content` MUST be present
- If `status` is `"no_change"` or `"clear"`, `content` MUST be absent
- `poll_interval_ms` MUST be at least 1000 (1 second)

### 3.2 Content

A sequence of frames with playback configuration.

```typescript
interface Content {
  content_id: string;
  frames: Frame[];
  playback?: PlaybackMode;
  metadata?: object;
}
```

**Fields:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `content_id` | string | Yes | Non-empty | Unique identifier for this content |
| `frames` | Frame[] | Yes | 1-1000 frames | Array of frames to display |
| `playback` | PlaybackMode | No | See below | Playback configuration |
| `metadata` | object | No | Max 10KB JSON | Optional metadata for debugging |

**Validation Rules:**
- `frames` MUST contain at least 1 frame
- `frames` MUST contain at most 1000 frames
- All frames MUST have identical `width` and `height`
- Total size of all frame data plus metadata MUST NOT exceed 5MB
- If `metadata` is present, JSON-encoded size MUST NOT exceed 10KB

### 3.3 Frame

A single image to display.

```typescript
interface Frame {
  data_b64: string;
  width: number;
  height: number;
  duration_ms?: number | null;
  metadata?: object;
}
```

**Fields:**

| Field | Type | Required | Constraints | Description |
|-------|------|----------|-------------|-------------|
| `data_b64` | string | Yes | Valid base64 | Base64-encoded packed bit data |
| `width` | integer | Yes | > 0 | Frame width in pixels |
| `height` | integer | Yes | > 0 | Frame height in pixels |
| `duration_ms` | integer/null | No | >= 0 or null | Display duration (null = indefinite) |
| `metadata` | object | No | Max 10KB JSON | Optional metadata |

**Validation Rules:**
- `data_b64` MUST be valid base64 encoding
- Decoded data MUST be at least `ceil(width * height / 8)` bytes
- `width` and `height` MUST match display dimensions (validated by driver)
- `duration_ms` of `null` or `0` means display indefinitely
- If `metadata` is present, JSON-encoded size MUST NOT exceed 10KB

### 3.4 PlaybackMode

Configuration for how content should be played.

```typescript
interface PlaybackMode {
  loop?: boolean;
  loop_count?: number | null;
  priority?: number;
  interruptible?: boolean;
}
```

**Fields:**

| Field | Type | Required | Default | Constraints | Description |
|-------|------|----------|---------|-------------|-------------|
| `loop` | boolean | No | false | - | Whether to loop frames |
| `loop_count` | integer/null | No | null | >= 1, requires loop=true | Number of loops (null = infinite) |
| `priority` | integer | No | 0 | 0-99 | Priority level |
| `interruptible` | boolean | No | true | - | Can be interrupted by higher priority |

**Priority Levels:**
- **0-9:** Normal content (clock, weather, ambient)
- **10-98:** Notifications (doorbell, messages, alerts)
- **99:** Urgent/emergency alerts

**Validation Rules:**
- `loop_count` can only be set if `loop` is `true`
- `priority` MUST be between 0 and 99 inclusive

## 4. Frame Data Format

### 4.1 Packed Bit Format

Frames use a packed binary format for efficiency:

1. **Bit Ordering:** Little-endian (LSB first)
2. **Packing Direction:** Row-by-row, left-to-right
3. **Padding:** Zero-padded to byte boundary
4. **Encoding:** Base64

### 4.2 Format Specification

Given a frame of `width × height` pixels:

1. Flatten pixels into a 1D array: row-major order (left-to-right, top-to-bottom)
2. Pack bits into bytes using little-endian bit order
3. Total bytes = `ceil(width × height / 8)`
4. Encode bytes as base64

**Bit Position Formula:**
```
byte_index = pixel_index / 8
bit_position = pixel_index % 8
bit_value = (byte[byte_index] >> bit_position) & 1
```

### 4.3 Example

**Display:** 3×2 pixels

```
Visual:     Pixel Array:    Bit Array:
1 0 1       [1, 0, 1,       [1, 0, 1, 0, 1, 1, 0, 0]
0 1 1        0, 1, 1]

Byte 0: 0b00110101 = 0x35

Base64: "NQ=="
```

**Python Generation:**
```python
import base64

def pack_bits_little_endian(bits):
    """Pack array of bits into bytes (little-endian)."""
    byte_array = bytearray((len(bits) + 7) // 8)
    for i, bit in enumerate(bits):
        if bit:
            byte_array[i // 8] |= 1 << (i % 8)
    return bytes(byte_array)

bits = [1, 0, 1, 0, 1, 1, 0, 0]
packed = pack_bits_little_endian(bits)
b64 = base64.b64encode(packed).decode()
# Result: "NQ=="
```

## 5. Security

### 5.1 Authentication

The server MUST implement one of the following authentication methods:

#### 5.1.1 Bearer Token

```
Authorization: Bearer {token}
```

- Server validates token on every request
- Return `401 Unauthorized` if invalid
- Token configured in driver via `auth.token`

#### 5.1.2 API Key

```
{header_name}: {api_key}
```

- Default header name: `X-API-Key`
- Configurable via `auth.header_name`
- Server validates key on every request
- Return `401 Unauthorized` if invalid
- Key configured in driver via `auth.key`

### 5.2 Content Limits

The server SHOULD respect these limits to prevent resource exhaustion:

| Limit | Value | Purpose |
|-------|-------|---------|
| Max frames per content | 1000 | Prevent memory exhaustion |
| Max total bytes | 5 MB | Prevent memory exhaustion |
| Max metadata per item | 10 KB | Prevent metadata abuse |
| Max push request size | 10 MB | Prevent network abuse |

**Note:** These limits are enforced by the driver's validation. Content exceeding limits will be rejected.

### 5.3 Rate Limiting

The server MAY implement rate limiting. Recommended approach:

- Return `429 Too Many Requests` if rate limit exceeded
- Include `Retry-After` header with seconds to wait
- Driver will apply exponential backoff on errors

### 5.4 HTTPS

The server SHOULD use HTTPS in production to protect:
- Authentication credentials
- Content data
- Polling patterns (privacy)

## 6. Behavior Specifications

### 6.1 Polling Behavior

**Driver Side:**
1. Driver polls at intervals specified by `poll_interval_ms`
2. On error, driver applies exponential backoff: 1s, 2s, 4s, 8s... up to 5min
3. Driver sets `last_poll_time` at start of request (even if it fails)
4. Driver includes request timeout (default 10s)

**Server Side:**
1. Server responds with current appropriate content
2. Server sets `poll_interval_ms` based on expected update frequency
3. Server may return `no_change` to reduce bandwidth
4. Server may use cache headers (driver respects them)

### 6.2 Content Updates

**New Content:**
```json
{
  "status": "updated",
  "content": { "content_id": "new-123", ... }
}
```

**No Change:**
```json
{
  "status": "no_change",
  "poll_interval_ms": 30000
}
```

**Clear Display:**
```json
{
  "status": "clear",
  "poll_interval_ms": 10000
}
```

### 6.3 Content Replacement

If the server returns content with the same `content_id` as currently playing content:
- Driver MAY replace the content in-place
- Driver attempts to preserve current frame index
- Useful for live updates (e.g., updating clock without restart)

### 6.4 Priority and Interruptions

**Priority Queue (Driver Side):**
1. Higher priority content interrupts lower priority (if interruptible)
2. Interrupted content pauses and resumes when interruption completes
3. Queue maintains priority order (highest first)
4. Max 50 items in queue, 10 interrupted items

**Server Recommendations:**
- Use priority 0-9 for ambient content (clock, weather)
- Use priority 10+ for notifications
- Use priority 99 only for urgent alerts
- Set `interruptible: false` for critical messages

### 6.5 Frame Timing

**Duration Behavior:**
- `duration_ms > 0`: Frame displays for exactly this duration
- `duration_ms = 0` or `null`: Frame displays indefinitely
- Timing pauses during interruptions
- Timing resumes when content is un-paused

**Loop Behavior:**
- `loop: false`: Play frames once, then complete
- `loop: true, loop_count: null`: Loop indefinitely
- `loop: true, loop_count: N`: Loop N times, then complete

## 7. Error Handling

### 7.1 HTTP Errors

| Status Code | Driver Behavior |
|-------------|-----------------|
| 401/403 | Log auth error, apply backoff |
| 404 | Log endpoint error, apply backoff |
| 429 | Apply backoff (respect Retry-After) |
| 500+ | Log server error, apply backoff |
| Timeout | Apply backoff |
| Network error | Apply backoff |

### 7.2 Validation Errors

If driver receives invalid data:
1. Log detailed validation error
2. Reject the content
3. Apply error backoff
4. Continue displaying previous content (if `error_fallback: keep_last`)

### 7.3 Fallback Behavior

Configured by driver's `error_fallback` setting:

| Mode | Behavior |
|------|----------|
| `keep_last` | Keep displaying last successful content |
| `blank` | Clear display on error |
| `error_message` | Show error state (future) |

## 8. Testing

### 8.1 Server Compliance Checklist

- [ ] GET endpoint returns valid ContentResponse JSON
- [ ] Authentication validates bearer token or API key
- [ ] Returns 401 on invalid authentication
- [ ] All frames in Content have matching dimensions
- [ ] Respects content size limits (1000 frames, 5MB total)
- [ ] Base64 data is valid and correct size
- [ ] status="updated" always includes content
- [ ] status="no_change"/"clear" never includes content
- [ ] poll_interval_ms is at least 1000
- [ ] Priority values are 0-99

### 8.2 Example Valid Responses

**Minimal Response:**
```json
{
  "status": "no_change",
  "poll_interval_ms": 30000
}
```

**Static Image:**
```json
{
  "status": "updated",
  "content": {
    "content_id": "hello-world",
    "frames": [{
      "data_b64": "AQIDBAUGBwgJ",
      "width": 56,
      "height": 14,
      "duration_ms": null
    }]
  },
  "poll_interval_ms": 60000
}
```

**Animation:**
```json
{
  "status": "updated",
  "content": {
    "content_id": "loading-spinner",
    "frames": [
      {
        "data_b64": "AQIDBA==",
        "width": 8,
        "height": 8,
        "duration_ms": 100
      },
      {
        "data_b64": "BQYHCA==",
        "width": 8,
        "height": 8,
        "duration_ms": 100
      }
    ],
    "playback": {
      "loop": true
    }
  },
  "poll_interval_ms": 30000
}
```

**High-Priority Notification:**
```json
{
  "status": "updated",
  "content": {
    "content_id": "doorbell-ring",
    "frames": [{
      "data_b64": "ISEhISE=",
      "width": 56,
      "height": 14,
      "duration_ms": 5000
    }],
    "playback": {
      "priority": 10,
      "interruptible": false
    }
  },
  "poll_interval_ms": 30000
}
```

## 9. OpenAPI Schema

See [openapi.yaml](./openapi.yaml) for machine-readable API specification.

## 10. Versioning

**Current Version:** 2.0

**Version History:**
- **2.0** (2025-11-05): New architecture with content server separation
- **1.0** (Legacy): Monolithic driver with built-in modes

**Breaking Changes in 2.0:**
- Content must be pre-rendered by server
- Packed bit format instead of live rendering
- Removed display modes from driver
- Added priority queue system

## 11. References

- [FlipDot Driver README](./README.md)
- [Driver Implementation](./flipdot/driver/)
- [Data Models](./flipdot/driver/models.py)
- [Example Content Generator](./examples/generate_content.py)

## Appendix A: ABNF Grammar

```abnf
ContentResponse = %s"{" *WSP
                  %s"\"status\"" *WSP ":" *WSP Status *WSP ","
                  [ %s"\"content\"" *WSP ":" *WSP Content *WSP "," ]
                  %s"\"poll_interval_ms\"" *WSP ":" *WSP Integer
                  *WSP %s"}"

Status = %s"\"updated\"" / %s"\"no_change\"" / %s"\"clear\""

Content = %s"{" *WSP
          %s"\"content_id\"" *WSP ":" *WSP String *WSP ","
          %s"\"frames\"" *WSP ":" *WSP "[" Frame *( "," Frame ) "]" *WSP
          [ "," *WSP %s"\"playback\"" *WSP ":" *WSP PlaybackMode ]
          [ "," *WSP %s"\"metadata\"" *WSP ":" *WSP Object ]
          *WSP %s"}"

Frame = %s"{" *WSP
        %s"\"data_b64\"" *WSP ":" *WSP String *WSP ","
        %s"\"width\"" *WSP ":" *WSP Integer *WSP ","
        %s"\"height\"" *WSP ":" *WSP Integer
        [ "," *WSP %s"\"duration_ms\"" *WSP ":" *WSP ( Integer / Null ) ]
        [ "," *WSP %s"\"metadata\"" *WSP ":" *WSP Object ]
        *WSP %s"}"

PlaybackMode = %s"{" *WSP
               [ %s"\"loop\"" *WSP ":" *WSP Boolean ]
               [ "," *WSP %s"\"loop_count\"" *WSP ":" *WSP ( Integer / Null ) ]
               [ "," *WSP %s"\"priority\"" *WSP ":" *WSP Integer ]
               [ "," *WSP %s"\"interruptible\"" *WSP ":" *WSP Boolean ]
               *WSP %s"}"
```

## Appendix B: Conversion Formulas

### Bits to Bytes
```
bytes_needed = ceil(width × height / 8)
```

### Pixel to Bit Index
```
bit_index = (row × width) + col
```

### Bit Index to Byte Position
```
byte_index = bit_index / 8
bit_position = bit_index % 8
```

### Extract Bit Value
```
bit_value = (byte[byte_index] >> bit_position) & 1
```

---

**Document Status:** Ready for Implementation
**Feedback:** Please open issues at the project repository
