import { Ionicons } from "@expo/vector-icons";
import { Image } from "expo-image";
import { LinearGradient } from "expo-linear-gradient";
import { StatusBar } from "expo-status-bar";
import React from "react";
import {
  Platform,
  Pressable,
  StyleSheet,
  Text,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

const lyraLogo = require("../assets/images/lyra-logo.png");

interface Props {
  onUseCamera: () => void;
  onUseLibrary: () => void;
}

export function HomeScreen({ onUseCamera, onUseLibrary }: Props) {
  const insets = useSafeAreaInsets();
  const topInset = Platform.OS === "web" ? 67 : insets.top;
  const bottomInset = Platform.OS === "web" ? 34 : insets.bottom;

  return (
    <View style={styles.container}>
      <StatusBar style="light" />
      <LinearGradient
        colors={["#1a0b2e", "#2d0a3d", "#000000"]}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
        style={StyleSheet.absoluteFill}
      />

      <View style={[styles.content, { paddingTop: topInset + 24 }]}>
        <View style={styles.hero}>
          <Image
            source={lyraLogo}
            style={styles.logo}
            contentFit="contain"
            accessibilityLabel="LYRA"
          />
          <Text style={styles.subtitle}>
            Lost for words? Say it with lyrics
          </Text>
        </View>

        <View style={[styles.actions, { paddingBottom: bottomInset + 28 }]}>
          <Pressable
            testID="use-camera"
            onPress={onUseCamera}
            style={({ pressed }) => [
              styles.primaryButton,
              pressed && styles.pressed,
            ]}
          >
            <Ionicons name="camera" size={22} color="#000000" />
            <Text style={styles.primaryButtonText}>Scatta o registra</Text>
          </Pressable>

          <Pressable
            testID="use-library"
            onPress={onUseLibrary}
            style={({ pressed }) => [
              styles.secondaryButton,
              pressed && styles.pressed,
            ]}
          >
            <Ionicons name="images" size={22} color="#ffffff" />
            <Text style={styles.secondaryButtonText}>Dalla galleria</Text>
          </Pressable>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#000000" },
  content: {
    flex: 1,
    justifyContent: "space-between",
    paddingHorizontal: 28,
  },
  hero: { flex: 1, justifyContent: "center", alignItems: "center" },
  logo: {
    width: 264,
    height: 264,
  },
  subtitle: {
    fontFamily: "Inter_300Light",
    fontSize: 16,
    lineHeight: 24,
    letterSpacing: 1.5,
    color: "rgba(255,255,255,0.65)",
    marginTop: 16,
    maxWidth: 320,
    textAlign: "center",
  },
  actions: { gap: 14 },
  primaryButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    backgroundColor: "#ffffff",
    paddingVertical: 18,
    borderRadius: 18,
  },
  primaryButtonText: {
    fontFamily: "Inter_600SemiBold",
    fontSize: 17,
    color: "#000000",
  },
  secondaryButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    backgroundColor: "rgba(255,255,255,0.1)",
    borderWidth: 1,
    borderColor: "rgba(255,255,255,0.18)",
    paddingVertical: 18,
    borderRadius: 18,
  },
  secondaryButtonText: {
    fontFamily: "Inter_600SemiBold",
    fontSize: 17,
    color: "#ffffff",
  },
  pressed: { opacity: 0.7 },
});
