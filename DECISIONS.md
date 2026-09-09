# Decision log

Non-obvious calls, and why. Several of these reversed my own starting position; those
are marked **[reversed]** because the reason for the change is the interesting part.

1. **Brand chosen by a measured criterion, not intuition. [reversed]**
   My first instinct was Uber_Support: trip / fare / driver / safety / refund are
   beautifully separable intents. Measuring deflection killed it — 88.3% of its threads
   route to DM or a link, so the retrieval corpus is overwhelmingly non-answers. An
   agent grounded on it would learn to deflect and would score *well* for doing so.
   AmericanAir: 26.1% deflection, lowest URL rate of any high-volume brand.

2. **Deflection measured as DM-language *or* link-routing.**
   The obvious regex looks for "DM". That reports Uber at 41.3% and hides the problem,
   because Uber deflects with "Visit this link so our team can assist". The definition
   change is what flipped the brand decision, so it is the single highest-leverage line
   of code in the project.

3. **Deflections labelled and excluded from the evidence pool, not dropped or ignored.**
   Excluded from grounding (they teach the agent to deflect) but retained in metadata,
   because "deflect" is a legitimate action the planner may sometimes choose. Usable
   grounding corpus: 22,019 of 28,543.

4. **A conversation is (component root, customer), not a connected component.**
   Union-find over reply links glues pile-on threads together: 5.9% of AmericanAir
   components hold more than one customer and the worst holds 170 customers across 204
   tweets. Retrieving that blob as one "case" would mix unrelated complaints.

5. **Ordering from parsed `created_at`, never `tweet_id`.**
   55.6% of replies have a higher-id parent. Sorting the raw Twitter timestamp string
   lexically is also meaningless. Both traps are silent — nothing errors, the threads
   just come out wrong.

6. **Temporal split, not random. Then reported the guard as a no-op.**
   Threads ordered by start time, 80/10/10. A random split lets the agent retrieve cases
   written *after* the message it is answering. The retriever additionally enforces
   `case.created < query.created`; I verified this changes nothing given the split, and
   said so rather than presenting a redundant guard as a fix.

7. **Taxonomy induced by four independent open-coding passes, then reconciled.**
   Rather than one pass or clustering (which does not produce action-distinct categories
   on short noisy tweets). The disagreements between the four are what located the real
   seams. It also produced the project's most useful finding: the standard airline
   taxonomy covers only ~23% of this traffic.

8. **Venting is a first-class intent, with a zero-anchor gate.**
   ~5% of traffic is complaint with nothing filable. It is not OTHER, because it has a
   known scriptable action the human agents already run (acknowledge, ask exactly one
   question). The gate stops it becoming a dump: one anchor of any kind — flight, date,
   station, person, amount — routes the message topically instead.

9. **OTHER appears twice in the precedence order.**
   First as a safety route (anchorless legal threats, self-harm language, medical
   crises), last as the residual. These messages are structurally indistinguishable from
   venting, and a canned empathy line is the worst possible response. Encoding it in the
   frozen codebook rather than as a runtime flag: a flag can be lost in configuration.

10. **Two golden sets that are never averaged.**
    Set B uniform-random for anything prior-dependent; Set A stratified for per-class
    diagnosis. A single stratified set would make every aggregate describe a
    distribution that does not exist — the most common way this deliverable goes wrong.

11. **Blind double annotation, to measure rather than assume label quality.**
    kappa=0.937, 14 of 250 disputed. It also caught my own error: the open-coding share
    estimate for `DIFFUSE_BRAND_VENT` (11.5%) is excluded by the measured interval
    [3.9, 6.7]. Both annotators being Claude is a real limitation and is reported as one.

12. **All comparisons paired; marginal intervals never used to conclude equivalence.**
    At n≈150 two systems 8 points apart have overlapping marginal intervals regardless.
    Paired bootstrap on the same resample plus McNemar. This is what let me distinguish
    a real +0.305 gain from a non-existent −0.008 one.

13. **Reported that embeddings do not beat TF-IDF. [reversed]**
    The plan had the embedding model as the main classifier. Paired test says
    delta −0.008 [−0.083, +0.068]. The embeddings stay as the *retriever*, where they
    earn their place; as a classifier they are an unearned dependency.

14. **kNN demoted to retriever only; classification by a calibrated linear head.**
    Raw cosine is not a probability, and the entire escalation layer is a threshold on
    confidence. An uncalibrated score makes every threshold meaningless. ECE 0.063.

15. **No FAISS.**
    28k cases, exact cosine matmul in numpy is ~10ms and adds no dependency or platform
    risk on Windows / Python 3.14. Being able to justify an absent component is worth
    more than the component.

16. **Judge split into faithfulness and resolution, never averaged.**
    A single groundedness axis rewards a bot that says "DM us" to everything, because
    that is authentically what the brand did. Resolution is judged with the evidence
    *hidden* so it cannot reward mimicry. The template-parrot baseline exists to prove
    the split is load-bearing: it scores 100% unsafe and 1.00 resolution.

17. **The brand's real human replies judged as just another anonymous system.**
    Turns "is the agent good?" into "better or worse than what @AmericanAir actually
    sent?", which has an answer. It also exposed the artifact in §6.2 of the report —
    the judge penalises humans for account lookups it cannot verify.

18. **Escalation reframed as selective prediction. [reversed]**
    Four OR'd booleans give one operating point, cannot be tuned, and cannot appear in a
    results table. One calibrated score swept into a risk-coverage curve, plus a hard
    override list whose cost in burnt coverage is reported separately.

19. **Escalation target includes "useless", not just "unsafe".**
    Judging safety alone gave 1 positive in 150 — unfittable. On this brand the
    realistic failure is a useless reply, not a dangerous one, and a support desk
    escalates those too. Base rate 12.0%.

20. **Kept and published the finding that the escalation signals do not work.**
    Intent confidence (AURC 0.089) and retrieval similarity (0.104) are both worse than
    random (0.070). Failure concentrates by intent instead — 35.3% for
    `LIVE_TRIP_DISRUPTION`, 0.0% for policy questions. A single measured feature beats
    the eleven-feature model, and even that cannot be shown to beat random at n=93.

21. **Thresholds above the base rate printed as `VACUOUS`.**
    "Coverage at 10% bad-send = 100%" is true and meaningless when the base rate is
    9.7%. The harness refuses to let it read as a result.

22. **Offline replay is the default and a cache miss is fatal.**
    A silently-skipped example changes the denominator of every metric. The miss raises
    with the missing key and the prompt tail. Cached outputs are labelled as replayed,
    not re-run, everywhere they appear.

23. **Committed the brand slice and fp16 embeddings; kept torch off the grader's path.**
    The raw input is a 516MB CSV behind Kaggle auth. `eval/` is 34MB and the whole
    reproduction runs in 134s with no network and no API key.

24. **Verified the mirror's schema instead of trusting its title.**
    The top HuggingFace hit for this dataset has been lowercased and Porter-stemmed
    ("pleas send us a privat messag") and has dropped every id, the `inbound` flag and
    both reply-link columns — thread reconstruction is impossible from it. Recorded the
    md5 of the correct mirror and check it before use.

25. **The golden labels and judge calibration are marked outstanding, not claimed.**
    The brief asks for examples *you* hand-labelled. Producing them with a model and
    calling them hand-labelled would be the one dishonest thing in this repo. The review
    tools are built, the disagreement set is small (14 items), and the gap is stated in
    the report.
