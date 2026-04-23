"use client";

import { useState } from "react";
import Link from "next/link";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { Plus, Search, Loader2, ChevronLeft, ChevronRight } from "lucide-react";
import { api } from "@/lib/api";
import { formatDateShort, formatMoney, formatPhone } from "@/lib/formatters";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ClientFormDialog } from "@/components/client-form-dialog";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import type { Client, PaginatedResponse } from "@/types";

const LIMIT = 25;

export default function ClientsPage() {
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 300);
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);

  const { data, isLoading, isFetching, error } = useQuery({
    queryKey: ["clients", { page, search: debouncedSearch }],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Client>>("/clients", {
        params: { page, limit: LIMIT, search: debouncedSearch || undefined },
      });
      return data;
    },
    placeholderData: keepPreviousData,
  });

  const clients = data?.data ?? [];
  const total = data?.meta.total ?? 0;
  const hasNext = data?.meta.has_next ?? false;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Клиенты</h2>
          <p className="text-muted-foreground">
            {total > 0 ? `Всего ${total} клиентов` : "Управление базой клиентов"}
          </p>
        </div>
        <Button onClick={() => setDialogOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />Добавить клиента
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <div className="flex items-center gap-2 p-4 border-b">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Имя, телефон или email..."
                value={search}
                onChange={(e) => {
                  setSearch(e.target.value);
                  setPage(1);
                }}
                className="pl-9"
              />
            </div>
            {isFetching && <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />}
          </div>

          {isLoading ? (
            <div className="py-16 flex justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="py-16 text-center text-sm text-muted-foreground">
              Не удалось загрузить список. Попробуйте позже.
            </div>
          ) : clients.length === 0 ? (
            <div className="py-16 text-center space-y-3">
              <p className="text-muted-foreground">
                {debouncedSearch ? "По запросу ничего не найдено" : "Клиентов пока нет"}
              </p>
              {!debouncedSearch && (
                <Button variant="outline" onClick={() => setDialogOpen(true)}>
                  <Plus className="h-4 w-4 mr-2" />Добавить первого клиента
                </Button>
              )}
            </div>
          ) : (
            <>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Имя</TableHead>
                    <TableHead>Телефон</TableHead>
                    <TableHead>Email</TableHead>
                    <TableHead>Тэги</TableHead>
                    <TableHead className="text-right">Визитов</TableHead>
                    <TableHead className="text-right">Потрачено</TableHead>
                    <TableHead>Последний визит</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {clients.map((c) => (
                    <TableRow key={c.id}>
                      <TableCell className="font-medium">
                        <Link href={`/clients/${c.id}`} className="block hover:underline">
                          {c.full_name}
                        </Link>
                      </TableCell>
                      <TableCell className="text-muted-foreground tabular-nums">
                        {formatPhone(c.phone)}
                      </TableCell>
                      <TableCell className="text-muted-foreground">{c.email ?? "—"}</TableCell>
                      <TableCell>
                        <div className="flex flex-wrap gap-1">
                          {c.tags.slice(0, 2).map((t) => (
                            <Badge key={t} variant="outline" className="text-xs">
                              {t}
                            </Badge>
                          ))}
                          {c.tags.length > 2 && (
                            <span className="text-xs text-muted-foreground">
                              +{c.tags.length - 2}
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-right tabular-nums">{c.total_visits}</TableCell>
                      <TableCell className="text-right tabular-nums">
                        {formatMoney(c.total_spent, { dashOnZero: true })}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {formatDateShort(c.last_visit_at)}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              <div className="flex items-center justify-between p-4 border-t">
                <p className="text-sm text-muted-foreground">
                  Страница {page} · показано {clients.length} из {total}
                </p>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={page === 1}
                    onClick={() => setPage((p) => Math.max(1, p - 1))}
                  >
                    <ChevronLeft className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    disabled={!hasNext}
                    onClick={() => setPage((p) => p + 1)}
                  >
                    <ChevronRight className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      <ClientFormDialog open={dialogOpen} onOpenChange={setDialogOpen} />
    </div>
  );
}
