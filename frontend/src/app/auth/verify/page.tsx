"use client";

import { Suspense, useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import Link from "next/link";

function VerifyContent() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token");
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");

  useEffect(() => {
    if (!token) { setStatus("error"); return; }
    fetch(`/api/v1/auth/verify/${token}`, { credentials: "include" })
      .then((r) => { setStatus(r.ok ? "success" : "error"); })
      .catch(() => setStatus("error"));
  }, [token]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-900">
      <div className="w-full max-w-sm rounded-xl border border-slate-200 bg-white p-6 text-center shadow-sm dark:border-slate-700 dark:bg-slate-800">
        {status === "loading" && <p className="text-sm text-slate-500">正在验证邮箱...</p>}
        {status === "success" && (
          <>
            <div className="mb-4 text-4xl">✅</div>
            <h2 className="mb-2 text-lg font-semibold">邮箱验证成功</h2>
            <p className="mb-4 text-sm text-slate-500">你的账号已激活，现在可以开始使用了。</p>
            <Link href="/" className="btn-primary inline-block">进入首页</Link>
          </>
        )}
        {status === "error" && (
          <>
            <div className="mb-4 text-4xl">❌</div>
            <h2 className="mb-2 text-lg font-semibold">验证失败</h2>
            <p className="mb-4 text-sm text-slate-500">验证链接无效或已过期，请重新注册。</p>
            <Link href="/auth/register" className="btn-primary inline-block">重新注册</Link>
          </>
        )}
      </div>
    </div>
  );
}

export default function VerifyPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center bg-slate-50 dark:bg-slate-900">
        <p className="text-sm text-slate-500">加载中...</p>
      </div>
    }>
      <VerifyContent />
    </Suspense>
  );
}
