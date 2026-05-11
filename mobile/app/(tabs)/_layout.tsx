import { Tabs } from "expo-router";
import { View, Text, StyleSheet } from "react-native";

function TabIcon({ title, active }: { title: string; active: boolean }) {
  return (
    <View style={styles.tabItem}>
      <Text style={[styles.tabLabel, active && styles.tabLabelActive]}>{title}</Text>
    </View>
  );
}

export default function TabsLayout() {
  return (
    <Tabs
      screenOptions={{
        headerStyle: { backgroundColor: "#0A1628" },
        headerTintColor: "#fff",
        tabBarStyle: { backgroundColor: "#0A1628", borderTopColor: "#1a2744" },
        tabBarActiveTintColor: "#F59E0B",
        tabBarInactiveTintColor: "#666",
      }}
    >
      <Tabs.Screen
        name="index"
        options={{ title: "Дашборд", tabBarLabel: "Дашборд" }}
      />
      <Tabs.Screen
        name="clients"
        options={{ title: "Клиенты", tabBarLabel: "Клиенты" }}
      />
      <Tabs.Screen
        name="conversations"
        options={{ title: "Диалоги", tabBarLabel: "Диалоги" }}
      />
      <Tabs.Screen
        name="ai-agent"
        options={{ title: "AI-агент", tabBarLabel: "AI" }}
      />
      <Tabs.Screen
        name="profile"
        options={{ title: "Профиль", tabBarLabel: "Профиль" }}
      />
    </Tabs>
  );
}

const styles = StyleSheet.create({
  tabItem: { alignItems: "center" },
  tabLabel: { fontSize: 10, color: "#666" },
  tabLabelActive: { color: "#F59E0B" },
});