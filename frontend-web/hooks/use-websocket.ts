"use client";

/**
 * Realtime WebSocket hook.
 *
 * Connects to the backend `/api/v1/ws?token=<jwt>` endpoint and fans out
 * parsed RealtimeEvent frames to a caller-provided handler. Handles:
 *   - auto-reconnect with exponential backoff (1s → 30s max)
 *   - heartbeat: replies "pong" to server `{"type":"ping"}`
 *   - typing send helper
 *   - optional suppression when there's no access token yet (pre-login)
 *
 * We intentionally use a ref for the handler so callers don't have to
 * memoize it — we always dispatch through the latest closure.
 */
import { useCallback, useEffect, useRef, useState } from "react";
import { auth } from "@/lib/auth";

export type RealtimeEventType =
  | "message.new"
  | "message.read"
  | "typing.start"
  | "typing.stop"
  | "presence.online"
  | "presence.offline";

export interface RealtimeEvent<P = Record<string, unknown>> {
  type: RealtimeEventType | "ping";
  team_id?: string;
  conversation_id?: string | null;
  user_id?: string | null;
  payload?: P;
  ts?: string;
}

function wsUrl(): string | null {
  const base = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";
  try {
    const u = new URL(base);
    u.protocol = u.protocol === "https:" ? "wss:" : "ws:";
    // API base already contains `/api/v1`; append `/ws`.
    u.pathname = u.pathname.replace(/\/$/, "") + "/ws";
    return u.toString();
  } catch {
    return null;
  }
}

export interface UseWebSocketOptions {
  onEvent: (event: RealtimeEvent) => void;
  enabled?: boolean;
}

export function useWebSocket({ onEvent, enabled = true }: UseWebSocketOptions) {
  const [status, setStatus] = useState<"idle" | "connecting" | "open" | "closed">("idle");
  const wsRef = useRef<WebSocket | null>(null);
  const handlerRef = useRef(onEvent);
  handlerRef.current = onEvent;
  const attemptRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const teardownRef = useRef(false);

  const send = useCallback((data: Record<string, unknown>) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(data));
    }
  }, []);

  const sendTyping = useCallback(
    (conversationId: string, kind: "start" | "stop") => {
      send({
        type: kind === "start" ? "typing.start" : "typing.stop",
        conversation_id: conversationId,
        // team_id/ts are filled in by the server from the JWT/clock.
        team_id: "00000000-0000-0000-0000-000000000000",
        ts: new Date().toISOString(),
      });
    },
    [send],
  );

  useEffect(() => {
    if (!enabled) return;
    teardownRef.current = false;

    const connect = () => {
      const token = auth.getAccess();
      const url = wsUrl();
      if (!token || !url) return;

      setStatus("connecting");
      const full = `${url}?token=${encodeURIComponent(token)}`;
      const ws = new WebSocket(full);
      wsRef.current = ws;

      ws.onopen = () => {
        attemptRef.current = 0;
        setStatus("open");
      };

      ws.onmessage = (ev) => {
        try {
          const data = JSON.parse(ev.data) as RealtimeEvent;
          if (data.type === "ping") {
            // Replying "pong" (server accepts either a JSON frame or the
            // literal string) so the idle timeout resets on both sides.
            ws.send("pong");
            return;
          }
          handlerRef.current(data);
        } catch {
          // Ignore malformed frames.
        }
      };

      const scheduleReconnect = () => {
        if (teardownRef.current) return;
        const attempt = attemptRef.current++;
        // 1s, 2s, 4s, 8s, 16s, capped at 30s. Small jitter to avoid
        // thundering herd on server restart.
        const backoff = Math.min(30000, 1000 * 2 ** attempt);
        const jitter = Math.random() * 500;
        reconnectTimerRef.current = setTimeout(connect, backoff + jitter);
      };

      ws.onerror = () => {
        // `onclose` always follows; let it drive reconnect.
      };

      ws.onclose = () => {
        wsRef.current = null;
        setStatus("closed");
        scheduleReconnect();
      };
    };

    connect();

    return () => {
      teardownRef.current = true;
      if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
      const ws = wsRef.current;
      wsRef.current = null;
      if (ws) {
        try {
          ws.close();
        } catch {
          /* ignore */
        }
      }
      setStatus("idle");
    };
  }, [enabled]);

  return { status, send, sendTyping };
}
