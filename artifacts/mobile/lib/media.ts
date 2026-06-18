import { ImageManipulator, SaveFormat } from "expo-image-manipulator";
import * as ImagePicker from "expo-image-picker";
import * as VideoThumbnails from "expo-video-thumbnails";

export type MediaType = "image" | "video";

export interface PickedMedia {
  uri: string;
  type: MediaType;
  /** Preview frame (first sampled frame). */
  dataUrl: string;
  /** All sampled frames as JPEG data URLs (one for images, ~1fps for videos). */
  frames: string[];
}

const MAX_VIDEO_FRAMES = 8;

export class CameraPermissionError extends Error {
  constructor() {
    super("camera-permission-denied");
    this.name = "CameraPermissionError";
  }
}

export class VideoThumbnailError extends Error {
  constructor() {
    super("video-thumbnail-failed");
    this.name = "VideoThumbnailError";
  }
}

async function buildDataUrl(uri: string): Promise<string> {
  const context = ImageManipulator.manipulate(uri);
  context.resize({ height: 720 });
  const ref = await context.renderAsync();
  const result = await ref.saveAsync({
    compress: 0.7,
    format: SaveFormat.JPEG,
    base64: true,
  });
  return `data:image/jpeg;base64,${result.base64 ?? ""}`;
}

async function buildVideoFrames(
  uri: string,
  durationMs: number | undefined,
): Promise<string[]> {
  const total = durationMs && durationMs > 0 ? durationMs : 1000;
  // ~1fps, capped so long clips don't explode the embedding cost. When the clip
  // is longer than the cap, sample evenly across its whole duration.
  const count = Math.min(MAX_VIDEO_FRAMES, Math.max(1, Math.floor(total / 1000)));
  const frames: string[] = [];
  for (let i = 0; i < count; i++) {
    // Evenly spaced including first (t=0) and last (t≈duration) frame.
    const time = count === 1 ? 0 : Math.round((i * (total - 1)) / (count - 1));
    try {
      const thumb = await VideoThumbnails.getThumbnailAsync(uri, { time });
      frames.push(await buildDataUrl(thumb.uri));
    } catch {
      // Skip a frame that fails to extract; keep the rest.
    }
  }
  if (frames.length === 0) throw new VideoThumbnailError();
  return frames;
}

async function processAsset(
  asset: ImagePicker.ImagePickerAsset,
): Promise<PickedMedia> {
  const type: MediaType = asset.type === "video" ? "video" : "image";
  const frames =
    type === "video"
      ? await buildVideoFrames(asset.uri, asset.duration ?? undefined)
      : [await buildDataUrl(asset.uri)];
  return { uri: asset.uri, type, dataUrl: frames[0], frames };
}

export async function pickFromLibrary(): Promise<PickedMedia | null> {
  const res = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ["images", "videos"],
    quality: 0.9,
  });
  if (res.canceled || !res.assets?.length) return null;
  return processAsset(res.assets[0]);
}

export async function captureFromCamera(): Promise<PickedMedia | null> {
  const perm = await ImagePicker.requestCameraPermissionsAsync();
  if (!perm.granted) throw new CameraPermissionError();
  const res = await ImagePicker.launchCameraAsync({
    mediaTypes: ["images", "videos"],
    quality: 0.9,
  });
  if (res.canceled || !res.assets?.length) return null;
  return processAsset(res.assets[0]);
}
