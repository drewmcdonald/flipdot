# FlipDot Patterns and Animations

This document describes the patterns and animations feature for the FlipDot display server.

## Overview

The FlipDot server now supports sending fun patterns and animations to the display, as well as transition effects that can be used between frames and commands.

## Features

- **13 Built-in Patterns**: Wave, rain, spiral, checkerboard, random, expand, Game of Life, Matrix, sparkle, pulse, scan, fire, and snake
- **9 Transition Effects**: Wipe, fade, dissolve, slide, checkerboard, blinds, center-out, corners, and spiral
- **Playlist Builder**: Web UI for creating sequences of text, patterns, and transitions
- **Configurable Parameters**: Each pattern and transition supports various options to customize behavior
- **Priority System**: Patterns integrate with the existing priority-based content system
- **TTL Support**: Patterns automatically expire after a configurable time-to-live

## API Endpoints

### Submit a Playlist

```bash
POST /api/flipdot/playlist
```

Submit a playlist containing multiple items (text, patterns, transitions) to display in sequence.

**Request Body:**
```json
{
  "items": [
    {
      "type": "text",
      "priority": 30,
      "ttl_ms": 60000,
      "config": {
        "text": "HELLO",
        "scroll": false,
        "frame_delay_ms": 100
      }
    },
    {
      "type": "pattern",
      "priority": 25,
      "ttl_ms": 30000,
      "config": {
        "pattern_type": "wave",
        "duration_ms": 3000,
        "frame_delay_ms": 100,
        "options": {}
      }
    },
    {
      "type": "text",
      "priority": 30,
      "ttl_ms": 60000,
      "config": {
        "text": "WORLD",
        "scroll": false
      }
    }
  ],
  "keep_clock": true
}
```

**Parameters:**
- `items` (required): Array of playlist items
- `keep_clock` (optional): Whether to keep the clock running (default: true)

Each item must have:
- `type`: "text", "pattern", or "transition"
- `priority`: Priority level 0-99
- `ttl_ms`: Display duration in milliseconds
- `config`: Type-specific configuration (see individual endpoints below)

**Response:**
```json
{
  "success": true,
  "message": "Playlist registered with 3 items",
  "items": [
    {
      "id": "text:HELLO:abc123",
      "type": "text",
      "priority": 30,
      "ttl_ms": 60000
    },
    ...
  ]
}
```

## API Endpoints (Individual Items)

### Submit a Pattern

```bash
POST /api/flipdot/pattern
```

Submit a pattern animation to the display.

**Request Body:**
```json
{
  "type": "wave",
  "duration_ms": 3000,
  "frame_delay_ms": 100,
  "priority": 15,
  "ttl_ms": 30000,
  "options": {
    "vertical": false,
    "speed": 0.3
  }
}
```

**Parameters:**
- `type` (required): Pattern type (see Available Patterns below)
- `duration_ms` (optional): Total duration in milliseconds (100-60000, default: 3000)
- `frame_delay_ms` (optional): Delay between frames in milliseconds (20-1000, default: 100)
- `priority` (optional): Priority level 0-99 (default: 15)
- `ttl_ms` (optional): Time-to-live in milliseconds (1000-3600000, default: 30000)
- `interruptible` (optional): Whether higher priority content can interrupt (default: true)
- `options` (optional): Pattern-specific options (see pattern descriptions below)

**Response:**
```json
{
  "success": true,
  "message": "Pattern registered",
  "source_id": "pattern:wave:abc123",
  "type": "pattern",
  "pattern_type": "wave",
  "priority": 15,
  "ttl_ms": 30000,
  "expires_at": "2025-11-13T12:30:00.000Z"
}
```

### Clear All Patterns

```bash
POST /api/flipdot/pattern/clear
```

Remove all active patterns from the display.

**Response:**
```json
{
  "success": true,
  "message": "All patterns cleared",
  "cleared_count": 3
}
```

### List Available Patterns

```bash
GET /api/flipdot/patterns/list
```

Get a list of all available pattern types and their options.

**Response:**
```json
{
  "patterns": [
    {
      "type": "wave",
      "description": "Horizontal or vertical sine wave",
      "options": {
        "vertical": "boolean",
        "amplitude": "number",
        "frequency": "number",
        "speed": "number"
      }
    },
    ...
  ],
  "active_patterns": 2
}
```

