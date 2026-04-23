"use client";

import { useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  Pencil,
  Trash2,
  Phone,
  Mail,
  Calendar,
  Car,
  MessageSquare,
  User as UserIcon,
  Loader2,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatDateLong, formatMoney } from "@/lib/formatters";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { ClientFormDialog } from "@/components/client-form-dialog";
import { initialsOf } from "@/hooks/use-me";
import type { Client } from "@/types";

function errorStatus(err: unknown): number | null {
  const s = (err as { response?: { status?: number } }).response?.status;
  return typeof s === "number" ? s : null;
}

export default function ClientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const qc = useQueryClient();
  const [editOpen, setEditOpen] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const { data: client, isLoading, error } = useQuery({
    queryKey: ["client", id],
    queryFn: async () => (await api.get<Client>(`/clients/${id}`)).data,
    enabled: !!id,
    retry: (failureCount, err) => errorStatus(err) !== 404 && failureCount < 2,
  });

  const del = useMutation({
    mutationFn: async () => {
      await api.delete(`/clients/${id}`);
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["clients"] });
      qc.removeQueries({ queryKey: ["client", id] });
      router.push("/clients");
    },
  });

  if (isLoading) {
    return (
      <div className="py-16 flex justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (error || !client) {
    const notFound = errorStatus(error) === 404;
    return (
      <div className="py-16 text-center space-y-4">
        <p className="text-muted-foreground">
          {notFound ? "Клиент не найден" : "Не удалось загрузить клиента. Попробуйте позже."}
        </p>
        <Button variant="outline" asChild>
          <Link href="/clients"><ArrowLeft className="h-4 w-4 mr-2" />К списку</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="space-y-6 max-w-5xl">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" asChild>
          <Link href="/clients"><ArrowLeft className="h-4 w-4 mr-2" />Клиенты</Link>
        </Button>
      </div>

      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-4">
          <div className="h-16 w-16 rounded-full bg-gradient-to-br from-primary to-violet-500 text-primary-foreground flex items-center justify-center text-xl font-semibold shrink-0">
            {initialsOf(client.full_name)}
          </div>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">{client.full_name}</h1>
            <p className="text-sm text-muted-foreground">
              Клиент с {formatDateLong(client.created_at)} · Источник: {client.source || "manual"}
            </p>
            {client.tags.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1">
                {client.tags.map((t) => (
                  <Badge key={t} variant="outline">{t}</Badge>
                ))}
              </div>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setEditOpen(true)}>
            <Pencil className="h-4 w-4 mr-2" />Редактировать
          </Button>
          <Button
            variant="outline"
            className="text-destructive hover:text-destructive"
            disabled={del.isPending}
            onClick={() => setConfirmOpen(true)}
          >
            {del.isPending ? (
              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
            ) : (
              <Trash2 className="h-4 w-4 mr-2" />
            )}
            Удалить
          </Button>
        </div>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <Card>
          <CardContent className="p-5">
            <div className="text-xs uppercase tracking-wider text-muted-foreground">Всего визитов</div>
            <div className="mt-1 text-2xl font-bold">{client.total_visits}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="text-xs uppercase tracking-wider text-muted-foreground">Потрачено</div>
            <div className="mt-1 text-2xl font-bold">{formatMoney(client.total_spent)}</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-5">
            <div className="text-xs uppercase tracking-wider text-muted-foreground">Последний визит</div>
            <div className="mt-1 text-2xl font-bold">{formatDateLong(client.last_visit_at)}</div>
          </CardContent>
        </Card>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview"><UserIcon className="h-4 w-4 mr-2" />Обзор</TabsTrigger>
          <TabsTrigger value="cars"><Car className="h-4 w-4 mr-2" />Автомобили</TabsTrigger>
          <TabsTrigger value="visits"><Calendar className="h-4 w-4 mr-2" />Визиты</TabsTrigger>
          <TabsTrigger value="messages"><MessageSquare className="h-4 w-4 mr-2" />Сообщения</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <Card>
            <CardHeader>
              <CardTitle>Контактные данные</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-lg bg-blue-500/10 text-blue-600 dark:text-blue-400 flex items-center justify-center">
                  <Phone className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Телефон</div>
                  <div className="font-medium">{client.phone}</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-lg bg-violet-500/10 text-violet-600 dark:text-violet-400 flex items-center justify-center">
                  <Mail className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Email</div>
                  <div className="font-medium">{client.email ?? "—"}</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-lg bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 flex items-center justify-center">
                  <Calendar className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">Дата рождения</div>
                  <div className="font-medium">{formatDateLong(client.birth_date)}</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-lg bg-amber-500/10 text-amber-600 dark:text-amber-400 flex items-center justify-center">
                  <MessageSquare className="h-4 w-4" />
                </div>
                <div>
                  <div className="text-xs text-muted-foreground">WhatsApp</div>
                  <div className="font-medium">{client.whatsapp_opted_in ? "Разрешён" : "Не подтверждён"}</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="cars">
          <Card><CardContent className="py-12 text-center text-muted-foreground">Автомобили скоро появятся</CardContent></Card>
        </TabsContent>
        <TabsContent value="visits">
          <Card><CardContent className="py-12 text-center text-muted-foreground">История визитов скоро появится</CardContent></Card>
        </TabsContent>
        <TabsContent value="messages">
          <Card><CardContent className="py-12 text-center text-muted-foreground">Диалоги по этому клиенту скоро появятся</CardContent></Card>
        </TabsContent>
      </Tabs>

      <ClientFormDialog open={editOpen} onOpenChange={setEditOpen} client={client} />

      <AlertDialog open={confirmOpen} onOpenChange={setConfirmOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить клиента?</AlertDialogTitle>
            <AlertDialogDescription>
              «{client.full_name}» будет удалён. Действие можно отменить, обратившись в поддержку.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={del.isPending}>Отмена</AlertDialogCancel>
            <AlertDialogAction
              disabled={del.isPending}
              onClick={(e) => {
                e.preventDefault();
                del.mutate(undefined, { onSuccess: () => setConfirmOpen(false) });
              }}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {del.isPending ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
              Удалить
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
