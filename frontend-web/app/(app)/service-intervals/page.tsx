"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Loader2,
  Plus,
  Pencil,
  Trash2,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Wrench,
} from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
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
import type { ServiceInterval, ServiceIntervalUnit, DueService } from "@/types";

const UNIT_OPTIONS: { value: ServiceIntervalUnit; label: string }[] = [
  { value: "km", label: "км" },
  { value: "days", label: "дней" },
  { value: "months", label: "месяцев" },
];

const UNIT_LABELS: Record<ServiceIntervalUnit, string> = {
  km: "км",
  days: "дн.",
  months: "мес.",
};

function IntervalFormDialog({
  open,
  onOpenChange,
  interval,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  interval?: ServiceInterval | null;
}) {
  const qc = useQueryClient();
  const isEdit = !!interval;

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [intervalValue, setIntervalValue] = useState("");
  const [unit, setUnit] = useState<ServiceIntervalUnit>("km");
  const [isActive, setIsActive] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const resetAndOpen = () => {
    if (interval) {
      setName(interval.name);
      setDescription(interval.description ?? "");
      setIntervalValue(String(interval.interval_value));
      setUnit(interval.interval_unit);
      setIsActive(interval.is_active);
    } else {
      setName("");
      setDescription("");
      setIntervalValue("");
      setUnit("km");
      setIsActive(true);
    }
    setError(null);
  };

  const mutation = useMutation({
    mutationFn: async () => {
      const body = {
        name,
        description: description || null,
        interval_value: Number(intervalValue),
        interval_unit: unit,
        is_active: isActive,
      };
      if (isEdit && interval) {
        return (await api.patch<ServiceInterval>(`/service-intervals/${interval.id}`, body)).data;
      }
      return (await api.post<ServiceInterval>("/service-intervals", body)).data;
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["service-intervals"] });
      onOpenChange(false);
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } }).response?.data?.detail;
      setError(msg ?? "Ошибка сохранения");
    },
  });

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        if (v) resetAndOpen();
        onOpenChange(v);
      }}
    >
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{isEdit ? "Редактировать интервал" : "Новый интервал ТО"}</DialogTitle>
          <DialogDescription>
            {isEdit
              ? "Измените параметры сервисного интервала"
              : "Задайте правило периодического обслуживания"}
          </DialogDescription>
        </DialogHeader>
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setError(null);
            mutation.mutate();
          }}
          className="space-y-4"
        >
          <div className="space-y-2">
            <Label htmlFor="si-name">Название</Label>
            <Input
              id="si-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Замена масла, ТО-1,inspection..."
              required
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="si-desc">Описание (необязательно)</Label>
            <Input
              id="si-desc"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Краткое описание услуги"
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="si-value">Интервал</Label>
              <Input
                id="si-value"
                type="number"
                min={1}
                value={intervalValue}
                onChange={(e) => setIntervalValue(e.target.value)}
                placeholder="10000"
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="si-unit">Единица</Label>
              <select
                id="si-unit"
                value={unit}
                onChange={(e) => setUnit(e.target.value as ServiceIntervalUnit)}
                className="w-full h-9 rounded-md border bg-background px-3 text-sm"
              >
                {UNIT_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>
                    {o.label}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input
              id="si-active"
              type="checkbox"
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="h-4 w-4 rounded border-border accent-primary"
            />
            <Label htmlFor="si-active" className="text-sm font-normal cursor-pointer">
              Активно (AI будет напоминать клиентам)
            </Label>
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

export default function ServiceIntervalsPage() {
  const qc = useQueryClient();
  const [formOpen, setFormOpen] = useState(false);
  const [editing, setEditing] = useState<ServiceInterval | null>(null);
  const [deleteId, setDeleteId] = useState<string | null>(null);
  const [showDue, setShowDue] = useState(false);

  const { data: intervals, isLoading } = useQuery({
    queryKey: ["service-intervals"],
    queryFn: async () => (await api.get<ServiceInterval[]>("/service-intervals")).data,
  });

  const { data: dueServices, isLoading: dueLoading } = useQuery({
    queryKey: ["due-services"],
    queryFn: async () => (await api.get<DueService[]>("/service-intervals/due")).data,
    enabled: showDue,
  });

  const del = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/service-intervals/${id}`);
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["service-intervals"] });
      setDeleteId(null);
    },
  });

  const items = intervals ?? [];

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl brand-gradient flex items-center justify-center shrink-0">
            <Wrench className="h-5 w-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-semibold">Интервалы ТО</h1>
            <p className="text-sm text-muted-foreground">
              Правила периодического обслуживания для AI-напоминаний
            </p>
          </div>
        </div>
        <Button onClick={() => setFormOpen(true)} className="brand-gradient brand-gradient-text brand-shadow-sm rounded-xl">
          <Plus className="h-4 w-4 mr-2" />Добавить интервал
        </Button>
      </div>

      <Card className="border-0 shadow-sm">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Список интервалов</CardTitle>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setShowDue(!showDue)}
            className="text-primary"
          >
            <AlertTriangle className="h-4 w-4 mr-1" />
            {showDue ? "Скрыть просроченные" : "Просроченные ТО"}
            {showDue ? <ChevronUp className="h-4 w-4 ml-1" /> : <ChevronDown className="h-4 w-4 ml-1" />}
          </Button>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="py-12 flex justify-center">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : items.length === 0 ? (
            <div className="py-12 text-center">
              <p className="text-muted-foreground">Интервалы пока не заданы</p>
              <Button variant="outline" className="mt-3" onClick={() => setFormOpen(true)}>
                <Plus className="h-4 w-4 mr-2" />Создать первый интервал
              </Button>
            </div>
          ) : (
            <div className="divide-y">
              {items.map((si) => (
                <div key={si.id} className="flex items-center justify-between py-3">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{si.name}</span>
                      {!si.is_active && (
                        <Badge variant="outline" className="text-muted-foreground">
                          Выключено
                        </Badge>
                      )}
                    </div>
                    <div className="text-sm text-muted-foreground mt-0.5">
                      Каждые {si.interval_value.toLocaleString("ru-RU")}{" "}
                      {UNIT_LABELS[si.interval_unit]}
                      {si.description && ` — ${si.description}`}
                    </div>
                  </div>
                  <div className="flex gap-1 shrink-0 ml-4">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8"
                      onClick={() => {
                        setEditing(si);
                        setFormOpen(true);
                      }}
                    >
                      <Pencil className="h-3.5 w-3.5" />
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-destructive hover:text-destructive"
                      onClick={() => setDeleteId(si.id)}
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {showDue && (
        <Card className="border-0 shadow-sm">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-amber-500" />
              Просроченные обслуживания
            </CardTitle>
          </CardHeader>
          <CardContent>
            {dueLoading ? (
              <div className="py-8 flex justify-center">
                <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              </div>
            ) : (dueServices ?? []).length === 0 ? (
              <p className="text-center text-muted-foreground py-8">
                Нет просроченных обслуживаний
              </p>
            ) : (
              <div className="divide-y">
                {(dueServices ?? []).map((ds, i) => (
                  <div key={`${ds.client_id}-${ds.car_id}-${i}`} className="py-3">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{ds.client_name}</span>
                      <Badge variant="outline" className="bg-amber-100 text-amber-800 dark:bg-amber-900 dark:text-amber-200 border-amber-300">
                        {ds.service_name}
                      </Badge>
                    </div>
                    <div className="text-sm text-muted-foreground mt-0.5">
                      {ds.car_name} — {ds.reason}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <IntervalFormDialog
        open={formOpen}
        onOpenChange={(v) => {
          setFormOpen(v);
          if (!v) setEditing(null);
        }}
        interval={editing}
      />

      <AlertDialog open={!!deleteId} onOpenChange={(v) => { if (!v) setDeleteId(null); }}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Удалить интервал?</AlertDialogTitle>
            <AlertDialogDescription>
              AI больше не будет напоминать клиентам об этом обслуживании.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={del.isPending}>Отмена</AlertDialogCancel>
            <AlertDialogAction
              disabled={del.isPending}
              onClick={(e) => {
                e.preventDefault();
                if (deleteId) del.mutate(deleteId);
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