# Server (Convex Backend + React Frontend)

For detailed Convex API reference (validators, function registration, queries, mutations, actions, crons, etc.), see [CONVEX_REFERENCE.md](./CONVEX_REFERENCE.md).

## Commands

```bash
npm install
npm run dev          # vite dev server
npm run build        # tsc -b && vite build
npm run test:run     # vitest single run
npm run test         # vitest watch mode
npm run lint         # eslint
```

## Schema

Three tables (defined in `convex/schema.ts`):

- `displays` -- final output consumed by driver/frontend
  - `name` (string, indexed `by_name`), `content`, `updatedAt`
- `content_sources` -- each content generator writes here
  - `source_id` (string, indexed `by_source_id`), `content` (same shape as displays), `updatedAt`
- `display_config` -- controls which sources show on each display
  - `display_name` (string, indexed `by_display_name`), `rotation[]` (`source_id`, `duration_s`), `overrides[]` (`source_id`, `priority`)

Each frame: `data_b64` (base64 packed bits), `width`, `height`, `duration_ms`, optional `metadata`.

## Content Pipeline

Content generators write to `content_sources` (not directly to `displays`). A compositor cron (every 10s) reads `display_config` + `content_sources`, picks the active source (overrides > rotation), and writes to `displays`. The driver/frontend subscribes to `displays` unchanged.

```
[clock cron] → content_sources["clock"] ─┐
[future sources] → content_sources[...] ─┤
                                         ├→ [compositor cron] → displays["main"]
[display_config for "main"] ─────────────┘
```

To add a new content source: create a generator in `convex/content/`, call `content_sources.updateSource`, add a cron, and add the source_id to `display_config` rotation.

## Key Files

```
convex/
  schema.ts              # displays, content_sources, display_config tables
  displays.ts            # getCurrentDisplay (public query), updateDisplay/clearDisplay (internal mutations)
  content_sources.ts     # updateSource/getSource/clearSource (internal), listSources (public query)
  display_config.ts      # getConfig (internal query), updateConfig (public mutation), seedDefaultConfig
  compositor.ts          # compose (internal mutation) -- picks active source, writes to displays
  types.ts               # Frame, Content, PlaybackMode, ContentResponse interfaces
  crons.ts               # clock (1 min), compositor (10s)
  content/clock.ts       # clock content generator (writes to content_sources["clock"])
  rendering/
    frame.ts             # createFrame(), DISPLAY_WIDTH=28, DISPLAY_HEIGHT=14, DISPLAY_BITS=392
    bits.ts              # packBitsLittleEndian(), bitsToBase64(), base64ToBits()
    compose.ts           # composeBits(a, b, mode) -- OR/XOR/AND for frame overlays
    fontLoader.ts        # getFont(), renderText(), renderScrollingText(), measureText()
    fonts/               # axion_6x7 (default), cg_pixel_4x5 -- embedded font data
src/
  App.tsx                # mounts VirtualDisplay
  components/
    VirtualDisplay.tsx   # canvas-based dot rendering, subscribes to getCurrentDisplay
  lib/
    frameRenderer.ts     # client-side base64ToBits() for display rendering
```

## Patterns

- **No HTTP endpoints** -- all interaction via Convex reactive queries (`useQuery`)
- **One content per display** -- `displays` table stores one content package per named display
- **Fonts are embedded** -- pre-rendered glyph data hardcoded in `convex/fonts/`, not loaded dynamically
- **Display baseline** is pixel 11 from top (3 pixels below for descenders on 14px height)
- **Rendering pipeline**: text -> font glyphs -> 392-bit array -> base64 -> stored in Convex -> subscribed by driver/frontend
- Content generators are **internal actions** that write to `content_sources` (not `displays` directly)
- **Compositor** is stateless -- uses `Date.now() % cycleDuration` for rotation, no pointer state
- **Override sources** take priority when present in `content_sources`; clearing the source deactivates the override
- Tests use `convex-test` and vitest; test files live alongside source (`*.test.ts`)
