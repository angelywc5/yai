"use client";

import { Suspense, useEffect, useState, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { ArrowLeft, Send, Loader2 } from "lucide-react";
import { characters, streamChat } from "@/lib/api";
import { useUser } from "@/lib/hooks";
import type { MessageResponse, ModelTier } from "@/lib/types";
import ChatBubble from "@/components/ChatBubble";
import { getAvatarUrl, TIER_LABELS, DIRECTIVE_PRESETS, parseSSELine, cn } from "@/lib/utils";

function NewChatContent() {
  const searchParams = useSearchParams();
  const characterId = searchParams.get("character_id") || "";
  const sceneId = searchParams.get("scene_id") || undefined;
  const router = useRouter();
  const { user } = useUser();

  const [charName, setCharName] = useState("AI");
  const [charAvatar, setCharAvatar] = useState<string | null>(null);
  const [messages, setMessages] = useState<MessageResponse[]>([]);
  const [input, setInput] = useState("");
  const [tier, setTier] = useState<ModelTier>("speed");
  const [sending, setSending] = useState(false);
  const [streamSpeech, setStreamSpeech] = useState("");
  const [streamAction, setStreamAction] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (characterId) {
      characters.get(characterId)
        .then((c) => { setCharName(c.name); setCharAvatar(c.avatar_url); })
        .catch(() => {});
    }
  }, [characterId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamSpeech]);

  const handleSend = async () => {
    if (!input.trim() || sending || !characterId) return;
    const text = input.trim();
    setInput("");
    setSending(true);
    setStreamSpeech("");
    setStreamAction("");

    const tempMsg: MessageResponse = {
      id: `temp-${Date.now()}`, role: "user", content: text, token_count: 0,
      turn_number: messages.length + 1, feedback: null, is_pinned: false,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempMsg]);

    try {
      const { reader: readerPromise } = streamChat({
        character_id: characterId,
        scene_id: sceneId,
        message: text,
        model_tier: tier,
        session_id: sessionId || undefined,
        directives: [],
      });

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
          if (!parsed || parsed.data === undefined) continue;
          try {
            const obj = JSON.parse(parsed.data);
            if (obj.session_id && !sessionId) setSessionId(obj.session_id);
            if (obj.speech !== undefined) { accSpeech = obj.speech; setStreamSpeech(accSpeech); }
            if (obj.action !== undefined) { accAction = obj.action; setStreamAction(accAction); }
            if (obj.emotion !== undefined) accEmotion = obj.emotion;
            if (obj.type === "done" || obj.done) {
              const finalMsg: MessageResponse = {
                id: obj.message_id || `ai-${Date.now()}`, role: "assistant",
                content: `speech: ${accSpeech}\naction: ${accAction}\nemotion: ${accEmotion}`,
                token_count: obj.token_count || 0, turn_number: messages.length + 2,
                feedback: null, is_pinned: false, created_at: new Date().toISOString(),
              };
              setMessages((prev) => [...prev, finalMsg]);
              setStreamSpeech("");
              setStreamAction("");
              // Redirect to session page if we got a session_id
              if (obj.session_id) {
                router.replace(`/chat/${obj.session_id}`);
              }
            }
          } catch {
            accSpeech += parsed.data;
            setStreamSpeech(accSpeech);
          }
        }
      }
    } catch {
      // error
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col lg:ml-[-1rem] lg:mr-[-1rem]">
      <div className="flex items-center gap-3 border-b border-slate-200 px-4 py-2 dark:border-slate-700">
        <button onClick={() => router.back()} className="btn-ghost p-1">
          <ArrowLeft className="h-5 w-5" />
        </button>
        <img src={getAvatarUrl(charAvatar, charName)} alt={charName} className="h-8 w-8 rounded-full object-cover" />
        <p className="text-sm font-semibold">{charName}</p>
        <span className="ml-auto text-xs text-slate-400">新对话</span>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4">
        <div className="mx-auto max-w-2xl space-y-4">
          {messages.map((msg) => (
            <ChatBubble key={msg.id} message={msg} characterName={charName} characterAvatar={charAvatar} />
          ))}
          {sending && streamSpeech && (
            <ChatBubble
              message={{ id: "s", role: "assistant", content: "", token_count: 0, turn_number: 0, feedback: null, is_pinned: false, created_at: "" }}
              characterName={charName} characterAvatar={charAvatar} isStreaming
              streamContent={{ speech: streamSpeech, action: streamAction, emotion: "" }}
            />
          )}
          {sending && !streamSpeech && (
            <div className="flex items-center gap-2 text-sm text-slate-400">
              <img src={getAvatarUrl(charAvatar, charName)} alt="" className="h-8 w-8 rounded-full" />
              正在输入...
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </div>

      <div className="border-t border-slate-200 bg-white px-4 py-3 dark:border-slate-700 dark:bg-slate-900">
        <div className="mx-auto flex max-w-2xl items-end gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); handleSend(); } }}
            placeholder="输入消息开始对话..."
            rows={1}
            className="textarea min-h-[40px] flex-1"
          />
          <button onClick={handleSend} disabled={!input.trim() || sending} className="btn-primary shrink-0 p-2.5">
            {sending ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function NewChatPage() {
  return (
    <Suspense fallback={
      <div className="flex h-[calc(100vh-3.5rem)] items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
      </div>
    }>
      <NewChatContent />
    </Suspense>
  );
}
