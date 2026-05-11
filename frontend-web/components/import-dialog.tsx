"use client";

import { useState, useRef } from "react";
import { Upload, FileSpreadsheet, X, Loader2, CheckCircle2, AlertTriangle } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import type { ImportLog } from "@/types";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onImported: () => void;
}

type Step = "upload" | "processing" | "done";

export function ImportDialog({ open, onOpenChange, onImported }: Props) {
  const [step, setStep] = useState<Step>("upload");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ImportLog | null>(null);
  const [error, setError] = useState("");
  const inputRef = useRef<HTMLInputElement>(null);

  const reset = () => {
    setStep("upload");
    setFile(null);
    setResult(null);
    setError("");
  };

  const handleUpload = async () => {
    if (!file) return;
    setStep("processing");
    setError("");
    const formData = new FormData();
    formData.append("file", file);
    try {
      const { data } = await api.post<ImportLog>("/imports/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(data);
      setStep("done");
      onImported();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Ошибка при импорте";
      setError(msg);
      setStep("upload");
    }
  };

  return (
    <Dialog open={open} onOpenChange={(v) => { if (!v) reset(); onOpenChange(v); }}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Импорт клиентов</DialogTitle>
          <DialogDescription>
            Загрузите CSV или XLSX файл со списком клиентов
          </DialogDescription>
        </DialogHeader>

        {step === "upload" && (
          <div className="space-y-4">
            <div
              className="border-2 border-dashed rounded-xl p-8 text-center cursor-pointer hover:border-amber-400 hover:bg-amber-50/50 transition-colors"
              onClick={() => inputRef.current?.click()}
            >
              <Upload className="h-8 w-8 mx-auto mb-3 text-muted-foreground" />
              <p className="text-sm font-medium">
                {file ? file.name : "Нажмите или перетащите файл"}
              </p>
              <p className="text-xs text-muted-foreground mt-1">
                CSV или XLSX, макс. 10 МБ
              </p>
            </div>
            <input
              ref={inputRef}
              type="file"
              accept=".csv,.xlsx"
              className="hidden"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) setFile(f);
              }}
            />
            {file && (
              <div className="flex items-center gap-2 p-3 bg-muted rounded-lg">
                <FileSpreadsheet className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm flex-1 truncate">{file.name}</span>
                <button onClick={() => setFile(null)} className="text-muted-foreground hover:text-foreground">
                  <X className="h-4 w-4" />
                </button>
              </div>
            )}
            <div className="text-xs text-muted-foreground space-y-1">
              <p>Обязательные колонки: <strong>full_name</strong>, <strong>phone</strong></p>
              <p>Дополнительные: email, birth_date, tags, telegram_username, total_visits, total_spent, last_visit_at</p>
            </div>
            {error && <p className="text-sm text-destructive">{error}</p>}
            <div className="flex justify-end gap-2">
              <Button variant="outline" onClick={() => { reset(); onOpenChange(false); }}>
                Отмена
              </Button>
              <Button onClick={handleUpload} disabled={!file} className="brand-gradient brand-gradient-text">
                Импортировать
              </Button>
            </div>
          </div>
        )}

        {step === "processing" && (
          <div className="py-12 flex flex-col items-center gap-3">
            <Loader2 className="h-8 w-8 animate-spin text-amber-500" />
            <p className="text-sm text-muted-foreground">Импортируем клиентов...</p>
          </div>
        )}

        {step === "done" && result && (
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-green-600">
              <CheckCircle2 className="h-5 w-5" />
              <span className="font-medium">Импорт завершён</span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="p-3 bg-muted rounded-lg">
                <p className="text-muted-foreground">Всего строк</p>
                <p className="text-lg font-semibold">{result.rows_total}</p>
              </div>
              <div className="p-3 bg-green-50 rounded-lg">
                <p className="text-green-700">Импортировано</p>
                <p className="text-lg font-semibold text-green-700">{result.rows_imported}</p>
              </div>
              <div className="p-3 bg-amber-50 rounded-lg">
                <p className="text-amber-700">Пропущено (дубли)</p>
                <p className="text-lg font-semibold text-amber-700">{result.rows_skipped}</p>
              </div>
              <div className="p-3 bg-red-50 rounded-lg">
                <p className="text-red-700">Ошибок</p>
                <p className="text-lg font-semibold text-red-700">{result.rows_failed}</p>
              </div>
            </div>
            {result.errors.length > 0 && (
              <div className="max-h-40 overflow-y-auto border rounded-lg p-3 text-xs space-y-1">
                <p className="font-medium text-destructive flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3" /> Ошибки:
                </p>
                {result.errors.slice(0, 20).map((e, i) => (
                  <p key={i} className="text-muted-foreground">
                    Строка {e.row}: {e.reason} {e.phone && `(${e.phone})`}
                  </p>
                ))}
                {result.errors.length > 20 && (
                  <p className="text-muted-foreground">...и ещё {result.errors.length - 20} ошибок</p>
                )}
              </div>
            )}
            <div className="flex justify-end">
              <Button onClick={() => { reset(); onOpenChange(false); }} className="brand-gradient brand-gradient-text">
                Готово
              </Button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}