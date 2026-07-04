# Hi, I'm Anas

I'm an AI engineer. Most of my work is about the unglamorous parts of AI systems: evaluation, cost control, observability, guardrails, and knowing when to put a human in the loop.

Contact: [anasamiar8@gmail.com](mailto:anasamiar8@gmail.com) / [LinkedIn](https://www.linkedin.com/in/anasamiar/)

Below are 16 projects I built around one idea: an AI output is a claim, not a fact, until you verify it. Each repo runs out of the box (usually just `pip install pydantic`), and has a README plus a STORY.md explaining the design decisions.

## Evaluation and correctness

| Project | What it does |
|---|---|
| [Model Regression Detection](https://github.com/Anas-Amiar/Project-1-model-regression-detector) | A CI gate that runs prompt changes against a golden dataset and blocks the merge if accuracy drops. Wired into GitHub Actions. |
| [LLM Output Arbitration](https://github.com/Anas-Amiar/Project-7-llm-output-arbitration) | Three critics with different detection strategies review every output, and an adjudicator resolves their disagreements into one verdict. |
| [Eval Dataset Generator](https://github.com/Anas-Amiar/Project-14-eval-dataset-generator) | Mines production logs into eval test cases. Prompt injections and gibberish get auto-labeled as adversarial cases instead of being thrown away. |
| [Prompt A/B Testing Platform](https://github.com/Anas-Amiar/Project-10-prompt-ab-platform) | Version control for prompts plus traffic splitting. It refused to declare a winner at p=0.68 and made me collect 12,000 samples to get p=0.014. |

## Cost and performance

| Project | What it does |
|---|---|
| [LLM Cost Autopilot](https://github.com/Anas-Amiar/Project-2-llm-cost-autopilot) | Routes each request to the cheapest model that can handle it, checks the answer, and escalates if needed. Cut costs 41% in testing with no quality loss. |
| [Semantic Caching Layer](https://github.com/Anas-Amiar/Project-8-semantic-cache) | Caches LLM responses by meaning instead of exact text. 89.7% savings in the load test, and I measured when cache hits start returning wrong answers, not just the hit rate. |
| [LLM Gateway](https://github.com/Anas-Amiar/Project-12-llm-gateway) | Rate limits and budgets per team, fallback across providers, circuit breakers. The demo simulates a full provider outage with zero failed user requests. |

## Observability

| Project | What it does |
|---|---|
| [Failure Forensics Tool](https://github.com/Anas-Amiar/Project-3-failure-forensics-tool) | Traces every step of a multi-step pipeline and points at the first step that broke, not the last one that looked bad. |
| [AI Feature Flags](https://github.com/Anas-Amiar/Project-13-ai-feature-flags) | Gradual rollouts with quality gates. It caught a variant that beat the baseline on average but was terrible for 10% of users, and rolled it back at 1% exposure. |
| [Self-Healing Docs](https://github.com/Anas-Amiar/Project-6-self-healing-docs) | Figures out which documentation a code change made stale. Fixes the mechanical cases itself, flags the rest for a human. |

## Guardrails

| Project | What it does |
|---|---|
| [Text-to-SQL with Guardrails](https://github.com/Anas-Amiar/Project-9-text-to-sql-guardrails) | Blocks the DELETE statement an LLM will happily write if you ask nicely, and back-translates generated SQL to check it answers the question that was actually asked. |
| [RAG with Citation Verification](https://github.com/Anas-Amiar/Project-5-rag-document-qa) | Checks two things before returning an answer: is it supported by the retrieved sources, and did retrieval even find content about the question. |
| [OCR Document Intelligence](https://github.com/Anas-Amiar/OCR) | Scores every extracted field individually. Shaky fields go to a human review queue, and corrections feed an accuracy benchmark. |

## Agents and training

| Project | What it does |
|---|---|
| [Agent Orchestration System](https://github.com/Anas-Amiar/Project-15-agent-orchestration) | A supervisor delegates to specialist agents, a reviewer validates their work, sensitive actions need human approval, and lessons get saved so mistakes don't repeat. |
| [AI Data Agents](https://github.com/Anas-Amiar/Project-16-ai-data-agents) | Four working tool-using agents (data analyst, data scientist, AI engineer, ML engineer) on a sandboxed agent loop I can test offline. |
| [LoRA Fine-Tuning Pipeline](https://github.com/Anas-Amiar/Project-11-lora-finetune-pipeline) | Everything around the training call: data deduplication, hyperparameter sweeps, early stopping, and a probe that catches catastrophic forgetting. |

## Notes on how these are built

Python, Pydantic, scikit-learn, FastAPI, GitHub Actions, SQLite, and the Anthropic/OpenAI SDKs.

Most projects run in mock mode by default: deterministic fake models with realistic failure behavior, and the real LLM call isolated behind one function. I did that on purpose. It means the whole system is testable for free, and the expensive part is a one-line swap when you go live.

If you want the short version of any project, each repo has a STORY.md written as a two-minute walkthrough.
