"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";
import { characters, scenes, credits } from "@/lib/api";
import { useUser } from "@/lib/hooks";
import type { CharacterPublicResponse, SceneResponse, TransactionResponse, PaginatedResponse } from "@/lib/types";
import CharacterCard from "@/components/CharacterCard";
import SceneCard from "@/components/SceneCard";
import { ListSkeleton } from "@/components/Skeleton";
import { cn, getAvatarUrl, timeAgo } from "@/lib/utils";
import { Coins, Plus } from "lucide-react";

type Tab = "characters" | "scenes" | "credits";

export default function ProfilePage() {
  const searchParams = useSearchParams();
  const initialTab = (searchParams.get("tab") || "characters") as Tab;
  const { user } = useUser();
  const [tab, setTab] = useState<Tab>(initialTab);
  const [myChars, setMyChars] = useState<CharacterPublicResponse[]>([]);
  const [myScenes, setMyScenes] = useState<SceneResponse[]>([]);
  const [transactions, setTransactions] = useState<TransactionResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    const load = async () => {
      try {
        if (tab === "characters") {
          const res = await characters.myList(1, 50);
          setMyChars(res.items);
        } else if (tab === "scenes") {
          const res = await scenes.myList(1, 50);
          setMyScenes(res.items);
        } else {
          const res = await credits.transactions(1, 50);
          setTransactions(res.items);
        }
      } catch {
        // pass
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [tab, user]);

  if (!user) {
    return (
      <div className="py-12 text-center">
        <p className="text-slate-500">请先登录</p>
        <Link href="/auth/login" className="btn-primary mt-4 inline-block">登录</Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      {/* Profile header */}
      <div className="flex items-center gap-4">
        <img
          src={getAvatarUrl(user.avatar_url, user.display_name)}
          alt={user.display_name}
          className="h-16 w-16 rounded-full object-cover ring-4 ring-slate-100 dark:ring-slate-700"
        />
        <div>
          <h1 className="text-lg font-bold">{user.display_name}</h1>
          <p className="text-sm text-slate-500">{user.email}</p>
          <div className="mt-1 flex items-center gap-1 text-sm">
            <Coins className="h-4 w-4 text-amber-500" />
            <span className="font-medium">{user.credits}</span>
            <span className="text-slate-400">积分</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-slate-200 dark:border-slate-700">
        {([
          { key: "characters", label: "我的角色" },
          { key: "scenes", label: "我的场景" },
          { key: "credits", label: "积分记录" },
        ] as { key: Tab; label: string }[]).map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={cn(
              "border-b-2 pb-2 text-sm font-medium transition-colors",
              tab === key ? "border-primary-600 text-primary-600" : "border-transparent text-slate-500",
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Content */}
      {loading ? (
        <ListSkeleton count={4} />
      ) : (
        <>
          {tab === "characters" && (
            <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
              {myChars.map((c) => <CharacterCard key={c.id} character={c} />)}
              <Link href="/create/character" className="card flex flex-col items-center justify-center p-6 text-slate-400 transition-colors hover:text-primary-600">
                <Plus className="mb-2 h-8 w-8" />
                <span className="text-sm">创建角色</span>
              </Link>
            </div>
          )}

          {tab === "scenes" && (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3">
              {myScenes.map((s) => <SceneCard key={s.id} scene={s} />)}
              <Link href="/create/scene" className="card flex flex-col items-center justify-center p-6 text-slate-400 transition-colors hover:text-primary-600">
                <Plus className="mb-2 h-8 w-8" />
                <span className="text-sm">创建场景</span>
              </Link>
            </div>
          )}

          {tab === "credits" && (
            <div className="space-y-2">
              {transactions.length === 0 ? (
                <p className="py-8 text-center text-slate-400">暂无积分记录</p>
              ) : (
                transactions.map((tx) => (
                  <div key={tx.id} className="flex items-center justify-between rounded-lg bg-slate-50 px-4 py-3 dark:bg-slate-800">
                    <div>
                      <p className="text-sm">{tx.reason}</p>
                      <p className="text-xs text-slate-400">{timeAgo(tx.created_at)}</p>
                    </div>
                    <span className={cn("text-sm font-medium", tx.amount > 0 ? "text-green-600" : "text-red-600")}>
                      {tx.amount > 0 ? "+" : ""}{tx.amount}
                    </span>
                  </div>
                ))
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
