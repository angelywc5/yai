"use client";

import Link from "next/link";
import { MessageCircle } from "lucide-react";
import type { CharacterPublicResponse } from "@/lib/types";
import { getAvatarUrl, formatNumber } from "@/lib/utils";

interface CharacterCardProps {
  character: CharacterPublicResponse;
  linkToChat?: boolean;
}

export default function CharacterCard({ character, linkToChat = true }: CharacterCardProps) {
  const href = linkToChat ? `/character/${character.id}` : `/character/${character.id}`;

  return (
    <Link href={href} className="card group flex flex-col items-center p-4 text-center">
      <img
        src={getAvatarUrl(character.avatar_url, character.name)}
        alt={character.name}
        className="mb-3 h-16 w-16 rounded-full object-cover ring-2 ring-slate-100 transition-transform group-hover:scale-105 dark:ring-slate-700"
        loading="lazy"
      />
      <h3 className="mb-1 text-sm font-semibold leading-tight">{character.name}</h3>
      <p className="mb-2 line-clamp-2 text-xs text-slate-500 dark:text-slate-400">
        {character.tagline || "暂无简介"}
      </p>
      <div className="mt-auto flex items-center gap-1 text-xs text-slate-400">
        <span>@{character.creator_username}</span>
      </div>
      <div className="mt-1 flex items-center gap-1 text-xs text-slate-400">
        <MessageCircle className="h-3 w-3" />
        <span>{formatNumber(character.chat_count)}</span>
      </div>
    </Link>
  );
}
