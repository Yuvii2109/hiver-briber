"""Exact cosine retrieval over the historical case corpus.

Deliberately NOT FAISS. At ~28k cases a brute-force matmul is ~10ms, exact, and
adds no dependency or platform risk -- FAISS would buy nothing here and is a
reproducibility liability on Windows/Python 3.14. Being able to justify the
absence of a component is worth more than the component.
"""
from __future__ import annotations
import numpy as np
import pandas as pd


class CaseIndex:
    def __init__(self, emb: np.ndarray, meta: pd.DataFrame, exclude_deflections: bool = True):
        """`emb` rows align with `meta` rows. Vectors must be L2-normalised."""
        self.meta = meta.reset_index(drop=True)
        self.emb = np.ascontiguousarray(emb, dtype=np.float32)
        # A deflection ("DM us") is not a resolution. Grounding on it teaches the
        # agent to deflect -- and it would score well for doing so, since that IS
        # what the brand did. Kept in `meta` so the planner can still CHOOSE to
        # deflect, but excluded from the evidence pool by default.
        self.pool = np.flatnonzero(~self.meta["deflection"].values) if exclude_deflections \
            else np.arange(len(self.meta))

    def search(self, qvec: np.ndarray, k: int = 5, before=None) -> pd.DataFrame:
        """Top-k most similar historical cases.

        `before` enforces the temporal constraint: a case may only be used as
        evidence if it was written BEFORE the message being answered. Without
        this the agent can retrieve from the future, which flatters retrieval.
        """
        cand = self.pool
        if before is not None:
            created = pd.to_datetime(self.meta["created"].values[cand], utc=True)
            ts = pd.Timestamp(before)
            ts = ts.tz_localize("UTC") if ts.tz is None else ts.tz_convert("UTC")
            cand = cand[created < ts]
        if cand.size == 0:
            return self.meta.iloc[[]].assign(sim=[])
        sims = self.emb[cand] @ np.asarray(qvec, dtype=np.float32).ravel()
        top = cand[np.argsort(-sims)[:k]]
        out = self.meta.iloc[top].copy()
        out["sim"] = sims[np.argsort(-sims)[:k]]
        return out
