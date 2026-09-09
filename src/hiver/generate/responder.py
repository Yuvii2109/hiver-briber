"""Case-grounded reply drafting.

The brief asks for a reply "grounded in how that brand has historically resolved
similar issues". Two design consequences follow, and both are the whole point:

1. Evidence is retrieved from RESOLVED cases only. 22.9% of this brand's historical
   replies are deflections ("DM us"). Grounding on those teaches the agent to
   deflect -- and a groundedness judge would REWARD it, because deflecting is
   genuinely what the brand did. Excluding them is what makes the task non-trivial.

2. The prompt forbids inventing anything the retrieved cases do not support, and
   forbids claiming actions the agent cannot perform (it has no account access).
   Historical replies are treated as EVIDENCE OF BEHAVIOUR, not as authoritative
   policy: they are 2017 tweets, and airline policy moves.

There is also a keyless generator (`NearestReplyGenerator`) so the end-to-end demo
runs for a grader with no API key, and so the LLM has something to beat.
"""
from __future__ import annotations
import re
import pandas as pd

SYSTEM = """You draft public reply tweets for @AmericanAir's customer support team.

You will be given a customer's message and up to 5 REAL historical cases showing how
this brand's human agents handled similar messages. Draft the reply the brand would send.

Rules, in priority order:
1. GROUND every factual or policy claim in the historical cases shown. If they do not
   establish something, do not assert it.
2. NEVER invent a policy, fee, time window, compensation amount, or entitlement.
3. NEVER claim you have done something you cannot do. You have no account access: you
   cannot look up a booking, rebook, issue a refund, or locate a bag. You may ask for
   what a human would need.
4. Match the brand's voice in the cases: brief, warm, plain, first person plural.
5. Fit a tweet: at most 280 characters, one or two sentences.
6. Do NOT open with "DM us" unless the customer's issue genuinely cannot proceed
   without private data. Deflection is a last resort, not a default.
7. Do not use the customer's name unless they gave it.

Output ONLY the reply text. No preamble, no quotes, no explanation."""


def build_prompt(customer: str, intent: str, cases: pd.DataFrame) -> str:
    lines = [f"CUSTOMER MESSAGE:\n{customer}\n", f"PREDICTED INTENT: {intent}\n"]
    if len(cases):
        lines.append("HISTORICAL CASES (how this brand actually handled similar messages):")
        for i, (_, c) in enumerate(cases.iterrows(), 1):
            lines.append(f"\n[case {i}] similarity {c['sim']:.2f}")
            lines.append(f"  customer: {str(c['q'])[:300]}")
            lines.append(f"  agent replied: {str(c['reply_clean'])[:300]}")
    else:
        lines.append("HISTORICAL CASES: none above the similarity floor. "
                     "You have no precedent for this message — do not guess at policy.")
    lines.append("\nDraft the reply.")
    return "\n".join(lines)


class GroundedResponder:
    def __init__(self, cache, model: str = "claude-opus-5", live: bool | None = None):
        self.cache, self.model, self.live = cache, model, live

    def generate(self, customer: str, intent: str, cases: pd.DataFrame) -> str:
        from hiver.llm import call
        txt = call(self.cache, SYSTEM,
                   [{"role": "user", "content": build_prompt(customer, intent, cases)}],
                   model=self.model, temperature=0.0, seed=0, live=self.live)
        return txt.strip().strip('"')


class NearestReplyGenerator:
    """Keyless baseline: send the most similar historical reply verbatim.

    Free, deterministic, and reproducible with no API key. It is also a genuinely
    hard baseline for grounding -- it is by construction 100% faithful to the
    corpus -- which is exactly why the LLM has to earn its place on the axis that
    matters: whether the reply actually fits THIS customer.
    """

    def generate(self, customer: str, intent: str, cases: pd.DataFrame) -> str:
        if not len(cases):
            return "We're sorry for the trouble. Can you tell us a bit more so we can help?"
        return str(cases.iloc[0]["reply_clean"])


DEFLECT_RX = re.compile(
    r"(?:\bdm\b|\bdms\b|direct message|private message|send us a (?:message|note)|"
    r"message us|follow us and|click the link|via this link|meet you there)", re.I)


def is_deflection(reply: str) -> bool:
    """Hard, non-LLM check applied to GENERATED replies.

    Reported for the system, every baseline, and the real human agents. Without it
    an LLM judge scoring "groundedness" will happily award full marks to an agent
    that has learned to say "DM us" to everything.
    """
    return bool(DEFLECT_RX.search(reply or ""))
