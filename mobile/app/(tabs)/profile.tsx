import { View, Text, StyleSheet, TouchableOpacity, Alert } from "react-native";
import { useAuth } from "../../stores/auth";
import { useRouter } from "expo-router";

export default function ProfileScreen() {
  const { user, logout } = useAuth();
  const router = useRouter();

  const handleLogout = () => {
    Alert.alert("Выйти?", "Вы уверены, что хотите выйти?", [
      { text: "Отмена", style: "cancel" },
      {
        text: "Выйти",
        style: "destructive",
        onPress: async () => {
          await logout();
          router.replace("/(auth)/login");
        },
      },
    ]);
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {user?.full_name?.split(" ").map((w) => w[0]).join("").slice(0, 2) ?? "?"}
          </Text>
        </View>
        <Text style={styles.name}>{user?.full_name ?? "..."}</Text>
        <Text style={styles.email}>{user?.email ?? ""}</Text>
        <Text style={styles.role}>{user?.role ?? ""}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Настройки</Text>
        {/* TODO: add settings links */}
      </View>

      <TouchableOpacity style={styles.logoutBtn} onPress={handleLogout} activeOpacity={0.8}>
        <Text style={styles.logoutText}>Выйти</Text>
      </TouchableOpacity>

      <Text style={styles.version}>AB-AI.kz v0.1.0</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0A1628" },
  header: { alignItems: "center", paddingTop: 40, paddingBottom: 24 },
  avatar: {
    width: 72,
    height: 72,
    borderRadius: 36,
    backgroundColor: "#F59E0B",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 12,
  },
  avatarText: { fontSize: 26, fontWeight: "bold", color: "#0A1628" },
  name: { fontSize: 22, fontWeight: "bold", color: "#fff" },
  email: { fontSize: 14, color: "#888", marginTop: 4 },
  role: {
    fontSize: 12,
    color: "#F59E0B",
    marginTop: 6,
    textTransform: "uppercase",
    fontWeight: "600",
  },
  section: { paddingHorizontal: 24, marginTop: 16 },
  sectionTitle: { fontSize: 12, color: "#666", textTransform: "uppercase", marginBottom: 8 },
  logoutBtn: {
    marginHorizontal: 24,
    marginTop: 40,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: "#ef4444",
    alignItems: "center",
  },
  logoutText: { color: "#ef4444", fontSize: 16, fontWeight: "600" },
  version: { textAlign: "center", color: "#444", fontSize: 12, marginTop: 24 },
});