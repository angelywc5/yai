"use client";

import { useEffect, useState, useCallback } from "react";
import { useSearchParams } from "next/navigation";
import { characters, scenes } from "@/lib/api";
import type { CharacterPublicResponse, SceneResponse } from "@/lib/types";
import CharacterCard from "@/components/CharacterCard";
import SceneCard from "@/components/SceneCard";
import { ListSkeleton, SceneCardSkeleton } from "@/components/Skeleton";
import { useDebounce, useIntersection } from "@/lib/hooks";
import { cn } from "@/lib/utils";
import { Search } from "lucide-react";

const CHAR_TAGS = ["全部", "闲聊", "角色扮演", "冒险", "恋爱", "恐怖", "科幻", "校园"];
const SCENE_TAGS = ["全部", "悬疑", "冒险", "恋爱", "恐怖", "科幻", "奇幻", "校园"];

type TabType = "characters" | "scenes";
type SortType = "popular" | "newest";

export default function ExplorePage() {
  const searchParams = useSearchParams();
  const initialTab = searchParams.get("tab") === "scenes" ? "scenes" : "characters";
  const initialTag = searchParams.get("tag") || "";

  const [tab, setTab] = useState<TabType>(initialTab);
  const [sort, setSort] = useState<SortType>("popular");
  const [query, setQuery] = useState("");
  const [selectedTag, setSelectedTag] = useState(initialTag);
  const debouncedQuery = useDebounce(query, 300);

  const [charItems, setCharItems] = useState<CharacterPublicResponse[]>([]);
  const [sceneItems, setSceneItems] = useState<SceneResponse[]>([]);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [loading, setLoading] = useState(true);

  const loadData = useCallback(async (reset = false) => {
    const p = reset ? 1 : page;
    setLoading(true);
    try {
      if (tab === "characters") {
        const tag = selectedTag && selectedTag !== "全部" ? selectedTag : undefined;
        const res = debouncedQuery
          ? await characters.search(debouncedQuery, p, 20, tag)
          : await characters.publicList(p, 20, sort);
        setCharItems(reset ? res.items : [...charItems, ...res.items]);
        setHasMore(p < res.pages);
      } else {
        const tag = selectedTag && selectedTag !== "全部" ? selectedTag : undefined;
        const res = debouncedQuery
          ? await scenes.search(debouncedQuery, p, 20, tag)
          : await scenes.publicList(p, 20, sort);
        setSceneItems(reset ? res.items : [...sceneItems, ...res.items]);
        setHasMore(p < res.pages);
      }
      if (reset) setPage(1);
    } catch {
      // pass
    } finally {
      setLoading(false);
    }
  }, [tab, sort, debouncedQuery, selectedTag, page, charItems, sceneItems]);

  useEffect(() => {
    loadData(true);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, sort, debouncedQuery, selectedTag]);

  const loadMore = useCallback(() => {
    if (!loading && hasMore) {
      setPage((p) => p + 1);
    }
  }, [loading, hasMore]);

  useEffect(() => {
    if (page > 1) loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  const sentinelRef = useIntersection(loadMore);

  const tags = tab === "characters" ? CHAR_TAGS : SCENE_TAGS;

  return (
    <div className="space-y-4">
      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="搜索角色和场景..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          className="input pl-9"
        />
      </div>

      {/* Tabs */}
      <div className="flex items-center gap-4">
        {(["characters", "scenes"] as TabType[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={cn(
              "border-b-2 pb-1 text-sm font-medium transition-colors",
              tab === t ? "border-primary-600 text-primary-600" : "border-transparent text-slate-500 hover:text-slate-700",
            )}
          >
            {t === "characters" ? "角色" : "场景"}
          </button>
        ))}
      </div>

      {/* Tags */}
      <div className="flex flex-wrap gap-2">
        {tags.map((tag) => (
          <button
            key={tag}
            onClick={() => setSelectedTag(tag === "全部" ? "" : tag)}
            className={cn(
              "badge transition-colors",
              (tag === "全部" && !selectedTag) || selectedTag === tag
                ? "bg-primary-100 text-primary-700 dark:bg-primary-900/40 dark:text-primary-400"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-300",
            )}
          >
            {tag}
          </button>
        ))}
      </div>

      {/* Sort */}
      <div className="flex gap-2 text-xs">
        {(["popular", "newest"] as SortType[]).map((s) => (
          <button
            key={s}
            onClick={() => setSort(s)}
            className={cn(
              "rounded-lg px-3 py-1.5 transition-colors",
              sort === s ? "bg-primary-600 text-white" : "bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300",
            )}
          >
            {s === "popular" ? "最热门" : "最新"}
          </button>
        ))}
      </div>

      {/* Grid */}
      {tab === "characters" ? (
        loading && charItems.length === 0 ? (
          <ListSkeleton count={8} />
        ) : (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
            {charItems.map((c) => (
              <CharacterCard key={c.id} character={c} />
            ))}
          </div>
        )
      ) : loading && sceneItems.length === 0 ? (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => <SceneCardSkeleton key={i} />)}
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3">
          {sceneItems.map((s) => (
            <SceneCard key={s.id} scene={s} />
          ))}
        </div>
      )}

      {/* Sentinel for infinite scroll */}
      {hasMore && <div ref={sentinelRef} className="h-10" />}
      {!hasMore && (charItems.length > 0 || sceneItems.length > 0) && (
        <p className="text-center text-sm text-slate-400">已加载全部内容</p>
      )}
    </div>
  );
}
