"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { characters, scenes, chat } from "@/lib/api";
import { useUser } from "@/lib/hooks";
import type { CharacterPublicResponse, SceneResponse, RecentCharacterResponse } from "@/lib/types";
import CharacterCard from "@/components/CharacterCard";
import SceneCard from "@/components/SceneCard";
import { ListSkeleton, SceneCardSkeleton } from "@/components/Skeleton";
import { getAvatarUrl, timeAgo } from "@/lib/utils";
import { ChevronRight } from "lucide-react";

const TAGS = ["闲聊", "角色扮演", "冒险", "恋爱", "恐怖", "科幻", "校园", "武侠", "治愈"];

export default function HomePage() {
  const { user } = useUser();
  const [recent, setRecent] = useState<RecentCharacterResponse[]>([]);
  const [hotChars, setHotChars] = useState<CharacterPublicResponse[]>([]);
  const [hotScenes, setHotScenes] = useState<SceneResponse[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [charsRes, scenesRes] = await Promise.all([
          characters.publicList(1, 8, "popular"),
          scenes.publicList(1, 6, "popular"),
        ]);
        setHotChars(charsRes.items);
        setHotScenes(scenesRes.items);
        if (user) {
          const rc = await chat.recentCharacters(6).catch(() => []);
          setRecent(rc);
        }
      } catch {
        // pass
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [user]);

  return (
    <div className="space-y-8">
      {/* Continue chats */}
      {user && recent.length > 0 && (
        <section>
          <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">
            📌 继续对话
          </h2>
          <div className="flex gap-3 overflow-x-auto pb-2">
            {recent.map((rc) => (
              <Link
                key={rc.character_id}
                href={`/chat/${rc.last_session_id}`}
                className="flex shrink-0 flex-col items-center gap-1 rounded-xl p-3 transition-colors hover:bg-slate-50 dark:hover:bg-slate-800"
              >
                <img
                  src={getAvatarUrl(rc.character_avatar_url, rc.character_name)}
                  alt={rc.character_name}
                  className="h-14 w-14 rounded-full object-cover ring-2 ring-primary-200 dark:ring-primary-800"
                />
                <span className="text-xs font-medium">{rc.character_name}</span>
                <span className="text-[10px] text-slate-400">{timeAgo(rc.last_message_at)}</span>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* Hot Characters */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-lg font-semibold">🔥 热门角色</h2>
          <Link href="/explore" className="btn-ghost text-xs">
            查看全部 <ChevronRight className="h-3 w-3" />
          </Link>
        </div>
        {loading ? (
          <ListSkeleton count={4} />
        ) : (
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
            {hotChars.map((c) => (
              <CharacterCard key={c.id} character={c} />
            ))}
          </div>
        )}
      </section>

      {/* Hot Scenes */}
      <section>
        <div className="mb-3 flex items-center justify-between">
          <h2 className="flex items-center gap-2 text-lg font-semibold">🎭 热门场景</h2>
          <Link href="/explore?tab=scenes" className="btn-ghost text-xs">
            查看全部 <ChevronRight className="h-3 w-3" />
          </Link>
        </div>
        {loading ? (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3">
            {Array.from({ length: 3 }).map((_, i) => <SceneCardSkeleton key={i} />)}
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3">
            {hotScenes.map((s) => (
              <SceneCard key={s.id} scene={s} />
            ))}
          </div>
        )}
      </section>

      {/* Category Tags */}
      <section>
        <h2 className="mb-3 flex items-center gap-2 text-lg font-semibold">📂 分类浏览</h2>
        <div className="flex flex-wrap gap-2">
          {TAGS.map((tag) => (
            <Link
              key={tag}
              href={`/explore?tag=${encodeURIComponent(tag)}`}
              className="badge bg-slate-100 text-slate-700 transition-colors hover:bg-primary-100 hover:text-primary-700 dark:bg-slate-700 dark:text-slate-300 dark:hover:bg-primary-900/30 dark:hover:text-primary-400"
            >
              {tag}
            </Link>
          ))}
        </div>
      </section>
    </div>
  );
}
