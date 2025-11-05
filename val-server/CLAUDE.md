# FlipDot Content Server - AI Agent Guidelines

You are working on the **FlipDot Content Server**, a Val Town project that serves pre-rendered content to a FlipDot display driver running on a Raspberry Pi.

## Project Overview

This server implements the **FlipDot Content Server API v2.0** specified in [CONTENT_SERVER_SPEC.md](./CONTENT_SERVER_SPEC.md). The driver polls this server for content, and the server is responsible for:

- Rendering text, animations, and graphics into frames
- Encoding frames in packed bit format (base64)
- Managing content display logic (what to show when)
- Handling authentication
- Responding to polling requests

**Key Architecture Principle:** The server does ALL rendering. The driver is minimal and only handles display queue management, timing, and hardware communication.

### Display Specifications

- **Dimensions:** 56×14 pixels (two 28×7 flipdot modules)
- **Module Layout:** `[[1], [2]]` (stacked vertically)
- **Pixel Format:** Binary (on/off), packed little-endian, base64-encoded
- **Update Method:** Polling (driver polls every 30s by default)

## Required Reading

**BEFORE implementing any features, read:**

1. **[CONTENT_SERVER_SPEC.md](./CONTENT_SERVER_SPEC.md)** - Complete API specification
   - Section 2: API Endpoints (polling endpoint is required)
   - Section 3: Data Models (ContentResponse, Content, Frame, PlaybackMode)
   - Section 4: Frame Data Format (packed bit encoding)
   - Section 5: Security (authentication requirements)

2. **Key Spec Sections:**
   - **Section 3.1** - ContentResponse structure (`status`, `content`, `poll_interval_ms`)
   - **Section 3.3** - Frame structure and `data_b64` encoding
   - **Section 4** - Packed bit format (little-endian, row-major)
   - **Example responses** - Section 8.2

## Project-Specific Guidelines

### 1. API Implementation

**Required Endpoint:**

```ts
// GET /api/flipdot/content
// Returns: ContentResponse JSON
export default async function (req: Request) {
  // 1. Validate authentication
  // 2. Determine what content to show
  // 3. Render content to frames
  // 4. Return ContentResponse
}
```

**Authentication:**

- Check for `X-API-Key` header (or `Authorization: Bearer` token)
- API key stored in environment variable: `Deno.env.get('FLIPDOT_API_KEY')`
- Return `401 Unauthorized` if missing/invalid
- Return `403 Forbidden` if insufficient permissions

**Response Structure:**

```ts
interface ContentResponse {
  status: "updated" | "no_change" | "clear";
  content?: Content; // Required when status="updated"
  poll_interval_ms: number; // >= 1000
}
```

### 2. Frame Rendering

**Critical:** Frames must use packed bit format (see spec Section 4).

**Reference Implementation Pattern:**

```ts
// Helper function to pack bits (little-endian)
function packBitsLittleEndian(bits: number[]): Uint8Array {
  const byteArray = new Uint8Array(Math.ceil(bits.length / 8));
  for (let i = 0; i < bits.length; i++) {
    if (bits[i]) {
      byteArray[Math.floor(i / 8)] |= 1 << i % 8;
    }
  }
  return byteArray;
}

// Convert packed bytes to base64
function bitsToBase64(bits: number[]): string {
  const packed = packBitsLittleEndian(bits);
  return btoa(String.fromCharCode(...packed));
}

// Create a frame
function createFrame(
  width: number,
  height: number,
  bits: number[],
  durationMs?: number,
) {
  return {
    data_b64: bitsToBase64(bits),
    width,
    height,
    duration_ms: durationMs ?? null,
  };
}
```

**Bitmap Font Rendering:**

- Use 5×7 or 6×8 bitmap fonts for text
- Render text to bit array (row-major, left-to-right)
- Consider using a font library or pre-defined character maps
- Example: https://github.com/olikraus/u8g2/wiki/fntlistall (for reference)

### 3. Content Types to Implement

**Phase 1 (MVP):**

- Static text messages
- Clock display (updating every minute)
- Simple animations (loading spinner, etc.)

