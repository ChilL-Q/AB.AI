import { useState } from "react";
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
} from "react-native";
import { useAuth } from "../../stores/auth";

export default function LoginScreen() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async () => {
    if (!email || !password) return;
    setLoading(true);
    setError(null);
    try {
      await login(email, password);
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(msg ?? "Ошибка входа");
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === "ios" ? "padding" : "height"}
      style={styles.container}
    >
      <View style={styles.inner}>
        <View style={styles.logoContainer}>
          <View style={styles.logoBadge}>
            <Text style={styles.logoText}>AB</Text>
          </View>
          <Text style={styles.brandMain}>
            <Text style={styles.brandAccent}>AB-</Text>AI.kz
          </Text>
          <Text style={styles.tagline}>aqyldy business</Text>
        </View>

        <View style={styles.form}>
          <TextInput
            style={styles.input}
            placeholder="Email"
            placeholderTextColor="#666"
            value={email}
            onChangeText={setEmail}
            autoCapitalize="none"
            keyboardType="email-address"
          />
          <TextInput
            style={styles.input}
            placeholder="Пароль"
            placeholderTextColor="#666"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />
          {error && <Text style={styles.error}>{error}</Text>}
          <TouchableOpacity
            style={styles.button}
            onPress={handleLogin}
            disabled={loading}
            activeOpacity={0.8}
          >
            {loading ? (
              <ActivityIndicator color="#0A1628" />
            ) : (
              <Text style={styles.buttonText}>Войти</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#0A1628" },
  inner: { flex: 1, justifyContent: "center", paddingHorizontal: 32 },
  logoContainer: { alignItems: "center", marginBottom: 48 },
  logoBadge: {
    width: 64,
    height: 64,
    borderRadius: 16,
    backgroundColor: "#F59E0B",
    justifyContent: "center",
    alignItems: "center",
    marginBottom: 16,
  },
  logoText: { fontSize: 24, fontWeight: "bold", color: "#0A1628" },
  brandMain: { fontSize: 32, fontWeight: "bold", color: "#fff" },
  brandAccent: { color: "#F59E0B" },
  tagline: { fontSize: 12, color: "#666", marginTop: 4 },
  form: { gap: 12 },
  input: {
    backgroundColor: "#1a2744",
    borderRadius: 12,
    paddingVertical: 14,
    paddingHorizontal: 16,
    color: "#fff",
    fontSize: 16,
  },
  button: {
    backgroundColor: "#F59E0B",
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: "center",
    marginTop: 8,
  },
  buttonText: { color: "#0A1628", fontSize: 16, fontWeight: "700" },
  error: { color: "#ef4444", fontSize: 14, textAlign: "center" },
});