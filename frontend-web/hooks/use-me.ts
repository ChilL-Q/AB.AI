"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { User } from "@/types";

// Re-export for backward compatibility with existing imports.
export { initialsOf } from "@/lib/formatters";

export function useMe() {
  return useQuery({
    queryKey: ["me"],
    queryFn: async () => (await api.get<User>("/me")).data,
    staleTime: 5 * 60 * 1000,
  });
}