**Phase 2:**

- Weather display
- Scrolling text
- Calendar/events
- Notifications (via push)

**Phase 3:**

- Dynamic content routing (multiple content sources)
- Content scheduling
- Conditional display logic

### 4. State Management

**Important:** The server should be mostly stateless. The driver manages:

- Content queue and priorities
- Frame timing and advancement
- Interruptions and resumptions

**Server MAY maintain:**

- Last shown content_id (to optimize `no_change` responses)
- Content generation cache (to avoid re-rendering unchanged content)
- Scheduled content calendar

### 5. Val Town Specific Considerations

**Storage:**

```ts
import { blob } from "https://esm.town/v/std/blob";

// Cache rendered content
await blob.setJSON("flipdot:last_content", contentResponse);

// Get cached content
const cached = await blob.getJSON("flipdot:last_content");
```

**Time-Based Content:**

```ts
// Use Deno's Date API
const now = new Date();
const hour = now.getHours();
const minute = now.getMinutes();

// Generate clock content
const clockText = `${hour.toString().padStart(2, "0")}:${minute.toString().padStart(2, "0")}`;
```

**Cron for Updates:**
If you need to pre-compute content, use a cron val:

```ts
// Update cache every minute
export default async function () {
  const content = await generateClockContent();
  await blob.setJSON("flipdot:current_content", content);
}
```

### 6. Testing and Development

**Test Responses:**
Use these patterns to test incrementally:

```ts
// Minimal valid response (no content change)
return Response.json({
  status: "no_change",
  poll_interval_ms: 30000,
});

// Static test frame (all pixels on)
const bits = new Array(56 * 14).fill(1);
return Response.json({
  status: "updated",
  content: {
    content_id: "test-pattern",
    frames: [
      {
        data_b64: bitsToBase64(bits),
        width: 56,
        height: 14,
        duration_ms: null,
      },
    ],
    playback: {
      priority: 0,
      interruptible: true,
    },
  },
  poll_interval_ms: 30000,
});
```

**Validation:**

- All frames must be 56×14 pixels
- Base64 must decode to at least `ceil(56 * 14 / 8) = 98` bytes
- `poll_interval_ms` must be >= 1000
- `content` required when `status="updated"`

**Local Testing:**

```bash
# Test the endpoint
curl -H "X-API-Key: your-key" https://your-val.val.run/api/flipdot/content
```

### 7. Project Structure Recommendation

```
val-server/
├── backend/
│   ├── index.ts              # Main HTTP handler (polling endpoint)
│   ├── auth.ts               # Authentication logic
│   ├── content/
│   │   ├── clock.ts          # Clock content generator
│   │   ├── text.ts           # Static text renderer
│   │   ├── weather.ts        # Weather content generator
│   │   └── router.ts         # Content routing logic
│   └── rendering/
│       ├── frame.ts          # Frame creation utilities
│       ├── font.ts           # Bitmap font rendering
│       └── bits.ts           # Bit packing utilities
├── shared/
│   └── types.ts              # Shared TypeScript types (Content, Frame, etc.)
├── CONTENT_SERVER_SPEC.md    # API specification
└── CLAUDE.md                 # This file
```

### 8. Type Definitions

Copy these from the spec into `shared/types.ts`:

```ts
export interface Frame {
  data_b64: string;
  width: number;
  height: number;
  duration_ms?: number | null;
  metadata?: Record<string, unknown>;
}

export interface PlaybackMode {
  loop?: boolean;
  loop_count?: number | null;
  priority?: number;
  interruptible?: boolean;
}

export interface Content {
  content_id: string;
  frames: Frame[];
  playback?: PlaybackMode;
  metadata?: Record<string, unknown>;
}

export type ResponseStatus = "updated" | "no_change" | "clear";

export interface ContentResponse {
  status: ResponseStatus;
  content?: Content;
  poll_interval_ms: number;
}
```

### 9. Common Pitfalls

**❌ Don't:**

- Return content with dimensions other than 56×14
- Use big-endian bit packing (must be little-endian)
- Forget to base64 encode the packed bits
- Return `poll_interval_ms` < 1000
- Include `content` when `status` is `"no_change"` or `"clear"`
- Hard-code secrets (use environment variables)

