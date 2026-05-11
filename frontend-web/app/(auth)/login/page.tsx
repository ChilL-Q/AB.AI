"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { auth } from "@/lib/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post("/auth/login", { email, password });
      auth.set(data.access_token, data.refresh_token);
      router.push("/dashboard");
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(msg ?? "Ошибка входа");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background relative overflow-hidden">
      <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
        <div className="absolute -top-40 -right-40 w-[500px] h-[500px] rounded-full bg-amber-500/5 blur-3xl" />
        <div className="absolute -bottom-40 -left-40 w-[400px] h-[400px] rounded-full bg-amber-500/5 blur-3xl" />
      </div>
      <div className="w-full max-w-md px-4 relative">
        <div className="text-center mb-8">
          <span className="font-bold tracking-tight text-3xl leading-none">
            <span className="text-primary">AB-</span>
            <span className="text-muted-foreground">AI.kz</span>
          </span>
          <p className="text-sm text-muted-foreground mt-2">aqyldy business</p>
        </div>
        <div className="bg-card border border-border rounded-2xl shadow-lg p-8">
          <h1 className="text-xl font-semibold text-center mb-1">С возвращением</h1>
          <p className="text-sm text-muted-foreground text-center mb-6">Войдите в аккаунт, чтобы продолжить</p>
          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="h-11"
                placeholder="name@example.com"
              />
            </div>
            <div className="flex items-center justify-between">
              <Label htmlFor="password">Пароль</Label>
              <Link href="/forgot-password" className="text-xs text-primary hover:underline">
                Забыли пароль?
              </Link>
            </div>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="h-11"
            />
            {error && (
              <div className="rounded-lg bg-destructive/10 text-destructive text-sm px-4 py-3">
                {error}
              </div>
            )}
            <Button type="submit" className="w-full h-11 brand-gradient font-semibold" disabled={loading}>
              {loading ? "Входим..." : "Войти"}
            </Button>
          </form>
          <p className="text-sm text-muted-foreground text-center mt-6">
            Нет аккаунта?{" "}
            <Link href="/register" className="text-primary hover:underline font-medium">
              Зарегистрироваться
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}