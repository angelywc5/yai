"use client";

import { ThumbsUp, ThumbsDown, Pin, RotateCcw, Trash2, MoreHorizontal } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import type { MessageResponse } from "@/lib/types";
import { getAvatarUrl, cn } from "@/lib/utils";

interface ChatBubbleProps {
  message: MessageResponse;
  characterName?: string;
  characterAvatar?: string | null;
  isStreaming?: boolean;
  streamContent?: { speech: string; action: string; emotion: string };
  onFeedback?: (feedback: string) => void;
  onPin?: () => void;
  onRegenerate?: () => void;
  onDelete?: () => void;
}

function parseYamlContent(raw: string): { speech: string; action: string; emotion: string } {
  try {
    const lines = raw.split("\n");
    let speech = "", action = "", emotion = "";
    for (const line of lines) {
      if (line.startsWith("speech:")) speech = line.slice(7).trim().replace(/^["']|["']$/g, "");
      else if (line.startsWith("action:")) action = line.slice(7).trim().replace(/^["']|["']$/g, "");
      else if (line.startsWith("emotion:")) emotion = line.slice(8).trim().replace(/^["']|["']$/g, "");
    }
    if (speech || action || emotion) return { speech, action, emotion };
  } catch {
    // fallback
  }
  return { speech: raw, action: "", emotion: "" };
}

export default function ChatBubble({
  message,
  characterName = "AI",
  characterAvatar,
  isStreaming = false,
  streamContent,
  onFeedback,
  onPin,
  onRegenerate,
  onDelete,
}: ChatBubbleProps) {
  const isUser = message.role === "user";
  const [showMenu, setShowMenu] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handle = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setShowMenu(false);
    };
    document.addEventListener("mousedown", handle);
    return () => document.removeEventListener("mousedown", handle);
  }, []);

  const parsed = isUser
    ? { speech: message.content, action: "", emotion: "" }
    : streamContent || parseYamlContent(message.content);

  return (
    <div className={cn("group flex gap-3", isUser ? "flex-row-reverse" : "flex-row")}>
      {/* Avatar */}
      {!isUser && (
        <img
          src={getAvatarUrl(characterAvatar ?? null, characterName)}
          alt={characterName}
          className="h-8 w-8 shrink-0 rounded-full object-cover"
        />
      )}

      <div className={cn("max-w-[75%] space-y-1", isUser ? "items-end" : "items-start")}>
        {/* Action (AI only) */}
        {!isUser && parsed.action && (
          <div className="rounded-lg bg-slate-50 px-3 py-1.5 text-sm italic text-slate-500 dark:bg-slate-700/50 dark:text-slate-400">
            *{parsed.action}*
          </div>
        )}

        {/* Speech bubble */}
        <div
          className={cn(
            "rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
            isUser
              ? "bg-primary-600 text-white"
              : "bg-slate-100 text-slate-800 dark:bg-slate-700 dark:text-slate-100",
          )}
        >
          {parsed.speech}
          {isStreaming && (
            <span className="ml-1 inline-flex gap-0.5">
              <span className="typing-dot h-1 w-1 rounded-full bg-current" />
              <span className="typing-dot h-1 w-1 rounded-full bg-current" />
              <span className="typing-dot h-1 w-1 rounded-full bg-current" />
            </span>
          )}
        </div>

        {/* Emotion tag */}
        {!isUser && parsed.emotion && (
          <span className="inline-block rounded-full bg-amber-50 px-2 py-0.5 text-xs text-amber-600 dark:bg-amber-900/30 dark:text-amber-400">
            {parsed.emotion}
          </span>
        )}

        {/* Actions bar */}
        {!isStreaming && (
          <div className={cn(
            "flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100",
            isUser ? "justify-end" : "justify-start",
          )}>
            {!isUser && onFeedback && (
              <>
                <button
                  onClick={() => onFeedback("like")}
                  className={cn("btn-ghost p-1", message.feedback === "like" && "text-green-600")}
                  title="赞"
                >
                  <ThumbsUp className="h-3.5 w-3.5" />
                </button>
                <button
                  onClick={() => onFeedback("dislike")}
                  className={cn("btn-ghost p-1", message.feedback === "dislike" && "text-red-600")}
                  title="踩"
                >
                  <ThumbsDown className="h-3.5 w-3.5" />
                </button>
              </>
            )}
            {!isUser && onPin && (
              <button
                onClick={onPin}
                className={cn("btn-ghost p-1", message.is_pinned && "text-amber-500")}
                title={message.is_pinned ? "取消固定" : "固定"}
              >
                <Pin className="h-3.5 w-3.5" />
              </button>
            )}
            <div ref={menuRef} className="relative">
              <button onClick={() => setShowMenu(!showMenu)} className="btn-ghost p-1" title="更多">
                <MoreHorizontal className="h-3.5 w-3.5" />
              </button>
              {showMenu && (
                <div className="absolute left-0 top-full z-10 mt-1 w-32 rounded-lg border border-slate-200 bg-white py-1 shadow-lg dark:border-slate-600 dark:bg-slate-800">
                  {!isUser && onRegenerate && (
                    <button onClick={() => { onRegenerate(); setShowMenu(false); }} className="flex w-full items-center gap-2 px-3 py-1.5 text-xs hover:bg-slate-50 dark:hover:bg-slate-700">
                      <RotateCcw className="h-3 w-3" /> 重新生成
                    </button>
                  )}
                  {onDelete && (
                    <button onClick={() => { onDelete(); setShowMenu(false); }} className="flex w-full items-center gap-2 px-3 py-1.5 text-xs text-red-600 hover:bg-slate-50 dark:hover:bg-slate-700">
                      <Trash2 className="h-3 w-3" /> 删除
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
