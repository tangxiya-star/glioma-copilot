# Glioma Copilot — 3-minute demo script

Hero case: **case-004** (TCGA-06-5413 · 67yo M · recurrent glioblastoma, IDH-wt · prior bevacizumab).
Thesis: **honesty** — not "the AI found a match." Claude is never the source of truth.

> 动作用中文，要讲的话用英文。目标 ~3:00（偏紧，超时先删【朋友经历】的细节或收尾）。
> 录前先预热 Render `/health`，页面停在 Patient panel。
> ⚠️ 两处要你自己确认：① 【朋友经历】占位符填成你的真实故事；② 是否公开哥哥的私人信息（需他同意）。

---

### 0:00–0:35 · 开场：我做了什么 + 朋友的经历 + 为什么
**【动作】** 停在 Patient panel，看镜头，不点任何东西。

> "I built **Glioma Copilot** — a tool that helps a doctor check, for one specific brain-cancer patient, whether a clinical trial actually fits, and then explain it to the patient in plain language.
>
> I started this because 【填入你朋友的经历 —— 例如：a close friend's family faced a glioblastoma diagnosis, and I watched them drown in trial pages they couldn't read, not knowing which ones were even possible】. Glioblastoma is one of the deadliest cancers — median survival is around **15 months** — so the time a family loses to confusion is time they don't have."

### 0:35–0:55 · 采访哥哥（临床可信度）
**【动作】** 继续对镜头；（可选）屏幕角落放一张哥哥/采访的照片或名字卡。

> "To make sure this was real, I interviewed a neuro-oncology expert — my brother, **Tianwei Long, PhD, an Atlantic Fellow** who studies glioma.
> 〔可选，需征得他同意：His own wife lives with IDH-mutant glioma, so this is personal for our family too.〕
> His clearest guidance — and this shaped the whole tool — was: **lead with the patient's side and with honesty, not the molecular engine.** So that's what I'll show."

### 0:55–1:10 · 真实数据 + 诚实
**【动作】** 划过 Patient panel 表格；点一下带 `*` 的 Steroid / Location 列头。

> "These are eight **real, de-identified TCGA patients** — molecular data from cBioPortal, treatment history from the NIH GDC. Anything we constructed for the demo is **labeled**, never hidden. Let's take a recurrent glioblastoma who's already had bevacizumab."

### 1:10–1:30 · 分析 → 分类 → grounding（展示 Claude Science 图标）
**【动作】** 点 case-004 的「Analyze →」→ 右上「Analyze」。等结果后：① 指向黄色 WHO CNS5 分类框；② 指向「PRIOR THERAPIES · NORMALIZED (RXNORM + CHEMBL)」卡片上的 RxCUI / ChEMBL 图标链接；③ 展开顶部「▸ Evidence & sources」折叠条。

> "One click. Classification first — the 2021 WHO diagnosis is a **deterministic rule engine**, not a model guess. Every fact is grounded in an outside authority: drug identity through **RxNorm and ChEMBL**, and — here — the literature layer.

### 1:30–1:45 · Claude Science 证据层（图标特写）
**【动作】** 「Evidence & sources」展开后，镜头/光标停在 “Claude Science (literature map)” 和 “PubMed E-utilities (esummary)-verified 23/23” 两个标记上，滑过几条带 PMID 的引用链接。

> "This evidence map was generated with **Claude Science**, then every single citation was checked against **PubMed** — twenty-three of twenty-three verified, zero hallucinated. Claude reasons, but it is never the source of truth."

### 1:45–2:05 · 逐条 fit 表（核心）
**【动作】** 点一个 ❓needs-workup 的试验，打开逐条 fit 表；滚动展示 met / unknown；指向「Tests to order」工作清单。

> "Now the core: a **per-criterion fit table** — what's met, and honestly, what's unknown. It never fakes a green 'eligible' — every unknown becomes a **workup checklist** of tests to order. This hand-check is exactly the manual step we're replacing."

### 2:05–2:35 · 诚实层：验证 + 独立审计
**【动作】** 点「Run independent audit」→ 右侧抽屉滑出；等出现「XX% clinically concordant」。指向顶部那句和红色「genuine challenges」/ 绿色 self-corrections。

> "Then the honesty layer. A three-agent loop drafts the assessment and an **Opus verifier rewrites any over-claim** back to the evidence. And separately — on the right — an **independent Opus auditor re-derives eligibility completely blind, then challenges our own table.** It even flags where our screen was too cautious. It's a check with teeth, not a rubber stamp."

### 2:35–2:55 · 患者侧：解释 + FAQ + handout（最高价值）
**【动作】** 关抽屉；点「Explain for patient」→ 弹窗出现，滚一下平白解释 + 常见问题，关弹窗；点「Shared decision」→ 「Generate shared-decision summary」；指向「Print / export handout」。

> "And the part my brother cared about most: the **conversation**. The doctor previews a plain-language explanation and a curated FAQ — no jargon, and a hard rule: **never a survival estimate.** Then a one-page **shared-decision handout** the patient takes home, where their own preferences re-rank the options."

### 2:55–3:10 · 收尾
**【动作】** 停在 handout / 回镜头。

> "Real data, verified per criterion, independently audited, explained honestly. **Nine Claude agents, each grounded in an external source of truth.** It doesn't recommend — it shows the doctor *why* a trial fits, or doesn't. Thank you."

---

### 备用问答（评委可能问，用英文答）
- **"Why an LLM and not if-statements?"** → "We use deterministic code where inputs are clean — our pre-screen and the WHO classifier are pure rules. But eligibility is free text on both sides; extracting the predicates is what rules can't do, which is why matching is still manual today."
- **"Doesn't strict eligibility cherry-pick the healthiest patients?"** → "We're inclusive by design — unknowns become workup, we never hide a patient, and we never recommend. The clinician stays in the loop."
- **"What exactly is Claude doing?"** → "Nine roles; verify and audit run on Opus for decorrelated adversarial checks. Identity is grounded in RxNorm/ChEMBL and literature is audited against PubMed. Claude reasons — it's never the source of truth."
