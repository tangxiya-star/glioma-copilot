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
type Provenance = {
  sample_id: string;
  study: string;
  study_name: string;
  pmid: string;
  url: string;
  markers: Record<string, string>;
};
type Patient = { id: string; label: string; report: string; provenance?: Provenance | null };
type Screen = { status: "clear" | "flagged"; reasons: string[] };
type Trial = {
  nct_id: string;
  title: string;
  locations: string[];
  url: string;
  screen?: Screen;
};

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

type Summary = { met: number; not_met: number; unknown: number };
type TriageSignal = "looks_eligible" | "needs_workup" | "conflict" | "no_criteria";
type Triage = { items: FitItem[]; summary: Summary; signal: TriageSignal };

// Triage label for clinician review — NOT a recommendation. Ordering below is
// conservative: hard conflicts sink, fewer unknowns rise; candidate set still
// comes from condition scoping (this is fit triage, not discovery).
const SIGNAL = {
  looks_eligible: { icon: "✅", label: "looks eligible", cls: "text-emerald-600", rank: 0 },
  needs_workup: { icon: "❓", label: "needs workup", cls: "text-amber-600", rank: 1 },
  conflict: { icon: "❌", label: "conflict", cls: "text-red-600", rank: 2 },
  no_criteria: { icon: "•", label: "no criteria", cls: "text-neutral-400", rank: 3 },
};

type Draft = { assessment: string; claims: { claim: string; citation: string }[] };
type VerifyEntry = {
  claim: string;
  status: "supported" | "overstated" | "unsupported";
  rewrite: string;
  reason: string;
};
type Review = {
  stage: string;
  draft?: Draft;
  verify?: { log: VerifyEntry[] };
  investigate?: { steps: { item: string; action: string }[] };
  done?: boolean;
};

const VSTATUS = {
  supported: { icon: "✅", cls: "text-emerald-600", label: "supported" },
  overstated: { icon: "⚠️", cls: "text-amber-600", label: "overstated" },
  unsupported: { icon: "❌", cls: "text-red-600", label: "unsupported" },
};

