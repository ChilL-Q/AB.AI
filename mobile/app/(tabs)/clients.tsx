import { View, Text, FlatList, StyleSheet, RefreshControl } from "react-native";
import { useState, useCallback } from "react";
import { api } from "../../lib/api";
import type { Client } from "../../lib/types";

export default function ClientsScreen() {
  const [clients, setClients] = useState<Client[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchClients = useCallback(async () => {
    setRefreshing(true);
    try {
      const { data } = await api.get("/clients", { params: { limit: 50 } });
      setClients(data.data ?? []);
    } catch {}
    setRefreshing(false);
  }, []);

  return (
    <View style={styles.container}>
      <FlatList
        data={clients}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.row}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>
                {item.full_name.split(" ").map((w) => w[0]).join("").slice(0, 2)}
              </Text>
            </View>
            <View style={styles.info}>
              <Text style={styles.name}>{item.full_name}</Text>
              <Text style={styles.sub}>{item.phone} · {item.total_visits} визитов</Text>
            </View>
            <Text style={styles.spent}>{item.total_spent}₸</Text>
          </View>
        )}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>Клиентов пока нет</Text>
            <Text style={styles.emptyHint}>Потяните вниз для обновления</Text>
          </View>
        }
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={fetchClients} tintColor="#F59E0B" />}
        contentContainerStyle={clients.length === 0 ? { flex: 1 } : undefined}
        onEndReached={fetchClients}
        onEndReachedThreshold={0}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0A1628" },
  row: {
    flexDirection: "row",
    alignItems: "center",
    paddingVertical: 14,
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: "#1a2744",
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: "#F59E0B",
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
  },
  avatarText: { fontSize: 14, fontWeight: "bold", color: "#0A1628" },
  info: { flex: 1 },
  name: { fontSize: 16, fontWeight: "600", color: "#fff" },
  sub: { fontSize: 13, color: "#888", marginTop: 2 },
  spent: { fontSize: 14, fontWeight: "600", color: "#F59E0B" },
  empty: { flex: 1, justifyContent: "center", alignItems: "center" },
  emptyText: { fontSize: 16, color: "#666" },
  emptyHint: { fontSize: 12, color: "#444", marginTop: 4 },
});