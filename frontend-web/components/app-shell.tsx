"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import {
  LayoutDashboard,
  Users,
  MessageSquare,
  Settings,
  LogOut,
  Megaphone,
  Bell,
  Sparkles,
  ChevronLeft,
  Search,
  FileText,
  Wrench,
} from "lucide-react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { auth } from "@/lib/auth";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useMe, initialsOf } from "@/hooks/use-me";
import { ThemeToggle } from "@/components/theme-toggle";
import type { Notification as NotificationType } from "@/types";

type NavItem = { href: string; label: string; icon: React.ComponentType<{ className?: string }> };

const NAV_MAIN: NavItem[] = [
  { href: "/dashboard", label: "Дашборд", icon: LayoutDashboard },
  { href: "/clients", label: "Клиенты", icon: Users },
  { href: "/conversations", label: "Диалоги", icon: MessageSquare },
  { href: "/templates", label: "Шаблоны", icon: FileText },
];

const NAV_GROWTH: NavItem[] = [
  { href: "/campaigns", label: "Кампании", icon: Megaphone },
  { href: "/ai-agent", label: "AI-агент", icon: Sparkles },
  { href: "/service-intervals", label: "Интервалы ТО", icon: Wrench },
];

const NAV_SYSTEM: NavItem[] = [
  { href: "/settings", label: "Настройки", icon: Settings },
];

function SidebarLink({ item, pathname, collapsed }: { item: NavItem; pathname: string; collapsed: boolean }) {
  const active = pathname === item.href || pathname.startsWith(item.href + "/");
  return (
    <Link
      href={item.href}
      className={cn(
        "group relative flex items-center gap-3 rounded-xl text-sm font-medium transition-all duration-200",
        collapsed ? "justify-center px-2 py-2.5" : "px-3 py-2.5",
        active
          ? "bg-primary/10 text-primary"
          : "text-muted-foreground hover:bg-secondary hover:text-foreground",
      )}
      title={collapsed ? item.label : undefined}
    >
      {active && (
        <span className="absolute left-0 top-1/2 -translate-y-1/2 h-5 w-1 rounded-r-full bg-primary" />
      )}
      <item.icon className={cn(
        "h-[18px] w-[18px] shrink-0 transition-colors",
        active ? "text-primary" : "text-muted-foreground group-hover:text-foreground",
      )} />
      {!collapsed && <span>{item.label}</span>}
      {active && !collapsed && (
        <span className="ml-auto h-1.5 w-1.5 rounded-full bg-primary" />
      )}
    </Link>
  );
}

