"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/api";
import { Loader2 } from "lucide-react";

export default function RegisterPage() {
  const router = useRouter();
  const [form, setForm] = useState({ email: "", password: "", username: "", display_name: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const update = (field: string, value: string) => setForm((f) => ({ ...f, [field]: value }));

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await auth.register(form);
      setSuccess(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "注册失败";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-900">
        <div className="w-full max-w-sm rounded-xl border border-slate-200 bg-white p-6 text-center shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <div className="mb-4 text-4xl">📧</div>
          <h2 className="mb-2 text-lg font-semibold">验证邮件已发送</h2>
          <p className="mb-4 text-sm text-slate-500">
            请检查 <strong>{form.email}</strong> 的收件箱，点击验证链接完成注册。
          </p>
          <Link href="/auth/login" className="btn-primary inline-block">前往登录</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-900">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <h1 className="text-3xl font-bold text-primary-600">YAI</h1>
          <p className="mt-2 text-sm text-slate-500">创建你的账号</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm dark:border-slate-700 dark:bg-slate-800">
          <h2 className="mb-4 text-lg font-semibold">注册</h2>

          {error && (
            <div className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600 dark:bg-red-900/30 dark:text-red-400">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="flex flex-col gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium">邮箱</label>
              <input type="email" value={form.email} onChange={(e) => update("email", e.target.value)} className="input" required />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">用户名</label>
              <input type="text" value={form.username} onChange={(e) => update("username", e.target.value)} className="input" placeholder="字母、数字、下划线" required minLength={2} maxLength={30} pattern="^[a-zA-Z0-9_-]+$" />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">显示名称</label>
              <input type="text" value={form.display_name} onChange={(e) => update("display_name", e.target.value)} className="input" required minLength={1} maxLength={50} />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium">密码</label>
              <input type="password" value={form.password} onChange={(e) => update("password", e.target.value)} className="input" required minLength={8} maxLength={128} />
            </div>
            <button type="submit" disabled={loading} className="btn-primary mt-2 w-full">
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : "注册"}
            </button>
          </form>

          <p className="mt-4 text-center text-sm text-slate-500">
            已有账号？{" "}
            <Link href="/auth/login" className="text-primary-600 hover:underline">登录</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
