"""Single chokepoint for every LLM call, with a committed content-addressed cache.

The grader has 15 minutes and probably no API key. Every generation and every
judgement is therefore replayed from `artifacts/cache/*.jsonl`, which is committed.

Two rules make this honest rather than a fudge:
  * OFFLINE IS THE DEFAULT, and a cache MISS RAISES. It never silently skips,
    stubs, or falls back -- a quietly-skipped example would turn the headline
    metric into a lie about a smaller set.
  * The key is a hash of everything that could change the output (provider,
    model, temperature, top_p, seed, system, messages), so an edited prompt
    cannot silently reuse an old completion; it misses, and the miss is loud.

Replayed numbers are NOT a re-run. The report says so explicitly.
"""
from __future__ import annotations
import hashlib
import json
import os
import pathlib
import threading

CACHE_DIR = pathlib.Path("artifacts/cache")
_LOCK = threading.Lock()


class CacheMiss(RuntimeError):
    pass


def cache_key(provider: str, model: str, system: str, messages: list[dict],
              temperature: float, top_p: float, seed: int | None) -> str:
    payload = json.dumps({
        "provider": provider, "model": model, "system": system,
        "messages": messages, "temperature": temperature, "top_p": top_p, "seed": seed,
    }, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class LLMCache:
    def __init__(self, name: str):
        self.path = CACHE_DIR / f"{name}.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._mem: dict[str, dict] = {}
        if self.path.exists():
            with self.path.open(encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        r = json.loads(line)
                        self._mem[r["key"]] = r

    def get(self, key: str):
        return self._mem.get(key)

    def put(self, key: str, request: dict, text: str, meta: dict) -> None:
        rec = {"key": key, "request": request, "response_text": text, **meta}
        with _LOCK:
            self._mem[key] = rec
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def __len__(self):
        return len(self._mem)


def call(cache: LLMCache, system: str, messages: list[dict], *,
         model: str = "claude-opus-5", provider: str = "anthropic",
         temperature: float = 0.0, top_p: float = 1.0, seed: int | None = 0,
         live: bool | None = None) -> str:
    """Return completion text. Offline by default; `live=True` needs an API key."""
    key = cache_key(provider, model, system, messages, temperature, top_p, seed)
    hit = cache.get(key)
    if hit is not None:
        return hit["response_text"]

    if live is None:
        live = os.environ.get("HIVER_LIVE") == "1"
    if not live:
        preview = (messages[-1]["content"] if messages else "")[:200]
        raise CacheMiss(
            f"cache MISS in {cache.path.name} for key={key[:16]}…\n"
            f"  prompt tail: {preview!r}\n"
            f"  Offline replay is the default and a miss is fatal by design: silently\n"
            f"  skipping would change the denominator of every metric. Re-run with\n"
            f"  HIVER_LIVE=1 and ANTHROPIC_API_KEY set to regenerate this entry."
        )

    from anthropic import Anthropic
    client = Anthropic()
    resp = client.messages.create(
        model=model, max_tokens=1024, temperature=temperature, top_p=top_p,
        system=system, messages=messages,
    )
    text = "".join(b.text for b in resp.content if b.type == "text")
    cache.put(key, {"system": system, "messages": messages, "model": model,
                    "temperature": temperature, "top_p": top_p, "seed": seed},
              text, {"model_id": resp.model,
                     "usage": {"in": resp.usage.input_tokens, "out": resp.usage.output_tokens}})
    return text
