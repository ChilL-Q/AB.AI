import { useEffect } from "react";
import { Stack, useRouter, useRootNavigationState } from "expo-router";
import { ActivityIndicator, View } from "react-native";
import { useAuth } from "../stores/auth";
import { isLoggedIn } from "../lib/api";

export default function RootLayout() {
  const router = useRouter();
  const rootNav = useRootNavigationState();
  const { user, loading, fetchMe } = useAuth();

  useEffect(() => {
    (async () => {
      const authed = await isLoggedIn();
      if (authed && !user) {
        await fetchMe();
      }
    })();
  }, []);

  useEffect(() => {
    if (!rootNav?.key || loading) return;
    if (!user) {
      router.replace("/(auth)/login");
    }
  }, [user, loading, rootNav?.key]);

  if (loading) {
    return (
      <View style={{ flex: 1, justifyContent: "center", alignItems: "center", backgroundColor: "#0A1628" }}>
        <ActivityIndicator size="large" color="#F59E0B" />
      </View>
    );
  }

  return (
    <Stack>
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      <Stack.Screen name="(auth)" options={{ headerShown: false }} />
    </Stack>
  );
}