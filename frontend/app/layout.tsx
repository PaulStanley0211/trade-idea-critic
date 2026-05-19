import type { Metadata } from "next";
import Link from "next/link";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Trade-Idea Critic",
  description:
    "An agentic system that critiques a trader's thesis before they take the trade. Covers US, Indian, and German equities. Never recommends buy or sell.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} bg-slate-50 text-slate-900 antialiased min-h-screen flex flex-col`}
      >
        <Providers>
          <header className="border-b border-slate-200 bg-white">
            <div className="mx-auto max-w-4xl px-6 py-4 flex items-center justify-between">
              <Link href="/" className="font-semibold tracking-tight">
                Trade-Idea Critic
              </Link>
              <nav className="text-sm text-slate-600 flex gap-6">
                <Link href="/about" className="hover:text-slate-900">
                  About
                </Link>
                <Link href="/disclaimer" className="hover:text-slate-900">
                  Disclaimer
                </Link>
              </nav>
            </div>
          </header>
          <main className="flex-1">{children}</main>
          <footer className="border-t border-slate-200 bg-white">
            <div className="mx-auto max-w-4xl px-6 py-4 text-xs text-slate-500 flex flex-wrap items-center justify-between gap-2">
              <span>Not financial advice. See the disclaimer.</span>
              <span>
                <Link href="/disclaimer" className="underline-offset-2 hover:underline">
                  Disclaimer
                </Link>
              </span>
            </div>
          </footer>
        </Providers>
      </body>
    </html>
  );
}