### Create a Transition

```bash
POST /api/flipdot/transition
```

Create a transition animation (from blank to filled screen).

**Request Body:**
```json
{
  "type": "wipe",
  "duration_ms": 1000,
  "frame_delay_ms": 50,
  "direction": "left"
}
```

**Parameters:**
- `type` (required): Transition type (see Available Transitions below)
- `duration_ms` (optional): Total duration in milliseconds (100-10000, default: 1000)
- `frame_delay_ms` (optional): Delay between frames in milliseconds (20-500, default: 50)
- `direction` (optional): Direction for directional transitions ("left", "right", "up", "down")

**Response:**
```json
{
  "success": true,
  "message": "Transition animation created",
  "content": {
    "content_id": "transition:wipe:1699876543210",
    "frames": [...],
    "playback": { "loop": false }
  },
  "frame_count": 20
}
```

### List Available Transitions

```bash
GET /api/flipdot/transitions/list
```

Get a list of all available transition types.

## Available Patterns

### Wave
Horizontal or vertical sine wave that moves across the display.

**Options:**
- `vertical` (boolean): Use vertical wave instead of horizontal (default: false)
- `amplitude` (number): Wave amplitude (default: width/4 or height/4)
- `frequency` (number): Wave frequency (default: 0.5)
- `speed` (number): Animation speed (default: 0.3)

**Example:**
```bash
curl -X POST http://localhost:8000/api/flipdot/pattern \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "wave",
    "duration_ms": 5000,
    "frame_delay_ms": 80,
    "options": {
      "vertical": true,
      "speed": 0.5
    }
  }'
```

### Rain
Falling dots that simulate rain.

**Options:**
- `density` (number): Density of rain drops, 0-1 (default: 0.3)
- `speed` (number): Fall speed (default: 1)

### Spiral
Rotating spiral pattern from the center.

**Options:**
- `speed` (number): Rotation speed (default: 0.5)
- `arms` (number): Number of spiral arms (default: 3)

### Checkerboard
Animated alternating checkerboard pattern.

**Options:**
- `size` (number): Size of checker squares in pixels (default: 2)

### Random
Random noise/static pattern.

**Options:**
- `density` (number): Density of pixels, 0-1 (default: 0.5)

### Expand
Expanding circles or squares from the center.

**Options:**
- `speed` (number): Expansion speed (default: 0.5)
- `shape` (string): "circle" or "square" (default: "circle")

### Game of Life
Conway's Game of Life cellular automaton.

**Options:**
- `density` (number): Initial density, 0-1 (default: 0.3)
- `seed` (number): Random seed for initial state (default: 42)

### Matrix
Matrix-style falling characters effect.

**Options:**
- `density` (number): Density of trails, 0-1 (default: 0.2)
- `speed` (number): Fall speed (default: 1)

### Sparkle
Random twinkling sparkles.

**Options:**
- `density` (number): Density of sparkles, 0-1 (default: 0.15)

### Pulse
Pulsing effect expanding from the center.

**Options:**
- `speed` (number): Pulse speed (default: 0.3)

### Scan
Back-and-forth scanner effect like KITT from Knight Rider.

**Options:**
- `vertical` (boolean): Scan vertically instead of horizontally (default: false)
- `speed` (number): Scan speed (default: 0.5)

### Fire
Fire effect rising from the bottom.

**Options:**
- `intensity` (number): Fire intensity, 0-1 (default: 0.7)

### Snake
Snake or worm moving around the display in a figure-8 pattern.

**Options:**
- `length` (number): Length of snake in pixels (default: 10)
- `speed` (number): Movement speed (default: 0.5)

## Available Transitions

### Wipe
Reveals new frame by wiping from one direction.

**Options:**
- `direction` (string): "left", "right", "up", or "down"

### Fade
Dithered fade effect using Bayer matrix (suitable for binary displays).

### Dissolve
Random pixel-by-pixel reveal.

**Options:**
- `seed` (number): Random seed for deterministic results

### Slide
Slides in the new frame from a direction.

**Options:**
- `direction` (string): "left", "right", "up", or "down"

### Checkerboard
Reveals in a checkerboard pattern.

