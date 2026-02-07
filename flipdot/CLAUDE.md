# FlipDot Python Driver

Minimal driver that subscribes to Convex for content and sends frames to flipdot hardware over serial.

## Commands

```bash
# Run driver
python -m flipdot.main --config flipdot/config.example.json

# Tests
pytest flipdot/tests/test_driver.py
pytest flipdot/tests/test_driver.py::TestClassName           # single class
pytest flipdot/tests/test_driver.py::TestClassName::test_fn  # single test

# Linting & type checking (these run in CI)
poetry run basedpyright flipdot
poetry run ruff check flipdot
```

## Key Files

```
main.py           # FlipDotDriver entry point, argparse --config, main loop, graceful shutdown
models.py         # Pydantic v2 models: Frame, Content, ContentResponse, PlaybackMode, DriverConfig
config.py         # Frozen dataclass constants: ContentLimits, QueueLimits, SerialConfig, LoopTiming
hardware.py       # Panel, FlippyModule, SerialConnection, pack_bits_little_endian()
queue.py          # ContentQueue (FIFO playlist), ContentState (per-content playback tracking)
convex_client.py  # ConvexContentClient -- background thread, subscribes to displays:getCurrentDisplay
font/             # DotFont class, get_font(), render_text(); pre-rendered JSON fonts in font/rendered/
tests/            # pytest suite with helpers: create_test_frame(), create_test_content()
```

## Config Format

```json
{
  "convex_url": "https://your-deployment.convex.cloud",
  "display_name": "main",
  "serial_device": "/dev/ttyUSB0",
  "serial_baudrate": 57600,
  "module_layout": [[1], [2]],
  "module_width": 28,
  "module_height": 7,
  "dev_mode": false,
  "log_level": "INFO"
}
```

Use `dev_mode: true` with no `serial_device` for development (logs hex to console).

## Architecture

```
ConvexContentClient (daemon thread, blocks on wait_for_update)
    └──> ContentQueue.set_playlist(playlist)
              └──> ContentState per content item (tracks frame index, timing, loops)

Main loop (50 iterations/sec, 20ms sleep):
    _poll_for_content(timeout)  →  blocks waiting for Convex subscription updates
    _render_frame()             →  queue.update() → Panel.set_content_from_frame() → serial write
```

## Patterns & Gotchas

- **Bit packing**: frame data is little-endian (LSB first). Module serial commands pack **column-wise** (differs from row-major frames).
- **Frame duration**: `None` or `0` = display indefinitely. Content with indefinite last frame never auto-advances.
- **Playlist preservation**: if new playlist shares `content_id` at position 0, playback state is preserved (smooth updates).
- **Serial reconnection**: exponential backoff (1s -> 60s max), gives up after 10 consecutive failures.
- **Dimension validation**: frames must match display dimensions or the entire playlist is rejected.
- **No priorities/interrupts**: server sends complete playlist, driver plays in FIFO order.
- **basedpyright config**: `graveyard` and `flipdot/tests` are excluded from type checking (see `pyproject.toml`).
- **Font pre-rendering**: to add fonts, put `.ttf` in `font/fonts/`, add config to `prerender_fonts.py`, run `python flipdot/font/prerender_fonts.py`.
