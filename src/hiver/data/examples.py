"""Turn threads into (context, customer message, brand reply) training/eval units.

The central data-quality fact for this corpus: a large share of brand replies are
not answers at all, they are routing ("DM us", "visit this link"). Measured share
of threads containing such a reply, by brand:

    GWRHelp 7.1% | VirginTrains 18.0% | SouthwestAir 24.9% | AmericanAir 26.1%
    Delta 26.9% | AmazonHelp 46.2% | AppleSupport 74.8% | Uber_Support 88.3%

If deflections are left in the retrieval corpus the agent learns to answer
"please DM us" to everything -- and scores HIGH on groundedness for doing so,
because that is genuinely what the brand did. So deflection is labelled
explicitly and handled as a modelling decision, not silently ignored.
"""
from __future__ import annotations
import re
import pandas as pd

# Routing to a private channel.
_DM = re.compile(
    r"(?:\bdm\b|\bdms\b|direct message|private message|\bpm us\b|message us|"
    r"send us a (?:message|note)|meet you there|shoot us a)", re.I)
# Routing to a URL ("visit this link ...", "follow up here; <url>").
_ROUTE = re.compile(
    r"(?:visit|follow up|click|head (?:to|over)|check out|reach out|contact us|"
    r"fill out|use|via|here)[^.!?]{0,40}https?://", re.I)

_SIG = re.compile(r"[\^\*\-~]\s?[A-Za-z]{1,3}\s*$")   # "^KC", "*AMV", "- Jordan"
_URL = re.compile(r"https?://\S+")
_MENTION = re.compile(r"@\w+")


def is_deflection(text: str) -> bool:
    t = text or ""
    return bool(_DM.search(t) or _ROUTE.search(t))


def clean_reply(text: str) -> str:
    """Strip agent signature, urls and mentions -> the substantive content."""
    t = _URL.sub(" ", text or "")
    t = _MENTION.sub(" ", t)
    t = _SIG.sub("", t.strip())
    return re.sub(r"\s+", " ", t).strip()


def nonascii_ratio(text: str) -> float:
    """Fraction of non-ASCII chars, ignoring emoji and smart punctuation."""
    t = text or ""
    if not t:
        return 0.0
    skip = {0x2019, 0x201C, 0x201D, 0x2018, 0x2026, 0x2014, 0x2013, 0x00A0}
    n = sum(
        1 for c in t
        if ord(c) > 127 and not (0x1F300 <= ord(c) <= 0x1FAFF) and ord(c) not in skip
    )
    return n / len(t)


def build_examples(threads: pd.DataFrame) -> pd.DataFrame:
    """One example per (customer turn -> immediately following brand turn).

    Consecutive same-speaker tweets are merged first: customers routinely tweet
    3-4 times in a row before the brand answers, and treating those as separate
    examples would attribute one reply to only the last fragment.
    """
    rows = []
    for tid, g in threads.groupby("conv", sort=False):
        g = g.sort_values("created", kind="mergesort")
        # merge consecutive same-speaker turns
        turns: list[dict] = []
        for _, r in g.iterrows():
            if turns and turns[-1]["inbound"] == r["inbound"]:
                turns[-1]["text"] += " " + str(r["text"])
            else:
                turns.append({"inbound": bool(r["inbound"]),
                              "text": str(r["text"]),
                              "created": r["created"],
                              "tweet_id": int(r["tweet_id"])})
        for i, t in enumerate(turns):
            if not t["inbound"]:
                continue
            reply = turns[i + 1] if i + 1 < len(turns) else None
            if reply is None or reply["inbound"]:
                continue
            rows.append({
                "conv": tid,
                "tweet_id": t["tweet_id"],
                "turn_index": i,
                "is_first_turn": i == 0,
                "context": " | ".join(
                    ("C: " if u["inbound"] else "A: ") + _URL.sub("", u["text"]).strip()
                    for u in turns[:i]
                ),
                "customer": str(t["text"]),
                "reply": reply["text"],
                "reply_clean": clean_reply(reply["text"]),
                "created": t["created"],
                "deflection": is_deflection(reply["text"]),
            })
    ex = pd.DataFrame(rows)
    if len(ex):
        ex["cust_words"] = ex["customer"].map(lambda s: len(_URL.sub("", _MENTION.sub("", s)).split()))
        ex["nonascii"] = ex["customer"].map(nonascii_ratio)
    return ex
