"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { scenes, characters } from "@/lib/api";
import type { CharacterPublicResponse } from "@/lib/types";
import { getAvatarUrl, cn } from "@/lib/utils";
import { Loader2, Plus, X, Search, ChevronRight, ChevronLeft } from "lucide-react";

const GENRE_SUGGESTIONS = ["Mystery", "Sci-Fi", "Fantasy", "Slice-of-Life", "Romance", "Action/Thriller", "Horror", "Comedy", "Adventure"];
const TIME_SUGGESTIONS = ["Prehistoric", "Ancient Times", "Middle Ages", "Renaissance", "1800s", "Modern", "Future"];
const LOCATION_SUGGESTIONS = ["Mansion", "Train", "Museum", "Space Station", "City", "Forest", "School", "Starship"];
const MOOD_SUGGESTIONS = ["Angry", "Cozy", "Tense", "Whimsical", "Dark", "Romantic", "Hopeful", "Comedic"];

function TagSuggestions({ suggestions, value, onChange }: { suggestions: string[]; value: string; onChange: (v: string) => void }) {
  return (
    <div className="mt-1 flex flex-wrap gap-1">
      {suggestions.map((s) => (
        <button
          key={s}
          type="button"
          onClick={() => onChange(s)}
          className={cn("badge transition-colors", value === s ? "bg-primary-100 text-primary-700" : "bg-slate-100 text-slate-500 hover:bg-slate-200")}
        >
          {s}
        </button>
      ))}
    </div>
  );
}

