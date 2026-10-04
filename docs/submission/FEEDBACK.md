# Feedback on Nebius and NVIDIA tools (Devpost field)

Paste the section below into the feedback field. Every item comes from something observed while building Countertrace between October 1 and October 4, 2026. Raw records are in `evaluation/results/` and `docs/evidence/`.

---

**What worked well.** The Token Factory API is OpenAI-compatible, so the integration needed only standard HTTP calls. Authentication and the model catalog worked as documented. Having Nemotron 3 Ultra, Super, and Nano behind one endpoint made it easy to measure the tiers against each other and route each task to the right one. Nemotron 3 Ultra followed a strict citation format well: 13 of 16 evaluation explanations cited only real cycles and signals, and the other three each included one non-signal word.

**1. Reasoning can use up the whole output budget before the answer.** Nemotron 3 Ultra sometimes spent all of `max_tokens` reasoning and returned no JSON, ending with `finish_reason: length`. In my first evaluation this happened in 12 repair requests and 2 explanation requests, and it caused one repair to fail outright. I then found that `chat_template_kwargs: {"enable_thinking": false}` turns reasoning off for Nemotron 3 on Token Factory. In the second evaluation, 4 repair requests ran out of tokens, and retrying each with reasoning off recovered all four. That switch is not mentioned in the model catalog or the cookbook pages I used. Suggestions: document the switch, offer a per-request reasoning budget, and report separately when a request ran out of tokens while still reasoning.

**2. Ultra latency varied a lot for the same kind of request.** Two brief-interpretation requests of about 500 input tokens took 66 and 72 seconds; four similar requests minutes later took 9.5 to 16 seconds. Nemotron 3 Super gave the same answers on those briefs in 4.7 to 9 seconds, and in 1.7 to 3.3 seconds with reasoning off. Suggestion: publish typical latency ranges per model and return queue time in a response header, so applications can tell waiting from generating.

**3. Model ID casing is inconsistent.** The catalog lists `nvidia/Nemotron-3-Ultra-550b-a55b`, `nvidia/nemotron-3-super-120b-a12b`, and `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`. Each uses a different capitalization and prefix pattern, which is easy to get wrong in configuration. A consistent scheme, or case-insensitive matching, would help.

**4. Prices and remaining credits are not available from the API.** I estimated spend from the cookbook list price for Ultra ($1 input and $3 output per million tokens) because the API returns no price, and the Super and Nano pages I found list no price at all. I also could not check from code how hackathon credits were applied or when they expire. A usage and balance endpoint, plus prices in the model list, would let applications enforce real budgets instead of estimates.

**5. Serverless Jobs for interactive agent loops (from the documentation).** My verification batch takes 5 to 20 seconds. The documented multi-minute startup and one-hour minimum timeout make a Job per run a poor fit for that, so verification runs in Docker on a CPU host. I did not run Jobs, so this is based on the documentation only. A warm pool or a short-job mode would make Jobs a natural home for this kind of tool-checking agent.

**6. Instruction following on a negative rule.** I asked Ultra not to state internal register values that are not in the sampled trace. It mostly complied but still sometimes wrote values inferred from the RTL. Citation checks catch references to cycles and signals that do not exist, but not this kind of over-claiming, so the prompt guidance on this would be worth testing on future model versions.
