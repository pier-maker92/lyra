---
name: Visual Lyrics video frame averaging
description: How video is turned into a query in the analyze pipeline, and the contract that ties the 3 layers together.
---

# Video frame averaging in /api/analyze

For video, the **client** (Expo `lib/media.ts`) samples frames at ~1fps using
`expo-video-thumbnails`, capped at a small max, evenly spaced **including first
(t=0) and last (t≈duration)** frame. Images produce a single frame. The client
sends `{ frames: string[] }` (JPEG data URLs).

The **engine** (`services/lyrics-engine`) embeds *every* frame conditioned on
*each* mood prompt, then averages the per-frame vectors element-wise into one
query vector per mood. A shared `asyncio.Semaphore` bounds OpenRouter
concurrency because the call count is `moods × frames` (5 × N) — without it the
free embed model rate-limits. The engine also re-caps frames (even sampling
including endpoints) as a server-side safety net.

**Contract rule:** the request shape lives in `lib/api-spec/openapi.yaml`
(`AnalyzeRequest.frames`, required, minItems 1). All three layers — mobile
client, `api-server` proxy, python engine — must agree on `frames`. After
editing the spec, run `pnpm --filter @workspace/api-spec run codegen` or the
generated client/zod drift from the server.

**Why:** the embed model is multimodal and embeds prompt+image *jointly*, so
there is no pure-image embedding to reuse across moods — averaging must happen
per mood. There is intentionally **no `imageDataUrl` backward-compat fallback**;
the canonical field is `frames` and keeping a second path made the OpenAPI
contract inconsistent with the code.
