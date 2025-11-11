# FlipDot Content Server API Specification v3.0

**Status:** Current
**Last Updated:** 2025-01-09
**Protocol Version:** 3.0

## Breaking Changes from v2.0

### Playlist-Based Architecture

**v2.0 (Old):** Server returned single highest-priority content. Driver managed priority queue and interruptions.

**v3.0 (New):** Server returns complete ordered playlist. Driver plays sequentially (simple FIFO).

### Key Differences

| Feature | v2.0 | v3.0 |
|---------|------|------|
| Response field | `content: Content` | `playlist: Content[]` |
| Status values | `"updated" \| "no_change" \| "clear"` | `"updated" \| "clear"` |
| Priority handling | Driver-side queue | Server-side ordering |
| Interruptions | Driver pauses/resumes | None (server controls order) |
| PlaybackMode fields | `loop`, `loop_count`, `priority`, `interruptible` | `loop`, `loop_count` only |

## API Endpoint

### GET /api/flipdot/content

**Purpose:** Driver polls for complete playlist

#### Request

**Method:** `GET`

**Headers:**
```
User-Agent: FlipDot-Driver/3.0
Content-Type: application/json
Authorization: Bearer {token}
```

#### Response

**Status Codes:**
- `200 OK` - Playlist returned
- `401 Unauthorized` - Auth failed
- `500 Internal Server Error` - Server error

**Body:**

```typescript
interface ContentResponse {
  status: "updated" | "clear";
  playlist: Content[];  // Ordered list, first plays immediately
  poll_interval_ms: number;  // >= 1000
}
```

**Example (Multiple items):**
```json
{
  "status": "updated",
  "playlist": [
    {
      "content_id": "urgent-alert",
      "frames": [{ "data_b64": "...", "width": 28, "height": 14, "duration_ms": 5000 }],
      "playback": { "loop": false }
    },
    {
      "content_id": "clock-12:00",
      "frames": [{ "data_b64": "...", "width": 28, "height": 14, "duration_ms": null }],
      "playback": { "loop": false }
    }
  ],
  "poll_interval_ms": 30000
}
```

**Example (Clear):**
```json
{
  "status": "clear",
  "playlist": [],
  "poll_interval_ms": 30000
}
```

## Data Models

### ContentResponse

```typescript
interface ContentResponse {
  status: "updated" | "clear";
  playlist: Content[];
  poll_interval_ms: number;
}
```

**Rules:**
- If `status` is `"updated"`, `playlist` SHOULD be non-empty (can be empty if server has no content)
- If `status` is `"clear"`, `playlist` MUST be empty
- `poll_interval_ms` MUST be >= 1000

### Content

```typescript
interface Content {
  content_id: string;
  frames: Frame[];
  playback?: PlaybackMode;
  metadata?: object;
}
```

**Rules:**
- `frames` MUST contain 1-1000 frames
- All frames MUST have identical dimensions
- Total size MUST NOT exceed 5MB

### Frame

```typescript
interface Frame {
  data_b64: string;
  width: number;
  height: number;
  duration_ms?: number | null;
  metadata?: object;
}
```

**Rules:**
- `data_b64` MUST be valid base64 (little-endian packed bits)
- `width` and `height` MUST match display (validated by driver)
- `duration_ms` of `null` or `0` means display indefinitely

### PlaybackMode

```typescript
interface PlaybackMode {
  loop?: boolean;
  loop_count?: number | null;
}
```

**Rules:**
- `loop_count` can only be set if `loop` is `true`
- ~~`priority` and `interruptible` removed~~ (server manages ordering)

## Behavior

### Server Responsibilities

1. **Playlist Ordering:** Server decides content order based on priorities, urgency, schedules, etc.
2. **Stateless Operation:** Each request computes fresh playlist (or uses cache)
3. **Content Management:** Add/remove content from sources
4. **Rendering:** Convert text/graphics to packed bit frames

### Driver Responsibilities

1. **Polling:** Poll at `poll_interval_ms` intervals
2. **FIFO Playback:** Play playlist items in order
3. **Frame Timing:** Advance frames based on `duration_ms`
4. **Serial Communication:** Send frames to hardware

### Playlist Behavior

**On `status: "updated"`:**
1. Driver replaces entire queue with new playlist
2. If `playlist[0].content_id` matches current content ID, preserve frame timing
3. Otherwise, start fresh with `playlist[0]`

**On `status: "clear"`:**
1. Driver clears all content
2. Display shows blank

### Server Implementation Example

```typescript
// Server maintains content sources with priorities
const sources = [
  { id: "clock", priority: 10, generate: () => generateClock() },
  { id: "alert", priority: 90, generate: () => generateAlert() },
];

// Generate playlist
async function generatePlaylist(): Promise<Content[]> {
  // Get all active content
  const content = await Promise.all(
    sources.map(s => s.generate())
  );

  // Sort by priority (highest first)
  content.sort((a, b) => b.priority - a.priority);

  // Return ordered list
  return content;
}
```

## Migration from v2.0

### Server Changes

1. Change `content: Content` to `playlist: Content[]`
2. Remove `status: "no_change"` logic
3. Return all active content, not just highest priority
4. Remove `priority` and `interruptible` from Content objects
5. Keep priority in server-side source management for ordering

### Driver Changes

1. Accept `playlist: Content[]` instead of `content: Content`
2. Remove priority queue logic
3. Remove interruption/resume logic
4. Simplify to FIFO queue
5. Preserve frame timing when `playlist[0]` has same ID

## Frame Data Format

Same as v2.0: Little-endian packed bits, row-major order, base64 encoded.

See v2.0 spec Section 4 for details.

## Security

Same as v2.0: Bearer token or API key authentication required.

## Testing

**Valid minimal response:**
```json
{
  "status": "updated",
  "playlist": [
    {
      "content_id": "test",
      "frames": [{ "data_b64": "AAAA", "width": 28, "height": 14 }]
    }
  ],
  "poll_interval_ms": 30000
}
```

**Test server compliance:**
- [ ] Returns `playlist` array (not `content` object)
- [ ] Status is either `"updated"` or `"clear"` (not `"no_change"`)
- [ ] PlaybackMode does not include `priority` or `interruptible`
- [ ] Multiple content items ordered correctly
- [ ] All frames have matching dimensions

---

**Document Status:** Ready for Implementation
