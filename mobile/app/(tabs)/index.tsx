import { View, Text, StyleSheet, ScrollView, RefreshControl } from "react-native";
import { useState, useCallback } from "react";
import { api } from "../../lib/api";
import { useAuth } from "../../stores/auth";
import type { OutreachMetrics } from "../../lib/types";

export default function DashboardScreen() {
  const { user } = useAuth();
  const [metrics, setMetrics] = useState<OutreachMetrics | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      const { data } = await api.get("/ai-agent/outreach/metrics");
      setMetrics(data);
    } catch {}
    setRefreshing(false);
  }, []);

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#F59E0B" />}
    >
      <View style={styles.header}>
        <View style={styles.logoBadge}>
          <Text style={styles.logoText}>AB</Text>
        </View>
        <View>
          <Text style={styles.greeting}>Добро пожаловать,</Text>
          <Text style={styles.name}>{user?.full_name ?? "..."}</Text>
        </View>
      </View>

      <View style={styles.statsGrid}>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{metrics?.total_outreach ?? "—"}</Text>
          <Text style={styles.statLabel}>Обращений AI</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>
            {metrics ? `${(metrics.reply_rate * 100).toFixed(0)}%` : "—"}
          </Text>
          <Text style={styles.statLabel}>Ответили</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>
            {metrics ? `${(metrics.retention_rate * 100).toFixed(0)}%` : "—"}
          </Text>
          <Text style={styles.statLabel}>Вернулись</Text>
        </View>
        <View style={styles.statCard}>
          <Text style={styles.statValue}>{metrics?.total_revenue ?? "—"}</Text>
          <Text style={styles.statLabel}>Выручка от AI</Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0A1628" },
  header: {
    flexDirection: "row",
    alignItems: "center",
    gap: 16,
    padding: 24,
  },
  logoBadge: {
    width: 48,
    height: 48,
    borderRadius: 14,
    backgroundColor: "#F59E0B",
    justifyContent: "center",
    alignItems: "center",
  },
  logoText: { fontSize: 18, fontWeight: "bold", color: "#0A1628" },
  greeting: { fontSize: 14, color: "#888" },
  name: { fontSize: 20, fontWeight: "bold", color: "#fff" },
  statsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    padding: 16,
    gap: 12,
  },
  statCard: {
    flex: 1,
    minWidth: "45%",
    backgroundColor: "#1a2744",
    borderRadius: 16,
    padding: 20,
  },
  statValue: { fontSize: 28, fontWeight: "bold", color: "#F59E0B" },
  statLabel: { fontSize: 12, color: "#888", marginTop: 4 },
});