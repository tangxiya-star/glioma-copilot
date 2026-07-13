# Glioma Copilot — 3-minute demo script

Hero case: **case-004** (TCGA-06-5413 · 67yo M · recurrent glioblastoma, IDH-wt · prior bevacizumab).
Structure: **who + what → why (friend) → problem → walk the app + how Claude is used.**
Thesis: **honesty** — not "the AI found a match." Claude is never the source of truth.

> 动作用中文，要讲的话用英文。**约 3:15**（偏紧）。要压回 3:00：problem statement 每点留一句、收尾缩短。
> 录前预热 Render `/health`，页面停在 Patient panel。
> ⚠️ 三处要你自己填/确认：① 【我是谁】；② 【朋友经历】填真实故事；③ 哥哥私人信息那句是否公开（需他同意）。

---

### 0:00–0:20 · 我是谁 + 我做了什么 + 为什么（朋友）
**【动作】** 看镜头，不点任何东西。

> "I'm 【填你的名字 / 身份，例：a student / an engineer】, and I built **Glioma Copilot**.
> I started it because 【填入你朋友的经历 —— 例：a close friend's family faced a glioblastoma diagnosis, and I watched them drown in clinical-trial pages they couldn't read — not even knowing which trials were possible】."

### 0:20–0:55 · Problem statement（我在解决什么）
**【动作】** 看镜头（可选：屏幕上打出 4 个关键词：*re-classification · free text · patient decision · unanswered questions*）。

> "Here's the problem.
> **One** — glioma diagnosis was rewritten in the 2021 WHO reclassification, so an old chart label can now imply the *wrong* eligibility.
> **Two** — that eligibility lives in **free text** on both sides, the trial's criteria and the patient's chart, so it can't be automated; today a clinician verifies it **by hand**, one line at a time.
> **Three** — no tool brings the **patient's own decision** into this. Yet for a disease this severe, joining a trial is one of the biggest choices they'll ever make.
> **And four** — because it's so severe, patients and families arrive with a flood of questions no one has time to answer.
> So that's what I'm solving: **verify fit honestly, and bring the patient into the decision.**"

### 0:55–1:15 · 真实数据（走进 app）
**【动作】** 划过 Patient panel 表格；点带 `*` 的 Steroid / Location 列头。

> "So — these are eight **real, de-identified TCGA patients**: molecular data from cBioPortal, treatment history from the NIH GDC. Anything we constructed for the demo is **labeled**, never hidden. Let's take a recurrent glioblastoma who's already had bevacizumab."

### 1:15–1:40 · 分析 → 分类 → grounding + Claude Science
**【动作】** 点 case-004 的「Analyze →」→ 右上「Analyze」。指黄色 WHO CNS5 分类框；指「PRIOR THERAPIES · NORMALIZED (RXNORM + CHEMBL)」卡片的 RxCUI/ChEMBL 图标；展开「▸ Evidence & sources」，停在 "Claude Science" 和 "PubMed-verified 23/23" 上。

> "One click. The 2021 WHO diagnosis is a **deterministic rule engine**, not a model guess. Drug identity is grounded in **RxNorm and ChEMBL**. And this literature layer was built with **Claude Science**, then every citation checked against **PubMed** — twenty-three of twenty-three verified, zero hallucinated. Claude reasons, but is never the source of truth."

### 1:40–2:00 · 逐条 fit 表（核心）
**【动作】** 点一个 ❓needs-workup 的试验，打开逐条 fit 表；滚动展示 met / unknown；指「Tests to order」工作清单。

> "The core: a **per-criterion fit table** — what's met, and honestly, what's unknown. It never fakes a green 'eligible' — every unknown becomes a **workup checklist** of tests to order. This hand-check is exactly the manual step we're replacing."

### 2:00–2:30 · 3-agent 流水线 + 独立审计
**【动作】** 点「Run 3-agent verification」→ 右侧抽屉，依次指 `1 Drafting → 2 Verification (Opus) → 3 Investigation`；再点「Run independent audit」→ 指「XX% clinically concordant」。

> "Then three agents, in order: a **drafting** agent writes the brief, an **Opus verification** agent rewrites any over-claim back to the evidence, and an **investigation** agent turns each unknown into a next step. And separately, an **independent Opus auditor** re-derives eligibility completely **blind** and challenges the whole table — a check with teeth, not a rubber stamp."

### 2:30–2:55 · 患者侧：解释 + FAQ + handout
**【动作】** 关抽屉；点「Explain for patient」→ 弹窗（平白解释 + 常见问题）→ 关；点「Shared decision」→「Generate shared-decision summary」；指「Print / export handout」。

> "Now the patient side — the part I built this for. The doctor previews a plain-language explanation and an FAQ — no jargon, and a hard rule: **never a survival estimate.** Then a one-page **shared-decision handout** the patient takes home, where their own preferences re-rank the options."

### 2:55–3:15 · Claude 的总用 + 收尾
**【动作】** 回镜头。

> "Under the hood it's **nine Claude agents** — verification and audit on Opus for independent, adversarial checks — and every one is grounded in an outside source of truth. It doesn't recommend; it shows the doctor **why** a trial fits, or doesn't, and helps them explain it to the patient. Thank you."

---

### 备用问答（评委可能问，用英文答）
- **"Why an LLM and not if-statements?"** → "We use deterministic code where inputs are clean — our pre-screen and the WHO classifier are pure rules. But eligibility is free text on both sides; extracting the predicates is what rules can't do, which is why matching is still manual today."
- **"Doesn't strict eligibility cherry-pick the healthiest patients?"** → "We're inclusive by design — unknowns become workup, we never hide a patient, and we never recommend. The clinician stays in the loop."
- **"What exactly is Claude doing?"** → "Nine roles; verify and audit run on Opus for decorrelated adversarial checks. Identity is grounded in RxNorm/ChEMBL and literature is audited against PubMed. Claude reasons — it's never the source of truth."
