"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { characters } from "@/lib/api";
import { Loader2, Plus, X } from "lucide-react";

export default function CreateCharacterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [name, setName] = useState("");
  const [tagline, setTagline] = useState("");
  const [background, setBackground] = useState("");
  const [beliefs, setBeliefs] = useState("");
  const [personality, setPersonality] = useState<string[]>([]);
  const [newTrait, setNewTrait] = useState("");
  const [tone, setTone] = useState("");
  const [catchphrases, setCatchphrases] = useState<string[]>([]);
  const [newPhrase, setNewPhrase] = useState("");
  const [punctuation, setPunctuation] = useState("");
  const [dialogues, setDialogues] = useState<{ user: string; character: string }[]>([{ user: "", character: "" }]);
  const [isPublic, setIsPublic] = useState(false);
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState("");

  const addTrait = () => {
    if (newTrait.trim() && personality.length < 5) {
      setPersonality([...personality, newTrait.trim()]);
      setNewTrait("");
    }
  };

  const addPhrase = () => {
    if (newPhrase.trim()) {
      setCatchphrases([...catchphrases, newPhrase.trim()]);
      setNewPhrase("");
    }
  };

  const addTag = () => {
    if (newTag.trim() && tags.length < 10) {
      setTags([...tags, newTag.trim()]);
      setNewTag("");
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (personality.length < 3) { setError("至少需要 3 个性格特质"); return; }
    setError("");
    setLoading(true);
    try {
      const result = await characters.create({
        name,
        tagline,
        definition: {
          identity: { name, background, beliefs },
          personality,
          speech_style: { tone, catchphrases, punctuation_habits: punctuation },
          sample_dialogues: dialogues.filter((d) => d.user && d.character),
        },
        tags,
        is_public: isPublic,
      });
      router.push(`/character/${result.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "创建失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="mb-6 text-xl font-bold">创建新角色</h1>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600 dark:bg-red-900/30 dark:text-red-400">{error}</div>
      )}

      <form onSubmit={handleSubmit} className="space-y-5">
        {/* Basic info */}
        <div>
          <label className="mb-1 block text-sm font-medium">角色名称 *</label>
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="input" required maxLength={100} />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">一句话简介</label>
          <input type="text" value={tagline} onChange={(e) => setTagline(e.target.value)} className="input" maxLength={200} placeholder="用一句话描述你的角色" />
        </div>

        {/* Identity */}
        <fieldset className="rounded-lg border border-slate-200 p-4 dark:border-slate-700">
          <legend className="text-sm font-semibold">📋 身份设定</legend>
          <div className="mt-2 space-y-3">
            <div>
              <label className="mb-1 block text-xs text-slate-500">背景故事 *</label>
              <textarea value={background} onChange={(e) => setBackground(e.target.value)} className="textarea" rows={3} required />
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-500">核心信念 *</label>
              <input type="text" value={beliefs} onChange={(e) => setBeliefs(e.target.value)} className="input" required />
            </div>
          </div>
        </fieldset>

        {/* Personality */}
        <fieldset className="rounded-lg border border-slate-200 p-4 dark:border-slate-700">
          <legend className="text-sm font-semibold">🎭 性格特质 (3-5个) *</legend>
          <div className="mt-2 flex flex-wrap gap-2">
            {personality.map((p, i) => (
              <span key={i} className="badge bg-primary-50 text-primary-700 dark:bg-primary-900/30 dark:text-primary-400">
                {p}
                <button type="button" onClick={() => setPersonality(personality.filter((_, j) => j !== i))} className="ml-1">
                  <X className="h-3 w-3" />
                </button>
              </span>
            ))}
          </div>
          {personality.length < 5 && (
            <div className="mt-2 flex gap-2">
              <input
                type="text"
                value={newTrait}
                onChange={(e) => setNewTrait(e.target.value)}
                onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addTrait(); } }}
                className="input flex-1"
                placeholder="添加特质..."
              />
              <button type="button" onClick={addTrait} className="btn-secondary"><Plus className="h-4 w-4" /></button>
            </div>
          )}
        </fieldset>

        {/* Speech style */}
        <fieldset className="rounded-lg border border-slate-200 p-4 dark:border-slate-700">
          <legend className="text-sm font-semibold">💬 说话风格</legend>
          <div className="mt-2 space-y-3">
            <div>
              <label className="mb-1 block text-xs text-slate-500">语调 *</label>
              <input type="text" value={tone} onChange={(e) => setTone(e.target.value)} className="input" required placeholder="例如：冷淡、温柔、傲娇" />
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-500">口头禅</label>
              <div className="flex flex-wrap gap-1">
                {catchphrases.map((p, i) => (
                  <span key={i} className="badge bg-slate-100 dark:bg-slate-700">
                    {p}
                    <button type="button" onClick={() => setCatchphrases(catchphrases.filter((_, j) => j !== i))} className="ml-1"><X className="h-3 w-3" /></button>
                  </span>
                ))}
              </div>
              <div className="mt-1 flex gap-2">
                <input type="text" value={newPhrase} onChange={(e) => setNewPhrase(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addPhrase(); } }} className="input flex-1" placeholder="添加口头禅..." />
                <button type="button" onClick={addPhrase} className="btn-secondary"><Plus className="h-4 w-4" /></button>
              </div>
            </div>
            <div>
              <label className="mb-1 block text-xs text-slate-500">标点习惯</label>
              <input type="text" value={punctuation} onChange={(e) => setPunctuation(e.target.value)} className="input" placeholder="例如：喜欢用省略号..." />
            </div>
          </div>
        </fieldset>

        {/* Sample dialogues */}
        <fieldset className="rounded-lg border border-slate-200 p-4 dark:border-slate-700">
          <legend className="text-sm font-semibold">📝 示例对话</legend>
          <div className="mt-2 space-y-3">
            {dialogues.map((d, i) => (
              <div key={i} className="rounded-lg bg-slate-50 p-3 dark:bg-slate-800">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-slate-400">示例 {i + 1}</span>
                  {dialogues.length > 1 && (
                    <button type="button" onClick={() => setDialogues(dialogues.filter((_, j) => j !== i))} className="text-red-500"><X className="h-3 w-3" /></button>
                  )}
                </div>
                <input type="text" value={d.user} onChange={(e) => { const nd = [...dialogues]; nd[i] = { ...nd[i], user: e.target.value }; setDialogues(nd); }} className="input mt-1" placeholder="用户说..." />
                <input type="text" value={d.character} onChange={(e) => { const nd = [...dialogues]; nd[i] = { ...nd[i], character: e.target.value }; setDialogues(nd); }} className="input mt-1" placeholder="角色说..." />
              </div>
            ))}
            {dialogues.length < 10 && (
              <button type="button" onClick={() => setDialogues([...dialogues, { user: "", character: "" }])} className="btn-secondary w-full gap-1">
                <Plus className="h-4 w-4" /> 添加示例对话
              </button>
            )}
          </div>
        </fieldset>

        {/* Tags */}
        <div>
          <label className="mb-1 block text-sm font-medium">标签</label>
          <div className="flex flex-wrap gap-1">
            {tags.map((t, i) => (
              <span key={i} className="badge bg-slate-100 dark:bg-slate-700">{t} <button type="button" onClick={() => setTags(tags.filter((_, j) => j !== i))}><X className="ml-1 h-3 w-3" /></button></span>
            ))}
          </div>
          <div className="mt-1 flex gap-2">
            <input type="text" value={newTag} onChange={(e) => setNewTag(e.target.value)} onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); addTag(); } }} className="input flex-1" placeholder="添加标签..." />
            <button type="button" onClick={addTag} className="btn-secondary"><Plus className="h-4 w-4" /></button>
          </div>
        </div>

        {/* Visibility */}
        <div className="flex items-center gap-3">
          <label className="text-sm font-medium">可见性:</label>
          <label className="flex items-center gap-1.5 text-sm">
            <input type="radio" checked={!isPublic} onChange={() => setIsPublic(false)} /> 仅自己
          </label>
          <label className="flex items-center gap-1.5 text-sm">
            <input type="radio" checked={isPublic} onChange={() => setIsPublic(true)} /> 公开
          </label>
        </div>

        <button type="submit" disabled={loading} className="btn-primary w-full">
          {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "保存角色"}
        </button>
      </form>
    </div>
  );
}
