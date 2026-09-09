# Building a support agent for @AmericanAir — and trying to break it

## 1. Problem framing, and how the brand was chosen

The brief says to pick one brand and draft replies *grounded in how that brand has
historically resolved similar issues*. That sentence is the whole problem, because it
silently assumes the corpus contains resolutions.

Mostly it does not. Twitter support deflects: the public reply says "DM us" and the
actual resolution happens off-dataset. I measured this across the corpus, counting a
reply as a deflection if it routes to a private channel **or** to a URL — the
link-routing half matters, and missing it is how the intuitive answer survives:

| brand | threads | deflection (DM only) | deflection (DM **or** link) |
|---|---:|---:|---:|
| GWRHelp | 10,674 | 2.5% | **7.1%** |
| VirginTrains | 14,825 | 4.5% | 18.0% |
| SouthwestAir | 21,524 | 22.0% | 24.9% |
| **AmericanAir** | **26,202** | **21.5%** | **26.1%** |
| Delta | 26,052 | 25.4% | 26.9% |
| AmazonHelp | 82,498 | 1.9% | 46.2% |
| AppleSupport | 80,639 | 64.8% | 74.8% |
| **Uber_Support** | 41,902 | 41.3% | **88.3%** |

Uber_Support is the intuitive pick — trip, fare, driver, safety and refund intents are
beautifully separable. It is also the third-worst brand in the dataset for this task.
At 88.3% deflection an agent trained to imitate it learns to answer "here's a link" to
nine messages in ten, and a groundedness judge would score that **highly**, because
that is genuinely what Uber did. The evaluation would have been unfalsifiable. The
naive DM-only regex reports 41.3% and hides this entirely.

AmericanAir wins on the combination that matters: enough volume (26,202 conversations,
49,423 inbound messages), real in-channel resolutions, and the **lowest URL rate of any
high-volume brand (8.9%)** — its replies are text, not link dumps. GWRHelp is cleaner
still, but much of its traffic is live train-times that no historical-retrieval system
can answer, and it has almost no escalation-worthy content.

**What "good" means here.** Not "sounds like the brand". Three things: the reply must
not assert anything the evidence does not support; it must move *this* customer
forward; and the system must know when to stop. Those are measured separately and
deliberately never averaged (§4).

**What I chose not to build.** No fine-tuning — it would spend the whole budget and
make the evaluation story muddier, not better. No FAISS: at 28k cases an exact cosine
matmul is ~10ms, and a dependency that buys nothing is a reproducibility liability. No
Recall@k or MRR for retrieval: there is no ground-truth relevant document here, so
those numbers would be fabricated rigour. No multi-turn dialogue manager — the graded
unit is the opening message.

## 2. The data is messier than its schema suggests

Four properties break the obvious implementation. All were measured on the full
2,811,774 rows, and all are handled in `src/hiver/data/`.

1. **A thread is a tree, not a chain.** `response_tweet_id` lists multiple ids for
   7.91% of tweets. Reconstruction walks child to parent instead, which is single-valued.
2. **`tweet_id` is not chronological.** 55.6% of replies have a *higher*-id parent.
   Ordering must come from parsed `created_at` — and lexically sorting Twitter's
   `Tue Oct 31 22:10:47 +0000 2017` format is meaningless.
3. **Connected components over-merge.** 5.9% of AmericanAir components contain more
   than one customer; the worst holds **170 customers across 204 tweets** — a pile-on
   thread. A component is not a conversation. Conversations are keyed by
   (root, customer), which is what stops unrelated complaints being retrieved as one case.
4. **22.9% of the brand's own replies are non-answers.** Deflections are labelled
   explicitly and excluded from the evidence pool, so the usable grounding corpus is
   **22,019 cases, not 28,543**. Leaving them in teaches the agent to deflect — and a
   groundedness judge rewards it for doing so.

**Splitting.** Temporal and conversation-level: threads are ordered by start time and
cut 80/10/10, so the retrieval corpus strictly pre-dates evaluation messages. Verified:
0 of 3,505 test examples predate the train boundary. The retriever also enforces
`case.created < query.created` at query time — belt-and-braces, and honestly reported
as such, since the split already guarantees it.

*The caveat that matters more than the fix:* **99.7% of this corpus is Oct–Dec 2017.**
The temporal split therefore tests robustness over about six weeks. It does not test
policy drift, and I do not claim it does.

## 3. The taxonomy is induced, not assumed

Four analysts open-coded the same 400 train-only openers from four angles
(action-first, topic-first, automatability-first, and a skeptic told to assume the
standard airline taxonomy was wrong), then reconciled. Eleven candidate intents were
cut; `eval/CODEBOOK.md` records each and why.

**The finding that justifies the exercise: the obvious airline taxonomy — baggage,
delay, refund, seat, loyalty — covers only about 23% of this traffic.** Refunds are
1.7%, baggage 4.1%. The two largest masses have no bucket in that framing:
social/praise traffic (20.6%) and complaint with nothing filable in it (5.1%). Roughly
**40% of inbound contains no answerable request at all**. A taxonomy written from
domain intuition would have left the biggest thing in the data invisible.

