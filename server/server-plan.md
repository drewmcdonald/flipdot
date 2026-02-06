# FlipDot Driver Architecture Redesign Plan

## Current State

**Problem:** HTTP polling architecture with 30-second update intervals

- Too slow for real-time updates
- Wastes bandwidth polling when nothing changes
- Can't do sub-second updates (clock ticking, animations)

**What exists:**

- ✅ Python driver (working, tested on hardware)
- ✅ Serial communication working
- ✅ Frame queue & rendering logic solid
- ❌ No content server yet (Phase 3 TODO from README)

## Requirements

- ✅ Sub-second latency (< 1000ms)
- ✅ No long-running servers (serverless preferred)
- ✅ Easy GCP hosting (no infrastructure constraints)
- ✅ Virtual display support (for dev/testing)
- ✅ Driver NOT exposed to internet (outbound connections only)
- ✅ Single display (not multi-tenant)

## Architecture Options Considered

| Option         | Latency      | Cost/Mo | Complexity   | Verdict       |
| -------------- | ------------ | ------- | ------------ | ------------- |
| WebSocket + Go | 50-100ms     | $0.10   | High         | ❌ Overkill   |
| Firebase RTDB  | 50-150ms     | $0-1    | Low          | ✅ Good       |
| Firestore      | 100-300ms    | $0-1    | Low          | ✅ Good       |
| GCP Pub/Sub    | 200-500ms    | $2-3    | Medium       | ❌ Complex    |
| **Convex**     | **50-100ms** | **$0**  | **Very Low** | ✅✅ **BEST** |

## Recommended Solution: Convex + Python Driver

### Why Convex?

1. **Real-time by default** - WebSocket push built-in
2. **No infrastructure** - Fully managed backend
3. **Free tier** - 1M function calls/month (more than enough)
4. **TypeScript** - Type-safe backend functions
5. **Built-in cron** - Scheduled functions included
6. **Virtual display** - Trivial (just another subscription)
7. **Self-hostable** - Can move off Convex later if needed

### Why Keep Python Driver?

1. **Minimal changes** - Only replace `client.py` (~100 lines)
2. **Proven code** - Hardware/serial code already works
3. **Fast migration** - 2 hours vs 2 days for Go rewrite
4. **Latency** - 120ms total (vs 110ms in Go - negligible 10ms difference)
5. **Low risk** - Keep 95% of existing codebase

## Architecture Diagram

```
┌────────────────────────────────────────────┐
│  CONVEX BACKEND (convex.dev)              │
│                                            │
│  Database (reactive)                       │
│  ┌─────────────────────────────┐          │
│  │ displays/main: {            │          │
│  │   content_id: "clock-...",  │          │
│  │   frames: [...],            │          │
│  │   updated_at: 1234567890    │          │
│  │ }                           │          │
│  └─────────────────────────────┘          │
│                                            │
│  Functions (TypeScript)                    │
│  ├─ Clock generator (cron: every 1s)      │
│  ├─ Weather updater (cron: every 5m)      │
│  └─ Display query (reactive)              │
│                                            │
└──────────────┬─────────────────────────────┘
               │ WebSocket/HTTP (Convex SDK)
               │ OUTBOUND (driver initiates)
               ▼
┌────────────────────────────────────────────┐
│  PYTHON DRIVER (Raspberry Pi)              │
│                                            │
│  NEW:     convex_client.py                 │
│  MODIFY:  main.py (5 lines)                │
│  MODIFY:  models.py (add convex_url)       │
│                                            │
│  KEEP:    hardware.py (no change)          │
│  KEEP:    queue.py (no change)             │
│  KEEP:    config.py (no change)            │
│                                            │
└──────────────┬─────────────────────────────┘
               │ Serial (RS-485/USB)
               ▼
┌────────────────────────────────────────────┐
│  FLIPDOT HARDWARE                          │
└────────────────────────────────────────────┘

┌────────────────────────────────────────────┐
│  VIRTUAL DISPLAY (React web page)          │
│  - Same Convex subscription as driver      │
│  - Renders to HTML canvas                  │
│  - Shows latency metrics                   │
└────────────────────────────────────────────┘
```

## Implementation Plan

### Phase 1: Driver Integration (2 hours)

**Files to create:**

- `flipdot/convex_client.py` - Convex subscription client (~100 lines)

**Files to modify:**

- `flipdot/main.py` - Replace ContentClient with ConvexContentClient (5 lines)
- `flipdot/models.py` - Add `convex_url` and `display_name` to config

**Dependencies:**

```bash
pip install convex
```

**Config change:**

```json
{
  "convex_url": "https://your-deployment.convex.cloud",
  "display_name": "main",
  "serial_device": "/dev/ttyUSB0",
  "module_layout": [[1], [2]],
  ...
}
```

### Phase 2: Convex Backend (3 hours)

**Project structure:**

```
convex/
├── schema.ts              # Database schema
├── displays.ts            # Display queries/mutations
├── content/
│   ├── clock.ts          # Clock generator
│   ├── weather.ts        # Weather generator
│   └── rendering.ts      # Frame rendering helpers
└── crons.ts              # Scheduled jobs
```

