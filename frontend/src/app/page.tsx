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
  treatment?: { source: string; url: string; agents: string[] };
};
type Patient = { id: string; label: string; report: string; provenance?: Provenance | null };
type Screen = { status: "clear" | "flagged"; reasons: string[] };
type Trial = {
  nct_id: string;
  title: string;
  locations: string[];
  url: string;
  phases?: string[];
  states?: string[];
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

// --- Day 5: shared-decision workspace ---
type Explanation = {
  what_it_is?: string;
  why_it_may_fit?: string;
  open_questions?: string[];
  what_it_involves?: string;
  questions_to_ask?: string[];
};
type ExplainResp = { trial: { nct_id: string; title: string; url: string }; explanation: Explanation };

type Prefs = {
  travel: "in_state" | "regional" | "anywhere" | "unsure";
  home_state: string;
  goal: "quality_of_life" | "balanced" | "aggressive" | "unsure";
  phase1: "avoid" | "open" | "unsure";
  caregiver: "strong" | "limited" | "unsure";
  financial_concern: boolean;
};
const DEFAULT_PREFS: Prefs = {
  travel: "unsure",
  home_state: "",
  goal: "unsure",
  phase1: "unsure",
  caregiver: "unsure",
  financial_concern: false,
};
type RankedTrial = {
  nct_id: string;
  title: string;
  url?: string | null;
  signal: TriageSignal;
  summary: Summary;
  phases: string[];
  base: number;
  adjustments: { delta: number; reason: string }[];
  score: number;
};
type SummaryResp = {
  ranked: RankedTrial[];
  preferences: Record<string, unknown>;
  note: { note?: string; discussion_points?: string[] };
};

type DrugNorm = {
  input: string;
  rxcui: string | null;
  ingredient: string | null;
  chembl_id: string | null;
  mechanisms: { mechanism_of_action: string; action_type?: string }[];
  sources: { rxnorm?: string | null; chembl?: string | null };
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

  // Day 5: plain-language explanation + preferences + shared-decision summary.
  const [explain, setExplain] = useState<ExplainResp | null>(null);
  const [explainLoading, setExplainLoading] = useState(false);
  const [prefs, setPrefs] = useState<Prefs>(DEFAULT_PREFS);
  const [summary, setSummary] = useState<SummaryResp | null>(null);
  const [summaryLoading, setSummaryLoading] = useState(false);
  // Drug normalization (RxNorm + ChEMBL) of the report's prior therapies.
  const [drugs, setDrugs] = useState<DrugNorm[] | null>(null);
  const [drugsLoading, setDrugsLoading] = useState(false);
  // Two-step flow: clinician review (evidence only) → shared decision (with patient).
  const [view, setView] = useState<"clinician" | "shared">("clinician");

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
    setExplain(null);
    setSummary(null);
    setDrugs(null);
    setView("clinician");
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
      // Ground the report's prior therapies in RxNorm + ChEMBL (parallel).
      runDrugs(report);
    } finally {
      setLoading(false);
    }
  }

  // Normalize the report's prior-therapy drug names via RxNorm + ChEMBL.
  async function runDrugs(reportText: string) {
    setDrugsLoading(true);
    setDrugs(null);
    try {
      const r = await fetch(`${API_URL}/api/drugs/from_patient`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ report: reportText }),
      });
      setDrugs((await r.json()).drugs ?? []);
    } catch {
      setDrugs([]);
    } finally {
      setDrugsLoading(false);
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
    setExplain(null);
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
    setExplain(null);
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

  // Day 5: plain-language explanation of the open trial's verified fit.
  async function runExplain() {
    if (!fit) return;
    setExplainLoading(true);
    setExplain(null);
    try {
      const r = await fetch(`${API_URL}/api/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nct_id: fit.trial.nct_id, patient_id: caseId }),
      });
      setExplain(await r.json());
    } finally {
      setExplainLoading(false);
    }
  }

  // Day 5: shared-decision summary — deterministic preference re-rank + narrative
  // over the DEEP-ASSESSED candidates (never the whole pool; never a recommendation).
  async function runSummary() {
    const candidates = Object.entries(triage)
      .filter(([, tri]) => tri.signal !== "no_criteria")
      .map(([nct, tri]) => {
        const t = trials?.find((x) => x.nct_id === nct);
        return {
          nct_id: nct,
          title: t?.title ?? nct,
          url: t?.url,
          signal: tri.signal,
          summary: tri.summary,
          phases: t?.phases ?? [],
          states: t?.states ?? [],
        };
      });
    if (candidates.length === 0) return;
    setSummaryLoading(true);
    setSummary(null);
    try {
      const r = await fetch(`${API_URL}/api/summary`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ patient_id: caseId, preferences: prefs, candidates }),
      });
      setSummary(await r.json());
    } finally {
      setSummaryLoading(false);
    }
  }

  const c = result?.classification;
  const prov = cases.find((p) => p.id === caseId)?.provenance;
  const hasTriage = Object.keys(triage).length > 0;

  const CARD =
    "rounded-2xl bg-white dark:bg-neutral-900 border border-slate-200/80 dark:border-neutral-800 shadow-sm";
  const PRIMARY =
    "rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-medium shadow-sm hover:opacity-95 disabled:opacity-50 transition";

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-neutral-950 text-slate-800 dark:text-neutral-200">
      <div className="flex">
        {/* ===== Sidebar ===== */}
        <aside className="sticky top-0 h-screen w-64 shrink-0 flex flex-col gap-6 bg-white dark:bg-neutral-900 border-r border-slate-200/80 dark:border-neutral-800 p-5">
          <div className="flex items-center gap-2">
            <div className="grid h-10 w-10 place-items-center rounded-xl bg-gradient-to-br from-indigo-600 to-violet-600 text-lg">
              🧠
            </div>
            <div className="leading-tight">
              <p className="font-bold">Glioma Copilot</p>
              <p className="text-[11px] text-slate-400">evidence · fit · shared decision</p>
            </div>
          </div>

          <div className="space-y-1.5">
            <p className="px-1 text-[11px] font-medium uppercase tracking-wide text-slate-400">
              Cases
            </p>
            {cases.map((p) => {
              const num = p.id.replace("case-", "");
              const desc = (p.label.split("—")[1] || "").split("(")[0].trim();
              const active = p.id === caseId;
              return (
                <button
                  key={p.id}
                  onClick={() => loadCase(p.id)}
                  className={`flex w-full items-center gap-3 rounded-xl px-2.5 py-2 text-left transition ${
                    active
                      ? "bg-indigo-50 dark:bg-indigo-950/40 ring-1 ring-indigo-200 dark:ring-indigo-900"
                      : "hover:bg-slate-50 dark:hover:bg-neutral-800/50"
                  }`}
                >
                  <span
                    className={`grid h-9 w-9 shrink-0 place-items-center rounded-full text-xs font-semibold ${
                      active
                        ? "bg-gradient-to-br from-indigo-600 to-violet-600 text-white"
                        : "bg-slate-100 dark:bg-neutral-800 text-slate-500"
                    }`}
                  >
                    {num}
                  </span>
                  <span className="min-w-0">
                    <span className="block text-sm font-medium">Case {num}</span>
                    <span className="block truncate text-[11px] text-slate-400">{desc}</span>
                  </span>
                </button>
              );
            })}
          </div>

          <div className="space-y-1.5">
            <p className="px-1 text-[11px] font-medium uppercase tracking-wide text-slate-400">
              Workflow
            </p>
            <StepButton active={view === "clinician"} onClick={() => setView("clinician")} n="1" label="Clinician review" />
            <StepButton
              active={view === "shared"}
              onClick={() => setView("shared")}
              disabled={!hasTriage}
              n="2"
              label="Shared decision"
              hint={!hasTriage ? "review first" : undefined}
            />
          </div>
        </aside>

        {/* ===== Main ===== */}
        <main className="min-w-0 flex-1 p-6 space-y-6">
          {/* Top bar */}
          <div className={`${CARD} flex flex-wrap items-center gap-3 px-5 py-3.5`}>
            <div className="min-w-0">
              <p className="text-lg font-bold">
                {c ? c.diagnosis : `Case ${caseId.replace("case-", "")}`}
                {c && (
                  <span className="ml-2 text-sm font-normal text-slate-400">
                    {c.grade != null ? `grade ${c.grade}` : "grade pending"}
                  </span>
                )}
              </p>
              <p className="text-xs text-slate-400">
                {view === "clinician"
                  ? "Clinician review — report → classification → trial fit, every step cited"
                  : "Shared decision — preferences re-weight the assessed options (for discussion)"}
              </p>
            </div>
            <button
              onClick={analyze}
              disabled={loading || !report}
              className={`${PRIMARY} ml-auto px-5 py-2 text-sm`}
            >
              {loading ? "Analyzing…" : "⚡ Analyze"}
            </button>
          </div>

          {/* Stat tiles */}
          {view === "clinician" && (result || pool) && (
            <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
              <div className="rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-600 p-4 text-white shadow-sm">
                <p className="text-[11px] uppercase tracking-wide text-white/70">WHO CNS5</p>
                <p className="mt-1 text-sm font-semibold leading-snug">
                  {c ? c.diagnosis : "—"}
                </p>
              </div>
              <StatTile label="Recruiting pulled" value={pool ? pool.total : "…"} tone="slate" sub="every one" />
              <StatTile label="Screen-clear" value={pool ? pool.clear : "…"} tone="emerald" sub={pool ? `${pool.flagged} flagged` : ""} />
              <StatTile
                label="Deep-assessed"
                value={pool ? pool.deepAssessed || (triaging ? "…" : 0) : "…"}
                tone="indigo"
                sub={pool ? `of ${pool.total}` : ""}
              />
            </div>
          )}

          {view === "clinician" && (
          <div className="grid gap-5 lg:grid-cols-2">
            {/* Report + provenance + classification + drugs */}
            <section className="space-y-5">
              <div className={`${CARD} p-5 space-y-3`}>
                <div className="flex items-center justify-between">
                  <h2 className="font-semibold">Molecular report</h2>
                </div>
                <textarea
                  value={report}
                  onChange={(e) => setReport(e.target.value)}
                  spellCheck={false}
                  className="w-full h-44 text-xs font-mono bg-slate-50 dark:bg-neutral-950 border border-slate-200 dark:border-neutral-800 rounded-xl p-3"
                />
              </div>

              {prov && (
            <div className="rounded-2xl border border-emerald-200 dark:border-emerald-900 bg-emerald-50/60 dark:bg-emerald-950/20 p-4 text-xs space-y-2">
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
                Molecular source: cBioPortal <span className="font-mono">{prov.study}</span> (TCGA,
                Cell 2016; PMID {prov.pmid}). Markers below trace to this real TCGA sample.
              </p>
              {prov.treatment && (
                <p className="text-neutral-500">
                  Prior therapy (real):{" "}
                  <span className="text-neutral-600 dark:text-neutral-300">
                    {prov.treatment.agents.join(" · ")}
                  </span>{" "}
                  —{" "}
                  <a
                    href={prov.treatment.url}
                    target="_blank"
                    rel="noreferrer"
                    className="text-emerald-700 dark:text-emerald-400 hover:underline"
                  >
                    NIH GDC record ↗
                  </a>
                </p>
              )}
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
            <div className={`${CARD} p-5 space-y-3`}>
              <div>
                <p className="text-xs uppercase tracking-wide text-indigo-500">
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

          {/* Prior therapies normalized via RxNorm + ChEMBL (authoritative identity). */}
          {(drugsLoading || (drugs && drugs.length > 0)) && (
            <div className="rounded-xl border border-teal-300 dark:border-teal-800 bg-teal-50/50 dark:bg-teal-950/20 p-4 space-y-2">
              <p className="text-xs uppercase tracking-wide text-teal-600">
                Prior therapies · normalized (RxNorm + ChEMBL)
              </p>
              {drugsLoading && !drugs && (
                <p className="text-sm text-neutral-500 animate-pulse">Normalizing drug names…</p>
              )}
              <ul className="space-y-2">
                {drugs?.map((d, i) => (
                  <li key={i} className="text-sm">
                    <span className="text-neutral-500">{d.input}</span>
                    <span className="mx-1 text-neutral-400">→</span>
                    <span className="font-medium">{d.ingredient ?? "unresolved"}</span>
                    {d.mechanisms[0]?.mechanism_of_action && (
                      <span className="ml-2 rounded-full border border-teal-400/60 px-2 py-0.5 text-[11px] text-teal-700 dark:text-teal-300">
                        {d.mechanisms[0].mechanism_of_action}
                      </span>
                    )}
                    <span className="block text-[11px] text-neutral-400 mt-0.5 space-x-2">
                      {d.sources.rxnorm && (
                        <a href={d.sources.rxnorm} target="_blank" rel="noreferrer" className="hover:underline">
                          RxCUI {d.rxcui} ↗
                        </a>
                      )}
                      {d.sources.chembl && (
                        <a href={d.sources.chembl} target="_blank" rel="noreferrer" className="hover:underline">
                          {d.chembl_id} ↗
                        </a>
                      )}
                    </span>
                  </li>
                ))}
              </ul>
              <p className="text-[11px] text-neutral-400">
                Claude names the drug; RxNorm + ChEMBL resolve identity & mechanism — grounding
                drug identity in an authoritative source.
              </p>
            </div>
          )}
        </section>

        {/* Live trials — click to assess fit */}
        <section className={`${CARD} p-5 space-y-3`}>
          <h2 className="font-semibold">
            Recruiting trials{" "}
            {matchedCondition ? (
              <span className="text-indigo-500 font-normal text-sm">
                · matched to “{matchedCondition}”
              </span>
            ) : (
              <span className="text-slate-400 font-normal text-sm">· step 2</span>
            )}
          </h2>

          {/* Flow is Analyze-first: trials are matched to the patient, not browsed. */}
          {!result && !loading && (
            <div className="rounded-lg border border-dashed border-neutral-300 dark:border-neutral-700 p-4 text-sm text-neutral-500">
              <span className="font-medium text-slate-600 dark:text-neutral-300">
                ① Run <span className="text-indigo-600">Analyze</span> first.
              </span>{" "}
              It classifies this patient (WHO CNS5), pulls <em>every</em> recruiting trial for the
              tumor type, screens all of them for hard conflicts, then runs the real per-criterion
              fit on the top screen-clear candidates. For clinician review — not a general trial
              search.
            </div>
          )}
          {loading && (
            <p className="text-sm text-indigo-500 animate-pulse">Matching trials to this patient…</p>
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
                    {triaging && <span className="text-indigo-500"> · working…</span>}
                  </p>
                  <p>
                    <span className="text-emerald-600">{pool.clear} screen-clear</span> ·{" "}
                    <span className="text-amber-600">{pool.flagged} flagged</span> (hard conflict,
                    deprioritized — not hidden) ·{" "}
                    <span className="text-indigo-600">
                      deep-assessed {pool.deepAssessed || (triaging ? "…" : 0)} of {pool.total}
                    </span>
                  </p>
                </div>
              ) : (
                <p className="text-sm text-indigo-500 animate-pulse">
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
                      <div
                        onClick={() => openTrial(t)}
                        role="button"
                        tabIndex={0}
                        className={`cursor-pointer border rounded-xl px-3 py-2 hover:border-indigo-400 ${
                          fitNct === t.nct_id
                            ? "border-indigo-400 bg-indigo-50/60 dark:bg-indigo-950/30"
                            : "border-slate-200 dark:border-neutral-800"
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
                        <span className="block text-xs text-slate-400 mt-1">
                          <a
                            href={t.url}
                            target="_blank"
                            rel="noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="font-medium text-indigo-500 hover:underline"
                          >
                            {t.nct_id} ↗
                          </a>
                          {t.locations.length > 0 && <> · {t.locations.slice(0, 2).join(" · ")}</>}
                        </span>
                      </div>
                    </li>
                  );
                })}
              </ul>
            </>
          )}
        </section>
      </div>
      )}

      {/* Fit assessment table — clinician review */}
      {view === "clinician" && (fitLoading || fit) && (
        <section className={`${CARD} p-5 space-y-3`}>
          <h2 className="font-semibold">
            Trial Fit Assessment
            {fitLoading && (
              <span className="ml-2 text-sm font-normal text-indigo-500 animate-pulse">
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
                <a href={fit.trial.url} target="_blank" rel="noreferrer" className="font-medium text-indigo-600 hover:underline">
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

              {/* Day 4: three-agent verification loop · Day 5: plain-language */}
              <div className="pt-2 flex flex-wrap gap-2">
                <button
                  onClick={runReview}
                  disabled={reviewLoading}
                  className={`${PRIMARY} text-sm px-4 py-2`}
                >
                  {reviewLoading ? "Running 3-agent review…" : "Run 3-agent verification"}
                </button>
                <button
                  onClick={runExplain}
                  disabled={explainLoading}
                  className="text-sm rounded-md border border-sky-400 text-sky-700 dark:text-sky-300 hover:bg-sky-50 dark:hover:bg-sky-950/30 disabled:opacity-50 px-3 py-1.5"
                >
                  {explainLoading ? "Explaining…" : "🗣 Explain for patient"}
                </button>
              </div>

              {explain && explain.explanation && (
                <div className="rounded-xl border border-sky-300 dark:border-sky-800 bg-sky-50/50 dark:bg-sky-950/20 p-4 space-y-3 text-sm">
                  <div className="flex items-center justify-between">
                    <p className="text-xs uppercase tracking-wide text-sky-500">
                      Plain-language explanation · for patient discussion
                    </p>
                    <span className="text-[11px] text-neutral-400">not medical advice</span>
                  </div>
                  {explain.explanation.what_it_is && (
                    <p>
                      <span className="font-medium">What it is: </span>
                      {explain.explanation.what_it_is}
                    </p>
                  )}
                  {explain.explanation.why_it_may_fit && (
                    <p>
                      <span className="font-medium">Why it may fit: </span>
                      {explain.explanation.why_it_may_fit}
                    </p>
                  )}
                  {explain.explanation.what_it_involves && (
                    <p>
                      <span className="font-medium">What it involves: </span>
                      {explain.explanation.what_it_involves}
                    </p>
                  )}
                  {explain.explanation.open_questions?.length ? (
                    <div>
                      <p className="font-medium">Still to confirm with your care team:</p>
                      <ul className="list-disc ml-5 text-neutral-600 dark:text-neutral-300">
                        {explain.explanation.open_questions.map((q, i) => (
                          <li key={i}>{q}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                  {explain.explanation.questions_to_ask?.length ? (
                    <div>
                      <p className="font-medium">Questions to ask your doctor:</p>
                      <ul className="list-disc ml-5 text-neutral-600 dark:text-neutral-300">
                        {explain.explanation.questions_to_ask.map((q, i) => (
                          <li key={i}>{q}</li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </div>
              )}

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

      {/* Step 2: shared-decision workspace — preferences visibly re-rank the
          already-assessed candidates (heuristic + documented, NOT a recommendation). */}
      {view === "shared" && (
        <section className="space-y-5">
          <div className={`${CARD} p-5 space-y-4`}>
          <div>
            <h2 className="font-semibold">Shared-decision workspace</h2>
            <p className="text-xs text-slate-400">
              Patient preferences (entered doctor-guided — not part of the chart) re-weight the
              assessed candidates. Transparent heuristic with reasons — for discussion, not a
              recommendation.
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-3">
            <PrefSelect
              label="Travel"
              value={prefs.travel}
              onChange={(v) => setPrefs({ ...prefs, travel: v as Prefs["travel"] })}
              options={[
                ["unsure", "No preference"],
                ["in_state", "Stay in my state"],
                ["regional", "Regional / limited"],
                ["anywhere", "Willing to travel"],
              ]}
            />
            <label className="text-sm space-y-1">
              <span className="block text-xs text-neutral-500">Home state (for travel)</span>
              <input
                value={prefs.home_state}
                onChange={(e) => setPrefs({ ...prefs, home_state: e.target.value })}
                placeholder="e.g. California"
                className="w-full border border-neutral-200 dark:border-neutral-800 bg-transparent rounded-md px-2 py-1.5"
              />
            </label>
            <PrefSelect
              label="Goal"
              value={prefs.goal}
              onChange={(v) => setPrefs({ ...prefs, goal: v as Prefs["goal"] })}
              options={[
                ["unsure", "No preference"],
                ["quality_of_life", "Prioritize quality of life"],
                ["balanced", "Balanced"],
                ["aggressive", "Aggressive / experimental"],
              ]}
            />
            <PrefSelect
              label="Earliest-phase (Phase 1) trials"
              value={prefs.phase1}
              onChange={(v) => setPrefs({ ...prefs, phase1: v as Prefs["phase1"] })}
              options={[
                ["unsure", "No preference"],
                ["avoid", "Prefer to avoid"],
                ["open", "Open to them"],
              ]}
            />
            <PrefSelect
              label="Caregiver support"
              value={prefs.caregiver}
              onChange={(v) => setPrefs({ ...prefs, caregiver: v as Prefs["caregiver"] })}
              options={[
                ["unsure", "No preference"],
                ["strong", "Strong"],
                ["limited", "Limited"],
              ]}
            />
            <label className="text-sm flex items-center gap-2 mt-5">
              <input
                type="checkbox"
                checked={prefs.financial_concern}
                onChange={(e) => setPrefs({ ...prefs, financial_concern: e.target.checked })}
              />
              <span>Financial / lodging is a concern</span>
            </label>
          </div>

          <button
            onClick={runSummary}
            disabled={summaryLoading}
            className={`${PRIMARY} text-sm px-4 py-2`}
          >
            {summaryLoading ? "Generating…" : "Generate shared-decision summary"}
          </button>
          </div>

          {summary && (
            <div className="space-y-4">
              <div>
                <p className="text-xs uppercase tracking-wide text-neutral-400 mb-2">
                  Preference-weighted ordering (each adjustment shown)
                </p>
                <ol className="space-y-2">
                  {summary.ranked.map((r, i) => {
                    const sig = SIGNAL[r.signal] ?? SIGNAL.no_criteria;
                    return (
                      <li
                        key={r.nct_id}
                        className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-3"
                      >
                        <div className="flex items-start justify-between gap-2">
                          <span className="text-sm font-medium">
                            {i + 1}. {r.title}
                          </span>
                          <span className={`text-xs whitespace-nowrap ${sig.cls}`}>
                            {sig.icon} {sig.label} · score {r.score}
                          </span>
                        </div>
                        <span className="block text-xs text-neutral-400 mt-0.5">
                          {r.nct_id}
                          {r.phases?.length ? <> · {r.phases.join("/")}</> : null}
                        </span>
                        {r.adjustments.length > 0 && (
                          <ul className="mt-1.5 space-y-0.5">
                            {r.adjustments.map((a, j) => (
                              <li
                                key={j}
                                className={`text-xs ${a.delta >= 0 ? "text-emerald-600" : "text-amber-600"}`}
                              >
                                {a.delta >= 0 ? `+${a.delta}` : a.delta} · {a.reason}
                              </li>
                            ))}
                          </ul>
                        )}
                      </li>
                    );
                  })}
                </ol>
              </div>

              {summary.note?.note && (
                <div className="rounded-xl border border-indigo-200 dark:border-indigo-900 bg-indigo-50/60 dark:bg-indigo-950/20 p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="text-xs uppercase tracking-wide text-indigo-500">
                      Shared-decision note
                    </p>
                    <span className="text-[11px] text-neutral-400">
                      for discussion · not a recommendation
                    </span>
                  </div>
                  <p className="text-sm">{summary.note.note}</p>
                  {summary.note.discussion_points?.length ? (
                    <ul className="list-disc ml-5 text-sm text-neutral-600 dark:text-neutral-300">
                      {summary.note.discussion_points.map((d, i) => (
                        <li key={i}>{d}</li>
                      ))}
                    </ul>
                  ) : null}
                </div>
              )}
            </div>
          )}
        </section>
      )}
        </main>
      </div>
    </div>
  );
}

function StepButton({
  active,
  onClick,
  disabled,
  n,
  label,
  hint,
}: {
  active: boolean;
  onClick: () => void;
  disabled?: boolean;
  n: string;
  label: string;
  hint?: string;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`flex w-full items-center gap-3 rounded-xl px-2.5 py-2 text-left transition disabled:opacity-40 disabled:cursor-not-allowed ${
        active
          ? "bg-indigo-50 dark:bg-indigo-950/40 ring-1 ring-indigo-200 dark:ring-indigo-900"
          : "hover:bg-slate-50 dark:hover:bg-neutral-800/50"
      }`}
    >
      <span
        className={`grid h-7 w-7 shrink-0 place-items-center rounded-lg text-xs font-semibold ${
          active ? "bg-gradient-to-br from-indigo-600 to-violet-600 text-white" : "bg-slate-100 dark:bg-neutral-800 text-slate-500"
        }`}
      >
        {n}
      </span>
      <span className="text-sm font-medium">
        {label}
        {hint && <span className="ml-1 text-[11px] font-normal text-slate-400">· {hint}</span>}
      </span>
    </button>
  );
}

const TONE: Record<string, string> = {
  slate: "text-slate-700 dark:text-slate-200",
  emerald: "text-emerald-600",
  indigo: "text-indigo-600",
};

function StatTile({ label, value, sub, tone }: { label: string; value: React.ReactNode; sub?: string; tone: string }) {
  return (
    <div className="rounded-2xl bg-white dark:bg-neutral-900 border border-slate-200/80 dark:border-neutral-800 shadow-sm p-4">
      <p className="text-[11px] uppercase tracking-wide text-slate-400">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${TONE[tone] ?? ""}`}>{value}</p>
      {sub && <p className="text-[11px] text-slate-400">{sub}</p>}
    </div>
  );
}

function PrefSelect({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: [string, string][];
}) {
  return (
    <label className="text-sm space-y-1">
      <span className="block text-xs text-slate-500">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl border border-slate-200 dark:border-neutral-800 bg-white dark:bg-neutral-900 px-3 py-2"
      >
        {options.map(([v, l]) => (
          <option key={v} value={v}>
            {l}
          </option>
        ))}
      </select>
    </label>
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

function TabButton({
  active,
  onClick,
  disabled,
  children,
}: {
  active: boolean;
  onClick: () => void;
  disabled?: boolean;
  children: React.ReactNode;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed ${
        active
          ? "border-violet-600 text-violet-700 dark:text-violet-300"
          : "border-transparent text-neutral-500 hover:text-neutral-800 dark:hover:text-neutral-200"
      }`}
    >
      {children}
    </button>
  );
}

function Chip({ children, cls }: { children: React.ReactNode; cls: string }) {
  return (
    <span className={`rounded-full border border-current px-2 py-0.5 text-xs ${cls}`}>
      {children}
    </span>
  );
}
