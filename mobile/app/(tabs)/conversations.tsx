import { View, Text, FlatList, StyleSheet, RefreshControl } from "react-native";
import { useState, useCallback } from "react";
import { api } from "../../lib/api";
import type { Conversation } from "../../lib/types";

const CHANNEL_ICONS: Record<string, string> = {
  whatsapp: "WA",
  telegram: "TG",
  sms: "SMS",
};

export default function ConversationsScreen() {
  const [convs, setConvs] = useState<Conversation[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  const fetchConvos = useCallback(async () => {
    setRefreshing(true);
    try {
      const { data } = await api.get("/conversations", { params: { limit: 50 } });
      setConvs(data.data ?? []);
    } catch {}
    setRefreshing(false);
  }, []);

  return (
    <View style={styles.container}>
      <FlatList
        data={convs}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={styles.row}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>
                {item.client?.full_name?.split(" ").map((w) => w[0]).join("").slice(0, 2) ?? "?"}
              </Text>
            </View>
            <View style={styles.info}>
              <Text style={styles.name}>{item.client?.full_name ?? "Неизвестный"}</Text>
              <Text style={styles.preview} numberOfLines={1}>
                {item.last_message_preview ?? "Нет сообщений"}
              </Text>
            </View>
            <View style={styles.meta}>
              <Text style={styles.channel}>{CHANNEL_ICONS[item.channel] ?? item.channel}</Text>
              {item.unread_count > 0 && (
                <View style={styles.badge}>
                  <Text style={styles.badgeText}>{item.unread_count}</Text>
                </View>
              )}
            </View>
          </View>
        )}
        ListEmptyComponent={
          <View style={styles.empty}>
            <Text style={styles.emptyText}>Нет диалогов</Text>
          </View>
        }
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={fetchConvos} tintColor="#F59E0B" />}
        contentContainerStyle={convs.length === 0 ? { flex: 1 } : undefined}
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
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: "#1a2744",
    justifyContent: "center",
    alignItems: "center",
    marginRight: 12,
  },
  avatarText: { fontSize: 15, fontWeight: "600", color: "#F59E0B" },
  info: { flex: 1 },
  name: { fontSize: 16, fontWeight: "600", color: "#fff" },
  preview: { fontSize: 13, color: "#888", marginTop: 2 },
  meta: { alignItems: "flex-end", gap: 6 },
  channel: { fontSize: 11, fontWeight: "700", color: "#F59E0B" },
  badge: {
    backgroundColor: "#F59E0B",
    borderRadius: 10,
    minWidth: 20,
    height: 20,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 6,
  },
  badgeText: { fontSize: 11, fontWeight: "bold", color: "#0A1628" },
  empty: { flex: 1, justifyContent: "center", alignItems: "center" },
  emptyText: { fontSize: 16, color: "#666" },
});