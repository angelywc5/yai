"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { characters, scenes } from "@/lib/api";
import type { CharacterPublicResponse, SceneResponse } from "@/lib/types";
import CharacterCard from "@/components/CharacterCard";
import SceneCard from "@/components/SceneCard";
import { ListSkeleton, SceneCardSkeleton } from "@/components/Skeleton";
import { cn } from "@/lib/utils";

type TabType = "all" | "characters" | "scenes";

function SearchContent() {
  const searchParams = useSearchParams();
  const q = searchParams.get("q") || "";
  const [tab, setTab] = useState<TabType>("all");
  const [charResults, setCharResults] = useState<CharacterPublicResponse[]>([]);
  const [sceneResults, setSceneResults] = useState<SceneResponse[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!q.trim()) return;
    setLoading(true);
    Promise.all([
      characters.search(q, 1, 20),
      scenes.search(q, 1, 20),
    ])
      .then(([cr, sr]) => {
        setCharResults(cr.items);
        setSceneResults(sr.items);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [q]);

  const showChars = tab === "all" || tab === "characters";
  const showScenes = tab === "all" || tab === "scenes";

  return (
    <div className="space-y-4">
      <h1 className="text-lg font-semibold">
        搜索 &ldquo;{q}&rdquo; 的结果
      </h1>

      {/* Tabs */}
      <div className="flex items-center gap-4">
        {([
          { key: "all", label: "全部" },
          { key: "characters", label: `角色(${charResults.length})` },
          { key: "scenes", label: `场景(${sceneResults.length})` },
        ] as { key: TabType; label: string }[]).map(({ key, label }) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={cn(
              "border-b-2 pb-1 text-sm font-medium transition-colors",
              tab === key ? "border-primary-600 text-primary-600" : "border-transparent text-slate-500",
            )}
          >
            {label}
          </button>
        ))}
      </div>

      {loading ? (
        <ListSkeleton count={8} />
      ) : (
        <>
          {showChars && charResults.length > 0 && (
            <section>
              {tab === "all" && <h2 className="mb-2 text-sm font-semibold text-slate-600">角色</h2>}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
                {charResults.map((c) => <CharacterCard key={c.id} character={c} />)}
              </div>
            </section>
          )}
          {showScenes && sceneResults.length > 0 && (
            <section className="mt-6">
              {tab === "all" && <h2 className="mb-2 text-sm font-semibold text-slate-600">场景</h2>}
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3">
                {sceneResults.map((s) => <SceneCard key={s.id} scene={s} />)}
              </div>
            </section>
          )}
          {charResults.length === 0 && sceneResults.length === 0 && !loading && q && (
            <p className="py-12 text-center text-slate-400">没有找到匹配的结果</p>
          )}
        </>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <Suspense fallback={<ListSkeleton count={8} />}>
      <SearchContent />
    </Suspense>
  );
}
