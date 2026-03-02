"use client";

import { useState, useRef, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Search, Plus, ChevronDown, Moon, Sun, LogOut, User as UserIcon, Coins, Menu,
} from "lucide-react";
import { useUser, useDarkMode, useDebounce } from "@/lib/hooks";
import { auth } from "@/lib/api";
import { getAvatarUrl } from "@/lib/utils";

interface TopBarProps {
  onToggleSidebar: () => void;
}

export default function TopBar({ onToggleSidebar }: TopBarProps) {
  const router = useRouter();
  const { user, setUser } = useUser();
  const { dark, toggle: toggleDark } = useDarkMode();
  const [searchQuery, setSearchQuery] = useState("");
  const debouncedQuery = useDebounce(searchQuery, 300);
  const [showCreateMenu, setShowCreateMenu] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const createRef = useRef<HTMLDivElement>(null);
  const userRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (debouncedQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(debouncedQuery)}`);
    }
  }, [debouncedQuery, router]);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (createRef.current && !createRef.current.contains(e.target as Node)) setShowCreateMenu(false);
      if (userRef.current && !userRef.current.contains(e.target as Node)) setShowUserMenu(false);
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const handleLogout = async () => {
    await auth.logout();
    setUser(null);
    router.push("/auth/login");
  };

  return (
    <header className="sticky top-0 z-50 flex h-14 items-center gap-3 border-b border-slate-200 bg-white/80 px-4 backdrop-blur-sm dark:border-slate-700 dark:bg-slate-900/80">
      <button onClick={onToggleSidebar} className="btn-ghost lg:hidden">
        <Menu className="h-5 w-5" />
      </button>

      <Link href="/" className="flex shrink-0 items-center gap-2 font-bold text-primary-600">
        <span className="text-xl">YAI</span>
      </Link>

      {/* Search */}
      <div className="relative mx-auto hidden w-full max-w-md sm:block">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="搜索角色和场景..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && searchQuery.trim()) {
              router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
            }
          }}
          className="input pl-9"
        />
      </div>

      <div className="flex items-center gap-2">
        {/* Dark mode */}
        <button onClick={toggleDark} className="btn-ghost" title="切换主题">
          {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </button>

        {user ? (
          <>
            {/* Create */}
            <div ref={createRef} className="relative">
              <button onClick={() => setShowCreateMenu(!showCreateMenu)} className="btn-primary gap-1">
                <Plus className="h-4 w-4" />
                <span className="hidden sm:inline">创建</span>
                <ChevronDown className="h-3 w-3" />
              </button>
              {showCreateMenu && (
                <div className="absolute right-0 top-full mt-1 w-40 rounded-lg border border-slate-200 bg-white py-1 shadow-lg dark:border-slate-700 dark:bg-slate-800">
                  <Link href="/create/character" className="block px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700" onClick={() => setShowCreateMenu(false)}>
                    创建角色
                  </Link>
                  <Link href="/create/scene" className="block px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700" onClick={() => setShowCreateMenu(false)}>
                    创建场景
                  </Link>
                </div>
              )}
            </div>

            {/* Credits */}
            <Link href="/profile" className="btn-ghost gap-1 text-sm">
              <Coins className="h-4 w-4 text-amber-500" />
              <span>{user.credits}</span>
            </Link>

            {/* User */}
            <div ref={userRef} className="relative">
              <button onClick={() => setShowUserMenu(!showUserMenu)} className="h-8 w-8 overflow-hidden rounded-full">
                <img src={getAvatarUrl(user.avatar_url, user.display_name)} alt={user.display_name} className="h-full w-full object-cover" />
              </button>
              {showUserMenu && (
                <div className="absolute right-0 top-full mt-1 w-48 rounded-lg border border-slate-200 bg-white py-1 shadow-lg dark:border-slate-700 dark:bg-slate-800">
                  <div className="border-b border-slate-100 px-4 py-2 dark:border-slate-700">
                    <p className="text-sm font-medium">{user.display_name}</p>
                    <p className="text-xs text-slate-500">{user.email}</p>
                  </div>
                  <Link href="/profile" className="flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700" onClick={() => setShowUserMenu(false)}>
                    <UserIcon className="h-4 w-4" /> 个人中心
                  </Link>
                  <button onClick={handleLogout} className="flex w-full items-center gap-2 px-4 py-2 text-left text-sm text-red-600 hover:bg-slate-50 dark:hover:bg-slate-700">
                    <LogOut className="h-4 w-4" /> 登出
                  </button>
                </div>
              )}
            </div>
          </>
        ) : (
          <Link href="/auth/login" className="btn-primary">登录</Link>
        )}
      </div>
    </header>
  );
}