**Options:**
- `size` (number): Size of checker squares in pixels

### Blinds
Venetian blinds effect.

**Options:**
- `vertical` (boolean): Vertical blinds instead of horizontal
- `blindSize` (number): Width/height of each blind

### Center Out
Expands from the center point outward.

### Corners
Reveals from all four corners simultaneously.

### Spiral
Spiral reveal from the center.

## Usage Examples

### Display a wave pattern for 10 seconds

```bash
curl -X POST http://localhost:8000/api/flipdot/pattern \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "wave",
    "duration_ms": 10000,
    "frame_delay_ms": 100,
    "priority": 20,
    "ttl_ms": 15000
  }'
```

### Display Matrix rain effect

```bash
curl -X POST http://localhost:8000/api/flipdot/pattern \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "matrix",
    "duration_ms": 5000,
    "frame_delay_ms": 80,
    "options": {
      "density": 0.3,
      "speed": 1.5
    }
  }'
```

### Create a wipe transition

```bash
curl -X POST http://localhost:8000/api/flipdot/transition \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "wipe",
    "duration_ms": 800,
    "frame_delay_ms": 40,
    "direction": "left"
  }'
```

## Using Patterns as Transitions

Patterns can effectively serve as transitions between other content by setting their priority and TTL appropriately:

1. **Set Priority**: Use a priority between your main content items to insert the pattern at the right time
2. **Set TTL**: Use a short TTL (e.g., 3-5 seconds) so the pattern plays once and expires
3. **Timing**: The pattern will play for its duration, then expire, allowing the next content to display

**Example: Transition between text messages**

```bash
# Submit text message 1
curl -X POST http://localhost:8000/api/flipdot/text \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "HELLO", "priority": 30, "ttl_ms": 10000}'

# Wait 5 seconds, then submit a transition pattern
sleep 5
curl -X POST http://localhost:8000/api/flipdot/pattern \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "spiral",
    "duration_ms": 2000,
    "frame_delay_ms": 50,
    "priority": 25,
    "ttl_ms": 3000
  }'

# Submit text message 2
curl -X POST http://localhost:8000/api/flipdot/text \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"text": "WORLD", "priority": 30, "ttl_ms": 10000}'
```

This will display "HELLO", then a spiral transition, then "WORLD".

## Priority System Integration

Patterns integrate with the existing priority-based content system:

- **Clock**: Priority 10 (default, always present)
- **Patterns**: Priority 15 (default, but configurable)
- **Custom Text**: Priority 20 (default)

Higher priority content will display first in the playlist. Set pattern priorities strategically to control when they display relative to other content.

## Implementation Details

### Architecture

- **Pattern Generators**: Pure functions that generate 2D boolean arrays (28×14 pixels)
- **Transition Generators**: Pure functions that interpolate between two frames
- **Frame Rendering**: Converts 2D arrays to packed bit format (little-endian base64)
- **Content Sources**: Patterns integrate as standard content sources with TTL and priority
- **Looping**: Patterns loop by default, transitions play once

### File Structure

```
val-server/backend/patterns/
├── types.ts         # TypeScript interfaces and types
├── generators.ts    # Pattern generator functions
├── transitions.ts   # Transition generator functions
├── render.ts        # Frame rendering and conversion
└── content.ts       # Content source integration
```

### Performance Considerations

- Patterns are rendered once and cached with TTL
- Frame generation is deterministic and efficient
- Adjust `frame_delay_ms` to balance smoothness vs. bandwidth
- Lower frame rates (higher delay) reduce network traffic

## Web UI - Playlist Builder

The FlipDot display now includes a web-based **Playlist Builder** that makes it easy to create and manage sequences of content without writing code or using curl commands.

### Features

- **Visual Playlist Editor**: Add, edit, remove, and reorder items with a simple UI
- **Three Content Types**:
  - Text messages (with scroll options)
  - Pattern animations (13 types)
  - Transitions (9 types)
- **Drag-Free Reordering**: Use up/down arrows to reorder playlist items
- **Priority Control**: Set priority for each item
- **Duration Control**: Configure how long each item displays
- **Pattern/Transition Selector**: Browse all available patterns and transitions with descriptions
- **Expandable Details**: Click to view/hide full configuration of each item
- **Live Preview**: See your playlist items displayed on the virtual flipdot

