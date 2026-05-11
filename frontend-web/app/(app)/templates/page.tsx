"use client";

import { useState } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Search, Loader2, Pencil, Trash2, FileText } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { TemplateFormDialog } from "@/components/template-form-dialog";
import type { Template, PaginatedResponse } from "@/types";

const CATEGORY_LABELS: Record<string, string> = {
  retention: "Удержание",
  reminder: "Напоминание",
  promotion: "Акция",
  greeting: "Приветствие",
  feedback: "Обратная связь",
};

const LIMIT = 25;

export default function TemplatesPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editTemplate, setEditTemplate] = useState<Template | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const qc = useQueryClient();

  const { data, isLoading, isFetching, error } = useQuery({
    queryKey: ["templates", { page }],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Template>>("/templates", {
        params: { page, limit: LIMIT },
      });
      return data;
    },
    placeholderData: keepPreviousData,
  });

  const templates = data?.data ?? [];
  const total = data?.meta.total ?? 0;
  const hasNext = data?.meta.has_next ?? false;

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/templates/${id}`);
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["templates"] });
      setDeleteId(null);
    },
  });

  const filtered = search
    ? templates.filter(
        (t) =>
          t.name.toLowerCase().includes(search.toLowerCase()) ||
          t.content.toLowerCase().includes(search.toLowerCase()) ||
          CATEGORY_LABELS[t.category]?.toLowerCase().includes(search.toLowerCase()),
      )
    : templates;

  const openEdit = (t: Template) => {
    setEditTemplate(t);
    setDialogOpen(true);
  };

  const openCreate = () => {
    setEditTemplate(null);
    setDialogOpen(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Шаблоны</h2>
          <p className="text-muted-foreground">
            {total > 0 ? `${total} шаблонов` : "Шаблоны сообщений для outreach и кампаний"}
          </p>
        </div>
        <Button onClick={openCreate} className="brand-gradient brand-gradient-text brand-shadow-sm rounded-xl">
          <Plus className="h-4 w-4 mr-2" />Новый шаблон
        </Button>
      </div>

      <Card className="border-0 shadow-sm">
        <CardContent className="p-0">
          <div className="flex items-center gap-2 p-4 border-b">
            <div className="relative flex-1 max-w-md">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <Input
                placeholder="Поиск шаблонов..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-9 h-8 text-sm bg-muted/50 border-0 focus-visible:ring-1"
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
              Не удалось загрузить шаблоны. Попробуйте позже.
            </div>
          ) : filtered.length === 0 ? (
            <div className="py-16 text-center space-y-3">
              <FileText className="h-10 w-10 text-muted-foreground/30 mx-auto" />
              <p className="text-muted-foreground">
                {search ? "По запросу ничего не найдено" : "Шаблонов пока нет"}
              </p>
              {!search && (
                <Button variant="outline" onClick={openCreate}>
                  <Plus className="h-4 w-4 mr-2" />Создать первый шаблон
                </Button>
              )}
            </div>
          ) : (
            <div className="divide-y">
              {filtered.map((t) => (
                <div
                  key={t.id}
                  className="flex items-start gap-4 p-4 hover:bg-muted/30 transition-colors"
                >
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-medium text-sm truncate">{t.name}</h3>
                      <Badge variant="outline" className="text-xs shrink-0">
                        {CATEGORY_LABELS[t.category] ?? t.category}
                      </Badge>
                      {t.team_id === null && (
                        <Badge className="text-xs shrink-0 bg-muted text-muted-foreground">
                          Системный
                        </Badge>
                      )}
                      {t.channels.map((ch) => (
                        <Badge key={ch} className="text-xs shrink-0 capitalize">
                          {ch}
                        </Badge>
                      ))}
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-2">{t.content}</p>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => openEdit(t)}
                      title="Редактировать"
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                    {t.team_id !== null && (
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-destructive hover:text-destructive"
                        onClick={() => setDeleteId(t.id)}
                        title="Удалить"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {!isLoading && total > LIMIT && (
            <div className="flex items-center justify-between p-4 border-t">
              <p className="text-sm text-muted-foreground">
                Страница {page} · показано {filtered.length} из {total}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 w-8 p-0 rounded-lg"
                  disabled={page === 1}
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                >
                  ‹
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="h-8 w-8 p-0 rounded-lg"
                  disabled={!hasNext}
                  onClick={() => setPage((p) => p + 1)}
                >
                  ›
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      <TemplateFormDialog
        open={dialogOpen}
        onOpenChange={(open) => {
          setDialogOpen(open);
          if (!open) setEditTemplate(null);
        }}
        template={editTemplate}
        onCreated={() => setPage(1)}
      />

      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setDeleteId(null)}>
          <div className="bg-card rounded-xl p-6 shadow-lg max-w-sm w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-semibold mb-2">Удалить шаблон?</h3>
            <p className="text-sm text-muted-foreground mb-4">
              Это действие нельзя отменить.
            </p>
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => setDeleteId(null)}>Отмена</Button>
              <Button
                variant="destructive"
                disabled={deleteMutation.isPending}
                onClick={() => deleteMutation.mutate(deleteId)}
              >
                {deleteMutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
                Удалить
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}