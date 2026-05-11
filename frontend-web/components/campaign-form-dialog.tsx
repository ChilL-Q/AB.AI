"use client";

import { useEffect, useRef, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { Campaign, Template } from "@/types";

const CAMPAIGN_TYPES = [
  { value: "one_time", label: "Разовая" },
  { value: "recurring", label: "Регулярная" },
  { value: "triggered", label: "По событию" },
];

const CHANNELS = [
  { value: "whatsapp", label: "WhatsApp" },
  { value: "telegram", label: "Telegram" },
  { value: "sms", label: "SMS" },
];

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  campaign?: Campaign | null;
  templates: Template[];
};

export function CampaignFormDialog({ open, onOpenChange, campaign, templates }: Props) {
  const qc = useQueryClient();
  const isEdit = !!campaign;

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [type, setType] = useState<Campaign["type"]>("one_time");
  const [selectedChannels, setSelectedChannels] = useState<string[]>(["whatsapp"]);
  const [templateId, setTemplateId] = useState("");
  const [error, setError] = useState<string | null>(null);

  const wasOpen = useRef(false);
  const campaignRef = useRef(campaign);
  campaignRef.current = campaign;
  useEffect(() => {
    if (open && !wasOpen.current) {
      const c = campaignRef.current;
      setName(c?.name ?? "");
      setDescription(c?.description ?? "");
      setType(c?.type ?? "one_time");
      setSelectedChannels(c?.channels ?? ["whatsapp"]);
      setTemplateId(c?.template_id ?? "");
      setError(null);
    }
    wasOpen.current = open;
  }, [open]);

  const toggleChannel = (ch: string) => {
    setSelectedChannels((prev) =>
      prev.includes(ch) ? prev.filter((c) => c !== ch) : [...prev, ch],
    );
  };

  const mutation = useMutation({
    mutationFn: async () => {
      const body = {
        name,
        description: description || null,
        type,
        channels: selectedChannels,
        template_id: templateId || null,
      };
      if (isEdit && campaign) {
        const { data } = await api.patch<Campaign>(`/campaigns/${campaign.id}`, body);
        return data;
      }
      const { data } = await api.post<Campaign>("/campaigns", body);
      return data;
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["campaigns"] });
      if (campaign) await qc.invalidateQueries({ queryKey: ["campaign", campaign.id] });
      onOpenChange(false);
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(msg ?? "Ошибка сохранения");
    },
  });

  const onSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    mutation.mutate();
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Редактировать кампанию" : "Новая кампания"}</DialogTitle>
          <DialogDescription>
            {isEdit ? "Обновите параметры кампании" : "Настройте кампанию для outreach'а"}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="c-name">Название</Label>
            <Input
              id="c-name"
              placeholder="Например: Напоминание о ТО"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="c-desc">Описание</Label>
            <Textarea
              id="c-desc"
              placeholder="Краткое описание кампании..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="c-type">Тип</Label>
            <select
              id="c-type"
              value={type}
              onChange={(e) => setType(e.target.value as Campaign["type"])}
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {CAMPAIGN_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label>Каналы</Label>
            <div className="flex gap-2 flex-wrap">
              {CHANNELS.map((ch) => (
                <button
                  key={ch.value}
                  type="button"
                  onClick={() => toggleChannel(ch.value)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    selectedChannels.includes(ch.value)
                      ? "bg-primary text-primary-foreground"
                      : "bg-secondary text-muted-foreground hover:bg-muted"
                  }`}
                >
                  {ch.label}
                </button>
              ))}
            </div>
          </div>

          {templates.length > 0 && (
            <div className="space-y-2">
              <Label htmlFor="c-template">Шаблон</Label>
              <select
                id="c-template"
                value={templateId}
                onChange={(e) => setTemplateId(e.target.value)}
                className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              >
                <option value="">Без шаблона</option>
                {templates.map((t) => (
                  <option key={t.id} value={t.id}>{t.name}</option>
                ))}
              </select>
            </div>
          )}

          {error && <p className="text-sm text-destructive">{error}</p>}
          <DialogFooter className="gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Отмена
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {isEdit ? "Сохранить" : "Создать"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}