### How to Use

1. **Access the Web UI**: Navigate to your FlipDot server URL in a web browser
2. **Add Items**: Click "+ Add Item" to open the item configuration modal
3. **Choose Type**: Select Text, Pattern, or Transition
4. **Configure**: Set all parameters (text, pattern type, priority, duration, etc.)
5. **Add to List**: Click "Add" to add the item to your playlist
6. **Reorder**: Use ↑ and ↓ buttons to reorder items
7. **Edit/Delete**: Use ✎ to edit or ✕ to delete items
8. **Send**: Click "Send Playlist" to submit to the display

### Playlist Item Configuration

**Text Items:**
- Text content (up to 100 characters)
- Scroll option (force scrolling even for short text)
- Frame delay (animation speed)
- Priority and display time

**Pattern Items:**
- Pattern type (wave, rain, spiral, etc.)
- Duration (total animation time)
- Frame delay (animation smoothness)
- Pattern-specific options
- Priority and display time

**Transition Items:**
- Transition type (wipe, fade, dissolve, etc.)
- Duration (transition time)
- Direction (for directional transitions)
- Priority and display time

### Tips for Creating Playlists

1. **Use Priority Strategically**: Higher numbers display first
   - Text: 30 (main content)
   - Patterns: 25 (transitions)
   - Clock: 10 (always visible when nothing else is active)

2. **Balance Display Times**:
   - Short text: 5-10 seconds
   - Scrolling text: 10-30 seconds
   - Patterns: 3-10 seconds
   - Transitions: 1-2 seconds

3. **Create Visual Flow**:
   - Add patterns between text messages for visual interest
   - Use transitions to smooth changes between content
   - Vary pattern types to keep the display engaging

4. **Example Sequence**:
   ```
   1. Text: "HELLO" (30s, priority 30)
   2. Pattern: Wave (3s, priority 25)
   3. Text: "WORLD" (30s, priority 30)
   4. Pattern: Matrix (5s, priority 25)
   5. Text: "GOODBYE" (30s, priority 30)
   ```

### Playlist Behavior

- Items are registered with the server when you click "Send Playlist"
- The server sorts items by priority (highest first)
- Items with the same priority play in order
- Each item displays for its TTL duration, then expires
- The clock (priority 10) displays when no higher priority content is active
- You can send a new playlist at any time to replace the current one

## Future Enhancements

Possible future improvements:

- Save/load playlist templates
- Pattern presets/favorites
- Drag-and-drop reordering
- Real-time pattern preview
- Automatic transitions between content items
- Pattern chaining (combine multiple patterns)
- User-uploaded custom patterns
- Pattern scheduling (time-based patterns)
- Loop count for patterns
- Playlist repeat mode

## Troubleshooting

### Pattern not displaying

1. Check priority - higher priority content may be displaying first
2. Check TTL - pattern may have expired
3. Verify authentication - all endpoints require Bearer token or API key
4. Check driver logs for errors

### Animation is jerky

1. Reduce `frame_delay_ms` for smoother animation
2. Check network latency between server and driver
3. Verify driver is polling at recommended interval

### Pattern expires too quickly

1. Increase `ttl_ms` in the request
2. Pattern will auto-expire after TTL, re-submit to keep displaying

## Examples Gallery

Here are some recommended configurations for different effects:

**Smooth Wave:**
```json
{"type": "wave", "duration_ms": 5000, "frame_delay_ms": 60, "options": {"speed": 0.2, "frequency": 0.3}}
```

**Fast Rain:**
```json
{"type": "rain", "duration_ms": 4000, "frame_delay_ms": 80, "options": {"density": 0.4, "speed": 1.5}}
```

**Slow Spiral:**
```json
{"type": "spiral", "duration_ms": 8000, "frame_delay_ms": 100, "options": {"speed": 0.3, "arms": 4}}
```

**Intense Fire:**
```json
{"type": "fire", "duration_ms": 5000, "frame_delay_ms": 70, "options": {"intensity": 0.8}}
```

**Scanner Effect:**
```json
{"type": "scan", "duration_ms": 3000, "frame_delay_ms": 50, "options": {"speed": 1.0}}
```
