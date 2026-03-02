"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import type { User } from "./types";
import { auth } from "./api";

/* ========== useUser: 全局用户状态 ========== */
let globalUser: User | null = null;
let globalLoading = true;
const listeners = new Set<() => void>();

function notifyListeners() {
  listeners.forEach((fn) => fn());
}

export function useUser() {
  const [, forceRender] = useState(0);

  useEffect(() => {
    const listener = () => forceRender((n) => n + 1);
    listeners.add(listener);
    return () => { listeners.delete(listener); };
  }, []);

  useEffect(() => {
    if (globalUser !== null || !globalLoading) return;
    auth.me()
      .then((u) => { globalUser = u; globalLoading = false; notifyListeners(); })
      .catch(() => { globalUser = null; globalLoading = false; notifyListeners(); });
  }, []);

  const setUser = useCallback((u: User | null) => {
    globalUser = u;
    globalLoading = false;
    notifyListeners();
  }, []);

  return { user: globalUser, loading: globalLoading, setUser };
}

/* ========== useDebounce ========== */
export function useDebounce<T>(value: T, delay = 300): T {
  const [debounced, setDebounced] = useState(value);
  useEffect(() => {
    const timer = setTimeout(() => setDebounced(value), delay);
    return () => clearTimeout(timer);
  }, [value, delay]);
  return debounced;
}

/* ========== useDarkMode ========== */
export function useDarkMode() {
  const [dark, setDark] = useState(false);

  useEffect(() => {
    const stored = localStorage.getItem("theme");
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    const isDark = stored === "dark" || (!stored && prefersDark);
    setDark(isDark);
    document.documentElement.classList.toggle("dark", isDark);
  }, []);

  const toggle = useCallback(() => {
    setDark((prev) => {
      const next = !prev;
      localStorage.setItem("theme", next ? "dark" : "light");
      document.documentElement.classList.toggle("dark", next);
      return next;
    });
  }, []);

  return { dark, toggle };
}

/* ========== useIntersection: 懒加载/无限滚动 ========== */
export function useIntersection(callback: () => void) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) callback(); },
      { threshold: 0.1 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, [callback]);

  return ref;
}