**✅ Do:**

- Validate authentication on every request
- Use consistent `content_id` for the same logical content
- Set appropriate `poll_interval_ms` (longer for static content)
- Test bit packing with known patterns first
- Log rendering errors for debugging
- Cache rendered content when possible

### 10. Security Checklist

- [ ] API key validated on every request
- [ ] API key stored in environment variable
- [ ] No secrets in code or logs
- [ ] Frame size limits enforced (max 1000 frames, 5MB total)
- [ ] Input validation on any user-provided content
- [ ] CORS headers set appropriately (if accessed from web)

---

## Val Town Standard Guidelines

The content below is standard Val Town guidance. See above for project-specific requirements.

---

## Core Guidelines

- Ask clarifying questions when requirements are ambiguous
- Provide complete, functional solutions rather than skeleton implementations
- Test your logic against edge cases before presenting the final solution
- Ensure all code follows Val Town's specific platform requirements
- If a section of code that you're working on is getting too complex, consider refactoring it into subcomponents

## Code Standards

- Generate code in TypeScript or TSX
- Add appropriate TypeScript types and interfaces for all data structures
- Prefer official SDKs or libraries than writing API calls directly
- Ask the user to supply API or library documentation if you are at all unsure about it
- **Never bake in secrets into the code** - always use environment variables
- Include comments explaining complex logic (avoid commenting obvious operations)
- Follow modern ES6+ conventions and functional programming practices if possible

## Types of triggers

### 1. HTTP Trigger

- Create web APIs and endpoints
- Handle HTTP requests and responses
- Example structure:

```ts
export default async function (req: Request) {
  return new Response("Hello World");
}
```

Files that are HTTP triggers have http in their name like `foobar.http.tsx`

### 2. Cron Triggers

- Run on a schedule
- Use cron expressions for timing
- Example structure:

```ts
export default async function () {
  // Scheduled task code
}
```

Files that are Cron triggers have cron in their name like `foobar.cron.tsx`

### 3. Email Triggers

- Process incoming emails
- Handle email-based workflows
- Example structure:

```ts
export default async function (email: Email) {
  // Process email
}
```

Files that are Email triggers have email in their name like `foobar.email.tsx`

## Val Town Standard Libraries

Val Town provides several hosted services and utility functions.

### Blob Storage

```ts
import { blob } from "https://esm.town/v/std/blob";
await blob.setJSON("myKey", { hello: "world" });
let blobDemo = await blob.getJSON("myKey");
let appKeys = await blob.list("app_");
await blob.delete("myKey");
```

### SQLite

```ts
import { sqlite } from "https://esm.town/v/stevekrouse/sqlite";
const TABLE_NAME = "todo_app_users_2";
// Create table - do this before usage and change table name when modifying schema
await sqlite.execute(`CREATE TABLE IF NOT EXISTS ${TABLE_NAME} (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL
)`);
// Query data
const result = await sqlite.execute(
  `SELECT * FROM ${TABLE_NAME} WHERE id = ?`,
  [1],
);
```

Note: When changing a SQLite table's schema, change the table's name (e.g., add \_2 or \_3) to create a fresh table.

### OpenAI

```ts
import { OpenAI } from "https://esm.town/v/std/openai";
const openai = new OpenAI();
const completion = await openai.chat.completions.create({
  messages: [{ role: "user", content: "Say hello in a creative way" }],
  model: "gpt-4o-mini",
  max_tokens: 30,
});
```

### Email

```ts
import { email } from "https://esm.town/v/std/email";
// By default emails the owner of the val
await email({
  subject: "Hi",
  text: "Hi",
  html: "<h1>Hi</h1>",
});
```

## Val Town Utility Functions

Val Town provides several utility functions to help with common project tasks.

### Importing Utilities

Always import utilities with version pins to avoid breaking changes:

```ts
import {
  parseProject,
  readFile,
  serveFile,
} from "https://esm.town/v/std/utils@85-main/index.ts";
```

