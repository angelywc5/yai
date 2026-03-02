"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { admin } from "@/lib/api";
import { useUser, useDebounce } from "@/lib/hooks";
import type {
  UserDetailResponse, AdminConsumptionResponse, CharacterPublicResponse, SceneResponse,
} from "@/lib/types";
import { cn, getAvatarUrl, timeAgo, formatNumber } from "@/lib/utils";
import {
  Search, RefreshCw, X, Shield, Coins, ChevronDown, Trash2, Loader2, Check,
} from "lucide-react";

export default function AdminUsersPage() {
  const router = useRouter();
  const { user } = useUser();
  const [users, setUsers] = useState<UserDetailResponse[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [query, setQuery] = useState("");
  const debouncedQuery = useDebounce(query, 300);
  const [loading, setLoading] = useState(true);

  // Detail panel
  const [selectedUser, setSelectedUser] = useState<UserDetailResponse | null>(null);
  const [consumption, setConsumption] = useState<AdminConsumptionResponse | null>(null);
  const [consumptionDays, setConsumptionDays] = useState(7);
  const [userChars, setUserChars] = useState<CharacterPublicResponse[]>([]);
  const [userScenes, setUserScenes] = useState<SceneResponse[]>([]);

  // Adjust credits
  const [creditAmount, setCreditAmount] = useState("");
  const [creditReason, setCreditReason] = useState("");
  const [adjusting, setAdjusting] = useState(false);

  // Permissions
  const [permChar, setPermChar] = useState(true);
  const [permScene, setPermScene] = useState(true);
  const [savingPerm, setSavingPerm] = useState(false);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await admin.users(page, 20, debouncedQuery || undefined);
      setUsers(res.items);
      setTotal(res.total);
    } catch {
      // pass
    } finally {
      setLoading(false);
    }
  }, [page, debouncedQuery]);

  useEffect(() => { loadUsers(); }, [loadUsers]);

  // Redirect non-admin
  useEffect(() => {
    if (user && !user.is_admin) router.push("/");
  }, [user, router]);

  const selectUser = async (u: UserDetailResponse) => {
    setSelectedUser(u);
    setPermChar(u.can_create_character);
    setPermScene(u.can_create_scene);
    setCreditAmount("");
    setCreditReason("");
    try {
      const [cons, chars, scs] = await Promise.all([
        admin.consumption(u.id, consumptionDays),
        admin.userCharacters(u.id),
        admin.userScenes(u.id),
      ]);
      setConsumption(cons);
      setUserChars(chars.items);
      setUserScenes(scs.items);
    } catch {
      // pass
    }
  };

  const handleAdjust = async () => {
    if (!selectedUser || !creditAmount || !creditReason) return;
    setAdjusting(true);
    try {
      await admin.adjustCredits(selectedUser.id, {
        user_id: selectedUser.id,
        amount: parseInt(creditAmount),
        reason: creditReason,
      });
      setCreditAmount("");
      setCreditReason("");
      loadUsers();
      selectUser(selectedUser);
    } catch {
      // pass
    } finally {
      setAdjusting(false);
    }
  };

  const handleSavePerm = async () => {
    if (!selectedUser) return;
    setSavingPerm(true);
    try {
      await admin.updatePermissions(selectedUser.id, {
        can_create_character: permChar,
        can_create_scene: permScene,
      });
      loadUsers();
    } catch {
      // pass
    } finally {
      setSavingPerm(false);
    }
  };

  const handleDeleteChar = async (charId: string) => {
    if (!selectedUser || !confirm("确定要删除该角色吗？（软删除）")) return;
    await admin.deleteUserCharacter(selectedUser.id, charId);
    setUserChars(userChars.filter((c) => c.id !== charId));
  };

  const handleDeleteScene = async (sceneId: string) => {
    if (!selectedUser || !confirm("确定要删除该场景吗？（软删除）")) return;
    await admin.deleteUserScene(selectedUser.id, sceneId);
    setUserScenes(userScenes.filter((s) => s.id !== sceneId));
  };

  const loadConsumption = async (days: number) => {
    if (!selectedUser) return;
    setConsumptionDays(days);
    const cons = await admin.consumption(selectedUser.id, days);
    setConsumption(cons);
  };

  if (!user?.is_admin) return null;

  return (
    <div className="space-y-4">
      <h1 className="flex items-center gap-2 text-xl font-bold">
        <Shield className="h-5 w-5 text-amber-500" /> 管理用户
      </h1>

      {/* Search bar */}
      <div className="flex items-center gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            placeholder="搜索用户（邮箱/用户名）..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="input pl-9"
          />
        </div>
        <button onClick={loadUsers} className="btn-secondary"><RefreshCw className="h-4 w-4" /></button>
      </div>

      <div className="flex gap-4">
        {/* User list */}
        <div className={cn("flex-1 space-y-1", selectedUser ? "hidden lg:block" : "")}>
          {loading ? (
            <div className="py-8 text-center text-slate-400"><Loader2 className="mx-auto h-6 w-6 animate-spin" /></div>
          ) : (
            <>
              <div className="overflow-x-auto rounded-lg border border-slate-200 dark:border-slate-700">
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 dark:bg-slate-800">
                    <tr>
                      <th className="px-3 py-2 text-left font-medium">用户</th>
                      <th className="px-3 py-2 text-right font-medium">积分</th>
                      <th className="hidden px-3 py-2 text-center font-medium sm:table-cell">角色权限</th>
                      <th className="hidden px-3 py-2 text-center font-medium sm:table-cell">场景权限</th>
                      <th className="px-3 py-2 text-right font-medium">操作</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                    {users.map((u) => (
                      <tr key={u.id} className="transition-colors hover:bg-slate-50 dark:hover:bg-slate-800">
                        <td className="px-3 py-2">
                          <div className="flex items-center gap-2">
                            <img src={getAvatarUrl(u.avatar_url, u.display_name)} alt="" className="h-7 w-7 rounded-full" />
                            <div>
                              <p className="text-sm font-medium">{u.display_name}</p>
                              <p className="text-xs text-slate-400">{u.email}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-3 py-2 text-right">{u.credits}</td>
                        <td className="hidden px-3 py-2 text-center sm:table-cell">
                          {u.can_create_character ? "✅" : "❌"}
                        </td>
                        <td className="hidden px-3 py-2 text-center sm:table-cell">
                          {u.can_create_scene ? "✅" : "❌"}
                        </td>
                        <td className="px-3 py-2 text-right">
                          <button onClick={() => selectUser(u)} className="btn-ghost text-xs text-primary-600">详情</button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="text-xs text-slate-400">共 {total} 个用户</p>
            </>
          )}
        </div>

        {/* Detail panel */}
        {selectedUser && (
          <div className="w-full space-y-4 rounded-xl border border-slate-200 bg-white p-4 dark:border-slate-700 dark:bg-slate-800 lg:w-96">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">用户详情</h3>
              <button onClick={() => setSelectedUser(null)} className="btn-ghost p-1"><X className="h-4 w-4" /></button>
            </div>

            {/* Basic info */}
            <div className="flex items-center gap-3">
              <img src={getAvatarUrl(selectedUser.avatar_url, selectedUser.display_name)} alt="" className="h-10 w-10 rounded-full" />
              <div>
                <p className="font-medium">{selectedUser.display_name}</p>
                <p className="text-xs text-slate-400">{selectedUser.email}</p>
                <p className="text-xs text-slate-400">注册: {new Date(selectedUser.created_at).toLocaleDateString("zh-CN")}</p>
              </div>
            </div>

            {/* Permissions */}
            <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-700/50">
              <p className="mb-2 text-xs font-semibold text-slate-500">权限控制</p>
              <label className="mb-1 flex items-center gap-2 text-sm">
                <input type="checkbox" checked={permChar} onChange={(e) => setPermChar(e.target.checked)} /> 允许创建角色
              </label>
              <label className="flex items-center gap-2 text-sm">
                <input type="checkbox" checked={permScene} onChange={(e) => setPermScene(e.target.checked)} /> 允许创建场景
              </label>
              <button onClick={handleSavePerm} disabled={savingPerm} className="btn-primary mt-2 w-full text-xs">
                {savingPerm ? <Loader2 className="h-3 w-3 animate-spin" /> : "保存权限"}
              </button>
            </div>

            {/* Credits */}
            <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-700/50">
              <p className="mb-2 text-xs font-semibold text-slate-500">积分调整 (当前: {selectedUser.credits})</p>
              <div className="flex gap-2">
                <input type="number" value={creditAmount} onChange={(e) => setCreditAmount(e.target.value)} className="input flex-1" placeholder="金额 (正/负)" />
              </div>
              <input type="text" value={creditReason} onChange={(e) => setCreditReason(e.target.value)} className="input mt-1" placeholder="调整原因 *" />
              <button onClick={handleAdjust} disabled={adjusting || !creditAmount || !creditReason} className="btn-primary mt-2 w-full text-xs">
                {adjusting ? <Loader2 className="h-3 w-3 animate-spin" /> : "确认调整"}
              </button>
            </div>

            {/* Consumption */}
            {consumption && (
              <div className="rounded-lg bg-slate-50 p-3 dark:bg-slate-700/50">
                <div className="mb-2 flex items-center justify-between">
                  <p className="text-xs font-semibold text-slate-500">近期消耗</p>
                  <div className="flex gap-1">
                    {[7, 30].map((d) => (
                      <button
                        key={d}
                        onClick={() => loadConsumption(d)}
                        className={cn("rounded px-2 py-0.5 text-xs", consumptionDays === d ? "bg-primary-600 text-white" : "bg-white text-slate-500 dark:bg-slate-600")}
                      >
                        {d}天
                      </button>
                    ))}
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="rounded bg-white p-2 dark:bg-slate-600">
                    <p className="text-red-600 font-medium">{consumption.total_consumed}</p>
                    <p className="text-slate-400">总消耗</p>
                  </div>
                  <div className="rounded bg-white p-2 dark:bg-slate-600">
                    <p className="text-green-600 font-medium">{consumption.total_refunded}</p>
                    <p className="text-slate-400">总退款</p>
                  </div>
                  <div className="rounded bg-white p-2 dark:bg-slate-600">
                    <p className="font-medium">{consumption.net_consumed}</p>
                    <p className="text-slate-400">净消耗</p>
                  </div>
                </div>

                {/* Daily trend (simple bar) */}
                {consumption.daily.length > 0 && (
                  <div className="mt-2">
                    <p className="mb-1 text-[10px] text-slate-400">按天趋势</p>
                    <div className="flex items-end gap-0.5" style={{ height: "40px" }}>
                      {consumption.daily.map((d, i) => {
                        const max = Math.max(...consumption.daily.map((x) => x.net), 1);
                        const h = Math.max((d.net / max) * 100, 4);
                        return (
                          <div key={i} className="flex-1 rounded-t bg-primary-400" style={{ height: `${h}%` }} title={`${d.date}: ${d.net}`} />
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Recent transactions */}
                {consumption.recent_transactions.length > 0 && (
                  <div className="mt-2 max-h-32 overflow-y-auto">
                    {consumption.recent_transactions.slice(0, 5).map((tx) => (
                      <div key={tx.id} className="flex items-center justify-between py-1 text-xs">
                        <span className="truncate text-slate-500">{tx.reason}</span>
                        <span className={tx.amount > 0 ? "text-green-600" : "text-red-600"}>{tx.amount > 0 ? "+" : ""}{tx.amount}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* User characters */}
            {userChars.length > 0 && (
              <div>
                <p className="mb-1 text-xs font-semibold text-slate-500">角色 ({userChars.length})</p>
                <div className="space-y-1">
                  {userChars.map((c) => (
                    <div key={c.id} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-1.5 text-sm dark:bg-slate-700/50">
                      <div className="flex items-center gap-2">
                        <img src={getAvatarUrl(c.avatar_url, c.name)} alt="" className="h-6 w-6 rounded-full" />
                        <span>{c.name}</span>
                      </div>
                      <button onClick={() => handleDeleteChar(c.id)} className="text-red-500 hover:text-red-700">
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* User scenes */}
            {userScenes.length > 0 && (
              <div>
                <p className="mb-1 text-xs font-semibold text-slate-500">场景 ({userScenes.length})</p>
                <div className="space-y-1">
                  {userScenes.map((s) => (
                    <div key={s.id} className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-1.5 text-sm dark:bg-slate-700/50">
                      <span>{s.name}</span>
                      <button onClick={() => handleDeleteScene(s.id)} className="text-red-500 hover:text-red-700">
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
