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
import type { Template } from "@/types";

const CATEGORIES = [
  { value: "retention", label: "Удержание" },
  { value: "reminder", label: "Напоминание" },
  { value: "promotion", label: "Акция" },
  { value: "greeting", label: "Приветствие" },
  { value: "feedback", label: "Обратная связь" },
];

const CHANNELS = [
  { value: "whatsapp", label: "WhatsApp" },
  { value: "telegram", label: "Telegram" },
  { value: "sms", label: "SMS" },
];

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  template?: Template | null;
  onCreated?: () => void;
};

export function TemplateFormDialog({ open, onOpenChange, template, onCreated }: Props) {
  const qc = useQueryClient();
  const isEdit = !!template;

  const [name, setName] = useState("");
  const [category, setCategory] = useState("retention");
  const [content, setContent] = useState("");
  const [selectedChannels, setSelectedChannels] = useState<string[]>(["whatsapp"]);
  const [error, setError] = useState<string | null>(null);

  const wasOpen = useRef(false);
  const templateRef = useRef(template);
  templateRef.current = template;
  useEffect(() => {
    if (open && !wasOpen.current) {
      const t = templateRef.current;
      setName(t?.name ?? "");
      setCategory(t?.category ?? "retention");
      setContent(t?.content ?? "");
      setSelectedChannels(t?.channels ?? ["whatsapp"]);
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
      const body = { name, category, content, channels: selectedChannels };
      if (isEdit && template) {
        const { data } = await api.patch<Template>(`/templates/${template.id}`, body);
        return data;
      }
      const { data } = await api.post<Template>("/templates", body);
      return data;
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["templates"] });
      if (template) await qc.invalidateQueries({ queryKey: ["template", template.id] });
      if (!isEdit) onCreated?.();
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
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? "Редактировать шаблон" : "Новый шаблон"}</DialogTitle>
          <DialogDescription>
            {isEdit ? "Обновите данные шаблона" : "Шаблон сообщения для outreach и кампаний"}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="t-name">Название</Label>
            <Input
              id="t-name"
              placeholder="Например: Напоминание о замене масла"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="t-category">Категория</Label>
            <select
              id="t-category"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              className="flex h-9 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              {CATEGORIES.map((c) => (
                <option key={c.value} value={c.value}>{c.label}</option>
              ))}
            </select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="t-content">Текст сообщения</Label>
            <Textarea
              id="t-content"
              placeholder="Привет, {name}! Пора заменить масло. Записать на {date}?"
              value={content}
              onChange={(e) => setContent(e.target.value)}
              required
              rows={5}
            />
            <p className="text-xs text-muted-foreground">
              Переменные: {"{name}"}, {"{car}"}, {"{service}"}, {"{date}"}
            </p>
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