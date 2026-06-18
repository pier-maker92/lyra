import { useVideoPlayer, VideoView } from "expo-video";
import React from "react";
import { Platform, StyleSheet } from "react-native";

function WebVideo({ uri }: { uri: string }) {
  return React.createElement("video", {
    ref: (el: HTMLVideoElement | null) => {
      if (!el) return;
      // Setting the property (not just the attribute) before play() is what
      // satisfies the browser muted-autoplay policy for blob: sources.
      el.muted = true;
      el.defaultMuted = true;
      const p = el.play();
      if (p && typeof p.catch === "function") p.catch(() => {});
    },
    src: uri,
    autoPlay: true,
    loop: true,
    muted: true,
    playsInline: true,
    style: {
      position: "absolute",
      top: 0,
      left: 0,
      width: "100%",
      height: "100%",
      objectFit: "cover",
    },
  });
}

function NativeVideo({ uri }: { uri: string }) {
  "use no memo";
  const player = useVideoPlayer(uri, (p) => {
    p.loop = true;
    p.muted = true;
    p.play();
  });
  return (
    <VideoView
      player={player}
      style={StyleSheet.absoluteFill}
      contentFit="cover"
      nativeControls={false}
    />
  );
}

export function VideoBackground({ uri }: { uri: string }) {
  if (Platform.OS === "web") {
    return <WebVideo uri={uri} />;
  }
  return <NativeVideo uri={uri} />;
}