export default function Home() {
  const [report, setReport] = useState("");
  const [cases, setCases] = useState<Patient[]>([]);
  const [caseId, setCaseId] = useState("");
  const [trials, setTrials] = useState<Trial[] | null>(null);
  const [result, setResult] = useState<ClassifyResp | null>(null);
  const [loading, setLoading] = useState(false);

  const [fit, setFit] = useState<FitResp | null>(null);
  const [fitNct, setFitNct] = useState("");
  const [fitLoading, setFitLoading] = useState(false);
  const [matchedCondition, setMatchedCondition] = useState("");

  // Proactive fit triage: nct_id -> badge summary + cached full items.
  const [triage, setTriage] = useState<Record<string, Triage>>({});
  const [triaging, setTriaging] = useState(false);
  // Stage 0/1 pool stats: full recruiting count, screen-clear/flagged, deep-assessed.
  const [pool, setPool] = useState<{
    total: number;
    clear: number;
    flagged: number;
    deepAssessed: number;
  } | null>(null);
  const TRIAGE_N = 4;

  const [review, setReview] = useState<Review | null>(null);
  const [reviewLoading, setReviewLoading] = useState(false);

  useEffect(() => {
    // Pull all synthetic cases ONCE (reports inline) — switching is then instant.
    fetch(`${API_URL}/api/patients`)
      .then((r) => r.json())
      .then((d: { patients: Patient[] }) => {
        setCases(d.patients);
        if (d.patients[0]) loadCase(d.patients[0].id, d.patients);
      })
      .catch(() => {});
    // Trials are NOT fetched up front — they are matched to the patient by
    // Analyze (condition-scoped), so the flow reads "Analyze first".
  }, []);

  // No fetch — the report is already in memory. `list` covers the first call
  // before `cases` state has flushed.
  function loadCase(id: string, list: Patient[] = cases) {
    setCaseId(id);
    setResult(null);
    setTrials(null); // clear the previous case's matched trials — Analyze re-matches
    setFit(null);
    setFitNct("");
    setReview(null);
    setTriage({});
    setPool(null);
    setMatchedCondition("");
    setReport(list.find((p) => p.id === id)?.report ?? "");
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
      setTriage({});
      setTrials(null);
      setPool(null);
      // The triage stream is now the single source of the trial list: it pulls
      // the FULL recruiting pool (Stage 0), screens all of it (Stage 1), and
      // deep-fits the top clear candidates (Stage 2).
      runTriage(cond);
    } finally {
      setLoading(false);
    }
  }

  // Stage 0/1/2 candidate triage stream: pool → screen (full list) → deep-fit.
  async function runTriage(cond: string) {
    setTriaging(true);
    setTriage({});
    try {
      const r = await fetch(`${API_URL}/api/triage/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patient_id: caseId, condition: cond, limit: TRIAGE_N }),
      });
      if (!r.body) return;
      const reader = r.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        let nl;
        while ((nl = buf.indexOf("\n")) >= 0) {
          const line = buf.slice(0, nl).trim();
          buf = buf.slice(nl + 1);
          if (!line) continue;
          let msg;
          try {
            msg = JSON.parse(line);
          } catch {
            continue;
          }
          if (msg.type === "pool") {
            setPool({ total: msg.total, clear: 0, flagged: 0, deepAssessed: 0 });
          } else if (msg.type === "screen") {
            // Full screened pool becomes the trial list (all listed, none hidden).
            setTrials(msg.trials as Trial[]);
            setPool((p) => ({
              total: p?.total ?? msg.trials.length,
              clear: msg.clear,
              flagged: msg.flagged,
              deepAssessed: 0,
            }));
          } else if (msg.type === "triage" && msg.trial && msg.items) {
            setTriage((prev) => ({
              ...prev,
              [msg.trial.nct_id]: {
                items: msg.items,
                summary: msg.summary,
                signal: msg.signal,
              },
            }));
          } else if (msg.type === "done") {
            setPool((p) => (p ? { ...p, deepAssessed: msg.deep_assessed } : p));
          }
        }
      }
    } finally {
      setTriaging(false);
    }
  }

  // Open a trial's full fit table. If it was already triaged, reuse the cached
  // items (instant) instead of re-streaming; otherwise run live fit.
  function openTrial(t: Trial) {
    const cached = triage[t.nct_id];
    if (cached && cached.items.length > 0) {
      setReview(null);
      setFitNct(t.nct_id);
      setFit({
        trial: { nct_id: t.nct_id, title: t.title, url: t.url, locations: t.locations },
        items: cached.items,
        summary: cached.summary,
      });
    } else {
      runFit(t.nct_id);
    }
  }

  async function runFit(nct_id: string) {
    setFitNct(nct_id);
    setFitLoading(true);
    setFit(null);
    setReview(null);
    try {
      const r = await fetch(`${API_URL}/api/fit/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nct_id, patient_id: caseId }),
      });
      if (!r.body) return;
      const reader = r.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      // Read NDJSON: one JSON message per line, rendered as it arrives.
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        let nl;
        while ((nl = buf.indexOf("\n")) >= 0) {
          const line = buf.slice(0, nl).trim();
          buf = buf.slice(nl + 1);
          if (!line) continue;
          let msg;
          try {
            msg = JSON.parse(line);
          } catch {
            continue;
          }
          if (msg.type === "start") {
            setFit({ trial: msg.trial, items: [], summary: { met: 0, not_met: 0, unknown: 0 } });
          } else if (msg.type === "item") {
            setFit((prev) => {
              if (!prev) return prev;
              const summary = { ...prev.summary };
              if (msg.item.verdict in summary) summary[msg.item.verdict as keyof typeof summary]++;
              return { ...prev, items: [...prev.items, msg.item], summary };
            });
          } else if (msg.type === "summary") {
            setFit((prev) => (prev ? { ...prev, summary: msg.summary } : prev));
          }
        }
      }
    } finally {
      setFitLoading(false);
    }
  }

  async function runReview() {
    if (!fit) return;
    setReviewLoading(true);
    setReview({ stage: "starting" });
    try {
      const r = await fetch(`${API_URL}/api/review/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nct_id: fit.trial.nct_id, patient_id: caseId }),
      });
      if (!r.body) return;
      const reader = r.body.getReader();
      const decoder = new TextDecoder();
      let buf = "";
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buf += decoder.decode(value, { stream: true });
        let nl;
        while ((nl = buf.indexOf("\n")) >= 0) {
          const line = buf.slice(0, nl).trim();
          buf = buf.slice(nl + 1);
          if (!line) continue;
          let msg;
          try {
            msg = JSON.parse(line);
          } catch {
            continue;
          }
          if (msg.type === "stage") setReview((p) => ({ ...p!, stage: msg.stage }));
          else if (msg.type === "draft") setReview((p) => ({ ...p!, draft: msg.draft }));
          else if (msg.type === "verify") setReview((p) => ({ ...p!, verify: msg.verify }));
          else if (msg.type === "investigate")
            setReview((p) => ({ ...p!, investigate: msg.investigate }));
          else if (msg.type === "done") setReview((p) => ({ ...p!, done: true }));
        }
      }
    } finally {
      setReviewLoading(false);
    }
  }

  const c = result?.classification;
  const prov = cases.find((p) => p.id === caseId)?.provenance;

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

          {prov && (
            <div className="rounded-lg border border-emerald-300 dark:border-emerald-800 bg-emerald-50/50 dark:bg-emerald-950/20 p-3 text-xs space-y-2">
              <div className="flex items-center justify-between gap-2">
                <span className="font-medium text-emerald-700 dark:text-emerald-300">
                  ✓ Real molecular data · de-identified
                </span>
                <a
                  href={prov.url}
                  target="_blank"
                  rel="noreferrer"
                  className="text-emerald-700 dark:text-emerald-400 hover:underline font-mono"
                >
                  {prov.sample_id} ↗
                </a>
              </div>
              <p className="text-neutral-500">
                Source: cBioPortal <span className="font-mono">{prov.study}</span> — {prov.study_name}{" "}
                (PMID {prov.pmid}). Molecular markers below are traceable to this real TCGA sample;
                the clinical course is a labeled constructed layer.
              </p>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(prov.markers).map(([k, v]) => (
                  <span
                    key={k}
                    className="rounded border border-emerald-300/60 dark:border-emerald-800/60 px-1.5 py-0.5 text-[11px] text-neutral-600 dark:text-neutral-300"
                  >
                    <span className="text-neutral-400">{k.replace(/_/g, " ").toLowerCase()}:</span> {v}
                  </span>
                ))}
              </div>
            </div>
          )}

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
              <span className="text-neutral-400 font-normal text-sm">· step 2</span>
            )}
          </h2>

          {/* Flow is Analyze-first: trials are matched to the patient, not browsed. */}
          {!result && !loading && (
            <div className="rounded-lg border border-dashed border-neutral-300 dark:border-neutral-700 p-4 text-sm text-neutral-500">
              <span className="font-medium text-neutral-600 dark:text-neutral-300">
                ① Run <span className="text-violet-600">Analyze</span> first.
              </span>{" "}
              It classifies this patient (WHO CNS5), pulls <em>every</em> recruiting trial for the
              tumor type, screens all of them for hard conflicts, then runs the real per-criterion
              fit on the top screen-clear candidates. For clinician review — not a general trial
              search.
            </div>
          )}
          {loading && (
            <p className="text-sm text-violet-500 animate-pulse">Matching trials to this patient…</p>
          )}

          {result && (
            <>
              {pool ? (
                <div className="text-xs text-neutral-500 space-y-0.5">
                  <p>
                    <span className="font-medium text-neutral-700 dark:text-neutral-200">
                      {pool.total}
                    </span>{" "}
                    recruiting trials pulled (every one — not a top-N slice)
                    {triaging && <span className="text-violet-500"> · working…</span>}
                  </p>
                  <p>
                    <span className="text-emerald-600">{pool.clear} screen-clear</span> ·{" "}
                    <span className="text-amber-600">{pool.flagged} flagged</span> (hard conflict,
                    deprioritized — not hidden) ·{" "}
                    <span className="text-violet-600">
                      deep-assessed {pool.deepAssessed || (triaging ? "…" : 0)} of {pool.total}
                    </span>
                  </p>
                </div>
              ) : (
                <p className="text-sm text-violet-500 animate-pulse">
                  Pulling every recruiting trial + screening…
                </p>
              )}
              <ul className="space-y-2 max-h-[30rem] overflow-auto">
                {sortByTriage(trials, triage).map((t) => {
                  const tri = triage[t.nct_id];
                  const sig = tri ? SIGNAL[tri.signal] ?? SIGNAL.no_criteria : null;
                  const flagged = t.screen?.status === "flagged";
                  return (
                    <li key={t.nct_id}>
                      <button
                        onClick={() => openTrial(t)}
                        className={`w-full text-left border rounded-md px-3 py-2 hover:border-violet-400 ${
                          fitNct === t.nct_id
                            ? "border-violet-500 bg-violet-50/50 dark:bg-violet-950/30"
                            : "border-neutral-200 dark:border-neutral-800"
                        } ${flagged ? "opacity-60" : ""}`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <span className="text-sm font-medium">{t.title}</span>
                          {sig ? (
                            <span
                              className={`shrink-0 rounded-full border border-current px-2 py-0.5 text-[11px] whitespace-nowrap ${sig.cls}`}
                            >
                              {sig.icon} {sig.label}
                            </span>
                          ) : (
                            flagged && (
                              <span className="shrink-0 rounded-full border border-current px-2 py-0.5 text-[11px] whitespace-nowrap text-amber-600">
                                ⚠ screened out
                              </span>
                            )
                          )}
                        </div>
                        {tri && tri.signal !== "no_criteria" && (
                          <span className="block text-xs mt-1 space-x-2">
                            <span className="text-emerald-600">✅ {tri.summary.met}</span>
                            <span className="text-amber-600">❓ {tri.summary.unknown}</span>
                            <span className="text-red-600">❌ {tri.summary.not_met}</span>
                          </span>
                        )}
                        {flagged && t.screen?.reasons?.length ? (
                          <span className="block text-[11px] text-amber-600 mt-1">
                            {t.screen.reasons.map((rsn, i) => (
                              <span key={i} className="block">
                                ⚠ {rsn}
                              </span>
                            ))}
                          </span>
                        ) : null}
                        <span className="block text-xs text-neutral-400 mt-1">
                          {t.nct_id}
                          {t.locations.length > 0 && <> · {t.locations.slice(0, 2).join(" · ")}</>}
                        </span>
                      </button>
                    </li>
                  );
                })}
              </ul>
            </>
          )}
        </section>
      </div>

      {/* Fit assessment table */}
      {(fitLoading || fit) && (
        <section className="space-y-3">
          <h2 className="font-semibold">
            Trial Fit Assessment
            {fitLoading && (
              <span className="ml-2 text-sm font-normal text-violet-500 animate-pulse">
                ● streaming…
              </span>
            )}
          </h2>
          {fitLoading && !fit && (
            <p className="text-sm text-neutral-500">Contacting trial + model…</p>
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

              {/* Day 4: three-agent verification loop */}
              <div className="pt-2">
                <button
                  onClick={runReview}
                  disabled={reviewLoading}
                  className="text-sm rounded-md bg-violet-600 hover:bg-violet-700 disabled:opacity-50 text-white px-3 py-1.5"
                >
                  {reviewLoading ? "Running 3-agent review…" : "Run 3-agent verification"}
                </button>
              </div>

              {review && (
                <div className="space-y-4 rounded-xl border border-neutral-200 dark:border-neutral-800 p-4">
                  {/* Drafting agent */}
                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-400">
                      1 · Drafting agent
                    </p>
                    {review.draft ? (
                      <>
                        <p className="text-sm font-medium mt-1">{review.draft.assessment}</p>
                        <ul className="mt-1 space-y-0.5">
                          {review.draft.claims.map((cl, i) => (
                            <li key={i} className="text-xs text-neutral-500">
                              • {cl.claim}
                            </li>
                          ))}
                        </ul>
                      </>
                    ) : (
                      <p className="text-sm text-neutral-400 animate-pulse">drafting…</p>
                    )}
                  </div>

                  {/* Verification agent */}
                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-400">
                      2 · Verification agent{" "}
                      <span className="text-neutral-300">(Opus · grounds every claim to source)</span>
                    </p>
                    {review.verify ? (
                      <ul className="mt-1 space-y-2">
                        {review.verify.log.map((e, i) => {
                          const v = VSTATUS[e.status] ?? VSTATUS.supported;
                          const flagged = e.status !== "supported";
                          return (
                            <li
                              key={i}
                              className={`text-sm rounded-md px-3 py-2 ${
                                flagged
                                  ? "bg-amber-50 dark:bg-amber-950/30 border border-amber-300 dark:border-amber-800"
                                  : ""
                              }`}
                            >
                              <span className={v.cls}>
                                {v.icon} {v.label}
                              </span>{" "}
                              <span className="text-neutral-600 dark:text-neutral-300">{e.claim}</span>
                              {flagged && (
                                <div className="mt-1 text-xs">
                                  <span className="font-medium text-amber-700 dark:text-amber-300">
                                    ↳ rewritten:
                                  </span>{" "}
                                  {e.rewrite}
                                  <span className="block text-neutral-400 mt-0.5">{e.reason}</span>
                                </div>
                              )}
                            </li>
                          );
                        })}
                      </ul>
                    ) : (
                      <p className="text-sm text-neutral-400 animate-pulse">
                        {review.draft ? "verifying…" : "waiting…"}
                      </p>
                    )}
                  </div>

                  {/* Investigation agent */}
                  <div>
                    <p className="text-xs uppercase tracking-wide text-neutral-400">
                      3 · Investigation agent
                    </p>
                    {review.investigate ? (
                      <ul className="mt-1 space-y-1">
                        {review.investigate.steps.map((s, i) => (
                          <li key={i} className="text-sm">
                            <span className="font-medium">{s.item}</span>
                            <span className="block text-xs text-neutral-500">→ {s.action}</span>
                          </li>
                        ))}
                      </ul>
                    ) : (
                      <p className="text-sm text-neutral-400 animate-pulse">
                        {review.verify ? "investigating…" : "waiting…"}
                      </p>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}
        </section>
      )}
    </main>
  );
}

// Triaged trials first (looks-eligible → needs-workup → conflict), fewer
// unknowns rising within a tier; un-triaged trials keep their original order
// below. Stable: preserves incoming order for equal ranks.
function sortByTriage(
  trials: Trial[] | null,
  triage: Record<string, Triage>
): Trial[] {
  if (!trials) return [];
  // Screen-flagged trials sink to the bottom (deprioritized, still listed);
  // among the rest, deep-fitted (triaged) trials rank by fit, then un-triaged.
  const rankOf = (t: Trial) => {
    const flagged = t.screen?.status === "flagged" ? 1 : 0;
    const tri = triage[t.nct_id];
    if (!tri) return { f: flagged, r: 9, u: 0 }; // un-triaged: after triaged
    return { f: flagged, r: SIGNAL[tri.signal]?.rank ?? 3, u: tri.summary.unknown };
  };
  return trials
    .map((t, i) => ({ t, i, ...rankOf(t) }))
    .sort((a, b) => a.f - b.f || a.r - b.r || a.u - b.u || a.i - b.i)
    .map((x) => x.t);
}

function Chip({ children, cls }: { children: React.ReactNode; cls: string }) {
  return (
    <span className={`rounded-full border border-current px-2 py-0.5 text-xs ${cls}`}>
      {children}
    </span>
  );
}
