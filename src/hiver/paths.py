"""Resolve inputs from the committed `eval/` bundle first, then the working tree.

A grader gets a clean clone, which has `eval/` but none of the intermediate build
outputs. Every eval script goes through here so the committed path is the one that is
actually exercised -- the reproduction claim was broken until this existed, because the
scripts silently read from local build artifacts that are not in the repo.
"""
from __future__ import annotations
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]

# logical name -> (committed bundle, working-tree build output)
_MAP = {
    "embeddings":  ("eval/embeddings_fp16.npy",     "artifacts/emb_all_fp16.npy"),
    "meta":        ("eval/meta.parquet",            "artifacts/meta_all.parquet"),
    "generation":  ("eval/generation_bundle.json",  "data/interim/gen_outputs.json"),
    "escalation":  ("eval/escalation_items.json",   "data/interim/escalation_items.json"),
    "golden":      ("eval/golden_raw.jsonl",        "eval/golden_raw.jsonl"),
}


def path(name: str) -> pathlib.Path:
    committed, working = _MAP[name]
    for p in (ROOT / committed, ROOT / working):
        if p.exists():
            return p
    raise FileNotFoundError(
        f"{name}: found neither {committed} nor {working}. The committed bundle is the "
        f"reproduction path; rebuild it with scripts/export_artifacts.py.")


def teacher_labels() -> dict[int, str]:
    """Teacher intent labels, from the committed jsonl or the raw workflow dump."""
    p = ROOT / "eval/teacher_labels.jsonl"
    if p.exists():
        rows = [json.loads(l) for l in p.open(encoding="utf-8") if l.strip()]
    else:
        rows = json.load((ROOT / "data/interim/labels_raw.json").open(encoding="utf-8"))["teach"]
    return {int(r["tweet_id"]): r["intent"] for r in rows}
