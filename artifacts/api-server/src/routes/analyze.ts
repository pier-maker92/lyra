import { Router, type IRouter } from "express";

const router: IRouter = Router();

const ENGINE_URL = process.env.LYRICS_ENGINE_URL ?? "http://127.0.0.1:8000";

router.post("/analyze", async (req, res) => {
  const rawFrames = Array.isArray(req.body?.frames) ? req.body.frames : [];
  const frames = rawFrames.filter(
    (f: unknown): f is string => typeof f === "string" && f.startsWith("data:"),
  );
  if (frames.length === 0) {
    res.status(400).json({ error: "frames must contain at least one data URL" });
    return;
  }

  try {
    const upstream = await fetch(`${ENGINE_URL}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ frames }),
    });

    const text = await upstream.text();
    res
      .status(upstream.status)
      .type(upstream.headers.get("content-type") ?? "application/json")
      .send(text);
  } catch (err) {
    req.log.error({ err }, "lyrics engine request failed");
    res.status(502).json({ error: "Lyrics engine is unavailable" });
  }
});

export default router;
