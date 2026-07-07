"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type Marker = { name: string; value: string; source?: string };
type Extract = {
  model: string;
  parsed: { markers?: Marker[] } | null;
  raw: string;
};
type Patient = { id: string; label: string; report: string };
type Trial = {
  nct_id: string;
  title: string;
  status: string;
  conditions: string[];
  locations: string[];
  url: string;
};

export default function Home() {
  const [patient, setPatient] = useState<Patient | null>(null);
  const [trials, setTrials] = useState<Trial[] | null>(null);
  const [extract, setExtract] = useState<Extract | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/api/patient`).then((r) => r.json()).then(setPatient);
    fetch(`${API_URL}/api/trials?limit=20`)
      .then((r) => r.json())
      .then((d) => setTrials(d.trials));
  }, []);

  async function runExtract() {
    setLoading(true);
    setExtract(null);
    try {
      const r = await fetch(`${API_URL}/api/extract`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({}),
      });
      setExtract(await r.json());
    } finally {
      setLoading(false);
    }
  }

  const markers = extract?.parsed?.markers ?? [];

  return (
    <main className="max-w-5xl mx-auto p-6 space-y-8">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold">🧠 Glioma Copilot</h1>
        <p className="text-neutral-500 text-sm">
          Clinical trial review, fit assessment &amp; verification for glioma care
        </p>
      </header>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Patient + extraction */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Patient</h2>
            <button
              onClick={runExtract}
              disabled={loading}
              className="text-sm rounded-md bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white px-3 py-1.5"
            >
              {loading ? "Extracting…" : "Extract markers"}
            </button>
          </div>
          {patient && (
            <p className="text-sm text-neutral-500">{patient.label}</p>
          )}
          <pre className="text-xs bg-neutral-100 dark:bg-neutral-900 rounded-lg p-3 max-h-56 overflow-auto whitespace-pre-wrap">
            {patient?.report ?? "Loading…"}
          </pre>

          {markers.length > 0 && (
            <div className="space-y-2">
              <p className="text-sm font-medium">
                Extracted markers{" "}
                <span className="text-neutral-400 font-normal">
                  ({extract?.model})
                </span>
              </p>
              <ul className="space-y-1">
                {markers.map((m, i) => (
                  <li
                    key={i}
                    className="text-sm border border-neutral-200 dark:border-neutral-800 rounded-md px-3 py-2"
                  >
                    <span className="font-medium">{m.name}:</span> {m.value}
                    {m.source && (
                      <span className="block text-xs text-neutral-400 mt-0.5">
                        ↳ “{m.source}”
                      </span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </section>

        {/* Live trials */}
        <section className="space-y-3">
          <h2 className="font-semibold">
            Recruiting glioma trials{" "}
            <span className="text-neutral-400 font-normal text-sm">
              (live · ClinicalTrials.gov)
            </span>
          </h2>
          {!trials && <p className="text-sm text-neutral-500">Loading trials…</p>}
          <ul className="space-y-2 max-h-[32rem] overflow-auto">
            {trials?.map((t) => (
              <li
                key={t.nct_id}
                className="border border-neutral-200 dark:border-neutral-800 rounded-md px-3 py-2"
              >
                <a
                  href={t.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-sm font-medium text-violet-600 hover:underline"
                >
                  {t.title}
                </a>
                <div className="text-xs text-neutral-400 mt-1">
                  {t.nct_id}
                  {t.locations.length > 0 && <> · {t.locations.slice(0, 2).join(" · ")}</>}
                </div>
              </li>
            ))}
          </ul>
        </section>
      </div>
    </main>
  );
}
