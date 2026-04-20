import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AB AI — платформа для автосервисов",
  description: "Удержание клиентов через AI-агентов в WhatsApp и Telegram",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru">
      <body>{children}</body>
    </html>
  );
}
