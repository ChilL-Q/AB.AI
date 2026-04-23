"use client";

import { useCallback, useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import {
  useInfiniteQuery,
  useMutation,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { useVirtualizer } from "@tanstack/react-virtual";
import {
  Loader2,
  MessageSquare,
  Search,
  Send,
  Phone,
  Mail,
  User as UserIcon,
  Check,
  CheckCheck,
  Clock,
  AlertCircle,
} from "lucide-react";
import { api } from "@/lib/api";
import { formatTimeAgo } from "@/lib/formatters";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { initialsOf } from "@/hooks/use-me";
import { useDebouncedValue } from "@/hooks/use-debounced-value";
import { cn } from "@/lib/utils";
import type {
  Conversation,
  ConversationChannel,
  Message,
  MessagePage,
  PaginatedResponse,
} from "@/types";

const MESSAGES_PAGE_SIZE = 50;

const CHANNEL_LABEL: Record<ConversationChannel, string> = {
  whatsapp: "WhatsApp",
  telegram: "Telegram",
  sms: "SMS",
};

const CHANNEL_COLOR: Record<ConversationChannel, string> = {
  whatsapp: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  telegram: "bg-sky-500/10 text-sky-600 dark:text-sky-400",
  sms: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
};

function MessageStatusIcon({ status }: { status: Message["status"] }) {
  if (status === "pending") return <Clock className="h-3 w-3 opacity-60" />;
  if (status === "sent") return <Check className="h-3 w-3 opacity-60" />;
  if (status === "delivered") return <CheckCheck className="h-3 w-3 opacity-60" />;
  if (status === "read") return <CheckCheck className="h-3 w-3 text-sky-400" />;
  if (status === "failed") return <AlertCircle className="h-3 w-3 text-destructive" />;
  return null;
}

export default function ConversationsPage() {
  const qc = useQueryClient();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const debouncedSearch = useDebouncedValue(search, 300);
  const [draft, setDraft] = useState("");
  const scrollRef = useRef<HTMLDivElement>(null);

  const conversationsQ = useQuery({
    queryKey: ["conversations", { search: debouncedSearch }],
    queryFn: async () => {
      const { data } = await api.get<PaginatedResponse<Conversation>>("/conversations", {
        params: { page: 1, limit: 50, search: debouncedSearch || undefined },
      });
      return data;
    },
  });

  const conversations = useMemo(
    () => conversationsQ.data?.data ?? [],
    [conversationsQ.data],
  );
  const selected = useMemo(
    () => conversations.find((c) => c.id === selectedId) ?? null,
    [conversations, selectedId],
  );

  // Auto-select first conversation; reselect if current one filtered out.
  useEffect(() => {
    if (conversations.length === 0) return;
    const stillVisible = selectedId && conversations.some((c) => c.id === selectedId);
    if (!stillVisible) {
      setSelectedId(conversations[0].id);
    }
  }, [conversations, selectedId]);

  const messagesQ = useInfiniteQuery({
    queryKey: ["conversation-messages", selectedId],
    // pageParam = cursor message id for `?before=`; null → most-recent page.
    initialPageParam: null as string | null,
    queryFn: async ({ pageParam }) => {
      const { data } = await api.get<MessagePage>(
        `/conversations/${selectedId}/messages`,
        { params: { limit: MESSAGES_PAGE_SIZE, before: pageParam ?? undefined } },
      );
      return data;
    },
    getNextPageParam: (lastPage) => (lastPage.has_more ? lastPage.next_cursor : undefined),
    enabled: !!selectedId,
  });

  // Pages come in reverse order (newest page first, then older pages), each
  // page is oldest→newest internally. To render chronologically we reverse the
  // page list and flat-concat.
  const messages = useMemo<Message[]>(() => {
    const pages = messagesQ.data?.pages ?? [];
    return [...pages].reverse().flatMap((p) => p.data);
  }, [messagesQ.data]);

  // Mark conversation as read when it opens or when new inbound messages arrive.
  const markReadMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.post(`/conversations/${id}/read`);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["conversations"] });
    },
  });
  const markReadRef = useRef(markReadMutation.mutate);
  markReadRef.current = markReadMutation.mutate;
  useEffect(() => {
    if (!selected || selected.unread_count === 0) return;
    markReadRef.current(selected.id);
  }, [selected]);

  // Virtualize the message list. Estimate keeps initial layout sane; real
  // heights are measured via `measureElement` and remembered after first render.
  const rowVirtualizer = useVirtualizer({
    count: messages.length,
    getScrollElement: () => scrollRef.current,
    estimateSize: () => 72,
    overscan: 8,
    getItemKey: (i) => messages[i]?.id ?? i,
  });
  const virtualItems = rowVirtualizer.getVirtualItems();
  const totalSize = rowVirtualizer.getTotalSize();

  // Scroll to bottom on conversation switch and when we send a new outbound.
  // We skip auto-scroll when older pages are being prepended (handled below).
  const previousMessagesCountRef = useRef(0);
  const prependAnchorRef = useRef<{ heightBefore: number; topBefore: number } | null>(null);

  // Capture scroll position *before* older messages prepend, so we can restore
  // the visible region after the DOM expands at the top.
  const loadOlder = useCallback(() => {
    if (!messagesQ.hasNextPage || messagesQ.isFetchingNextPage) return;
    if (scrollRef.current) {
      prependAnchorRef.current = {
        heightBefore: scrollRef.current.scrollHeight,
        topBefore: scrollRef.current.scrollTop,
      };
    }
    messagesQ.fetchNextPage();
  }, [messagesQ]);

  // Trigger "load older" when the user scrolls near the top.
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    const onScroll = () => {
      if (el.scrollTop < 80) loadOlder();
    };
    el.addEventListener("scroll", onScroll, { passive: true });
    return () => el.removeEventListener("scroll", onScroll);
  }, [loadOlder]);

  useLayoutEffect(() => {
    const el = scrollRef.current;
    if (!el) return;

    // Case 1: we just prepended an older page — keep the previously-visible
    // message under the user's eye by restoring scrollTop + height delta.
    if (prependAnchorRef.current) {
      const { heightBefore, topBefore } = prependAnchorRef.current;
      el.scrollTop = el.scrollHeight - heightBefore + topBefore;
      prependAnchorRef.current = null;
      previousMessagesCountRef.current = messages.length;
      return;
    }

    // Case 2: selection changed or first load — pin to bottom.
    // Case 3: new outbound/inbound at the tail — also pin to bottom
    //   (we only detect growth at the end; prepend is handled above).
    const grew = messages.length > previousMessagesCountRef.current;
    const firstLoad = previousMessagesCountRef.current === 0 && messages.length > 0;
    if (firstLoad || grew) {
      rowVirtualizer.scrollToIndex(messages.length - 1, { align: "end" });
    }
    previousMessagesCountRef.current = messages.length;
  }, [messages, rowVirtualizer]);

  // Reset bottom-anchoring bookkeeping whenever we switch threads.
  useEffect(() => {
    previousMessagesCountRef.current = 0;
    prependAnchorRef.current = null;
  }, [selectedId]);

  const sendMutation = useMutation({
    mutationFn: async (text: string) => {
      const { data } = await api.post<Message>(
        `/conversations/${selectedId}/messages`,
        { text },
      );
      return data;
    },
    onSuccess: async () => {
      setDraft("");
      await qc.invalidateQueries({ queryKey: ["conversation-messages", selectedId] });
      await qc.invalidateQueries({ queryKey: ["conversations"] });
    },
  });

  const sendError = sendMutation.error
    ? (sendMutation.error as { response?: { data?: { detail?: string } }; message?: string })
        .response?.data?.detail ??
      (sendMutation.error as { message?: string }).message ??
      "Не удалось отправить сообщение"
    : null;

  const onSend = (e: React.FormEvent) => {
    e.preventDefault();
    const text = draft.trim();
    if (!text || !selectedId || sendMutation.isPending) return;
    sendMutation.mutate(text);
  };

  return (
    <div className="h-[calc(100vh-6rem)] -mx-6 -my-6 flex border-t">
      {/* Left: conversations list */}
      <aside className="w-80 border-r flex flex-col bg-card/50">
        <div className="p-4 border-b">
          <h2 className="text-lg font-semibold mb-3">Диалоги</h2>
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Имя или телефон..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="pl-9 h-9"
            />
          </div>
        </div>

        <div className="flex-1 overflow-y-auto">
          {conversationsQ.isLoading ? (
            <div className="py-12 flex justify-center">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
            </div>
          ) : conversations.length === 0 ? (
            <div className="py-16 px-4 text-center text-sm text-muted-foreground">
              {search ? "Ничего не найдено" : "Диалогов пока нет"}
            </div>
          ) : (
            <ul>
              {conversations.map((c) => {
                const active = c.id === selectedId;
                const name = c.client?.full_name ?? "Без имени";
                return (
                  <li key={c.id}>
                    <button
                      type="button"
                      onClick={() => setSelectedId(c.id)}
                      className={cn(
                        "w-full text-left px-4 py-3 flex gap-3 border-b hover:bg-accent/50 transition-colors",
                        active && "bg-accent",
                      )}
                    >
                      <div className="h-10 w-10 shrink-0 rounded-full bg-gradient-to-br from-primary to-violet-500 text-primary-foreground flex items-center justify-center text-sm font-semibold">
                        {initialsOf(name)}
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-medium truncate">{name}</span>
                          <span className="text-xs text-muted-foreground shrink-0">
                            {formatTimeAgo(c.last_message_at ?? c.created_at)}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span
                            className={cn(
                              "text-[10px] px-1.5 py-0.5 rounded font-medium uppercase tracking-wider",
                              CHANNEL_COLOR[c.channel],
                            )}
                          >
                            {CHANNEL_LABEL[c.channel] ?? c.channel}
                          </span>
                          <span
                            className={cn(
                              "text-xs truncate flex-1",
                              c.unread_count > 0 && !active
                                ? "text-foreground font-medium"
                                : "text-muted-foreground",
                            )}
                          >
                            {c.last_message_preview ?? "—"}
                          </span>
                          {c.unread_count > 0 && !active && (
                            <span className="shrink-0 min-w-[18px] h-[18px] px-1 rounded-full bg-primary text-primary-foreground text-[10px] font-semibold flex items-center justify-center">
                              {c.unread_count > 99 ? "99+" : c.unread_count}
                            </span>
                          )}
                        </div>
                      </div>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
        </div>
      </aside>

      {/* Center: thread */}
      <section className="flex-1 flex flex-col min-w-0">
        {!selected ? (
          <div className="flex-1 flex flex-col items-center justify-center text-muted-foreground gap-3">
            <MessageSquare className="h-12 w-12 opacity-30" />
            <p>Выберите диалог слева</p>
          </div>
        ) : (
          <>
            <header className="px-6 py-4 border-b flex items-center gap-3">
              <div className="h-10 w-10 rounded-full bg-gradient-to-br from-primary to-violet-500 text-primary-foreground flex items-center justify-center text-sm font-semibold">
                {initialsOf(selected.client?.full_name ?? "?")}
              </div>
              <div className="min-w-0 flex-1">
                <div className="font-semibold truncate">{selected.client?.full_name ?? "Без имени"}</div>
                <div className="text-xs text-muted-foreground flex items-center gap-2">
                  <span
                    className={cn(
                      "px-1.5 py-0.5 rounded font-medium uppercase tracking-wider text-[10px]",
                      CHANNEL_COLOR[selected.channel],
                    )}
                  >
                    {CHANNEL_LABEL[selected.channel] ?? selected.channel}
                  </span>
                  <span>·</span>
                  <span className="capitalize">{selected.status}</span>
                </div>
              </div>
            </header>

            <div ref={scrollRef} className="flex-1 overflow-y-auto">
              {messagesQ.isLoading ? (
                <div className="py-12 flex justify-center">
                  <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
                </div>
              ) : messages.length === 0 ? (
                <div className="py-12 text-center text-sm text-muted-foreground">
                  Сообщений пока нет
                </div>
              ) : (
                <div
                  style={{ height: totalSize, position: "relative" }}
                  className="px-6 py-4"
                >
                  {messagesQ.isFetchingNextPage && (
                    <div className="absolute top-1 left-0 right-0 flex justify-center z-10">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground bg-background/80 backdrop-blur px-3 py-1 rounded-full border">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        Загрузка истории...
                      </div>
                    </div>
                  )}
                  {virtualItems.map((vi) => {
                    const m = messages[vi.index];
                    if (!m) return null;
                    const out = m.direction === "outbound";
                    return (
                      <div
                        key={vi.key}
                        data-index={vi.index}
                        ref={rowVirtualizer.measureElement}
                        style={{
                          position: "absolute",
                          top: 0,
                          left: 0,
                          right: 0,
                          transform: `translateY(${vi.start}px)`,
                        }}
                        className="pb-3"
                      >
                        <div className={cn("flex", out ? "justify-end" : "justify-start")}>
                          <div
                            className={cn(
                              "max-w-[70%] rounded-2xl px-4 py-2 text-sm",
                              out
                                ? "bg-primary text-primary-foreground rounded-br-md"
                                : "bg-muted rounded-bl-md",
                            )}
                          >
                            {m.sent_by === "ai" && (
                              <div className="text-[10px] uppercase tracking-wider opacity-70 mb-1">
                                AI
                              </div>
                            )}
                            <div className="whitespace-pre-wrap break-words">{m.text ?? ""}</div>
                            <div
                              className={cn(
                                "flex items-center justify-end gap-1 mt-1 text-[10px]",
                                out ? "opacity-80" : "text-muted-foreground",
                              )}
                            >
                              <span>{formatTimeAgo(m.sent_at ?? m.created_at)}</span>
                              {out && <MessageStatusIcon status={m.status} />}
                            </div>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>

            <div className="border-t">
              {sendError && (
                <div className="px-4 pt-3 text-xs text-destructive flex items-center gap-2">
                  <AlertCircle className="h-3.5 w-3.5 shrink-0" />
                  <span className="truncate">{sendError}</span>
                </div>
              )}
              <form onSubmit={onSend} className="p-4 flex gap-2">
                <Input
                  placeholder="Написать сообщение..."
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  disabled={sendMutation.isPending}
                  className="flex-1"
                />
                <Button type="submit" disabled={!draft.trim() || sendMutation.isPending}>
                  {sendMutation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Send className="h-4 w-4" />
                  )}
                </Button>
              </form>
            </div>
          </>
        )}
      </section>

      {/* Right: client sidebar */}
      {selected && selected.client && (
        <aside className="w-72 border-l bg-card/50 hidden lg:flex flex-col">
          <div className="p-6 text-center border-b">
            <div className="h-16 w-16 mx-auto rounded-full bg-gradient-to-br from-primary to-violet-500 text-primary-foreground flex items-center justify-center text-xl font-semibold">
              {initialsOf(selected.client.full_name)}
            </div>
            <div className="mt-3 font-semibold">{selected.client.full_name}</div>
            <Link
              href={`/clients/${selected.client.id}`}
              className="text-xs text-primary hover:underline inline-flex items-center gap-1 mt-1"
            >
              <UserIcon className="h-3 w-3" />
              Карточка клиента
            </Link>
          </div>
          <div className="p-4 space-y-3 text-sm">
            <div className="flex items-center gap-3">
              <Phone className="h-4 w-4 text-muted-foreground shrink-0" />
              <span className="tabular-nums">{selected.client.phone}</span>
            </div>
            <div className="flex items-center gap-3">
              <Mail className="h-4 w-4 text-muted-foreground shrink-0" />
              {selected.client.email ? (
                <a
                  href={`mailto:${selected.client.email}`}
                  className="truncate hover:underline"
                >
                  {selected.client.email}
                </a>
              ) : (
                <span className="text-muted-foreground">—</span>
              )}
            </div>
            <div className="pt-2 border-t">
              <Badge variant="outline" className="text-xs">
                {CHANNEL_LABEL[selected.channel] ?? selected.channel}
              </Badge>
            </div>
          </div>
        </aside>
      )}
    </div>
  );
}