Ten intents plus OTHER, each action-distinct, with a strict precedence order that makes
the label a deterministic function of the text. OTHER appears **twice** in that order —
first as a safety route (anchorless legal threats, self-harm language, medical crises,
which must never receive a canned empathy line) and last as the residual.

**Both golden sets were double-annotated blind: Cohen's kappa = 0.937**, with 14 of 250
items disputed. Measuring this also caught my own error: the open-coding share estimates
were wrong. `DIFFUSE_BRAND_VENT` was eyeballed at 11.5% and measures **5.1% [3.9, 6.7]**
— a confidence interval that excludes the estimate.

**Two golden sets, never averaged.** Set B (n=100) is a uniform random draw from
held-out test threads and is the only place prior-dependent numbers are computed. Set A
(n=150) is stratified so per-class diagnosis has anything to look at. Reporting one
accuracy over a stratified set describes a distribution that does not exist.

## 4. Results

### Intent classification

Set A (stratified), macro-F1 with cluster-bootstrap 95% confidence intervals:

| system | macro-F1 | 95% CI | accuracy |
|---|---:|---|---:|
| majority class | 0.017 | [0.010, 0.024] | 0.105 |
| keyword rules *(trivial)* | 0.297 | [0.226, 0.354] | 0.329 |
| TF-IDF + logistic regression *(simple)* | **0.610** | [0.524, 0.677] | 0.629 |
| embeddings + logistic regression | 0.602 | [0.516, 0.672] | 0.615 |

The marginal intervals overlap. That is expected at n=143 and is **not** evidence of no
difference, which is why every comparison is paired on the same resample:

- vs keyword: **delta +0.305 [+0.210, +0.396], p<0.0001** (McNemar n10=54, n01=13, p<0.0001)
- vs TF-IDF: **delta −0.008 [−0.083, +0.068], p=0.83** (McNemar p=0.86)

**The neural model does not beat TF-IDF.** Reporting that is the point: the embeddings
still earn their place as the *retriever*, but as a classifier they are an unearned
dependency. The keyword baseline fails for a measurable reason — 52.7% of real openers
contain none of the domain keywords a person would think to write down.

Calibration ECE = 0.063. This matters because the escalation threshold is a threshold
on exactly this number.

### Reply generation

150 held-out messages, four systems, judged blind on two axes that are never averaged:

| system | faithfulness | resolution | deflection rate | unsafe-to-send |
|---|---:|---:|---:|---:|
| **grounded LLM (this system)** | **4.83** | **3.86** | **0.7%** | 0.7% [0, 4] |
| nearest historical reply *(keyless)* | 3.25 | 2.34 | 0.0% | 59.3% [51, 67] |
| template parrot *(trivial)* | 2.02 | 1.00 | 0.0% | 100% [98, 100] |
| the brand's real human agents | 3.91 | 3.69 | 14.0% | 6.0% [3, 11] |

Paired on the same items, resolution: **+1.52** vs nearest-reply, **+2.86** vs parrot,
**+0.17 vs the real humans** (p=0.033).

The **template parrot** exists precisely to expose a scoring failure. It always emits
the brand's single most common historical reply, and on a single "groundedness" axis it
would look defensible — it is 100% authentic brand language. Split into two axes it
collapses: faithfulness 2.02, resolution 1.00, unsafe 100%. Any evaluation that cannot
tell this system apart from a real one is not measuring support quality.

The **nearest-reply** baseline is the more interesting failure: it is by construction
perfectly faithful to the corpus, yet **59.3% unsafe**, because verbatim reuse imports
another customer's flight number, name, or departure time into a new conversation.

### Escalation

Reframed from four OR'd booleans (which yield one operating point and cannot be
compared to anything) to selective prediction. Target: `NEEDS_HUMAN` = the draft is
unsafe to send **or** fails to move the customer forward. Base rate 12.0%.

Judging safety alone gave **1 positive in 150** — too sparse to fit anything. That
sparsity is itself the finding: on this brand the realistic failure is not a dangerous
reply, it is a useless one.

| escalation signal | AURC (lower better) | coverage at 5% bad-send |
|---|---:|---:|
| random | 0.0695 | 43.0% |
| 1 − intent confidence | 0.0895 | 10.8% |
| 1 − retrieval similarity | 0.1038 | 7.5% |
| **measured intent difficulty alone** | **0.0552** | **50.5%** |
| full 11-feature risk model | 0.0636 | 49.5% |

**Both signals the original design was built on are worse than random.** The fitted
weight on confidence came out *positive* — higher confidence predicting *more* risk.
The diagnostic explains it: failure concentrates by intent, not by certainty.
`LIVE_TRIP_DISRUPTION` needs a human 35.3% of the time and `SERVICE_INCIDENT_REPORT`
33.3%, while `POLICY_AND_ELIGIBILITY_QUESTION` and `EMPLOYEE_KUDOS` need one **0.0%**.
Being sure *what* the customer wants tells you nothing about whether you can *help*
them: a flight-status question is trivial to classify and impossible to answer without
live operational data. Retrieval similarity carries no signal either (r=+0.10, p=0.22).

