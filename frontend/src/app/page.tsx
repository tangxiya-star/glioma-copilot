"use client";

import { useEffect, useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

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
  classification: Classification;
  trial_condition: string;
};
type Patient = { id: string; label: string; report: string };
type PatientSummary = { id: string; label: string };
type Trial = { nct_id: string; title: string; locations: string[]; url: string };

type FitItem = {
  criterion: string;
  kind: string;
  verdict: "met" | "not_met" | "unknown";
  citation?: string;
  rationale?: string;
};
type FitResp = {
  trial: { nct_id: string; title: string; url: string; locations: string[] };
  items: FitItem[];
  summary: { met: number; not_met: number; unknown: number };
};

const VERDICT = {
  met: { icon: "✅", label: "met", cls: "text-emerald-600" },
  not_met: { icon: "❌", label: "not met", cls: "text-red-600" },
  unknown: { icon: "❓", label: "unknown", cls: "text-amber-600" },
};

export default function Home() {
  const [report, setReport] = useState("");
  const [cases, setCases] = useState<PatientSummary[]>([]);
  const [caseId, setCaseId] = useState("");
  const [trials, setTrials] = useState<Trial[] | null>(null);
  const [result, setResult] = useState<ClassifyResp | null>(null);
  const [loading, setLoading] = useState(false);

  const [fit, setFit] = useState<FitResp | null>(null);
  const [fitNct, setFitNct] = useState("");
  const [fitLoading, setFitLoading] = useState(false);
  const [matchedCondition, setMatchedCondition] = useState("");

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
    setFit(null);
    setMatchedCondition("");
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
        body: JSON.stringify({ report }),
      });
      const data: ClassifyResp = await r.json();
      setResult(data);
      // Narrow the candidate trials to this patient's tumor type.
      const cond = data.trial_condition ?? "glioma";
      setMatchedCondition(cond);
      setFit(null);
      setFitNct("");
      const tr = await fetch(`${API_URL}/api/trials?limit=20&condition=${encodeURIComponent(cond)}`);
      setTrials((await tr.json()).trials);
    } finally {
      setLoading(false);
    }
  }

  async function runFit(nct_id: string) {
    setFitNct(nct_id);
    setFitLoading(true);
    setFit(null);
    try {
      const r = await fetch(`${API_URL}/api/fit`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nct_id, patient_id: caseId }),
      });
      setFit(await r.json());
    } finally {
      setFitLoading(false);
    }
  }

  const c = result?.classification;

  return (
    <main className="max-w-6xl mx-auto p-6 space-y-8">
      <header className="space-y-1">
        <h1 className="text-3xl font-bold">🧠 Glioma Copilot</h1>
        <p className="text-neutral-500 text-sm">
          Clinician view — report → WHO CNS5 classification → per-criterion trial fit, every step cited
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
            className="w-full h-44 text-xs font-mono bg-neutral-50 dark:bg-neutral-900 border border-neutral-200 dark:border-neutral-800 rounded-lg p-3"
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
              <ol className="space-y-1">
                {c.reasoning.map((s, i) => (
                  <li key={i} className="text-sm">
                    <span className="text-neutral-400 mr-1">{i + 1}.</span>
                    {s.rule}
                    {s.source && (
                      <span className="block text-xs text-neutral-400 ml-4">↳ “{s.source}”</span>
                    )}
                  </li>
                ))}
              </ol>
              {c.reclassification_note && (
                <p className="text-xs bg-amber-100 dark:bg-amber-950/40 text-amber-800 dark:text-amber-300 rounded-md p-2">
                  ⚠ {c.reclassification_note}
                </p>
              )}
            </div>
          )}
        </section>

        {/* Live trials — click to assess fit */}
        <section className="space-y-3">
          <h2 className="font-semibold">
            Recruiting trials{" "}
            {matchedCondition ? (
              <span className="text-violet-500 font-normal text-sm">
                · matched to “{matchedCondition}”
              </span>
            ) : (
              <span className="text-neutral-400 font-normal text-sm">
                · broad glioma (Analyze to match the patient)
              </span>
            )}
          </h2>
          <p className="text-xs text-neutral-400">Click a trial to assess per-criterion fit.</p>
          {!trials && <p className="text-sm text-neutral-500">Loading trials…</p>}
          <ul className="space-y-2 max-h-[30rem] overflow-auto">
            {trials?.map((t) => (
              <li key={t.nct_id}>
                <button
                  onClick={() => runFit(t.nct_id)}
                  className={`w-full text-left border rounded-md px-3 py-2 hover:border-violet-400 ${
                    fitNct === t.nct_id
                      ? "border-violet-500 bg-violet-50/50 dark:bg-violet-950/30"
                      : "border-neutral-200 dark:border-neutral-800"
                  }`}
                >
                  <span className="text-sm font-medium">{t.title}</span>
                  <span className="block text-xs text-neutral-400 mt-1">
                    {t.nct_id}
                    {t.locations.length > 0 && <> · {t.locations.slice(0, 2).join(" · ")}</>}
                  </span>
                </button>
              </li>
            ))}
          </ul>
        </section>
      </div>

      {/* Fit assessment table */}
      {(fitLoading || fit) && (
        <section className="space-y-3">
          <h2 className="font-semibold">Trial Fit Assessment</h2>
          {fitLoading && (
            <p className="text-sm text-neutral-500">Assessing eligibility criteria…</p>
          )}
          {fit && (
            <div className="space-y-3">
              <div className="flex flex-wrap items-center gap-3 text-sm">
                <a href={fit.trial.url} target="_blank" rel="noreferrer" className="font-medium text-violet-600 hover:underline">
                  {fit.trial.nct_id}
                </a>
                <span className="text-neutral-500">{fit.trial.title}</span>
                <span className="ml-auto flex gap-2">
                  <Chip cls="text-emerald-600">✅ {fit.summary.met} met</Chip>
                  <Chip cls="text-amber-600">❓ {fit.summary.unknown} unknown</Chip>
                  <Chip cls="text-red-600">❌ {fit.summary.not_met} not met</Chip>
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm border-collapse">
                  <thead>
                    <tr className="text-left text-xs text-neutral-400 border-b border-neutral-200 dark:border-neutral-800">
                      <th className="py-2 pr-3 font-medium">Verdict</th>
                      <th className="py-2 pr-3 font-medium">Criterion</th>
                      <th className="py-2 font-medium">Citation / rationale</th>
                    </tr>
                  </thead>
                  <tbody>
                    {fit.items.map((it, i) => {
                      const v = VERDICT[it.verdict] ?? VERDICT.unknown;
                      return (
                        <tr key={i} className="border-b border-neutral-100 dark:border-neutral-900 align-top">
                          <td className={`py-2 pr-3 whitespace-nowrap ${v.cls}`}>
                            {v.icon} {v.label}
                            <span className="block text-[11px] text-neutral-400">{it.kind}</span>
                          </td>
                          <td className="py-2 pr-3">{it.criterion}</td>
                          <td className="py-2 text-xs text-neutral-500">
                            {it.citation && <span className="block">“{it.citation}”</span>}
                            {it.rationale && <span className="block text-neutral-400 mt-0.5">→ {it.rationale}</span>}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </section>
      )}
    </main>
  );
}

function Chip({ children, cls }: { children: React.ReactNode; cls: string }) {
  return (
    <span className={`rounded-full border border-current px-2 py-0.5 text-xs ${cls}`}>
      {children}
    </span>
  );
}