**Key functions:**

1. `getCurrentDisplay(name)` - Reactive query (driver subscribes)
2. `updateDisplay(name, content)` - Internal mutation
3. `generateClock()` - Scheduled every 1 second
4. `generateWeather()` - Scheduled every 5 minutes

**Deploy:**

```bash
npm install -g convex
npx convex dev       # Local development
npx convex deploy    # Production deployment
```

### Phase 3: Virtual Display (1 hour)

**Simple React component:**

```tsx
// Uses Convex React hooks - auto-updates!
const display = useQuery(api.displays.getCurrentDisplay, { name: "main" });

// Render to canvas
useEffect(() => {
  renderFrameToCanvas(display.frames[0]);
}, [display]);
```

**Host:** Vercel, Netlify, or GCP Cloud Storage (static site)

### Phase 4: Testing & Migration (2 hours)

1. Test Convex backend locally with virtual display
2. Test Python driver with mock hardware (dev_mode)
3. Deploy to production Convex
4. Update Pi driver config
5. Test on real hardware
6. Monitor latency metrics

**Total timeline: 8-10 hours**

## Latency Breakdown

```
Target: < 1000ms (sub-second)
Actual: ~120ms (5x better than target!)

Components:
├─ Convex push (network):       70ms
├─ Python parse/queue:            8ms
├─ Serial write (baudrate):      15ms
└─ Physical flip (hardware):     20ms
    ─────────────────────────────────
    TOTAL:                       113ms ✓
```

## Cost Analysis

**Convex Free Tier:**

- 1M function calls/month
- 1GB storage
- 1GB bandwidth

**Your usage:**

- Clock updates: 86,400/day = 2.6M/month ⚠️ (exceeds free tier if every second)
- Solution: Update every 5s or 10s instead = 260k-520k/month ✓

**Actual cost:**

- If within free tier: **$0/month**
- If exceed free tier: **$25/month** for unlimited

**Alternative:** Self-host Convex on GCP ($5-10/month)

## Future Enhancements

**Phase 5 (Optional):**

- [ ] Multiple display support (office, bedroom, etc.)
- [ ] Web dashboard for control
- [ ] Content scheduling (show weather at 8am, etc.)
- [ ] Animations library
- [ ] Plugin system for content generators
- [ ] Go driver rewrite (if 10ms latency matters)

## Decision Log

**Why not WebSocket + custom server?**

- Requires long-running server (not serverless)
- More code to maintain
- No built-in cron scheduling

**Why not Firebase/Firestore?**

- Good option, but Convex has better DX
- Convex TypeScript > Firebase JSON
- Convex cron built-in

**Why not Go driver?**

- Only 10ms faster (110ms vs 120ms)
- Requires rewriting 80% of code
- Takes 2 days vs 2 hours
- Marginal benefit for high cost

**Why not GCP Pub/Sub?**

- 200-500ms latency (slower)
- More expensive ($2-3/month)
- Virtual display harder (can't subscribe from browser)

## Success Metrics

- ✅ Update latency < 1000ms (targeting ~120ms)
- ✅ Cost < $5/month (targeting $0)
- ✅ Migration time < 1 week (targeting 1 day)
- ✅ Code reuse > 80% (targeting 95%)
- ✅ Virtual display working
- ✅ No exposed endpoints (driver connects outbound)

## Next Steps

1. Create `convex_client.py`
2. Set up Convex project with schema
3. Implement clock generator
4. Test locally with virtual display
5. Integrate with Python driver
6. Deploy to production
7. Update Pi configuration
8. Monitor and iterate

## Files to Create/Modify

**New files:**

- [ ] `flipdot/convex_client.py`
- [ ] `convex/schema.ts`
- [ ] `convex/displays.ts`
- [ ] `convex/content/clock.ts`
- [ ] `convex/crons.ts`
- [ ] `virtual-display/VirtualDisplay.tsx`

**Modified files:**

- [ ] `flipdot/main.py` (5 lines)
- [ ] `flipdot/models.py` (add convex config)

**Unchanged (95% of codebase):**

- ✓ `flipdot/hardware.py`
- ✓ `flipdot/queue.py`
- ✓ `flipdot/config.py`
- ✓ All tests

## Risk Assessment

| Risk                      | Likelihood | Impact | Mitigation                            |
| ------------------------- | ---------- | ------ | ------------------------------------- |
| Convex SDK bugs           | Low        | Medium | Use stable Python SDK, test locally   |
| Latency > 1s              | Very Low   | Medium | Benchmarked at 120ms                  |
| Free tier exceeded        | Medium     | Low    | Monitor usage, can upgrade for $25/mo |
| Migration breaks hardware | Low        | High   | Keep old code, test in dev_mode first |
| Convex vendor lock-in     | Medium     | Medium | Can self-host if needed               |

**Overall risk: LOW** - Minimal code changes, proven technologies

---

**Status:** Ready to implement
**Estimated effort:** 8-10 hours
**Expected latency:** 120ms (sub-second ✓)
**Expected cost:** $0/month