function NotificationBell() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const { data: countData } = useQuery({
    queryKey: ["notifications-unread"],
    queryFn: async () => (await api.get<{ count: number }>("/notifications/unread-count")).data,
    refetchInterval: 30_000,
  });

  const { data: notifsData } = useQuery({
    queryKey: ["notifications", { unread_only: true }],
    queryFn: async () => (await api.get<{ data: NotificationType[] }>("/notifications", { params: { limit: 10, unread_only: open } })).data,
    enabled: open,
  });

  const markAllMutation = useMutation({
    mutationFn: async () => api.post("/notifications/mark-all-read"),
    onSuccess: async () => {
      await qc.invalidateQueries({ queryKey: ["notifications-unread"] });
      await qc.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    if (open) document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, [open]);

  const unread = countData?.count ?? 0;

  return (
    <div ref={ref} className="relative">
      <Button variant="ghost" size="icon" className="relative h-8 w-8" onClick={() => setOpen(!open)}>
        <Bell className="h-4 w-4" />
        {unread > 0 && (
          <span className="absolute top-1 right-1 min-w-[16px] h-4 flex items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground px-1">
            {unread > 9 ? "9+" : unread}
          </span>
        )}
      </Button>
      {open && (
        <div className="absolute right-0 top-full mt-2 w-80 bg-card border rounded-xl shadow-lg z-50 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 border-b">
            <h3 className="font-semibold text-sm">Уведомления</h3>
            {unread > 0 && (
              <button
                className="text-xs text-primary hover:underline"
                onClick={() => markAllMutation.mutate()}
                disabled={markAllMutation.isPending}
              >
                Прочитать все
              </button>
            )}
          </div>
          <div className="max-h-80 overflow-y-auto divide-y">
            {(notifsData?.data ?? []).length === 0 ? (
              <p className="text-sm text-muted-foreground text-center py-6">Нет новых уведомлений</p>
            ) : (
              (notifsData?.data ?? []).map((n) => (
                <div key={n.id} className="px-4 py-3 hover:bg-muted/50 transition-colors">
                  <p className="text-sm font-medium">{n.title}</p>
                  <p className="text-xs text-muted-foreground mt-0.5">{n.body}</p>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { data: me } = useMe();
  const isOnboarding = pathname.startsWith("/onboarding");
  const [collapsed, setCollapsed] = useState(false);

  useEffect(() => {
    if (!auth.isAuthed()) router.replace("/login");
  }, [router]);

  useEffect(() => {
    if (me && !me.team_id && !isOnboarding) router.replace("/onboarding");
  }, [me, isOnboarding, router]);

  const logout = () => {
    auth.clear();
    router.push("/login");
  };

  const currentLabel =
    [...NAV_MAIN, ...NAV_GROWTH, ...NAV_SYSTEM].find((n) => pathname.startsWith(n.href))?.label ?? "AB-AI.kz";

  // Onboarding layout
  if (isOnboarding) {
    return (
      <div className="min-h-screen bg-background">
        <header className="sticky top-0 z-30 h-14 border-b bg-card/80 backdrop-blur-xl flex items-center px-6">
          <span className="font-bold tracking-tight text-xl">
            <span className="text-primary">AB-</span><span className="text-muted-foreground">AI.kz</span>
          </span>
          <Button variant="ghost" size="sm" className="ml-auto" onClick={logout}>
            <LogOut className="h-4 w-4 mr-2" />Выйти
          </Button>
        </header>
        <main className="p-6 max-w-2xl mx-auto">{children}</main>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex bg-background">
      {/* ─── Sidebar ─── */}
      <aside className={cn(
        "sticky top-0 h-screen flex flex-col border-r bg-card transition-all duration-300 shrink-0",
        collapsed ? "w-[68px]" : "w-60",
      )}>
        {/* Logo */}
        <div className={cn(
          "h-16 flex items-center border-b shrink-0 transition-all duration-300",
          collapsed ? "justify-center px-2" : "px-4 gap-2.5",
        )}>
          <div className="h-9 w-9 rounded-xl brand-gradient flex items-center justify-center shrink-0">
            <span className="font-extrabold text-sm text-white tracking-tight">AB</span>
          </div>
          {!collapsed && (
            <div className="min-w-0">
              <span className="font-bold tracking-tight text-lg leading-none block">
                <span className="text-primary">AB-</span><span className="text-muted-foreground">AI.kz</span>
              </span>
              <p className="text-[10px] text-muted-foreground/50 leading-none mt-0.5">aqyldy business</p>
            </div>
          )}
        </div>

        {/* Nav sections */}
        <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-5">
          <div className="space-y-1">
            {!collapsed && <p className="px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/40 mb-1.5">Основное</p>}
            {NAV_MAIN.map((item) => (
              <SidebarLink key={item.href} item={item} pathname={pathname} collapsed={collapsed} />
            ))}
          </div>

          <div className="space-y-1">
            {!collapsed && <p className="px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/40 mb-1.5">Рост</p>}
            {NAV_GROWTH.map((item) => (
              <SidebarLink key={item.href} item={item} pathname={pathname} collapsed={collapsed} />
            ))}
          </div>

          <div className="space-y-1">
            {!collapsed && <p className="px-3 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground/40 mb-1.5">Система</p>}
            {NAV_SYSTEM.map((item) => (
              <SidebarLink key={item.href} item={item} pathname={pathname} collapsed={collapsed} />
            ))}
          </div>
        </nav>

        {/* Collapse toggle */}
        <div className="px-2 py-1 border-t">
          <button
            onClick={() => setCollapsed(!collapsed)}
            className="w-full flex items-center justify-center h-8 rounded-lg text-muted-foreground hover:bg-secondary hover:text-foreground transition-colors"
          >
            {collapsed ? <ChevronLeft className="h-4 w-4 rotate-180" /> : <ChevronLeft className="h-4 w-4" />}
          </button>
        </div>

        {/* User */}
        <div className={cn("p-3 border-t", collapsed ? "flex justify-center" : "")}>
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-full brand-gradient text-white flex items-center justify-center text-xs font-bold shrink-0 shadow-sm">
              {me ? initialsOf(me.full_name) : "?"}
            </div>
            {!collapsed && (
              <>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate leading-tight">{me?.full_name ?? "..."}</p>
                  <p className="text-[11px] text-muted-foreground truncate">{me?.email ?? ""}</p>
                </div>
                <Button variant="ghost" size="icon" onClick={logout} title="Выйти" className="shrink-0 h-8 w-8">
                  <LogOut className="h-3.5 w-3.5" />
                </Button>
              </>
            )}
          </div>
        </div>
      </aside>

      {/* ─── Main ─── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="sticky top-0 z-30 h-14 border-b bg-card/80 backdrop-blur-xl flex items-center gap-4 px-6">
          <h1 className="text-sm font-semibold">{currentLabel}</h1>
          <div className="ml-auto flex items-center gap-2">
            <div className="relative hidden md:block">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground" />
              <Input placeholder="Поиск..." className="pl-9 w-56 h-8 bg-muted/50 border-0 text-sm focus-visible:ring-1" />
            </div>
            <ThemeToggle />
            <NotificationBell />
          </div>
        </header>

        {/* Content */}
        <main className="flex-1 p-6 max-w-[1440px] w-full">{children}</main>
      </div>
    </div>
  );
}