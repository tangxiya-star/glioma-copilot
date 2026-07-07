"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

type Field = { value: string; source?: string };
type ReasoningStep = { rule: string; basis: string; source?: string | null };
type Classification = {
  diagnosis: string;
  grade: number | null;
  reasoning: ReasoningStep[];
  reclassification_note: string | null;
  source: string;
};
type ClassifyResp = {
  model: string;
  profile: Record<string, Field>;
  classification: Classification;
};
type Patient = { id: string; label: string; report: string };
type PatientSummary = { id: string; label: string };
type Trial = {
  nct_id: string;
  title: string;
  status: string;
  locations: string[];
  url: string;
};

export default function Home() {
  const [report, setReport] = useState("");
  const [cases, setCases] = useState<PatientSummary[]>([]);
  const [caseId, setCaseId] = useState("");
  const [trials, setTrials] = useState<Trial[] | null>(null);
  const [result, setResult] = useState<ClassifyResp | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetch(`${API_URL}/api/patients`)
      .then((r) => r.json())
      .then((d) => {
        setCases(d.patients);
        if (d.patients[0]) loadCase(d.patients[0].id);
      });
    fetch(`${API_URL}/api/trials?limit=20`)
      .then((r) => r.json())
      .then((d) => setTrials(d.trials));
  }, []);

  function loadCase(id: string) {
    setCaseId(id);
    setResult(null);
    fetch(`${API_URL}/api/patient?id=${id}`)
      .then((r) => r.json())
      .then((p: Patient) => setReport(p.report));
  }

  async function analyze() {
    setLoading(true);
    setResult(null);
    try {
      const r = await fetch(`${API_URL}/api/classify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        // Send the (possibly edited) report; backend defaults to demo patient if empty.
        body: JSON.stringify({ report }),
      });
      setResult(await r.json());
    } finally {
      setLoading(false);
    }
  }

  const c = result?.classification;

  return (
    <main className="max-w-5xl mx-auto p-6 space-y-8">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold">🧠 Glioma Copilot</h1>
        <p className="text-neutral-500 text-sm">
          Report → WHO CNS5 classification → trial review, with every step cited
        </p>
      </header>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Report + classification */}
        <section className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">Molecular report</h2>
            <button
              onClick={analyze}
              disabled={loading || !report}
              className="text-sm rounded-md bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white px-3 py-1.5"
            >
              {loading ? "Analyzing…" : "Analyze"}
            </button>
          </div>
          <select
            value={caseId}
            onChange={(e) => loadCase(e.target.value)}
            className="w-full text-sm border border-neutral-200 dark:border-neutral-800 bg-transparent rounded-md px-2 py-1.5"
          >
            {cases.map((p) => (
              <option key={p.id} value={p.id}>
                {p.label}
              </option>
            ))}
          </select>
          <textarea
            value={report}
            onChange={(e) => setReport(e.target.value)}
            spellCheck={false}
            className="w-full h-52 text-xs font-mono bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg p-3"
            placeholder="Paste a glioma molecular report…"
          />

          {c && (
            <div className="rounded-xl border border-violet-300 dark:border-violet-800 bg-violet-50/50 dark:bg-violet-950/30 p-4 space-y-3">
              <div>
                <p className="text-xs uppercase tracking-wide text-violet-500">
                  WHO CNS5 classification
                </p>
                <p className="text-lg font-bold">
                  {c.diagnosis}
                  <span className="ml-2 text-sm font-normal text-neutral-500">
                    {c.grade != null ? `grade ${c.grade}` : "grade pending histologic review"}
                  </span>
                </p>
              </div>

              <div>
                <p className="text-xs font-medium mb-1">Reasoning (deterministic)</p>
                <ol className="space-y-1">
                  {c.reasoning.map((s, i) => (
                    <li key={i} className="text-sm">
                      <span className="text-neutral-400 mr-1">{i + 1}.</span>
                      {s.rule}
                      {s.source && (
                        <span className="block text-xs text-neutral-400 ml-4">
                          ↳ “{s.source}”
                        </span>
                      )}
                    </li>
                  ))}
                </ol>
              </div>

              {c.reclassification_note && (
                <p className="text-xs bg-amber-100 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 rounded-md p-2">
                  ⚠ {c.reclassification_note}
                </p>
              )}
              <p className="text-[11px] text-neutral-400">
                Source: {c.source} · normalized by {result?.model}
              </p>
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
          <ul className="space-y-2 max-h-[36rem] overflow-auto">
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
