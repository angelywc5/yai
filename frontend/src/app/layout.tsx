import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "YAI — 拟人化 AI 对话平台",
  description: "与 AI 角色进行沉浸式对话体验",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN" suppressHydrationWarning>
      <body className="min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}
