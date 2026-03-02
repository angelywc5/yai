"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/api";
import { useUser } from "@/lib/hooks";
import { Loader2 } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { setUser } = useUser();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await auth.login({ email, password });
      const user = await auth.me();
      setUser(user);
      router.push("/");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "登录失败";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-900">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-primary-600">YAI</h1>
          <p className="mt-2 text-sm text-slate-500">拟人化 AI 对话平台</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <h2 className="mb-4 text-lg font-semibold">登录</h2>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600 dark:bg-red-900/30 dark:text-red-400">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium">邮箱</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input" placeholder="you@example.com" required />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">密码</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} className="input" placeholder="至少 8 位" required minLength={8} />
            </div>
            <button type="submit" disabled={loading} className="btn-primary mt-2 w-full">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "登录"}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-slate-500">
            还没有账号？{" "}
            <Link href="/auth/register" className="text-primary-600 hover:underline">注册</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
