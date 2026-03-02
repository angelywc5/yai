import { clsx, type ClassValue } from "clsx";

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatNumber(n: number): string {
  if (n >= 1000000) return `${(n / 1000000).toFixed(1)}M`;
  if (n >= 1000) return `${(n / 1000).toFixed(1)}k`;
  return String(n);
}

export function timeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "刚刚";
  if (mins < 60) return `${mins}分钟前`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours}小时前`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days}天前`;
  return new Date(dateStr).toLocaleDateString("zh-CN");
}

export function getAvatarUrl(url: string | null, name: string): string {
  if (url) return url;
  return `https://ui-avatars.com/api/?name=${encodeURIComponent(name)}&background=6366f1&color=fff&size=128`;
}

export function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str;
  return str.slice(0, maxLen) + "...";
}

/* Parse SSE text stream */
export function parseSSELine(line: string): { event?: string; data?: string } | null {
  if (line.startsWith("event:")) return { event: line.slice(6).trim() };
  if (line.startsWith("data:")) return { data: line.slice(5).trim() };
  return null;
}

export const TIER_LABELS: Record<string, { label: string; cost: string; color: string }> = {
  speed: { label: "Speed", cost: "10积分/1K", color: "text-green-600" },
  pro: { label: "Pro", cost: "50积分/1K", color: "text-blue-600" },
  elite: { label: "Elite", cost: "150积分/1K", color: "text-purple-600" },
};

export const DIRECTIVE_PRESETS = [
  { mode: "narration", label: "旁白", instruction: "以第三人称旁白描写" },
  { mode: "ooc", label: "OOC", instruction: "跳出角色回复" },
  { mode: "inner", label: "内心", instruction: "描写内心独白" },
  { mode: "camera", label: "摄像机视角", instruction: "近景特写" },
  { mode: "narration", label: "描写画面", instruction: "详细描绘当前画面" },
  { mode: "narration", label: "详细描写", instruction: "增加细节描写" },
  { mode: "continue", label: "继续", instruction: "" },
];
