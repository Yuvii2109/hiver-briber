"""Temporal, thread-level splitting.

Two distinct leakage risks, both real here:

* Thread-level  -- the same conversation must never straddle splits, or the
  retriever can return a neighbouring turn of the very thread being evaluated.
* Temporal      -- a random split lets the agent retrieve cases written AFTER the
  message it is answering. Support language and policy drift within the corpus
  window, so a random split flatters retrieval. We split by thread start time.

We additionally drop near-duplicate replies from the retrieval corpus: brand
agents paste templates, so an unfiltered corpus makes "retrieval" trivially
return the same boilerplate and inflates apparent grounding.
"""
from __future__ import annotations
import hashlib
import re
import pandas as pd

_NORM = re.compile(r"[^a-z0-9 ]+")


def template_key(reply_clean: str) -> str:
    """Normalised fingerprint of a reply, for collapsing pasted templates."""
    t = _NORM.sub(" ", (reply_clean or "").lower())
    t = re.sub(r"\b\d+\b", "#", t)
    t = re.sub(r"\s+", " ", t).strip()
    return hashlib.md5(t.encode()).hexdigest()[:16]


def temporal_split(ex: pd.DataFrame, train_frac: float, dev_frac: float) -> pd.DataFrame:
    """Assign each example to train/dev/test by its THREAD's start time."""
    start = ex.groupby("conv")["created"].min().sort_values()
    n = len(start)
    n_tr, n_dev = int(n * train_frac), int(n * dev_frac)
    split = pd.Series("test", index=start.index)
    split.iloc[:n_tr] = "train"
    split.iloc[n_tr:n_tr + n_dev] = "dev"
    ex = ex.copy()
    ex["split"] = ex["conv"].map(split)
    return ex


def dedupe_corpus(train: pd.DataFrame, max_per_template: int = 3) -> pd.DataFrame:
    """Cap how many times any one reply template can appear in the retrieval corpus."""
    t = train.copy()
    t["tkey"] = t["reply_clean"].map(template_key)
    return t.groupby("tkey", group_keys=False).head(max_per_template)
