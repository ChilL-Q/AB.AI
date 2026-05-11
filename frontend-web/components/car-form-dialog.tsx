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
import type { Car } from "@/types";

type Props = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  clientId: string;
  car?: Car | null;
};

export function CarFormDialog({ open, onOpenChange, clientId, car }: Props) {
  const qc = useQueryClient();
  const isEdit = !!car;

  const [brand, setBrand] = useState("");
  const [model, setModel] = useState("");
  const [year, setYear] = useState("");
  const [color, setColor] = useState("");
  const [licensePlate, setLicensePlate] = useState("");
  const [vin, setVin] = useState("");
  const [mileage, setMileage] = useState("");
  const [error, setError] = useState<string | null>(null);

  const wasOpen = useRef(false);
  const carRef = useRef(car);
  carRef.current = car;
  useEffect(() => {
    if (open && !wasOpen.current) {
      const c = carRef.current;
      setBrand(c?.brand ?? "");
      setModel(c?.model ?? "");
      setYear(c?.year?.toString() ?? "");
      setColor(c?.color ?? "");
      setLicensePlate(c?.license_plate ?? "");
      setVin(c?.vin ?? "");
      setMileage(c?.mileage?.toString() ?? "");
      setError(null);
    }
    wasOpen.current = open;
  }, [open]);

  const mutation = useMutation({
    mutationFn: async () => {
      const body = {
        brand,
        model,
        year: year ? Number(year) : null,
        color: color || null,
        license_plate: licensePlate || null,
        vin: vin || null,
        mileage: mileage ? Number(mileage) : null,
      };
      if (isEdit && car) {
        const { data } = await api.patch<Car>(`/cars/${car.id}`, body);
        return data;
      }
      const { data } = await api.post<Car>(`/cars/client/${clientId}`, body);
      return data;
    },
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["cars", clientId] });
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
          <DialogTitle>{isEdit ? "Редактировать автомобиль" : "Новый автомобиль"}</DialogTitle>
          <DialogDescription>
            {isEdit ? "Обновите данные автомобиля" : "Добавьте автомобиль клиенту"}
          </DialogDescription>
        </DialogHeader>
        <form onSubmit={onSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="car-brand">Марка</Label>
            <Input id="car-brand" value={brand} onChange={(e) => setBrand(e.target.value)} required />
          </div>
          <div className="space-y-2">
            <Label htmlFor="car-model">Модель</Label>
            <Input id="car-model" value={model} onChange={(e) => setModel(e.target.value)} required />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="car-year">Год</Label>
              <Input id="car-year" type="number" value={year} onChange={(e) => setYear(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="car-color">Цвет</Label>
              <Input id="car-color" value={color} onChange={(e) => setColor(e.target.value)} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-2">
              <Label htmlFor="car-plate">Гос. номер</Label>
              <Input id="car-plate" value={licensePlate} onChange={(e) => setLicensePlate(e.target.value)} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="car-vin">VIN</Label>
              <Input id="car-vin" maxLength={17} value={vin} onChange={(e) => setVin(e.target.value)} />
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="car-mileage">Пробег (км)</Label>
            <Input id="car-mileage" type="number" value={mileage} onChange={(e) => setMileage(e.target.value)} />
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