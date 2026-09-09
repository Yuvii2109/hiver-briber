# @AmericanAir support agent — Hiver SDE intern take-home

A retrieval-grounded support agent for one brand in the Kaggle *Customer Support on
Twitter* corpus: it classifies an incoming message, drafts a reply grounded in how
@AmericanAir actually handled similar cases, and decides whether to auto-send or
escalate — with a stated reason.

The proof matters more than the system, so the short version of what the evidence says:

| claim | verdict |
|---|---|
| Beats a trivial baseline on intent | **Yes.** macro-F1 0.60 vs 0.30, paired Δ +0.305 [+0.210, +0.396], p<0.0001 |
| Neural embeddings beat TF-IDF | **No.** Δ −0.008 [−0.083, +0.068], p=0.83. The extra dependency is not earned. |
| Drafts beat the brand's real human replies | **Yes, but partly an artifact.** Resolution +0.17 (p=0.033); faithfulness +0.91 is inflated because human agents had account access and the judge penalises them for it. |
| Deflection ("DM us") is reduced | **Yes.** 14.0% of human replies vs 0.7% of drafts. |
| The escalation layer beats random | **Cannot be shown at this sample size.** AURC Δ vs random −0.014, 95% CI [−0.058, +0.020]. |

---

## Reproduce the headline numbers

```bash
python -m venv .venv && .venv/Scripts/pip install -r requirements.txt   # ~40s
python repro.py
```

**Measured: 134 seconds. No network, no API key, no 516MB download.** Everything
replays from committed artifacts in `eval/`. Add `--demo` to watch the agent run
end-to-end on real held-out messages.

`repro.py` prints its own caveats. The most important: cached model outputs are
**replayed, not re-run**. That is a weaker claim than reproduction and is labelled as
such everywhere it appears.

To rebuild from the raw corpus instead (~20 min, needs `requirements-full.txt` for
torch): `python scripts/build_corpus.py && python scripts/build_embeddings.py`.

## What is where

```
src/hiver/
  data/       thread reconstruction, example pairing, temporal splitting
  taxonomy/   the frozen 10-intent taxonomy (induced, not assumed)
  classify/   baselines + the distilled linear classifier
  retrieve/   exact-cosine case retrieval (deliberately not FAISS)
  generate/   case-grounded drafting + the keyless fallback generator
  escalate/   selective prediction: calibrated risk + hard overrides
  evaluate/   judge rubrics, bootstrap/paired statistics
eval/         CODEBOOK.md, golden set, cached model outputs, embeddings  ← committed
scripts/      one script per pipeline stage; review tools for the human passes
REPORT.md     the writeup, including "what is misleading about my headline number"
DECISIONS.md  the decision log
```

## Two things a reviewer should poke at first

1. **Brand choice was measured, not intuited.** The deciding metric is how often a
   brand deflects to DM instead of answering. Grounding a "reply as this brand did"
   agent on a corpus of non-answers makes the task unfalsifiable. Uber_Support — the
   intuitive pick — is 88.3% deflection. AmericanAir is 26.1%. `data/SOURCE.md` and
   `REPORT.md §1` carry the table.
2. **The escalation result is negative and stays negative.** It would have been easy
   to report "coverage @ ≤10% bad-send rate = 100%". That number is vacuous: the base
   rate is 9.7%, so doing nothing already meets it. The harness prints `VACUOUS` next
   to any such threshold rather than letting it read as a result.

## Human-in-the-loop steps

Two deliverables genuinely require a person, and the tooling is built but the passes
are not yet done. Both are flagged in `REPORT.md` as outstanding rather than papered over.

```bash
python scripts/review_labels.py       # adjudicate the golden set (14 of 250 disputed)
python scripts/judge_calibration.py   # score ~50 replies -> judge-vs-human agreement
```
