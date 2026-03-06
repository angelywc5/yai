"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { characters, chat } from "@/lib/api";
import type { CharacterResponse, SessionResponse } from "@/lib/types";
import { useUser } from "@/lib/hooks";
import { getAvatarUrl, formatNumber, timeAgo, truncate } from "@/lib/utils";
import { MessageCircle, Heart, Loader2, Plus, X } from "lucide-react";
import SceneCard from "@/components/SceneCard";

export default function CharacterDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const router = useRouter();
  const { user } = useUser();
  const [character, setCharacter] = useState<CharacterResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [starting, setStarting] = useState(false);
  const [showSessionPicker, setShowSessionPicker] = useState(false);
  const [sessions, setSessions] = useState<SessionResponse[]>([]);
  const [loadingSessions, setLoadingSessions] = useState(false);

  useEffect(() => {
    characters.get(id)
      .then(setCharacter)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [id]);

  const handleStartChat = async () => {
    if (!user) { router.push("/auth/login"); return; }
    setStarting(true);
    try {
      setLoadingSessions(true);
      const sessionList = await chat.sessions(id);
      if (sessionList.length === 0) {
        router.push(`/chat/new?character_id=${id}`);
      } else if (sessionList.length === 1) {
        router.push(`/chat/${sessionList[0].session_id}`);
      } else {
        setSessions(sessionList);
        setShowSessionPicker(true);
      }
    } catch {
      router.push(`/chat/new?character_id=${id}`);
    } finally {
      setStarting(false);
      setLoadingSessions(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  if (!character) {
    return <p className="py-12 text-center text-slate-400">角色不存在</p>;
  }

  const def = character.definition;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      {/* Header */}
      <div className="flex items-start gap-4">
        <img
          src={getAvatarUrl(character.avatar_url, character.name)}
          alt={character.name}
          className="h-20 w-20 rounded-full object-cover ring-4 ring-slate-100 dark:ring-slate-700"
        />
        <div className="flex-1">
          <h1 className="text-xl font-bold">{character.name}</h1>
          <p className="text-sm text-slate-500">{character.tagline}</p>
          <div className="mt-2 flex items-center gap-4 text-sm text-slate-400">
            <span>@{character.creator_username}</span>
            <span className="flex items-center gap-1">
              <MessageCircle className="h-3.5 w-3.5" /> {formatNumber(character.chat_count)}
            </span>
            <span className="flex items-center gap-1">
              <Heart className="h-3.5 w-3.5" /> {formatNumber(character.like_count)}
            </span>
          </div>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button onClick={handleStartChat} disabled={starting} className="btn-primary flex-1 gap-2">
          {starting ? <Loader2 className="h-4 w-4 animate-spin" /> : <MessageCircle className="h-4 w-4" />}
          开始对话
        </button>
      </div>

      {/* Session Picker Modal */}
      {showSessionPicker && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40" onClick={() => setShowSessionPicker(false)}>
          <div
            className="mx-4 w-full max-w-md rounded-xl bg-white p-5 shadow-2xl dark:bg-slate-800"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="mb-4 flex items-center justify-between">
              <h3 className="text-base font-semibold">选择对话</h3>
              <button onClick={() => setShowSessionPicker(false)} className="rounded p-1 text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700">
                <X className="h-5 w-5" />
              </button>
            </div>

            <div className="max-h-64 space-y-2 overflow-y-auto">
              {sessions.map((s, i) => (
                <button
                  key={s.session_id}
                  onClick={() => { setShowSessionPicker(false); router.push(`/chat/${s.session_id}`); }}
                  className="w-full rounded-lg border border-slate-200 p-3 text-left transition-colors hover:border-primary-300 hover:bg-primary-50/50 dark:border-slate-700 dark:hover:border-primary-700 dark:hover:bg-primary-900/10"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">
                      {i === 0 ? "最近对话" : `对话 ${sessions.length - i}`}
                    </span>
                    <span className="text-xs text-slate-400">{timeAgo(s.last_message_at)}</span>
                  </div>
                  <div className="mt-1 flex items-center gap-3 text-xs text-slate-400">
                    <span>{s.message_count} 条消息</span>
                  </div>
                  {s.last_message_preview && (
                    <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
                      &ldquo;{truncate(s.last_message_preview, 50)}&rdquo;
                    </p>
                  )}
                </button>
              ))}
            </div>

            <button
              onClick={() => { setShowSessionPicker(false); router.push(`/chat/new?character_id=${id}`); }}
              className="btn-secondary mt-4 flex w-full items-center justify-center gap-2"
            >
              <Plus className="h-4 w-4" /> 开始新对话
            </button>
          </div>
        </div>
      )}

      {/* Tags */}
      {character.tags.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {character.tags.map((tag) => (
            <span key={tag} className="badge bg-slate-100 text-slate-600 dark:bg-slate-700 dark:text-slate-300">{tag}</span>
          ))}
        </div>
      )}

      {/* Description */}
      <section>
        <h2 className="mb-2 text-sm font-semibold text-slate-600 dark:text-slate-400">角色介绍</h2>
        <div className="rounded-lg bg-slate-50 p-4 text-sm leading-relaxed dark:bg-slate-800">
          <p>{def.identity.background}</p>
          {def.identity.beliefs && (
            <p className="mt-2 text-slate-500">核心信念: {def.identity.beliefs}</p>
          )}
        </div>
      </section>

      {/* Personality */}
      <section>
        <h2 className="mb-2 text-sm font-semibold text-slate-600 dark:text-slate-400">性格特质</h2>
        <div className="flex flex-wrap gap-2">
          {def.personality.map((p) => (
            <span key={p} className="badge bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400">{p}</span>
          ))}
        </div>
      </section>

      {/* Speech style */}
      <section>
        <h2 className="mb-2 text-sm font-semibold text-slate-600 dark:text-slate-400">说话风格</h2>
        <div className="rounded-lg bg-slate-50 p-4 text-sm dark:bg-slate-800">
          <p>语调: {def.speech_style.tone}</p>
          {def.speech_style.catchphrases.length > 0 && (
            <p className="mt-1">口头禅: {def.speech_style.catchphrases.join("、")}</p>
          )}
        </div>
      </section>

      {/* Sample dialogues */}
      {def.sample_dialogues.length > 0 && (
        <section>
          <h2 className="mb-2 text-sm font-semibold text-slate-600 dark:text-slate-400">示例对话</h2>
          <div className="space-y-3">
            {def.sample_dialogues.map((d, i) => (
              <div key={i} className="rounded-lg bg-slate-50 p-3 text-sm dark:bg-slate-800">
                <p className="text-primary-600">用户: {d.user}</p>
                <p className="mt-1">{character.name}: {d.character}</p>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
