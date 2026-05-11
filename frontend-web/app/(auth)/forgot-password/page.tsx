"use client";

import { useState } from "react";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      await api.post("/auth/password-reset", { email });
      setSent(true);
    } catch {
      setSent(true);
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
          <Link href="/login" className="font-bold tracking-tight text-3xl leading-none">
            <span className="text-primary">AB-</span>
            <span className="text-muted-foreground">AI.kz</span>
          </Link>
        </div>
        <div className="bg-card border border-border rounded-2xl shadow-lg p-8">
          {sent ? (
            <>
              <h1 className="text-xl font-semibold text-center mb-2">Письмо отправлено</h1>
              <p className="text-sm text-muted-foreground text-center mb-6">
                Если {email ? <strong>{email}</strong> : "ваш email"} зарегистрирован, вы получите ссылку для сброса пароля.
              </p>
              <Link href="/login">
                <Button variant="outline" className="w-full h-11">Вернуться к входу</Button>
              </Link>
            </>
          ) : (
            <>
              <h1 className="text-xl font-semibold text-center mb-1">Сброс пароля</h1>
              <p className="text-sm text-muted-foreground text-center mb-6">
                Введите email, и мы отправим ссылку для сброса пароля
              </p>
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
                {error && (
                  <div className="rounded-lg bg-destructive/10 text-destructive text-sm px-4 py-3">
                    {error}
                  </div>
                )}
                <Button type="submit" className="w-full h-11 brand-gradient font-semibold" disabled={loading}>
                  {loading ? "Отправляем..." : "Отправить ссылку"}
                </Button>
              </form>
              <p className="text-sm text-muted-foreground text-center mt-6">
                <Link href="/login" className="text-primary hover:underline font-medium">
                  Вернуться к входу
                </Link>
              </p>
            </>
          )}
        </div>
      </div>
    </div>
  );
}