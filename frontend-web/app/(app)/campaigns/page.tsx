"use client";

import { useState } from "react";
import { keepPreviousData, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Loader2, Megaphone, Pencil, Trash2, Play, Pause } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CampaignFormDialog } from "@/components/campaign-form-dialog";
import type { Campaign, Template, PaginatedResponse } from "@/types";

const TYPE_LABELS: Record<string, string> = {
  one_time: "Разовая",
  recurring: "Регулярная",
  triggered: "По событию",
};

const STATUS_STYLES: Record<string, { variant: "default" | "success" | "warning" | "outline"; label: string }> = {
  draft: { variant: "outline", label: "Черновик" },
  running: { variant: "success", label: "Запущена" },
  paused: { variant: "warning", label: "На паузе" },
  completed: { variant: "default", label: "Завершена" },
  archived: { variant: "outline", label: "Архив" },
};

const LIMIT = 25;

export default function CampaignsPage() {
  const [page, setPage] = useState(1);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editCampaign, setEditCampaign] = useState<Campaign | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const qc = useQueryClient();

  const { data, isLoading, isFetching, error } = useQuery({
    queryKey: ["campaigns", { page }],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Campaign>>("/campaigns", {
        params: { page, limit: LIMIT },
      });
      return data;
    },
    placeholderData: keepPreviousData,
  });

  const { data: templatesData } = useQuery({
    queryKey: ["templates"],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Template>>("/templates", {
        params: { limit: 100 },
      });
      return data;
    },
  });

  const templates = templatesData?.data ?? [];
  const campaigns = data?.data ?? [];
  const total = data?.meta.total ?? 0;
  const hasNext = data?.meta.has_next ?? false;

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/campaigns/${id}`);
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["campaigns"] });
      setDeleteId(null);
    },
  });

  const statusMutation = useMutation({
    mutationFn: async ({ id, status }: { id: string; status: string }) => {
      await api.patch(`/campaigns/${id}`, { status });
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["campaigns"] });
    },
  });

  const runMutation = useMutation({
    mutationFn: async (id: string) => {
      const { data } = await api.post<Campaign>(`/campaigns/${id}/run`);
      return data;
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["campaigns"] });
    },
  });

  const openEdit = (c: Campaign) => {
    setEditCampaign(c);
    setDialogOpen(true);
  };

  const openCreate = () => {
    setEditCampaign(null);
    setDialogOpen(true);
  };

  const toggleStatus = (c: Campaign) => {
    if (c.status === "draft" || c.status === "paused") {
      runMutation.mutate(c.id);
    } else if (c.status === "running") {
      statusMutation.mutate({ id: c.id, status: "paused" });
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight">Кампании</h2>
          <p className="text-muted-foreground">
            {total > 0 ? `${total} кампаний` : "Управление outreach-кампаниями"}
          </p>
        </div>
        <Button onClick={openCreate} className="brand-gradient brand-gradient-text brand-shadow-sm rounded-xl">
          <Plus className="h-4 w-4 mr-2" />Новая кампания
        </Button>
      </div>

      <Card className="border-0 shadow-sm">
        <CardContent className="p-0">
          {isLoading ? (
            <div className="py-16 flex justify-center">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : error ? (
            <div className="py-16 text-center text-sm text-muted-foreground">
              Не удалось загрузить кампании. Попробуйте позже.
            </div>
          ) : campaigns.length === 0 ? (
            <div className="py-16 text-center space-y-3">
              <Megaphone className="h-10 w-10 text-muted-foreground/30 mx-auto" />
              <p className="text-muted-foreground">Кампаний пока нет</p>
              <Button variant="outline" onClick={openCreate}>
                <Plus className="h-4 w-4 mr-2" />Создать первую кампанию
              </Button>
            </div>
          ) : (
            <div className="divide-y">
              {campaigns.map((c) => {
                const st = STATUS_STYLES[c.status] ?? STATUS_STYLES.draft;
                return (
                  <div key={c.id} className="flex items-start gap-4 p-4 hover:bg-muted/30 transition-colors">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium text-sm truncate">{c.name}</h3>
                        <Badge variant={st.variant}>{st.label}</Badge>
                        <Badge variant="outline" className="text-xs">
                          {TYPE_LABELS[c.type] ?? c.type}
                        </Badge>
                        {c.channels.map((ch) => (
                          <Badge key={ch} className="text-xs capitalize">{ch}</Badge>
                        ))}
                      </div>
                      {c.description && (
                        <p className="text-sm text-muted-foreground line-clamp-1">{c.description}</p>
                      )}
                      {Boolean(c.stats.sent || c.stats.replied) && (
                        <div className="flex gap-4 mt-1 text-xs text-muted-foreground">
                          {Boolean(c.stats.sent) && <span>Отправлено: {Number(c.stats.sent)}</span>}
                          {Boolean(c.stats.replied) && <span>Ответов: {Number(c.stats.replied)}</span>}
                        </div>
                      )}
                    </div>
                    <div className="flex items-center gap-1 shrink-0">
                      {(c.status === "draft" || c.status === "paused" || c.status === "running") && (
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8"
                          onClick={() => toggleStatus(c)}
                          title={c.status === "running" ? "Пауза" : "Запустить"}
                        >
                          {c.status === "running" ? (
                            <Pause className="h-3.5 w-3.5" />
                          ) : (
                            <Play className="h-3.5 w-3.5" />
                          )}
                        </Button>
                      )}
                      <Button variant="ghost" size="icon" className="h-8 w-8" onClick={() => openEdit(c)} title="Редактировать">
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-8 w-8 text-destructive hover:text-destructive"
                        onClick={() => setDeleteId(c.id)}
                        title="Удалить"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {total > LIMIT && (
            <div className="flex items-center justify-between p-4 border-t">
              <p className="text-sm text-muted-foreground">
                Страница {page} · показано {campaigns.length} из {total}
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
          {isFetching && !isLoading && (
            <div className="flex justify-center py-2">
              <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
            </div>
          )}
        </CardContent>
      </Card>

      <CampaignFormDialog
        open={dialogOpen}
        onOpenChange={(open) => {
          setDialogOpen(open);
          if (!open) setEditCampaign(null);
        }}
        campaign={editCampaign}
        templates={templates}
      />

      {deleteId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={() => setDeleteId(null)}>
          <div className="bg-card rounded-xl p-6 shadow-lg max-w-sm w-full mx-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-semibold mb-2">Удалить кампанию?</h3>
            <p className="text-sm text-muted-foreground mb-4">Это действие нельзя отменить.</p>
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