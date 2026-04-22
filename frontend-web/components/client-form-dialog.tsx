"use client";

import { useEffect, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { Client } from "@/types";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  client?: Client | null;
};

export function ClientFormDialog({ open, onOpenChange, client }: Props) {
  const qc = useQueryClient();
  const isEdit = !!client;

  const [fullName, setFullName] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [tags, setTags] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setFullName(client?.full_name ?? "");
      setPhone(client?.phone ?? "");
      setEmail(client?.email ?? "");
      setTags((client?.tags ?? []).join(", "));
      setError(null);
    }
  }, [open, client]);

  const mutation = useMutation({
    mutationFn: async () => {
      const body = {
        full_name: fullName,
        phone,
        email: email || null,
        tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
      };
      if (isEdit && client) {
        const { data } = await api.patch<Client>(`/clients/${client.id}`, body);
        return data;
      }
      const { data } = await api.post<Client>("/clients", body);
      return data;
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["clients"] });
      if (client) await qc.invalidateQueries({ queryKey: ["client", client.id] });
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
          <DialogTitle>{isEdit ? "Редактировать клиента" : "Новый клиент"}</DialogTitle>
          <DialogDescription>
            {isEdit ? "Обновите данные клиента" : "Добавьте клиента вручную"}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="c-name">Имя</Label>
            <Input id="c-name" value={fullName} onChange={(e) => setFullName(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="c-phone">Телефон</Label>
            <Input
              id="c-phone"
              type="tel"
              placeholder="+7 777 123 45 67"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
              minLength={7}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="c-email">Email (необязательно)</Label>
            <Input
              id="c-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="c-tags">Тэги (через запятую)</Label>
            <Input
              id="c-tags"
              placeholder="vip, регулярный"
              value={tags}
              onChange={(e) => setTags(e.target.value)}
            />
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
