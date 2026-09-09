"""FROZEN intent taxonomy for @AmericanAir.

Induced by open coding 400 real conversation openers from the TRAIN split only
(never dev/test). Four analysts coded the same sample independently from four
angles -- action-first, topic-first, automatability-first, and a skeptic told to
assume the obvious airline taxonomy was wrong -- and their proposals were then
reconciled into this single taxonomy. 11 candidate intents were cut; the reasons
are recorded in eval/CODEBOOK.md.

The headline finding that shaped it: the generic airline taxonomy
(baggage/delay/refund/seat/loyalty) accounts for only ~23% of this traffic, while
~40% of inbound contains no answerable request at all. A taxonomy copied from
domain intuition would have left the two largest masses invisible.

See eval/CODEBOOK.md for the full annotation rules. This file is the frozen
artifact the code imports; it must not drift from the codebook.
"""
from __future__ import annotations

INTENTS: list[str] = [
    "PRAISE_AND_TRAVEL_CHATTER",
    "SERVICE_INCIDENT_REPORT",
    "POLICY_AND_ELIGIBILITY_QUESTION",
    "LIVE_TRIP_DISRUPTION",
    "DIFFUSE_BRAND_VENT",
    "EMPLOYEE_KUDOS",
    "SELF_SERVICE_OR_CHANNEL_FAILURE",
    "RESERVATION_OR_ACCOUNT_ACTION",
    "MONEY_CLAIM",
    "BAGGAGE_MISHANDLING",
    "OTHER",
]

# Harm if a bot auto-answers this wrongly. Drives the escalation override list.
RISK_TIER: dict[str, str] = {
    "PRAISE_AND_TRAVEL_CHATTER": "low",
    "SERVICE_INCIDENT_REPORT": "high",
    "POLICY_AND_ELIGIBILITY_QUESTION": "medium",
    "LIVE_TRIP_DISRUPTION": "medium",
    "DIFFUSE_BRAND_VENT": "medium",
    "EMPLOYEE_KUDOS": "low",
    "SELF_SERVICE_OR_CHANNEL_FAILURE": "medium",
    "RESERVATION_OR_ACCOUNT_ACTION": "high",
    "MONEY_CLAIM": "high",
    "BAGGAGE_MISHANDLING": "medium",
    "OTHER": "high",
}

# Prior share (%) estimated on the 400-message coding sample, for reference only.
EST_SHARE: dict[str, float] = {
    "PRAISE_AND_TRAVEL_CHATTER": 22,
    "SERVICE_INCIDENT_REPORT": 15,
    "POLICY_AND_ELIGIBILITY_QUESTION": 14,
    "LIVE_TRIP_DISRUPTION": 13,
    "DIFFUSE_BRAND_VENT": 11.5,
    "EMPLOYEE_KUDOS": 6.5,
    "SELF_SERVICE_OR_CHANNEL_FAILURE": 5,
    "RESERVATION_OR_ACCOUNT_ACTION": 4,
    "MONEY_CLAIM": 3.5,
    "BAGGAGE_MISHANDLING": 2.5,
    "OTHER": 3.5,
}

# Applied top-down; the FIRST match wins, which makes the label a deterministic
# function of the message and keeps single-label evaluation defensible.
PRECEDENCE: list[str] = [
    "OTHER_SAFETY",
    "LIVE_TRIP_DISRUPTION",
    "BAGGAGE_MISHANDLING",
    "RESERVATION_OR_ACCOUNT_ACTION",
    "MONEY_CLAIM",
    "SERVICE_INCIDENT_REPORT",
    "SELF_SERVICE_OR_CHANNEL_FAILURE",
    "POLICY_AND_ELIGIBILITY_QUESTION",
    "EMPLOYEE_KUDOS",
    "PRAISE_AND_TRAVEL_CHATTER",
    "DIFFUSE_BRAND_VENT",
    "OTHER",
]
