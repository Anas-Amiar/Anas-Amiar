# Hi, I'm Anas 👋

**AI Engineer** — I build the parts of AI systems that demos skip: evaluation, cost control, observability, guardrails, and human-in-the-loop safety.

**16 production-minded AI engineering projects**, one thesis running through all of them:

> *AI output is a claim, not a fact, until it's verified — and AI systems earn autonomy by proving they know when they can't be trusted.*

Every project runs out of the box (`pip install pydantic` is usually all you need), has a full README, a STORY.md with the design decisions, and an interview-style build guide PDF.

---

## 🎯 Correctness & Evaluation
*How do you know an LLM output is good — and stays good?*

| Project | The one-liner |
|---|---|
| [Model Regression Detection](https://github.com/Anas-Amiar/Project-1-model-regression-detector) | CI gate that blocks prompt changes when accuracy drops — unit tests for LLM behavior, wired into GitHub Actions |
| [LLM Output Arbitration](https://github.com/Anas-Amiar/Project-7-llm-output-arbitration) | Three critics with different blind spots audit every output; an adjudicator resolves their disagreements |
| [Eval Dataset Generator](https://github.com/Anas-Amiar/Project-14-eval-dataset-generator) | Mines production logs into a self-growing eval dataset — injection attempts auto-labeled as adversarial test cases |
| [Prompt A/B Testing Platform](https://github.com/Anas-Amiar/Project-10-prompt-ab-platform) | Git-for-prompts + traffic splitting; refuses to declare winners without statistical significance (p=0.68 → keep collecting; p=0.014 → ship) |

## 💰 Cost & Performance
*The economics of running LLMs at scale.*

| Project | The one-liner |
|---|---|
| [LLM Cost Autopilot](https://github.com/Anas-Amiar/Project-2-llm-cost-autopilot) | Routes each request to the cheapest capable model, verifies quality, auto-escalates — 41% cost cut, zero quality loss |
| [Semantic Caching Layer](https://github.com/Anas-Amiar/Project-8-semantic-cache) | Caches on meaning, not text — 89.7% cost savings, with the threshold tradeoff measured against ground-truth wrong-hit rates |
| [LLM Gateway](https://github.com/Anas-Amiar/Project-12-llm-gateway) | Per-team rate limits, budget caps, multi-provider fallback, circuit breakers — a full provider outage with zero failed user requests |

## 🔍 Observability & Reliability
*When it breaks, know exactly where and why.*

| Project | The one-liner |
|---|---|
| [Failure Forensics Tool](https://github.com/Anas-Amiar/Project-3-failure-forensics-tool) | Traces every pipeline step and finds the *first* failure, not the loudest symptom — a scoped-down LangSmith |
| [AI Feature Flags](https://github.com/Anas-Amiar/Project-13-ai-feature-flags) | Gradual rollout with quality gates; caught a variant whose mean *beat* baseline but whose worst-10% was disastrous — at 1% rollout |
| [Self-Healing Docs](https://github.com/Anas-Amiar/Project-6-self-healing-docs) | Detects which doc sections a code change made stale; auto-fixes the mechanical, flags the structural for review |

## 🛡️ Trust & Guardrails
*Shipping AI a compliance team would approve.*

| Project | The one-liner |
|---|---|
| [Text-to-SQL with Guardrails](https://github.com/Anas-Amiar/Project-9-text-to-sql-guardrails) | Blocks the DELETE an obedient LLM will happily write; back-translates SQL to catch answers to the wrong question |
| [RAG with Citation Verification](https://github.com/Anas-Amiar/Project-5-rag-document-qa) | Two-axis grounding check: is the answer supported by the sources, and did retrieval even address the question? |
| [OCR Document Intelligence](https://github.com/Anas-Amiar/OCR) | Per-field confidence routing: shaky fields go to human review, corrections feed an accuracy benchmark |

## 🤖 Agents & Training
*The frontier — with the safety rails built in.*

| Project | The one-liner |
|---|---|
| [Agent Orchestration System](https://github.com/Anas-Amiar/Project-15-agent-orchestration) | Supervisor/specialist/reviewer agents, hard human-approval gates on sensitive ops, and memory that measurably reduces repeat mistakes |
| [AI Data Agents](https://github.com/Anas-Amiar/Project-16-ai-data-agents) | Four functional tool-using agents (analyst / scientist / AI engineer / ML engineer) on a sandboxed local agent loop, verified offline |
| [LoRA Fine-Tuning Pipeline](https://github.com/Anas-Amiar/Project-11-lora-finetune-pipeline) | The 95% around the training call: data hygiene, sweeps, early stopping — and a probe that catches catastrophic forgetting |

---

## 🛠️ How these are built

Python 3.11+ · Pydantic v2 · scikit-learn · FastAPI patterns · GitHub Actions · SQLite · Anthropic/OpenAI SDKs

Mock-first by design: every pipeline runs deterministically with zero API keys, with the real-LLM swap point isolated to one function. That's a deliberate architecture decision — testable systems first, expensive calls last.

## 📫 Contact

- 📧 anasamiar8@gmail.com
- 💼 [LinkedIn](https://www.linkedin.com/in/anasamiar/)
