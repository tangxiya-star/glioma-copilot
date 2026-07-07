"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type Health = { status: string; db: boolean; models: Record<string, string> };

export default function Home() {
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetch(`${API_URL}/health`)
      .then((r) => r.json())
      .then(setHealth)
      .catch((e) => setError(String(e)));
  }, []);

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 p-8">
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold">🧠 Glioma Copilot</h1>
        <p className="text-neutral-500">
          Clinical trial review, fit assessment &amp; verification for glioma care
        </p>
      </div>

      <div className="rounded-xl border border-neutral-200 dark:border-neutral-800 p-6 w-full max-w-md">
        <h2 className="font-semibold mb-3">Backend connection</h2>
        {error && <p className="text-red-500 text-sm">❌ {error}</p>}
        {!error && !health && <p className="text-neutral-500 text-sm">Checking…</p>}
        {health && (
          <div className="text-sm space-y-3">
            <ul className="space-y-1">
              <li>
                API status: <b>{health.status}</b> ✅
              </li>
              <li>
                Database: <b>{health.db ? "connected ✅" : "down ❌"}</b>
              </li>
            </ul>
            <div>
              <p className="font-medium mb-1">Per-agent models</p>
              <ul className="space-y-0.5 font-mono text-xs">
                {Object.entries(health.models).map(([agent, model]) => (
                  <li key={agent} className="flex justify-between gap-4">
                    <span className="text-neutral-500">{agent}</span>
                    <span className={model.includes("opus") ? "text-violet-500 font-semibold" : ""}>
                      {model}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      <p className="text-xs text-neutral-400">
        Scaffold — full features land per <code>docs/six-day-build.md</code>
      </p>
    </main>
  );
}
