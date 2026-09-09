"""Baselines, including two whose job is to make the main system falsifiable.

The assignment asks for a trivial baseline and a simple one. Two of these exist
specifically to catch ways a support agent can look good while being useless:

* MajorityBaseline / TemplateParrot -- always emit the single most frequent
  historical reply. On a corpus where the brand deflects, a parrot scores well on
  "groundedness" precisely because deflecting IS what the brand did. If the real
  system cannot beat this on resolution value, it has not earned its complexity.
* KeywordBaseline -- the obvious rules-based approach. It is expected to do badly:
  52.7% of real opening messages contain none of the domain keywords a person
  would think to write down.
"""
from __future__ import annotations
import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import Normalizer

# Written from domain intuition BEFORE looking at per-class results, deliberately:
# this is the baseline a person writes in ten minutes, and its failure is the point.
RULES: list[tuple[str, str]] = [
    ("OTHER",                          r"\b(lawyer|attorney|sue|lawsuit|assault|kill myself|suicide)\b"),
    ("BAGGAGE_MISHANDLING",            r"\b(bag|bags|baggage|luggage|suitcase|carry.?on)\b"),
    ("MONEY_CLAIM",                    r"\b(refund|reimburse|compensat|voucher|money back|charged)\b"),
    ("LIVE_TRIP_DISRUPTION",           r"\b(delay|delayed|cancel|cancelled|stuck|stranded|missed connection|diverted)\b"),
    ("RESERVATION_OR_ACCOUNT_ACTION",  r"\b(rebook|change my flight|seat|upgrade|reservation|booking|record locator)\b"),
    ("SELF_SERVICE_OR_CHANNEL_FAILURE",r"\b(website|app|online|login|log in|error|crash|check.?in)\b"),
    ("POLICY_AND_ELIGIBILITY_QUESTION",r"\b(policy|allowed|can i|do i need|how much|rules?|fee)\b"),
    ("EMPLOYEE_KUDOS",                 r"\b(thank|thanks|kudos|amazing|awesome|great job|shout ?out)\b"),
    ("SERVICE_INCIDENT_REPORT",        r"\b(rude|unprofessional|disrespect|terrible|awful|worst|complain)\b"),
]


class KeywordBaseline:
    """Trivial baseline: first matching rule wins, else the majority class."""

    def __init__(self, fallback: str = "PRAISE_AND_TRAVEL_CHATTER"):
        self.fallback = fallback
        self._rx = [(lab, re.compile(p, re.I)) for lab, p in RULES]

    def fit(self, X=None, y=None):
        if y is not None and len(y):
            vals, cnt = np.unique(np.asarray(y), return_counts=True)
            self.fallback = str(vals[cnt.argmax()])
        return self

    def predict(self, X):
        out = []
        for t in X:
            lab = self.fallback
            for name, rx in self._rx:
                if rx.search(str(t)):
                    lab = name
                    break
            out.append(lab)
        return np.asarray(out)


class MajorityBaseline:
    """The floor. Every metric must be read against this, not against zero."""

    def fit(self, X, y):
        vals, cnt = np.unique(np.asarray(y), return_counts=True)
        self.maj_ = str(vals[cnt.argmax()])
        return self

    def predict(self, X):
        return np.asarray([self.maj_] * len(X))


def tfidf_logreg(seed: int = 0):
    """Simple non-neural baseline. Char n-grams matter on tweets: they absorb
    hashtags, elongation ("sooo late"), and misspellings that word features miss."""
    from sklearn.pipeline import FeatureUnion
    return make_pipeline(
        FeatureUnion([
            ("w", TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True)),
            ("c", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=3, sublinear_tf=True)),
        ]),
        Normalizer(),
        LogisticRegression(max_iter=2000, class_weight="balanced", random_state=seed),
    )


class TemplateParrot:
    """Generation baseline: always emit the brand's most common historical reply.

    Exists to expose a specific failure of the evaluation, not to be competitive.
    A judge scoring "is this grounded in how the brand historically replied?" will
    rate this highly. If the real system does not clearly beat it on RESOLUTION
    VALUE, then the headline generation number is measuring mimicry.
    """

    def fit(self, replies: list[str]):
        from collections import Counter
        norm = [re.sub(r"\s+", " ", r.strip().lower()) for r in replies if r and r.strip()]
        self.reply_ = Counter(norm).most_common(1)[0][0] if norm else "We're sorry to hear that."
        return self

    def generate(self, *_args, **_kw) -> str:
        return self.reply_
