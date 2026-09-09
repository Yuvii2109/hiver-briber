"""Uncertainty and significance, sized for a ~200-example golden set.

Why this module exists: at n=200 across ~9 classes the per-class estimates carry
roughly +/-17pp of noise, and marginal CIs for two systems ~8 points apart will
almost always overlap even when the systems genuinely differ. Reporting bare
point estimates -- or concluding "no difference" from overlapping marginal CIs --
would both be wrong. Every comparison here is therefore PAIRED: resample the
examples once and score both systems on the same resample.

Resampling is done at CONVERSATION level, because turns from one conversation are
not independent.
"""
from __future__ import annotations
import numpy as np
from sklearn.metrics import f1_score


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval -- correct near 0 and 1, unlike normal approximation."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (max(0.0, (c - h) / d), min(1.0, (c + h) / d))


def _groups(groups, n):
    return np.arange(n) if groups is None else np.asarray(groups)


def bootstrap_metric(y_true, y_pred, metric=None, groups=None, n_boot=2000, seed=0):
    """Cluster bootstrap CI for one system. Returns (point, lo, hi)."""
    y_true, y_pred = np.asarray(y_true), np.asarray(y_pred)
    metric = metric or (lambda a, b: f1_score(a, b, average="macro", zero_division=0))
    g = _groups(groups, len(y_true))
    uniq = np.unique(g)
    idx_by_g = {u: np.flatnonzero(g == u) for u in uniq}
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([idx_by_g[u] for u in pick])
        vals.append(metric(y_true[idx], y_pred[idx]))
    return float(metric(y_true, y_pred)), float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def paired_bootstrap(y_true, pred_a, pred_b, metric=None, groups=None, n_boot=2000, seed=0):
    """CI on the DIFFERENCE (a - b), scoring both systems on the same resample.

    This is the comparison that can actually resolve a difference at n=200;
    overlapping marginal intervals are expected here and are not evidence of
    equivalence.
    """
    y_true = np.asarray(y_true)
    pred_a, pred_b = np.asarray(pred_a), np.asarray(pred_b)
    metric = metric or (lambda a, b: f1_score(a, b, average="macro", zero_division=0))
    g = _groups(groups, len(y_true))
    uniq = np.unique(g)
    idx_by_g = {u: np.flatnonzero(g == u) for u in uniq}
    rng = np.random.default_rng(seed)
    diffs = []
    for _ in range(n_boot):
        pick = rng.choice(uniq, size=len(uniq), replace=True)
        idx = np.concatenate([idx_by_g[u] for u in pick])
        diffs.append(metric(y_true[idx], pred_a[idx]) - metric(y_true[idx], pred_b[idx]))
    diffs = np.asarray(diffs)
    point = metric(y_true, pred_a) - metric(y_true, pred_b)
    return {
        "delta": float(point),
        "lo": float(np.percentile(diffs, 2.5)),
        "hi": float(np.percentile(diffs, 97.5)),
        "p_two_sided": float(2 * min((diffs <= 0).mean(), (diffs >= 0).mean())),
    }


def mcnemar(y_true, pred_a, pred_b) -> dict:
    """Exact binomial McNemar on discordant pairs -- assumption-light companion."""
    from scipy.stats import binomtest
    y_true, pred_a, pred_b = np.asarray(y_true), np.asarray(pred_a), np.asarray(pred_b)
    a_ok, b_ok = pred_a == y_true, pred_b == y_true
    n01 = int((~a_ok & b_ok).sum())
    n10 = int((a_ok & ~b_ok).sum())
    if n01 + n10 == 0:
        return {"n10": n10, "n01": n01, "p": 1.0}
    p = binomtest(n10, n10 + n01, 0.5).pvalue
    return {"n10": n10, "n01": n01, "p": float(p)}


def krippendorff_ordinal(m) -> float:
    """Krippendorff's alpha for ORDINAL data (rubric scores).

    Pearson r is the wrong statistic for judge-vs-human rubric agreement: it is
    invariant to a judge that is uniformly one point generous, and it is badly
    inflated or deflated by range restriction. Alpha penalises systematic offset.
    `m` is (n_raters, n_items) with np.nan for missing.
    """
    m = np.asarray(m, dtype=float)
    vals = m[~np.isnan(m)]
    if vals.size == 0:
        return float("nan")
    lo, hi = vals.min(), vals.max()
    if hi == lo:
        return 1.0

    def d(a, b):                       # ordinal-ish squared distance
        return (a - b) ** 2

    num = den = 0.0
    for j in range(m.shape[1]):        # observed disagreement, within item
        col = m[:, j][~np.isnan(m[:, j])]
        if col.size < 2:
            continue
        for x in col:
            for y in col:
                num += d(x, y) / (col.size - 1)
    for x in vals:                     # expected disagreement, across all
        for y in vals:
            den += d(x, y) / (vals.size - 1)
    return float(1 - num / den) if den else float("nan")