export default function CreateScenePage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Step 1
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [genre, setGenre] = useState("");
  const [timePeriod, setTimePeriod] = useState("");
  const [settingLocation, setSettingLocation] = useState("");
  const [mood, setMood] = useState("");
  const [sceneDefinition, setSceneDefinition] = useState("");
  const [playerObjective, setPlayerObjective] = useState("");

  // Step 2
  const [greeting, setGreeting] = useState("");
  const [allowCharSelection, setAllowCharSelection] = useState(false);
  const [boundChars, setBoundChars] = useState<CharacterPublicResponse[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<CharacterPublicResponse[]>([]);
  const [tags, setTags] = useState<string[]>([]);
  const [newTag, setNewTag] = useState("");
  const [isPublic, setIsPublic] = useState(false);

  const searchChars = async () => {
    try {
      const res = searchQuery
        ? await characters.search(searchQuery, 1, 10)
        : await characters.myList(1, 10);
      setSearchResults(res.items);
    } catch {
      setSearchResults([]);
    }
  };

  const addTag = () => {
    if (newTag.trim() && tags.length < 10) {
      setTags([...tags, newTag.trim()]);
      setNewTag("");
    }
  };

  const handleSubmit = async () => {
    setError("");
    setLoading(true);
    try {
      const result = await scenes.create({
        name,
        description,
        genre,
        time_period: timePeriod,
        setting_location: settingLocation,
        mood,
        scene_definition: sceneDefinition,
        player_objective: playerObjective,
        greeting,
        allow_character_selection: allowCharSelection,
        character_ids: boundChars.map((c) => c.id),
        tags,
        is_public: isPublic,
      });
      router.push(`/scene/${result.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "创建失败");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-xl">
      <h1 className="mb-1 text-xl font-bold">创建新场景</h1>
      <p className="mb-6 text-sm text-slate-500">步骤 {step}/2</p>

      {error && (
        <div className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600 dark:bg-red-900/30 dark:text-red-400">{error}</div>
      )}

      {step === 1 && (
        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">场景名称 *</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} className="input" required maxLength={100} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">场景描述 (玩家可见) *</label>
            <textarea value={description} onChange={(e) => setDescription(e.target.value)} className="textarea" rows={3} required />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">场景类型 (genre)</label>
            <input type="text" value={genre} onChange={(e) => setGenre(e.target.value)} className="input" maxLength={100} />
            <TagSuggestions suggestions={GENRE_SUGGESTIONS} value={genre} onChange={setGenre} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">时期</label>
            <input type="text" value={timePeriod} onChange={(e) => setTimePeriod(e.target.value)} className="input" maxLength={100} />
            <TagSuggestions suggestions={TIME_SUGGESTIONS} value={timePeriod} onChange={setTimePeriod} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">地点</label>
            <input type="text" value={settingLocation} onChange={(e) => setSettingLocation(e.target.value)} className="input" maxLength={100} />
            <TagSuggestions suggestions={LOCATION_SUGGESTIONS} value={settingLocation} onChange={setSettingLocation} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">语调</label>
            <input type="text" value={mood} onChange={(e) => setMood(e.target.value)} className="input" maxLength={100} />
            <TagSuggestions suggestions={MOOD_SUGGESTIONS} value={mood} onChange={setMood} />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">背景故事 *</label>
            <p className="mb-1 text-xs text-slate-400">使用 {"{{user}}"} 表示用户，{"{{char}}"} 表示角色</p>
            <textarea value={sceneDefinition} onChange={(e) => setSceneDefinition(e.target.value)} className="textarea" rows={5} required />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium">玩家目标</label>
            <textarea value={playerObjective} onChange={(e) => setPlayerObjective(e.target.value)} className="textarea" rows={2} maxLength={1000} />
          </div>
          <button onClick={() => setStep(2)} disabled={!name || !description || !sceneDefinition} className="btn-primary w-full gap-1">
            下一步 <ChevronRight className="h-4 w-4" />
          </button>
        </div>
      )}

      {step === 2 && (
        <div className="space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium">角色开场白 *</label>
            <textarea value={greeting} onChange={(e) => setGreeting(e.target.value)} className="textarea" rows={3} required maxLength={2000} />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium">角色绑定</label>
            <div className="mb-2 flex items-center gap-3 text-sm">
              <label className="flex items-center gap-1.5">
                <input type="radio" checked={!allowCharSelection} onChange={() => setAllowCharSelection(false)} /> 使用预设角色
              </label>
              <label className="flex items-center gap-1.5">
                <input type="radio" checked={allowCharSelection} onChange={() => setAllowCharSelection(true)} /> 允许用户自选
              </label>
            </div>

            {/* Character search */}
            <div className="relative mb-2">
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onFocus={searchChars}
                onKeyDown={(e) => { if (e.key === "Enter") { e.preventDefault(); searchChars(); } }}
                className="input pl-9"
                placeholder="搜索角色..."
              />
            </div>
            {searchResults.length > 0 && (
              <div className="mb-2 max-h-40 overflow-y-auto rounded-lg border border-slate-200 dark:border-slate-700">
                {searchResults.map((c) => (
                  <button
                    key={c.id}
                    type="button"
                    onClick={() => {
                      if (!boundChars.find((bc) => bc.id === c.id)) setBoundChars([...boundChars, c]);
                      setSearchResults([]);
                      setSearchQuery("");
                    }}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-700"
                  >
                    <img src={getAvatarUrl(c.avatar_url, c.name)} alt={c.name} className="h-6 w-6 rounded-full" />
                    {c.name}
                  </button>
                ))}
              </div>
            )}
            <div className="flex flex-wrap gap-2">
              {boundChars.map((c) => (
                <div key={c.id} className="flex items-center gap-1 rounded-lg bg-slate-100 px-2 py-1 text-sm dark:bg-slate-700">
                  <img src={getAvatarUrl(c.avatar_url, c.name)} alt={c.name} className="h-5 w-5 rounded-full" />
                  {c.name}
                  <button type="button" onClick={() => setBoundChars(boundChars.filter((bc) => bc.id !== c.id))}><X className="h-3 w-3" /></button>
                </div>
              ))}
            </div>
          </div>

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
            <label className="flex items-center gap-1.5 text-sm"><input type="radio" checked={!isPublic} onChange={() => setIsPublic(false)} /> 仅自己</label>
            <label className="flex items-center gap-1.5 text-sm"><input type="radio" checked={isPublic} onChange={() => setIsPublic(true)} /> 公开</label>
          </div>

          <div className="flex gap-3">
            <button onClick={() => setStep(1)} className="btn-secondary flex-1 gap-1">
              <ChevronLeft className="h-4 w-4" /> 上一步
            </button>
            <button onClick={handleSubmit} disabled={loading || !greeting} className="btn-primary flex-1">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "保存并开始"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
