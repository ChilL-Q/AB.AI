import { StyleSheet, Text, View } from "react-native";

export default function DashboardScreen() {
  return (
    <View style={styles.container}>
      <Text style={styles.title}>AB AI</Text>
      <Text style={styles.subtitle}>Дашборд</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center" },
  title: { fontSize: 28, fontWeight: "bold" },
  subtitle: { fontSize: 16, color: "#666", marginTop: 8 },
});
