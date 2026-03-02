"use client";

import Link from "next/link";
import { Eye, Play } from "lucide-react";
import type { SceneResponse } from "@/lib/types";
import { getAvatarUrl, formatNumber } from "@/lib/utils";

interface SceneCardProps {
  scene: SceneResponse;
}

export default function SceneCard({ scene }: SceneCardProps) {
  return (
    <Link href={`/scene/${scene.id}`} className="card group overflow-hidden p-0">
      {/* Cover */}
      <div className="relative h-32 bg-gradient-to-br from-primary-400 to-purple-500">
        {scene.cover_image_url && (
          <img src={scene.cover_image_url} alt={scene.name} className="h-full w-full object-cover" loading="lazy" />
        )}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 to-transparent" />
        <div className="absolute bottom-2 left-3 right-3">
          <h3 className="text-sm font-bold text-white">{scene.name}</h3>
        </div>
      </div>

      <div className="p-3">
        <p className="mb-2 line-clamp-2 text-xs text-slate-500 dark:text-slate-400">
          {scene.description}
        </p>

        {/* Tags */}
        {(scene.genre || scene.mood) && (
          <div className="mb-2 flex flex-wrap gap-1">
            {scene.genre && (
              <span className="badge bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400">
                {scene.genre}
              </span>
            )}
            {scene.mood && (
              <span className="badge bg-purple-50 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400">
                {scene.mood}
              </span>
            )}
          </div>
        )}

        {/* Character avatars */}
        {scene.characters.length > 0 && (
          <div className="mb-2 flex -space-x-2">
            {scene.characters.slice(0, 4).map((c) => (
              <img
                key={c.id}
                src={getAvatarUrl(c.avatar_url, c.name)}
                alt={c.name}
                className="h-6 w-6 rounded-full border-2 border-white object-cover dark:border-slate-800"
                title={c.name}
              />
            ))}
            {scene.characters.length > 4 && (
              <div className="flex h-6 w-6 items-center justify-center rounded-full border-2 border-white bg-slate-200 text-[10px] dark:border-slate-800 dark:bg-slate-600">
                +{scene.characters.length - 4}
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <div className="flex items-center justify-between text-xs text-slate-400">
          <div className="flex items-center gap-1">
            <Play className="h-3 w-3" /> 开始
          </div>
          <div className="flex items-center gap-1">
            <Eye className="h-3 w-3" /> {formatNumber(scene.play_count)}
          </div>
        </div>
      </div>
    </Link>
  );
}
