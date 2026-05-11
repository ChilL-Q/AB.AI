import { View, Text, StyleSheet, ScrollView, TouchableOpacity, RefreshControl } from "react-native";
import { useState, useCallback } from "react";
import { api } from "../../lib/api";
import type { OutreachMetrics } from "../../lib/types";

export default function AIAgentScreen() {
  const [metrics, setMetrics] = useState<OutreachMetrics | null>(null);
  const [isActive, setIsActive] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    try {
      const [m, cfg] = await Promise.all([
        api.get("/ai-agent/outreach/metrics"),
        api.get("/ai-agent/config"),
      ]);
      setMetrics(m.data);
      setIsActive(cfg.data.is_active);
    } catch {}
    setRefreshing(false);
  }, []);

  const toggleActive = async () => {
    const next = !isActive;
    setIsActive(next);
    try {
      await api.patch("/ai-agent/config", { is_active: next });
    } catch {
      setIsActive(!next);
    }
  };

  return (
    <ScrollView
      style={styles.container}
      refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#F59E0B" />}
    >
      <View style={styles.statusRow}>
        <Text style={styles.title}>AI-агент</Text>
        <TouchableOpacity onPress={toggleActive} activeOpacity={0.8}>
          <View style={[styles.toggle, isActive ? styles.toggleOn : styles.toggleOff]}>
            <View style={[styles.toggleDot, isActive ? styles.dotOn : styles.dotOff]} />
          </View>
        </TouchableOpacity>
      </View>
      <Text style={styles.status}>{isActive ? "AI работает" : "AI остановлен"}</Text>

      <View style={styles.metricsGrid}>
        <View style={styles.metricCard}>
          <Text style={styles.metricValue}>{metrics?.total_outreach ?? "—"}</Text>
          <Text style={styles.metricLabel}>Обращений</Text>
        </View>
        <View style={styles.metricCard}>
          <Text style={styles.metricValue}>
            {metrics ? `${(metrics.reply_rate * 100).toFixed(0)}%` : "—"}
          </Text>
          <Text style={styles.metricLabel}>Ответили</Text>
        </View>
        <View style={styles.metricCard}>
          <Text style={styles.metricValue}>
            {metrics ? `${(metrics.retention_rate * 100).toFixed(0)}%` : "—"}
          </Text>
          <Text style={styles.metricLabel}>Вернулись</Text>
        </View>
        <View style={styles.metricCard}>
          <Text style={styles.metricValue}>{metrics?.escalated ?? "—"}</Text>
          <Text style={styles.metricLabel}>Эскалаций</Text>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0A1628" },
  statusRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingHorizontal: 24,
    paddingTop: 24,
  },
  title: { fontSize: 28, fontWeight: "bold", color: "#fff" },
  toggle: {
    width: 52,
    height: 28,
    borderRadius: 14,
    padding: 2,
  },
  toggleOn: { backgroundColor: "#22c55e" },
  toggleOff: { backgroundColor: "#333" },
  toggleDot: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: "#fff",
  },
  dotOn: { alignSelf: "flex-end" },
  dotOff: { alignSelf: "flex-start" },
  status: { fontSize: 14, color: "#888", paddingHorizontal: 24, marginTop: 4 },
  metricsGrid: {
    flexDirection: "row",
    flexWrap: "wrap",
    padding: 16,
    gap: 12,
    marginTop: 16,
  },
  metricCard: {
    flex: 1,
    minWidth: "45%",
    backgroundColor: "#1a2744",
    borderRadius: 16,
    padding: 20,
  },
  metricValue: { fontSize: 28, fontWeight: "bold", color: "#F59E0B" },
  metricLabel: { fontSize: 12, color: "#888", marginTop: 4 },
});