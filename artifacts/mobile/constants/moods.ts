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
  best: { label: "Migliori", color: "#FFFFFF", icon: "star" },
  romantic_love: { label: "Amore", color: "#FF4D6D", icon: "heart" },
  heartbreak: { label: "Cuore spezzato", color: "#FB7185", icon: "heart-dislike" },
  desire_sensuality: { label: "Desiderio", color: "#F472B6", icon: "flame" },
  euphoria_dance: { label: "Euforia", color: "#A855F7", icon: "sparkles" },
  party_hype: { label: "Festa", color: "#C084FC", icon: "musical-notes" },
  summer_good_times: { label: "Estate", color: "#FACC15", icon: "sunny" },
  holiday_festive: { label: "Festivo", color: "#F87171", icon: "gift" },
  freedom_adventure: { label: "Avventura", color: "#22D3EE", icon: "compass" },
  motivation_grind: { label: "Grinta", color: "#F59E0B", icon: "barbell" },
  confidence_flex: { label: "Sicurezza", color: "#FBBF24", icon: "flash" },
  wealth_luxury: { label: "Lusso", color: "#EAB308", icon: "diamond" },
  street_hustle: { label: "Strada", color: "#F97316", icon: "walk" },
  anger_rebellion: { label: "Ribellione", color: "#EF4444", icon: "skull" },
  chill_relaxed: { label: "Relax", color: "#34D399", icon: "leaf" },
  nostalgia_memory: { label: "Nostalgia", color: "#818CF8", icon: "time" },
  melancholy: { label: "Malinconia", color: "#60A5FA", icon: "rainy" },
  lonely_isolated: { label: "Solitudine", color: "#7DD3FC", icon: "cloudy-night" },
  dark_introspective: { label: "Introspezione", color: "#94A3B8", icon: "moon" },
  spiritual_faith: { label: "Spiritualità", color: "#A78BFA", icon: "planet" },
};

const FALLBACK: MoodMeta = {
  label: "Altro",
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
