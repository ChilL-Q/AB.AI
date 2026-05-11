"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";

function VerifyEmailInner() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [loading, setLoading] = useState(true);
  const [verified, setVerified] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      return;
    }
    (async () => {
      try {
        await api.post("/auth/verify-email", null, { params: { token } });
        setVerified(true);
      } catch (err: unknown) {
        const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
        setError(msg ?? "Ошибка подтверждения email");
      } finally {
        setLoading(false);
      }
    })();
  }, [token]);

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
        <div className="bg-card border border-border rounded-2xl shadow-lg p-8 text-center">
          {loading ? (
            <p className="text-muted-foreground">Подтверждаем email...</p>
          ) : !token ? (
            <>
              <h1 className="text-xl font-semibold mb-2">Подтверждение email</h1>
              <p className="text-sm text-muted-foreground mb-6">
                Перейдите в настройки, чтобы отправить письмо подтверждения повторно.
              </p>
              <Link href="/login">
                <Button className="brand-gradient font-semibold">Войти</Button>
              </Link>
            </>
          ) : verified ? (
            <>
              <h1 className="text-xl font-semibold mb-2">Email подтверждён!</h1>
              <p className="text-sm text-muted-foreground mb-6">
                Ваш email успешно подтверждён. Теперь вы можете войти.
              </p>
              <Link href="/login">
                <Button className="brand-gradient font-semibold">Войти</Button>
              </Link>
            </>
          ) : (
            <>
              <h1 className="text-xl font-semibold mb-2">Ошибка</h1>
              <p className="text-sm text-destructive mb-4">{error}</p>
              <p className="text-sm text-muted-foreground mb-6">
                Ссылка устарела или недействительна. Запросите новую в настройках.
              </p>
              <Link href="/login">
                <Button variant="outline">Войти</Button>
              </Link>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense>
      <VerifyEmailInner />
    </Suspense>
  );
}