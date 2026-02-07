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

Single table `displays` (defined in `convex/schema.ts`):
- `name` (string, indexed by `by_name`) -- display identifier
- `content` -- content package: `content_id`, `frames[]`, `playback`, `metadata`
- `updatedAt` (number) -- last update timestamp

Each frame: `data_b64` (base64 packed bits), `width`, `height`, `duration_ms`, optional `metadata`.

## Key Files

```
convex/
  schema.ts              # displays table definition
  displays.ts            # getCurrentDisplay (public query), updateDisplay/clearDisplay (internal mutations)
  types.ts               # Frame, Content, PlaybackMode, ContentResponse interfaces
  crons.ts               # clock update every 1 minute
  content/clock.ts       # clock content generator (internal action, Eastern timezone)
  rendering/
    frame.ts             # createFrame(), DISPLAY_WIDTH=28, DISPLAY_HEIGHT=14, DISPLAY_BITS=392
    bits.ts              # packBitsLittleEndian(), bitsToBase64(), base64ToBits()
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
- Content generators are **internal actions** that call internal mutations to update displays
- Tests use `convex-test` and vitest; test files live alongside source (`*.test.ts`)
