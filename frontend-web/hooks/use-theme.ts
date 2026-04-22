"use client";

import { useCallback, useEffect, useState } from "react";

export type Theme = "light" | "dark";

function read(): Theme {
  if (typeof document === "undefined") return "light";
  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

export function useTheme() {
  const [theme, setThemeState] = useState<Theme>("light");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setThemeState(read());
    setMounted(true);
  }, []);

  const setTheme = useCallback((t: Theme) => {
    document.documentElement.classList.toggle("dark", t === "dark");
    localStorage.setItem("theme", t);
    setThemeState(t);
  }, []);

  const toggle = useCallback(() => {
    setTheme(read() === "dark" ? "light" : "dark");
  }, [setTheme]);

  return { theme, setTheme, toggle, mounted };
}