### Available Utilities

#### **serveFile** - Serve project files with proper content types

For example, in Hono:

```ts
// serve all files in frontend/ and shared/
app.get("/frontend/*", (c) => serveFile(c.req.path, import.meta.url));
app.get("/shared/*", (c) => serveFile(c.req.path, import.meta.url));
```

#### **readFile** - Read files from within the project:

```ts
// Read a file from the project
const fileContent = await readFile("/frontend/index.html", import.meta.url);
```

#### **listFiles** - List all files in the project

```ts
const files = await listFiles(import.meta.url);
```

#### **parseProject** - Extract information about the current project from import.meta.url

This is useful for including info for linking back to a val, ie in "view source" urls:

```ts
const projectVal = parseProject(import.meta.url);
console.log(projectVal.username); // Owner of the project
console.log(projectVal.name); // Project name
console.log(projectVal.version); // Version number
console.log(projectVal.branch); // Branch name
console.log(projectVal.links.self.project); // URL to the project page
```

However, it's _extremely importing_ to note that `parseProject` and other Standard Library utilities ONLY RUN ON THE SERVER.
If you need access to this data on the client, run it in the server and pass it to the client by splicing it into the HTML page
or by making an API request for it.

## Val Town Platform Specifics

- **Redirects:** Use `return new Response(null, { status: 302, headers: { Location: "/place/to/redirect" }})` instead of `Response.redirect` which is broken
- **Images:** Avoid external images or base64 images. Use emojis, unicode symbols, or icon fonts/libraries instead
- **AI Image:** To inline generate an AI image use: `<img src="https://maxm-imggenurl.web.val.run/the-description-of-your-image" />`
- **Storage:** DO NOT use the Deno KV module for storage
- **Browser APIs:** DO NOT use the `alert()`, `prompt()`, or `confirm()` methods
- **Weather Data:** Use open-meteo for weather data (doesn't require API keys) unless otherwise specified
- **View Source:** Add a view source link by importing & using `import.meta.url.replace("ems.sh", "val.town)"` (or passing this data to the client) and include `target="_top"` attribute
- **Error Debugging:** Add `<script src="https://esm.town/v/std/catch"></script>` to HTML to capture client-side errors
- **Error Handling:** Only use try...catch when there's a clear local resolution; Avoid catches that merely log or return 500s. Let errors bubble up with full context
- **Environment Variables:** Use `Deno.env.get('keyname')` when you need to, but generally prefer APIs that don't require keys
- **Imports:** Use `https://esm.sh` for npm and Deno dependencies to ensure compatibility on server and browser
- **Storage Strategy:** Only use backend storage if explicitly required; prefer simple static client-side sites
- **React Configuration:** When using React libraries, pin versions with `?deps=react@18.2.0,react-dom@18.2.0` and start the file with `/** @jsxImportSource https://esm.sh/react@18.2.0 */`
- Ensure all React dependencies and sub-dependencies are pinned to the same version
- **Styling:** Default to using TailwindCSS via `<script src="https://cdn.twind.style" crossorigin></script>` unless otherwise specified

## Common Gotchas and Solutions

1. **Environment Limitations:**
   - Val Town runs on Deno in a serverless context, not Node.js
   - Code in `shared/` must work in both frontend and backend environments
   - Cannot use `Deno` keyword in shared code
   - Use `https://esm.sh` for imports that work in both environments

2. **SQLite Peculiarities:**
   - Limited support for ALTER TABLE operations
   - Create new tables with updated schemas and copy data when needed
   - Always run table creation before querying

3. **React Configuration:**
   - All React dependencies must be pinned to 18.2.0
   - Always include `@jsxImportSource https://esm.sh/react@18.2.0` at the top of React files
   - Rendering issues often come from mismatched React versions

4. **File Handling:**
   - Val Town only supports text files, not binary
   - Use the provided utilities to read files across branches and forks
   - For files in the project, use `readFile` helpers

5. **API Design:**
   - `fetch` handler is the entry point for HTTP vals
   - Run the Hono app with `export default app.fetch // This is the entry point for HTTP vals`
