"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

type Client = { id: string; full_name: string; phone: string; email?: string };

export default function ClientsPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["clients"],
    queryFn: async () => (await api.get<Client[]>("/clients")).data,
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Клиенты</h2>
          <p className="text-muted-foreground">База ваших клиентов</p>
        </div>
        <Button><Plus className="h-4 w-4 mr-2" />Добавить</Button>
      </div>
      <Card>
        <CardHeader><CardTitle>Список</CardTitle></CardHeader>
        <CardContent>
          {isLoading && <p className="text-muted-foreground">Загрузка...</p>}
          {error && (
            <p className="text-sm text-muted-foreground">
              Пока нет данных. Создайте команду в настройках, чтобы добавить клиентов.
            </p>
          )}
          {data && data.length === 0 && <p className="text-muted-foreground">Клиентов пока нет</p>}
          {data && data.length > 0 && (
            <div className="divide-y">
              {data.map((c) => (
                <div key={c.id} className="py-3 flex justify-between">
                  <div>
                    <div className="font-medium">{c.full_name}</div>
                    <div className="text-sm text-muted-foreground">{c.phone}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