A single measured feature beats the eleven-feature model. **And none of it clears the
bar:** AURC(intent difficulty) − AURC(random) = **−0.0138, 95% CI [−0.0575, +0.0196]**.
The interval spans zero. **At n=93 I cannot demonstrate that this escalation layer beats
random**, and I am not going to claim otherwise.

## 5. Top failure modes, from the data

1. **Live operational questions are unanswerable by construction.** "Why is AA2112
   delayed?" needs a live feed. 35.3% of `LIVE_TRIP_DISRUPTION` drafts need a human —
   the single largest failure concentration. *Hypothesis: this is not a model problem
   and more data will not fix it; it needs an ops API or an honest refusal.*
2. **`SERVICE_INCIDENT_REPORT` is the worst real class (F1 0.34, n=15).** The confusion
   matrix shows it scattering across seven other classes. *Hypothesis: it is defined by
   what it is not — a residue of "grievance with an anchor but no money ask" — and
   residual categories are hard to learn.*
3. **Verbatim retrieval leaks other customers' facts.** The nearest-reply baseline is
   59.3% unsafe: "Flight 1839 already arrived" pasted to someone else entirely.
   *Hypothesis: retrieval must supply patterns, never text — which is why the LLM
   rewriting layer exists at all.*
4. **Sarcastic thanks.** "Thanks for delaying my flight three times" is a service
   incident. Any sentiment-led router files it as praise. Handled by a codebook rule
   forcing classification on the described event, never the polarity word.
5. **The `DIFFUSE_BRAND_VENT` / `PRAISE` boundary.** 3 of 13 vents were called praise.
   *Hypothesis: the zero-anchor test is applied inconsistently to very short messages —
   this is also where the two blind annotators disagreed most often.*

## 6. What is misleading about my headline number

The headline is **macro-F1 0.60 and a draft that beats the brand's own agents**. Here is
everything wrong with it, in order of how much it should worry you.

1. **The gold labels are LLM-authored.** Both annotators were Claude applying my
   codebook. kappa=0.937 measures the codebook's internal consistency, **not**
   human-level reliability, and two annotators from one model family share their blind
   spots. Only the 14 disputed items are queued for human adjudication. Every classifier
   number is therefore *agreement with a model-derived standard*, not accuracy.
2. **The +0.91 faithfulness win over human agents is largely an artifact.** The judge
   grades against the retrieved evidence. Human agents *had account access*, so
   "We have an ETD of 6:50p, Hemant" is scored **1** for "claims a lookup the drafter
   cannot do" — but that agent could do it, and that reply is genuinely more useful than
   anything my system produced. I am penalising humans for having the tool that makes
   them good. The resolution comparison (+0.17) is fairer, and it is small and marginal.
3. **The judge and the generator are the same model family.** No cross-family judge and
   no self-preference control. Groundedness judged against passages the generator was
   handed measures faithfulness, not correctness.
4. **The escalation layer is not shown to work.** Point estimates favour it; the interval
   spans zero. And "coverage at 10% bad-send rate = 100%" is *vacuous* — the base rate is
   9.7%, so doing nothing already meets it. The harness prints `VACUOUS` on such rows
   rather than letting them read as results.
5. **Generation numbers are replayed, not re-run.** `repro.py` reproduces the *analysis*
   deterministically; it does not re-invoke the model.
6. **Per-class F1 at n≈13 is uninterpretable alone.** A recall of 0.80 at n=15 has a
   Wilson interval of [0.55, 0.93] — plus or minus 19 points. Per-class numbers are
   printed with `n` and their interval in the same cell so they cannot be misread. Note
   that *merging intents would not fix this*: macro-F1 precision is driven by total N,
   not by per-class n.
7. **Set A aggregates are not population estimates**, which is why they are never quoted
   as such — its class prior is manufactured by design.
8. **One brand, one six-week window, 2017.** Historical replies are evidence of
   *behaviour*, not authoritative policy. Airline policy has moved since.
9. **I designed the taxonomy, wrote the codebook, built the golden set, wrote the judge
   rubric and chose the metrics.** Every layer shares one person's priors.

## 7. With one more week

In value order: (a) a genuine human pass over all 250 golden labels plus about 50 judge
calibration scores, which converts the two biggest caveats into measurements — the
tooling is built and the gap is honest, not hidden; (b) a cross-family judge to break
the self-preference confound; (c) grow the escalation set to roughly n=400, the size the
interval says is needed to resolve it; (d) an ops-data tool for `LIVE_TRIP_DISRUPTION`,
the largest failure bucket; (e) re-run the frozen pipeline unchanged on Delta as a
transfer check, which turns a one-brand result into evidence.
