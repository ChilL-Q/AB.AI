"use client";

import { useEffect, useRef, useState } from "react";
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
import type { Car, Visit } from "@/types";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  clientId: string;
  cars: Car[];
  visit?: Visit | null;
};

export function VisitFormDialog({ open, onOpenChange, clientId, cars, visit }: Props) {
  const qc = useQueryClient();
  const isEdit = !!visit;

  const [carId, setCarId] = useState("");
  const [visitedAt, setVisitedAt] = useState("");
  const [totalAmount, setTotalAmount] = useState("");
  const [serviceName, setServiceName] = useState("");
  const [servicePrice, setServicePrice] = useState("");
  const [services, setServices] = useState<{ name: string; price: string }[]>([]);
  const [notes, setNotes] = useState("");
  const [error, setError] = useState<string | null>(null);

  const wasOpen = useRef(false);
  const visitRef = useRef(visit);
  visitRef.current = visit;
  useEffect(() => {
    if (open && !wasOpen.current) {
      const v = visitRef.current;
      setCarId(v?.car_id ?? "");
      setVisitedAt(v?.visited_at?.slice(0, 16) ?? new Date().toISOString().slice(0, 16));
      setTotalAmount(v?.total_amount ?? "");
      setServices(v?.services ?? []);
      setNotes(v?.notes ?? "");
      setError(null);
    }
    wasOpen.current = open;
  }, [open]);

  const addService = () => {
    if (!serviceName.trim()) return;
    setServices([...services, { name: serviceName, price: servicePrice || "0" }]);
    setServiceName("");
    setServicePrice("");
  };

  const removeService = (idx: number) => {
    setServices(services.filter((_, i) => i !== idx));
  };

  const mutation = useMutation({
    mutationFn: async () => {
      const body = {
        client_id: clientId,
        car_id: carId || null,
        visited_at: new Date(visitedAt).toISOString(),
        total_amount: totalAmount || "0",
        services,
        notes: notes || null,
        source: "manual",
      };
      if (isEdit && visit) {
        const { data } = await api.patch<Visit>(`/visits/${visit.id}`, body);
        return data;
      }
      const { data } = await api.post<Visit>("/visits", body);
      return data;
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["visits", clientId] });
      await qc.invalidateQueries({ queryKey: ["client", clientId] });
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
          <DialogTitle>{isEdit ? "Редактировать визит" : "Новый визит"}</DialogTitle>
          <DialogDescription>
            {isEdit ? "Обновите данные визита" : "Добавьте визит клиенту"}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          {cars.length > 0 && (
            <div className="space-y-2">
              <Label htmlFor="visit-car">Автомобиль</Label>
              <select
                id="visit-car"
                className="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-xs"
                value={carId}
                onChange={(e) => setCarId(e.target.value)}
              >
                <option value="">Не указан</option>
                {cars.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.brand} {c.model} {c.license_plate ? `(${c.license_plate})` : ""}
                  </option>
                ))}
              </select>
            </div>
          )}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="visit-date">Дата визита</Label>
              <Input
                id="visit-date"
                type="datetime-local"
                value={visitedAt}
                onChange={(e) => setVisitedAt(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="visit-amount">Сумма (₸)</Label>
              <Input
                id="visit-amount"
                type="number"
                value={totalAmount}
                onChange={(e) => setTotalAmount(e.target.value)}
              />
            </div>
          </div>
          <div className="space-y-2">
            <Label>Услуги</Label>
            {services.length > 0 && (
              <div className="space-y-1">
                {services.map((s, i) => (
                  <div key={i} className="flex items-center gap-2 text-sm">
                    <span className="flex-1">{s.name}</span>
                    <span className="text-muted-foreground">{s.price} ₸</span>
                    <Button type="button" variant="ghost" size="sm" onClick={() => removeService(i)}>
                      ×
                    </Button>
                  </div>
                ))}
              </div>
            )}
            <div className="flex gap-2">
              <Input
                placeholder="Название услуги"
                value={serviceName}
                onChange={(e) => setServiceName(e.target.value)}
              />
              <Input
                placeholder="Цена"
                type="number"
                className="w-24"
                value={servicePrice}
                onChange={(e) => setServicePrice(e.target.value)}
              />
              <Button type="button" variant="outline" onClick={addService}>
                +
              </Button>
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="visit-notes">Заметки</Label>
            <Input id="visit-notes" value={notes} onChange={(e) => setNotes(e.target.value)} />
          </div>
          {error && <p className="text-sm text-destructive">{error}</p>}
          <DialogFooter className="gap-2">
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Отмена
            </Button>
            <Button type="submit" disabled={mutation.isPending}>
              {mutation.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {isEdit ? "Сохранить" : "Добавить"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}