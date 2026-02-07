# FlipDot v2.0

Lightweight driver + content server for flipdot displays. The driver (Python) runs on a Raspberry Pi, subscribes to real-time updates from a Convex backend (TypeScript), and sends frames over serial to the hardware.

## Monorepo Structure

- `flipdot/` - Python driver package (runs on Pi, talks to hardware)
- `server/` - Convex backend + React virtual display (content generation & serving)

## Commands

```bash
# Python driver
poetry install --with dev
poetry run pytest flipdot/tests/test_driver.py     # tests
poetry run basedpyright flipdot                     # type checking (CI)
poetry run ruff check flipdot                       # linting (CI)

# Server
cd server && npm install
npm run dev                                         # vite dev server
npm run test:run                                    # vitest (single run)
npm run lint                                        # eslint
```

## Architecture

```
[Convex Backend]  ──real-time subscription──>  [Python Driver]  ──serial──>  [FlipDot Hardware]
       │                                              │
   cron: clock                                   ContentQueue
   rendering pipeline                            Panel → FlippyModule
   displays table                                SerialConnection
       │
[React Virtual Display]  (dev/testing UI, subscribes to same query)
```

- Single Convex table `displays` stores content per named display (e.g. "main")
- Driver subscribes to `displays:getCurrentDisplay` query via Convex Python SDK
- Content is a playlist of `Content` items, each with `Frame`s (base64-encoded bit arrays)
- Display dimensions: **28x14 pixels** (two 28x7 modules stacked vertically)

## Key Gotchas

- **Bit packing is little-endian** (LSB first) -- both Python and TypeScript sides must match
- Frame `duration_ms: null` or `0` means "display indefinitely" (never advances)
- Module serial commands pack bits **column-wise**, which differs from row-major frame data
- `module_layout` is a 2D array of addresses: `[[1], [2]]` = 2 modules stacked, `[[1, 2]]` = side-by-side
- Convex MCP server is configured in `.mcp.json` for interactive development
