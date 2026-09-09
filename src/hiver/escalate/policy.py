"""Escalation as SELECTIVE PREDICTION, not a boolean flag.

The original design was four OR'd thresholds. That yields exactly one operating
point, so it cannot be tuned, cannot be compared against a baseline, and cannot
answer the only question an ops lead actually asks: "how much can we automate
before the error rate becomes unacceptable?"

Two mechanisms instead:

1. A single calibrated scalar `risk` in [0,1], fit on DEV against the human
   send-safety label. Sweeping one threshold over it produces a risk-coverage
   curve, which is the deliverable.
2. A hard OVERRIDE list that escalates regardless of the score. Overrides are not
   a fallback for a weak model; they encode harms where no accuracy number would
   justify automation. Their cost is reported separately -- how much coverage they
   burn, and how many unsafe sends they actually catch -- so they cannot hide a
   bad model.

The scores that feed this are DELIBERATELY not raw cosine similarity: cosine is
not a probability, and a policy built on uncalibrated numbers means nothing.
"""
from __future__ import annotations
import re
import numpy as np
from dataclasses import dataclass, field

# Harms where automation is refused on principle. Recall-first: these patterns are
# meant to over-trigger, and their false-positive cost is reported, not hidden.
OVERRIDE_PATTERNS: dict[str, str] = {
    "safety_or_violence": r"\b(assault|assaulted|groped|attack(?:ed)?|threat(?:en|ened)?|weapon|hit me|punched|abus(?:e|ed|ive))\b",
    "self_harm": r"\b(kill myself|suicid|end my life|want to die|self.?harm)\b",
    "medical_emergency": r"\b(ambulance|hospital|heart attack|seizure|stroke|medical emergency|unconscious|dying)\b",
    "legal_or_regulator": r"\b(lawyer|attorney|lawsuit|sue you|small claims|attorney general|\bDOT\b|\bFAA\b|regulator|litigat)\b",
    "discrimination": r"\b(racist|racism|discriminat|homophob|sexist|profil(?:ed|ing))\b",
    "minor_unaccompanied": r"\b(unaccompanied minor|my (?:child|son|daughter|toddler|infant) (?:is|was) alone|\bUMNR\b)\b",
    "explicit_human_request": r"\b(speak to a (?:human|person|manager|supervisor)|real person|stop the bot|talk to someone)\b",
}
_COMPILED = {k: re.compile(v, re.I) for k, v in OVERRIDE_PATTERNS.items()}


def overrides(text: str) -> list[str]:
    return [k for k, rx in _COMPILED.items() if rx.search(text or "")]


@dataclass
class Signals:
    """Everything the risk model sees.

    The feature set was CHANGED after measurement. The original design escalated on
    low intent confidence and low retrieval similarity; on this data both are worse
    than random at predicting whether a draft is safe to send (AURC 0.089 and 0.104
    vs 0.070 for random), and the fitted weight on confidence came out POSITIVE --
    the opposite of the assumed direction.

    The diagnostic explains why. Failure concentrates by INTENT, not by certainty:
    LIVE_TRIP_DISRUPTION needs 35.3% human handling and SERVICE_INCIDENT_REPORT
    33.3%, while POLICY_AND_ELIGIBILITY_QUESTION and EMPLOYEE_KUDOS need 0.0%. Being
    sure WHAT the customer wants says nothing about whether the agent can HELP: a
    flight-status question is easy to classify and impossible to answer without live
    operational data. So the load-bearing feature is the intent's measured
    automatability, estimated on the dev half and applied to the test half.
    """
    intent_conf: float          # kept, and reported: it is nearly uninformative here
    intent_margin: float        # top1 - top2 probability
    top_sim: float              # kept: r=+0.10, p=0.22 -- no signal, reported as such
    mean_sim: float
    neighbour_disagree: float
    risk_tier: float            # 0/0.5/1 from the codebook
    anger: float
    msg_len: float
    n_overrides: float
    intent_difficulty: float = 0.0   # measured needs-human rate for the predicted intent
    draft_len: float = 0.0           # r=+0.21, p=0.0099: the model rambles when stuck


ANGER = re.compile(r"\b(fuck|shit|damn|hell|ridiculous|disgrace|unacceptable|worst|never again|"
                   r"appalling|outrageous|furious|livid|garbage|useless|incompetent)\b", re.I)


def anger_score(text: str) -> float:
    t = (text or "").split()
    return min(1.0, 3.0 * len(ANGER.findall(text or "")) / max(len(t), 1))


class RiskModel:
    """Logistic regression over Signals, fit on DEV against the human label.

    Deliberately a linear model: every coefficient is inspectable, which matters
    more here than a point of AUC. The report shows the fitted weights.
    """

    FEATURES = ["intent_conf", "intent_margin", "top_sim", "mean_sim",
                "neighbour_disagree", "risk_tier", "anger", "msg_len", "n_overrides",
                "intent_difficulty", "draft_len"]

    def __init__(self, seed: int = 0):
        from sklearn.linear_model import LogisticRegression
        self.clf = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=seed)

    @staticmethod
    def to_matrix(sigs: list[Signals]) -> np.ndarray:
        return np.array([[getattr(s, f) for f in RiskModel.FEATURES] for s in sigs], dtype=float)

    def fit(self, sigs: list[Signals], unsafe: np.ndarray):
        self.clf.fit(self.to_matrix(sigs), np.asarray(unsafe).astype(int))
        return self

    def risk(self, sigs: list[Signals]) -> np.ndarray:
        return self.clf.predict_proba(self.to_matrix(sigs))[:, 1]

    def weights(self) -> dict[str, float]:
        return dict(zip(self.FEATURES, self.clf.coef_[0].round(3).tolist()))


def decide(risk: float, tau: float, override_hits: list[str]) -> tuple[str, str]:
    """Return (action, human-readable reason). The brief requires a stated reason."""
    if override_hits:
        return "ESCALATE", f"override:{'+'.join(override_hits)} — never auto-handled regardless of model confidence"
    if risk >= tau:
        return "ESCALATE", f"risk {risk:.2f} >= tau {tau:.2f}"
    return "AUTO_SEND", f"risk {risk:.2f} < tau {tau:.2f}"


def risk_coverage_curve(risk: np.ndarray, unsafe: np.ndarray, forced: np.ndarray | None = None):
    """The core artifact: what error rate do we pay for each level of automation?

    Returns (coverage, selective_risk, tau) arrays. `forced` marks items escalated
    by override, which are removed from coverage at every threshold.
    """
    risk, unsafe = np.asarray(risk, float), np.asarray(unsafe).astype(int)
    forced = np.zeros(len(risk), bool) if forced is None else np.asarray(forced, bool)
    taus = np.unique(np.concatenate([[0.0], np.sort(risk), [1.0 + 1e-9]]))
    cov, sel = [], []
    for t in taus:
        auto = (risk < t) & ~forced
        n = auto.sum()
        cov.append(n / len(risk))
        sel.append(unsafe[auto].mean() if n else 0.0)
    return np.array(cov), np.array(sel), taus


def aurc(cov: np.ndarray, sel: np.ndarray) -> float:
    """Area under the risk-coverage curve; lower is better."""
    o = np.argsort(cov)
    return float(np.trapezoid(sel[o], cov[o]))


def coverage_at_risk(cov: np.ndarray, sel: np.ndarray, max_risk: float) -> float:
    """Headline number: the most we can automate while holding error <= max_risk."""
    ok = sel <= max_risk
    return float(cov[ok].max()) if ok.any() else 0.0
