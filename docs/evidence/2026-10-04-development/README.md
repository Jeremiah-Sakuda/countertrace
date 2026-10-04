# October 4, 2026 development evidence

Raw reports behind development claims in [STATUS.md](../../STATUS.md). These used **development** briefs and faults only, never the eval-v1 suite. They are prompt-development and engineering measurements, not evaluation results.

| File | What it shows |
| --- | --- |
| `interpret-ultra.json` | First live interpretation: Nemotron 3 Ultra, 6 development briefs, 3/3 conflicts and 3/3 compatible; 9.5–72.6 s per brief. |
| `interpret-super.json` | Nemotron 3 Super, same briefs, 6/6; 4.7–9.0 s. |
| `interpret-nano.json` | Nemotron 3 Nano, same briefs, 6/6 (one conflict on a neighboring topic); 8.4–15.2 s. |
| `interpret-super-thinking-off.json` | Super with `chat_template_kwargs: {"enable_thinking": false}`, 6/6; 1.7–2.9 s. Basis for the reasoning-off default on interactive tasks. |
| `explain-three-faults.json` | Ultra explanations of three development faults before the configuration line was added; one misstated DEPTH. |
| `interpret-super-flags-topic.json` | After eval-v2 exposed a missing flag-meaning topic: Super with reasoning off and the new `flags` topic, 7 development briefs (one new), 4/4 conflicts and 3/3 compatible; 1.9–3.3 s. |
| `repair-edits-five-faults.json` | Edit-based repair on five development faults: 5/5 passed unchanged checks on the first candidate with one-line diffs. |

Known metadata error: the top-level `model_id` in the three Super/Nano interpretation files records the explanation model (Ultra) because of a bug fixed on October 4. The per-call `model_id` entries are correct and authoritative.
