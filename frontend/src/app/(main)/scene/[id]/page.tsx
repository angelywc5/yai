"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { scenes, characters } from "@/lib/api";
import type { SceneResponse, CharacterPublicResponse } from "@/lib/types";
import { useUser } from "@/lib/hooks";
import { getAvatarUrl, formatNumber, cn } from "@/lib/utils";
import { Eye, Play, Search, Loader2, X, Check } from "lucide-react";
import CharacterCard from "@/components/CharacterCard";

export default function SceneDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const router = useRouter();
  const { user } = useUser();
  const [scene, setScene] = useState<SceneResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCharId, setSelectedCharId] = useState<string | null>(null);
  const [showSearch, setShowSearch] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<CharacterPublicResponse[]>([]);
  const [searchTab, setSearchTab] = useState<"discover" | "mine" | "recent">("discover");
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    scenes.get(id)
      .then((s) => {
        setScene(s);
        if (s.characters.length === 1 && !s.allow_character_selection) {
          setSelectedCharId(s.characters[0].id);
        }
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  useEffect(() => {
    if (!showSearch) return;
    const load = async () => {
      try {
        if (searchTab === "discover") {
          const res = searchQuery
            ? await characters.search(searchQuery, 1, 20)
            : await characters.publicList(1, 20, "popular");
          setSearchResults(res.items);
        } else if (searchTab === "mine") {
          const res = await characters.myList(1, 20);
          setSearchResults(res.items);
        }
      } catch {
        setSearchResults([]);
      }
    };
    const timer = setTimeout(load, 300);
    return () => clearTimeout(timer);
  }, [showSearch, searchTab, searchQuery]);

  const handleStart = async () => {
    if (!user) { router.push("/auth/login"); return; }
    if (!selectedCharId) return;
    setStarting(true);
    router.push(`/chat/new?character_id=${selectedCharId}&scene_id=${id}`);
  };

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  if (!scene) {
    return <p className="py-12 text-center text-slate-400">场景不存在</p>;
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Cover */}
      <div className="relative h-48 overflow-hidden rounded-xl bg-gradient-to-br from-primary-400 to-purple-500">
        {scene.cover_image_url && (
          <img src={scene.cover_image_url} alt={scene.name} className="h-full w-full object-cover" />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
        <div className="absolute bottom-4 left-4 right-4">
          <h1 className="text-xl font-bold text-white">{scene.name}</h1>
          <div className="mt-1 flex items-center gap-3 text-sm text-white/80">
            <span>@{scene.creator_username}</span>
            <span className="flex items-center gap-1"><Eye className="h-3.5 w-3.5" /> {formatNumber(scene.play_count)}</span>
            <span>{scene.characters.length} 个角色</span>
          </div>
        </div>
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-2">
        {scene.genre && <span className="badge bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400">{scene.genre}</span>}
        {scene.mood && <span className="badge bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">{scene.mood}</span>}
        {scene.time_period && <span className="badge bg-amber-50 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400">{scene.time_period}</span>}
        {scene.setting_location && <span className="badge bg-green-50 text-green-700 dark:bg-green-900/30 dark:text-green-400">{scene.setting_location}</span>}
        {scene.tags.map((t) => (
          <span key={t} className="badge bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300">{t}</span>
        ))}
      </div>

      {/* Description */}
      <section>
        <h2 className="mb-2 text-sm font-semibold text-slate-600 dark:text-slate-400">场景描述</h2>
        <div className="rounded-lg bg-slate-50 p-4 text-sm leading-relaxed dark:bg-slate-800">
          {scene.description}
        </div>
      </section>

      {/* Objective */}
      {scene.player_objective && (
        <section>
          <h2 className="mb-2 text-sm font-semibold text-slate-600 dark:text-slate-400">🎯 你的目标</h2>
          <div className="rounded-lg bg-amber-50 p-4 text-sm dark:bg-amber-900/20">
            {scene.player_objective}
          </div>
        </section>
      )}

      {/* Character selection */}
      <section>
        <h2 className="mb-3 text-sm font-semibold text-slate-600 dark:text-slate-400">选择角色</h2>
        <div className="flex gap-3 overflow-x-auto pb-2">
          {/* Search button */}
          <button
            onClick={() => setShowSearch(true)}
            className="flex shrink-0 flex-col items-center gap-1 rounded-xl border-2 border-dashed border-slate-300 p-3 transition-colors hover:border-primary-400 dark:border-slate-600"
          >
            <Search className="h-10 w-10 text-slate-400" />
            <span className="text-xs text-slate-500">搜索全部</span>
          </button>
          {scene.characters.map((c) => (
            <button
              key={c.id}
              onClick={() => setSelectedCharId(c.id)}
              className={cn(
                "flex shrink-0 flex-col items-center gap-1 rounded-xl p-3 transition-all",
                selectedCharId === c.id
                  ? "bg-primary-50 ring-2 ring-primary-500 dark:bg-primary-900/30"
                  : "hover:bg-slate-50 dark:hover:bg-slate-800",
              )}
            >
              <div className="relative">
                <img src={getAvatarUrl(c.avatar_url, c.name)} alt={c.name} className="h-12 w-12 rounded-full object-cover" />
                {selectedCharId === c.id && (
                  <div className="absolute -bottom-0.5 -right-0.5 rounded-full bg-primary-600 p-0.5">
                    <Check className="h-3 w-3 text-white" />
                  </div>
                )}
              </div>
              <span className="max-w-[60px] truncate text-xs font-medium">{c.name}</span>
              <span className="text-[10px] text-slate-400">建议</span>
            </button>
          ))}
        </div>
      </section>

      {/* Start button */}
      <button
        onClick={handleStart}
        disabled={!selectedCharId || starting}
        className="btn-primary w-full gap-2"
      >
        {starting ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
        开启场景
      </button>

      {/* Character Search Modal */}
      {showSearch && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="w-full max-w-md rounded-xl bg-white shadow-xl dark:bg-slate-800">
            <div className="flex items-center justify-between border-b border-slate-200 px-4 py-3 dark:border-slate-700">
              <h3 className="font-semibold">选择角色</h3>
              <button onClick={() => setShowSearch(false)} className="btn-ghost p-1"><X className="h-4 w-4" /></button>
            </div>

            {/* Tabs */}
            <div className="flex gap-4 border-b border-slate-200 px-4 dark:border-slate-700">
              {([
                { key: "discover", label: "发现" },
                { key: "mine", label: "您的角色" },
                { key: "recent", label: "最近记录" },
              ] as { key: typeof searchTab; label: string }[]).map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => setSearchTab(key)}
                  className={cn(
                    "border-b-2 py-2 text-sm font-medium transition-colors",
                    searchTab === key ? "border-primary-600 text-primary-600" : "border-transparent text-slate-500",
                  )}
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Search input */}
            <div className="p-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <input
                  type="text"
                  placeholder="搜索角色..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="input pl-9"
                />
              </div>
            </div>

            {/* Results */}
            <div className="max-h-72 overflow-y-auto px-3 pb-3">
              {searchResults.map((c) => {
                const isRecommended = scene.characters.some((sc) => sc.id === c.id);
                return (
                  <button
                    key={c.id}
                    onClick={() => {
                      setSelectedCharId(c.id);
                      setShowSearch(false);
                    }}
                    className="flex w-full items-center gap-3 rounded-lg p-2 text-left transition-colors hover:bg-slate-50 dark:hover:bg-slate-700"
                  >
                    <img src={getAvatarUrl(c.avatar_url, c.name)} alt={c.name} className="h-10 w-10 rounded-full object-cover" />
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium">{c.name}</span>
                        {isRecommended && (
                          <span className="badge bg-amber-100 text-amber-700 text-[10px] dark:bg-amber-900/30 dark:text-amber-400">
                            Suggested
                          </span>
                        )}
                      </div>
                      <p className="truncate text-xs text-slate-400">{c.tagline}</p>
                    </div>
                    {selectedCharId === c.id && <Check className="h-4 w-4 text-primary-600" />}
                  </button>
                );
              })}
              {searchResults.length === 0 && (
                <p className="py-8 text-center text-sm text-slate-400">没有找到角色</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
