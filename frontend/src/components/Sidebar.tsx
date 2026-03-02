"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Home, Compass, PlusCircle, MessageCircle, BookOpen, Gamepad2, Coins, Shield, X,
} from "lucide-react";
import { useUser } from "@/lib/hooks";
import { chat } from "@/lib/api";
import type { RecentCharacterResponse } from "@/lib/types";
import { cn, getAvatarUrl, timeAgo } from "@/lib/utils";

interface SidebarProps {
  open: boolean;
  onClose: () => void;
}

export default function Sidebar({ open, onClose }: SidebarProps) {
  const pathname = usePathname();
  const { user } = useUser();
  const [recentChats, setRecentChats] = useState<RecentCharacterResponse[]>([]);

  useEffect(() => {
    if (user) {
      chat.recentCharacters(8).then(setRecentChats).catch(() => {});
    }
  }, [user]);

  const navItems = [
    { href: "/", icon: Home, label: "首页" },
    { href: "/explore", icon: Compass, label: "发现" },
    { href: "/create/character", icon: PlusCircle, label: "创建" },
  ];

  const bottomItems = [
    { href: "/profile?tab=characters", icon: BookOpen, label: "我的角色" },
    { href: "/profile?tab=scenes", icon: Gamepad2, label: "我的场景" },
    { href: "/profile?tab=credits", icon: Coins, label: "积分记录" },
  ];

  return (
    <>
      {/* Overlay for mobile */}
      {open && (
        <div className="fixed inset-0 z-40 bg-black/30 lg:hidden" onClick={onClose} />
      )}

      <aside
        className={cn(
          "fixed left-0 top-14 z-40 flex h-[calc(100vh-3.5rem)] w-60 flex-col border-r border-slate-200 bg-white transition-transform dark:border-slate-700 dark:bg-slate-900",
          "lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        {/* Close button for mobile */}
        <button onClick={onClose} className="absolute right-2 top-2 btn-ghost lg:hidden">
          <X className="h-4 w-4" />
        </button>

        {/* Main nav */}
        <nav className="flex flex-col gap-0.5 px-3 pt-4">
          {navItems.map(({ href, icon: Icon, label }) => (
            <Link
              key={href}
              href={href}
              onClick={onClose}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                pathname === href
                  ? "bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400"
                  : "text-slate-600 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800",
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          ))}
        </nav>

        {/* Recent chats */}
        {user && recentChats.length > 0 && (
          <div className="mt-4 flex-1 overflow-y-auto px-3">
            <p className="mb-2 px-3 text-xs font-semibold uppercase text-slate-400">最近对话</p>
            {recentChats.map((rc) => (
              <Link
                key={rc.character_id}
                href={`/chat/${rc.last_session_id}`}
                onClick={onClose}
                className="flex items-center gap-2 rounded-lg px-3 py-2 text-sm transition-colors hover:bg-slate-100 dark:hover:bg-slate-800"
              >
                <img
                  src={getAvatarUrl(rc.character_avatar_url, rc.character_name)}
                  alt={rc.character_name}
                  className="h-7 w-7 shrink-0 rounded-full object-cover"
                />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm font-medium">{rc.character_name}</p>
                  <p className="truncate text-xs text-slate-400">{timeAgo(rc.last_message_at)}</p>
                </div>
              </Link>
            ))}
          </div>
        )}

        {/* Bottom nav */}
        {user && (
          <nav className="mt-auto flex flex-col gap-0.5 border-t border-slate-200 px-3 py-3 dark:border-slate-700">
            {bottomItems.map(({ href, icon: Icon, label }) => (
              <Link
                key={label}
                href={href}
                onClick={onClose}
                className="flex items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-600 transition-colors hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800"
              >
                <Icon className="h-4 w-4" />
                {label}
              </Link>
            ))}
            {user.is_admin && (
              <Link
                href="/admin/users"
                onClick={onClose}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  pathname.startsWith("/admin")
                    ? "bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400"
                    : "text-amber-600 hover:bg-amber-50 dark:text-amber-400 dark:hover:bg-amber-900/20",
                )}
              >
                <Shield className="h-4 w-4" />
                管理用户
              </Link>
            )}
          </nav>
        )}
      </aside>
    </>
  );
}
