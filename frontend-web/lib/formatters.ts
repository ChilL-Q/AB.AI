/**
 * Shared formatters for dates, money, and phone numbers.
 * Locale: ru-RU. Currency: KZT (₸).
 */

/**
 * Format a numeric money value (accepts string from Decimal or number) as
 * thousand-separated integer with ₸ suffix. Returns "—" for zero/invalid.
 */
export function formatMoney(v: string | number, options: { dashOnZero?: boolean } = {}): string {
  const n = typeof v === "number" ? v : Number(v);
  if (!Number.isFinite(n)) return options.dashOnZero ? "—" : "0 ₸";
  if (n === 0 && options.dashOnZero) return "—";
  return new Intl.NumberFormat("ru-RU").format(Math.round(n)) + " ₸";
}

/**
 * Short date: "23 апр 2026".
 */
export function formatDateShort(d: string | null): string {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

/**
 * Long date: "23 апреля 2026".
 */
export function formatDateLong(d: string | null): string {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("ru-RU", {
    day: "2-digit",
    month: "long",
    year: "numeric",
  });
}

/**
 * Time/relative formatting used in chat lists: HH:MM for today,
 * weekday for this week, "DD MMM" older.
 */
export function formatTimeAgo(d: string | null): string {
  if (!d) return "";
  const date = new Date(d);
  const now = new Date();
  if (date.toDateString() === now.toDateString()) {
    return date.toLocaleTimeString("ru-RU", { hour: "2-digit", minute: "2-digit" });
  }
  const diffDays = (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24);
  if (diffDays < 7) return date.toLocaleDateString("ru-RU", { weekday: "short" });
  return date.toLocaleDateString("ru-RU", { day: "2-digit", month: "short" });
}

/**
 * Best-effort international phone formatting. Handles common cases for
 * CIS countries (KZ/RU: 11 digits, UZ: 12 digits with 998 prefix).
 * Returns input unchanged when format is unknown.
 */
export function formatPhone(p: string): string {
  const digits = p.replace(/\D/g, "");
  // +7/8 XXX XXX XX XX
  if (digits.length === 11 && (digits[0] === "7" || digits[0] === "8")) {
    return `+${digits[0]} ${digits.slice(1, 4)} ${digits.slice(4, 7)} ${digits.slice(7, 9)} ${digits.slice(9)}`;
  }
  // +998 XX XXX XX XX
  if (digits.length === 12 && digits.startsWith("998")) {
    return `+${digits.slice(0, 3)} ${digits.slice(3, 5)} ${digits.slice(5, 8)} ${digits.slice(8, 10)} ${digits.slice(10)}`;
  }
  return p;
}
