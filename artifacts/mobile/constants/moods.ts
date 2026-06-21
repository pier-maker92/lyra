import { Ionicons } from "@expo/vector-icons";

type IconName = keyof typeof Ionicons.glyphMap;

export interface MoodMeta {
  label: string;
  color: string;
  icon: IconName;
}

/** The first bucket always returned by the engine: pure visual best matches. */
export const BEST_KEY = "best";

/**
 * Curated label/color/icon per catalog mood. The catalog's mood taxonomy is
 * dynamic, so this is a lookup with a prettified fallback for any unmapped key.
 */
const MOOD_META_MAP: Record<string, MoodMeta> = {
  best: { label: "Best", color: "#FFFFFF", icon: "star" },
  romantic_love: { label: "Love", color: "#FF4D6D", icon: "heart" },
  heartbreak: { label: "Heartbreak", color: "#FB7185", icon: "heart-dislike" },
  desire_sensuality: { label: "Desire", color: "#F472B6", icon: "flame" },
  euphoria_dance: { label: "Euphoria", color: "#A855F7", icon: "sparkles" },
  party_hype: { label: "Party", color: "#C084FC", icon: "musical-notes" },
  summer_good_times: { label: "Summer", color: "#FACC15", icon: "sunny" },
  holiday_festive: { label: "Festive", color: "#F87171", icon: "gift" },
  freedom_adventure: { label: "Adventure", color: "#22D3EE", icon: "compass" },
  motivation_grind: { label: "Grind", color: "#F59E0B", icon: "barbell" },
  confidence_flex: { label: "Confidence", color: "#FBBF24", icon: "flash" },
  wealth_luxury: { label: "Luxury", color: "#EAB308", icon: "diamond" },
  street_hustle: { label: "Street", color: "#F97316", icon: "walk" },
  anger_rebellion: { label: "Rebellion", color: "#EF4444", icon: "skull" },
  chill_relaxed: { label: "Chill", color: "#34D399", icon: "leaf" },
  nostalgia_memory: { label: "Nostalgia", color: "#818CF8", icon: "time" },
  melancholy: { label: "Melancholy", color: "#60A5FA", icon: "rainy" },
  lonely_isolated: { label: "Lonely", color: "#7DD3FC", icon: "cloudy-night" },
  dark_introspective: { label: "Introspective", color: "#94A3B8", icon: "moon" },
  spiritual_faith: { label: "Spiritual", color: "#A78BFA", icon: "planet" },
};

const FALLBACK: MoodMeta = {
  label: "Other",
  color: "#A1A1AA",
  icon: "ellipsis-horizontal",
};

function prettyLabel(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function getMoodMeta(key: string): MoodMeta {
  const meta = MOOD_META_MAP[key];
  if (meta) return meta;
  return { ...FALLBACK, label: prettyLabel(key) };
}
