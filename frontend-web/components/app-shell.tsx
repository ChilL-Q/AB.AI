"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import {
  LayoutDashboard,
  Users,
  MessageSquare,
  Settings,
  LogOut,
  Car,
  Megaphone,
  Bell,
  Search,
} from "lucide-react";
import { auth } from "@/lib/auth";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useMe, initialsOf } from "@/hooks/use-me";
import { ThemeToggle } from "@/components/theme-toggle";

type NavItem = { href: string; label: string; icon: React.ComponentType<{ className?: string }> };

const NAV_MAIN: NavItem[] = [
  { href: "/dashboard", label: "Дашборд", icon: LayoutDashboard },
  { href: "/clients", label: "Клиенты", icon: Users },
  { href: "/conversations", label: "Диалоги", icon: MessageSquare },
];

const NAV_GROWTH: NavItem[] = [
  { href: "/campaigns", label: "Кампании", icon: Megaphone },
];

const NAV_SYSTEM: NavItem[] = [
  { href: "/settings", label: "Настройки", icon: Settings },
];

function NavSection({ label, items, pathname }: { label: string; items: NavItem[]; pathname: string }) {
  return (
    <div className="space-y-1">
      <p className="px-3 text-xs font-medium uppercase tracking-wider text-muted-foreground/70">{label}</p>
      {items.map(({ href, label, icon: Icon }) => {
        const active = pathname === href || pathname.startsWith(href + "/");
        return (
          <Link
            key={href}
            href={href}
            className={cn(
              "relative flex items-center gap-3 px-3 py-2 rounded-md text-sm transition-colors",
              active
                ? "bg-accent text-accent-foreground font-medium"
                : "text-muted-foreground hover:bg-accent/60 hover:text-foreground"
            )}
          >
            {active && <span className="absolute left-0 top-1.5 bottom-1.5 w-0.5 rounded-r-full bg-primary" />}
            <Icon className="h-4 w-4" />
            {label}
          </Link>
        );
      })}
    </div>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { data: me } = useMe();
  const isOnboarding = pathname.startsWith("/onboarding");

  useEffect(() => {
    if (!auth.isAuthed()) router.replace("/login");
  }, [router]);

  useEffect(() => {
    if (me && !me.team_id && !isOnboarding) router.replace("/onboarding");
  }, [me, isOnboarding, router]);

  if (isOnboarding) {
    return (
      <div className="min-h-screen bg-muted/20">
        <header className="h-16 border-b bg-card flex items-center px-6">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-primary text-primary-foreground flex items-center justify-center">
              <Car className="h-5 w-5" />
            </div>
            <span className="font-semibold">AB AI</span>
          </div>
          <Button variant="ghost" size="sm" className="ml-auto" onClick={() => { auth.clear(); router.push("/login"); }}>
            <LogOut className="h-4 w-4 mr-2" />Выйти
          </Button>
        </header>
        <main className="p-6">{children}</main>
      </div>
    );
  }

  const logout = () => {
    auth.clear();
    router.push("/login");
  };

  const currentLabel =
    [...NAV_MAIN, ...NAV_GROWTH, ...NAV_SYSTEM].find((n) => pathname.startsWith(n.href))?.label ?? "AB AI";

  return (
    <div className="min-h-screen flex bg-muted/20">
      <aside className="w-64 border-r bg-card flex flex-col">
        <div className="h-16 flex items-center gap-2 px-6 border-b">
          <div className="h-8 w-8 rounded-lg bg-primary text-primary-foreground flex items-center justify-center">
            <Car className="h-5 w-5" />
          </div>
          <div>
            <div className="font-semibold leading-tight">AB AI</div>
            <div className="text-[10px] text-muted-foreground">Автосервис OS</div>
          </div>
        </div>
        <nav className="flex-1 p-3 space-y-5 overflow-y-auto">
          <NavSection label="Основное" items={NAV_MAIN} pathname={pathname} />
          <NavSection label="Рост" items={NAV_GROWTH} pathname={pathname} />
          <NavSection label="Система" items={NAV_SYSTEM} pathname={pathname} />
        </nav>
        <div className="p-3 border-t">
          <div className="flex items-center gap-3 px-2 py-2 rounded-md">
            <div className="h-9 w-9 rounded-full bg-gradient-to-br from-primary to-violet-500 text-primary-foreground flex items-center justify-center text-sm font-semibold">
              {me ? initialsOf(me.full_name) : "—"}
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{me?.full_name ?? "..."}</p>
              <p className="text-xs text-muted-foreground truncate">{me?.email ?? ""}</p>
            </div>
            <Button variant="ghost" size="icon" onClick={logout} title="Выйти">
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </aside>
      <div className="flex-1 flex flex-col min-w-0">
        <header className="h-16 border-b bg-card/80 backdrop-blur flex items-center gap-4 px-6 sticky top-0 z-10">
          <h1 className="text-lg font-semibold">{currentLabel}</h1>
          <div className="ml-auto flex items-center gap-3">
            <div className="relative hidden md:block">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input placeholder="Поиск клиентов, авто, визитов..." className="pl-9 w-72 h-9 bg-muted/40" />
            </div>
            <ThemeToggle />
            <Button variant="ghost" size="icon" className="relative">
              <Bell className="h-4 w-4" />
              <span className="absolute top-2 right-2 h-1.5 w-1.5 rounded-full bg-primary" />
            </Button>
          </div>
        </header>
        <main className="flex-1 p-6 max-w-[1400px] w-full">{children}</main>
      </div>
    </div>
  );
}
