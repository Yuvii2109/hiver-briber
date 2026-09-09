"""Reconstruct support threads from the raw TWCS tweet table.

Three properties of this dataset break the obvious implementation, all measured
on the full 2,811,774-row file:

1. ``response_tweet_id`` lists MULTIPLE ids for 7.91% of tweets, so a thread is a
   tree, not a chain. We walk child->parent (``in_response_to_tweet_id``), which is
   single-valued, and group by root.
2. ``tweet_id`` is NOT chronological: 55.6% of replies have a parent with a higher
   id. Ordering must come from parsed ``created_at``.
3. ``created_at`` is a Twitter-format string ("Tue Oct 31 22:10:47 +0000 2017");
   sorting it lexically is meaningless.
"""
from __future__ import annotations
import pandas as pd

TWITTER_TS = "%a %b %d %H:%M:%S %z %Y"


def load_raw(path: str) -> pd.DataFrame:
    df = pd.read_csv(
        path,
        dtype={
            "tweet_id": "int64", "author_id": "str", "inbound": "str",
            "created_at": "str", "text": "str",
            "response_tweet_id": "str", "in_response_to_tweet_id": "str",
        },
    )
    df["inbound"] = df["inbound"].str.strip().str.lower().eq("true")
    df["parent"] = pd.to_numeric(df["in_response_to_tweet_id"], errors="coerce")
    # Trap 3: parse, never lex-sort.
    df["created"] = pd.to_datetime(df["created_at"], format=TWITTER_TS, utc=True, errors="coerce")
    return df


def add_thread_ids(df: pd.DataFrame) -> pd.DataFrame:
    """Group tweets into threads by walking parent pointers to a root (union-find-ish).

    Uses child->parent because it is single-valued; ``response_tweet_id`` is not
    (trap 1). Path compression keeps this linear over ~2.8M rows.
    """
    known = set(df["tweet_id"].tolist())
    parent = {
        int(t): int(p)
        for t, p in zip(df["tweet_id"], df["parent"])
        if pd.notna(p) and int(p) in known
    }
    root_of: dict[int, int] = {}

    for start in df["tweet_id"].tolist():
        node, path = int(start), []
        while node in parent and node not in root_of:
            path.append(node)
            node = parent[node]
            if len(path) > 500:            # defensive: malformed cycle
                break
        root = root_of.get(node, node)
        for n in path:
            root_of[n] = root
        root_of[node] = root

    df["thread"] = df["tweet_id"].map(root_of).astype("int64")
    return df


def split_pileups(df: pd.DataFrame) -> pd.DataFrame:
    """Split over-merged components into one conversation per customer.

    A connected component is not a conversation. When several customers reply to
    the same brand tweet, the union-find above glues them into one blob: measured
    on AmericanAir, 5.9% of components contain more than one customer author and
    the worst holds 170 customers across 204 tweets. Retrieval over such a blob
    would mix unrelated complaints into a single "case".

    Conversation key = (component root, customer author). Brand tweets are
    assigned to the conversation of the customer they reply to.
    """
    cust = df["author_id"].where(df["inbound"])
    # a brand tweet inherits the customer of its parent
    by_id = df.set_index("tweet_id")["author_id"]
    inbound_by_id = df.set_index("tweet_id")["inbound"]
    parent_author = df["parent"].map(by_id)
    parent_inbound = df["parent"].map(inbound_by_id).fillna(False).astype(bool)
    cust = cust.fillna(parent_author.where(parent_inbound))
    # remaining gaps: fall back to the component's most frequent customer
    fallback = (df.loc[df["inbound"]].groupby("thread")["author_id"]
                  .agg(lambda s: s.value_counts().index[0]))
    cust = cust.fillna(df["thread"].map(fallback))
    df = df.copy()
    df["conv"] = df["thread"].astype(str) + ":" + cust.astype(str)
    return df


def brand_threads(df: pd.DataFrame, brand: str) -> pd.DataFrame:
    """Conversations whose brand-side replies belong to `brand`."""
    owner = df.loc[~df["inbound"]].groupby("conv")["author_id"].first()
    keep = set(owner[owner == brand].index)
    out = df[df["conv"].isin(keep)].copy()
    return out.sort_values(["conv", "created"], kind="mergesort")
