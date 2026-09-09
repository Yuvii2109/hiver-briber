"""Intent classifier: a calibrated linear head on sentence embeddings.

Why not kNN-as-classifier, which was the original plan: raw cosine similarity is
not a probability. The entire escalation layer is a threshold on confidence, so an
uncalibrated score would make every threshold meaningless. `predict_proba` from a
linear head, checked with a reliability curve, is the thing that makes the policy
interpretable. kNN stays in the system -- as the retriever, which is its job.

Label provenance, stated plainly because it changes what the numbers mean: the
training labels are TEACHER labels produced by an LLM applying the frozen codebook,
not human ground truth. This is distillation. The honest framing is "a linear model
distilled from an LLM teacher at a fraction of the inference cost", and the teacher's
own accuracy on the human golden set is the ceiling being chased -- so it is reported
as a row in the results table, not hidden.
"""
from __future__ import annotations
import numpy as np
from sklearn.linear_model import LogisticRegression


class EmbeddingIntentClassifier:
    def __init__(self, seed: int = 0, C: float = 4.0):
        # multinomial is the default in sklearn >=1.5; the explicit kwarg was
        # removed in 1.9, so passing it would break on a current install.
        self.clf = LogisticRegression(
            max_iter=3000, C=C, class_weight="balanced", random_state=seed)

    def fit(self, emb: np.ndarray, y):
        self.clf.fit(np.asarray(emb, dtype=np.float32), np.asarray(y))
        self.classes_ = self.clf.classes_
        return self

    def predict(self, emb):
        return self.clf.predict(np.asarray(emb, dtype=np.float32))

    def predict_proba(self, emb):
        return self.clf.predict_proba(np.asarray(emb, dtype=np.float32))

    def confidence(self, emb):
        """Return (top1 prob, margin). Margin separates 'sure' from 'sure between
        two options', which a max-probability threshold alone cannot see."""
        p = self.predict_proba(emb)
        s = np.sort(p, axis=1)
        return s[:, -1], s[:, -1] - s[:, -2]


def reliability(probs: np.ndarray, correct: np.ndarray, bins: int = 10):
    """Reliability curve + ECE. If confidence is not calibrated, no threshold on it
    means what its number says, and the risk-coverage curve inherits the error."""
    probs, correct = np.asarray(probs), np.asarray(correct).astype(float)
    edges = np.linspace(0, 1, bins + 1)
    rows, ece = [], 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (probs > lo) & (probs <= hi)
        if not m.any():
            continue
        conf, acc = probs[m].mean(), correct[m].mean()
        rows.append({"bin": f"({lo:.1f},{hi:.1f}]", "n": int(m.sum()),
                     "confidence": round(float(conf), 3), "accuracy": round(float(acc), 3)})
        ece += m.mean() * abs(acc - conf)
    return rows, float(ece)
