"use client";

import { useEffect, useState, useRef, useCallback } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Send, Loader2, ClipboardList, BookOpen, MessageSquarePlus } from "lucide-react";
import { chat, streamChat } from "@/lib/api";
import { useUser } from "@/lib/hooks";
import type { MessageResponse, ChatDirective, ModelTier } from "@/lib/types";
import ChatBubble from "@/components/ChatBubble";
import ModelSelector from "@/components/ModelSelector";
import SessionDrawer from "@/components/SessionDrawer";
import SummaryDrawer from "@/components/SummaryDrawer";
import { cn, TIER_LABELS, DIRECTIVE_PRESETS, parseSSELine, getAvatarUrl } from "@/lib/utils";

export default function ChatPage() {
  const params = useParams();
  const sessionId = params.sessionId as string;
  const router = useRouter();
  const { user } = useUser();

  const [messages, setMessages] = useState<MessageResponse[]>([]);
  const [characterId, setCharacterId] = useState("");
  const [characterName, setCharacterName] = useState("AI");
  const [characterAvatar, setCharacterAvatar] = useState<string | null>(null);
  const [sceneName, setSceneName] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [input, setInput] = useState("");
  const [tier, setTier] = useState<ModelTier>("speed");
  const [directives, setDirectives] = useState<ChatDirective[]>([]);
  const [streamSpeech, setStreamSpeech] = useState("");
  const [streamAction, setStreamAction] = useState("");
  const [hasMore, setHasMore] = useState(false);
  const [nextBefore, setNextBefore] = useState<string | null>(null);
  const [showSessions, setShowSessions] = useState(false);
  const [showSummary, setShowSummary] = useState(false);

  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const abortRef = useRef<(() => void) | null>(null);

  // Load initial history
  useEffect(() => {
    if (!user) return;
    const loadHistory = async () => {
      try {
        const recentChars = await chat.recentCharacters(20);
        const match = recentChars.find((rc) => rc.last_session_id === sessionId);
        if (match) {
          setCharacterId(match.character_id);
          setCharacterName(match.character_name);
          setCharacterAvatar(match.character_avatar_url);
          const hist = await chat.history(match.character_id, sessionId);
          setMessages(hist.items);
          setHasMore(hist.has_more);
          setNextBefore(hist.next_before_message_id);
        }
      } catch {
        // pass
      } finally {
        setLoading(false);
      }
    };
    loadHistory();
  }, [sessionId, user]);

  // Auto scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamSpeech]);

  // Load more history
  const loadMore = useCallback(async () => {
    if (!hasMore || !nextBefore || !characterId) return;
    const hist = await chat.history(characterId, sessionId, nextBefore);
    setMessages((prev) => [...hist.items, ...prev]);
    setHasMore(hist.has_more);
    setNextBefore(hist.next_before_message_id);
  }, [hasMore, nextBefore, characterId, sessionId]);

  // Send message
  const handleSend = async () => {
    if (!input.trim() || sending || !characterId) return;
    const text = input.trim();
    setInput("");
    setSending(true);
    setStreamSpeech("");
    setStreamAction("");

    const tempUserMsg: MessageResponse = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: text,
      token_count: 0,
      turn_number: messages.length + 1,
      feedback: null,
      is_pinned: false,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const { reader: readerPromise, abort } = streamChat({
        character_id: characterId,
        message: text,
        model_tier: tier,
        session_id: sessionId,
        directives,
      });
      abortRef.current = abort;

      const reader = await readerPromise;
      const decoder = new TextDecoder();
      let buffer = "";
      let accSpeech = "";
      let accAction = "";
      let accEmotion = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          if (!line.trim()) continue;
          const parsed = parseSSELine(line);
          if (!parsed) continue;

          if (parsed.data !== undefined) {
            try {
              const obj = JSON.parse(parsed.data);
              if (obj.speech !== undefined) { accSpeech = obj.speech; setStreamSpeech(accSpeech); }
              if (obj.action !== undefined) { accAction = obj.action; setStreamAction(accAction); }
              if (obj.emotion !== undefined) accEmotion = obj.emotion;
              if (obj.type === "done" || obj.done) {
                const finalMsg: MessageResponse = {
                  id: obj.message_id || `ai-${Date.now()}`,
                  role: "assistant",
                  content: `speech: ${accSpeech}\naction: ${accAction}\nemotion: ${accEmotion}`,
                  token_count: obj.token_count || 0,
                  turn_number: messages.length + 2,
                  feedback: null,
                  is_pinned: false,
                  created_at: new Date().toISOString(),
                };
                setMessages((prev) => [...prev, finalMsg]);
                setStreamSpeech("");
                setStreamAction("");
              }
            } catch {
              accSpeech += parsed.data;
              setStreamSpeech(accSpeech);
            }
          }
        }
      }
    } catch (err) {
      if ((err as Error).name !== "AbortError") {
        const errorMsg: MessageResponse = {
          id: `err-${Date.now()}`,
          role: "assistant",
          content: "speech: 抱歉，出现了一点问题，请重试。",
          token_count: 0,
          turn_number: messages.length + 2,
          feedback: null,
          is_pinned: false,
          created_at: new Date().toISOString(),
        };
        setMessages((prev) => [...prev, errorMsg]);
      }
    } finally {
      setSending(false);
      setDirectives([]);
      abortRef.current = null;
    }
  };

  const toggleDirective = (preset: (typeof DIRECTIVE_PRESETS)[number]) => {
    setDirectives((prev) => {
      const exists = prev.find((d) => d.mode === preset.mode && d.instruction === preset.instruction);
      if (exists) return prev.filter((d) => d !== exists);
      return [...prev, { mode: preset.mode, instruction: preset.instruction }];
    });
  };

  if (loading) {
    return (
      <div className="flex h-[60vh] items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary-600" />
      </div>
    );
  }

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col lg:ml-[-1rem] lg:mr-[-1rem]">
      {/* Header */}
      <div className="flex items-center gap-3 border-b border-slate-200 px-4 py-2 dark:border-slate-700">
        <button onClick={() => router.back()} className="btn-ghost p-1">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <img
          src={getAvatarUrl(characterAvatar, characterName)}
          alt={characterName}
          className="h-8 w-8 rounded-full object-cover"
        />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-semibold">{characterName}</p>
          {sceneName && <p className="text-xs text-slate-400">{sceneName}</p>}
        </div>
        <div className="flex items-center gap-1">
          <button onClick={() => setShowSessions(true)} className="btn-ghost p-1.5" title="会话记录">
            <ClipboardList className="h-4.5 w-4.5" />
          </button>
          <button onClick={() => setShowSummary(true)} className="btn-ghost p-1.5" title="故事梗概">
            <BookOpen className="h-4.5 w-4.5" />
          </button>
          <button
            onClick={() => router.push(`/chat/new?character_id=${characterId}`)}
            className="btn-ghost flex items-center gap-1 px-2 py-1.5 text-xs font-medium"
          >
            <MessageSquarePlus className="h-4 w-4" /> 新对话
          </button>
        </div>
      </div>

      {/* Messages */}
      <div ref={containerRef} className="flex-1 overflow-y-auto px-4 py-4">
        {hasMore && (
          <button onClick={loadMore} className="mx-auto mb-4 block text-xs text-primary-600 hover:underline">
            加载更早的消息
          </button>
        )}
        <div className="mx-auto max-w-2xl space-y-4">
          {messages.map((msg) => (
            <ChatBubble
              key={msg.id}
              message={msg}
              characterName={characterName}
              characterAvatar={characterAvatar}
              onFeedback={(fb) => chat.feedback(msg.id, { feedback: fb })}
              onPin={() => chat.pin(msg.id)}
              onRegenerate={() => chat.regenerate(msg.id, { model_tier: tier })}
              onDelete={() => {
                chat.deleteMessage(msg.id);
                setMessages((prev) => prev.filter((m) => m.id !== msg.id));
              }}
            />
          ))}
          {/* Streaming bubble */}
          {sending && streamSpeech && (
            <ChatBubble
              message={{
                id: "streaming",
                role: "assistant",
                content: "",
                token_count: 0,
                turn_number: 0,
                feedback: null,
                is_pinned: false,
                created_at: new Date().toISOString(),
              }}
              characterName={characterName}
              characterAvatar={characterAvatar}
              isStreaming
              streamContent={{ speech: streamSpeech, action: streamAction, emotion: "" }}
            />
          )}
          {sending && !streamSpeech && (
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <img src={getAvatarUrl(characterAvatar, characterName)} alt="" className="h-8 w-8 rounded-full" />
              <span className="flex gap-1">
                正在输入
                <span className="typing-dot h-1.5 w-1.5 rounded-full bg-slate-400" />
                <span className="typing-dot h-1.5 w-1.5 rounded-full bg-slate-400" />
                <span className="typing-dot h-1.5 w-1.5 rounded-full bg-slate-400" />
              </span>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      {/* Input area */}
      <div className="border-t border-slate-200 bg-white px-4 py-3 dark:border-slate-700 dark:bg-slate-900">
        <div className="mx-auto max-w-2xl">
          {/* Directives */}
          <div className="mb-2 flex flex-wrap gap-1.5">
            {DIRECTIVE_PRESETS.map((preset) => {
              const active = directives.some(
                (d) => d.mode === preset.mode && d.instruction === preset.instruction,
              );
              return (
                <button
                  key={preset.label}
                  onClick={() => toggleDirective(preset)}
                  className={cn(
                    "rounded-full px-2.5 py-1 text-xs transition-colors",
                    active
                      ? "bg-primary-100 text-primary-700 dark:bg-primary-900/40 dark:text-primary-400"
                      : "bg-slate-100 text-slate-500 hover:bg-slate-200 dark:bg-slate-700 dark:text-slate-400",
                  )}
                >
                  {preset.label}
                </button>
              );
            })}
          </div>

          {/* Input box with model selector */}
          <div className="flex items-end gap-2">
            <ModelSelector value={tier} onChange={setTier} />
            <div className="relative flex-1">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); }
                }}
                placeholder="输入消息..."
                rows={1}
                className="textarea max-h-32 min-h-[40px] pr-4"
                style={{ height: "auto", overflow: "hidden" }}
                onInput={(e) => {
                  const t = e.currentTarget;
                  t.style.height = "auto";
                  t.style.height = `${Math.min(t.scrollHeight, 128)}px`;
                }}
              />
            </div>
            <button
              onClick={handleSend}
              disabled={!input.trim() || sending}
              className="btn-primary shrink-0 p-2.5"
            >
              {sending ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
            </button>
          </div>

          {/* Footer info */}
          <div className="mt-1.5 flex items-center justify-between text-xs text-slate-400">
            <span className={TIER_LABELS[tier].color}>
              {TIER_LABELS[tier].cost}
            </span>
            {directives.length > 0 && (
              <span>指令: {directives.map((d) => d.mode).join(", ")}</span>
            )}
            {user && <span>积分: {user.credits}</span>}
          </div>
        </div>
      </div>

      {/* Drawers */}
      {characterId && (
        <SessionDrawer
          characterId={characterId}
          currentSessionId={sessionId}
          open={showSessions}
          onClose={() => setShowSessions(false)}
          onSelectSession={(id) => router.push(`/chat/${id}`)}
          onNewSession={() => router.push(`/chat/new?character_id=${characterId}`)}
        />
      )}
      <SummaryDrawer
        sessionId={sessionId}
        open={showSummary}
        onClose={() => setShowSummary(false)}
      />
    </div>
  );
}
