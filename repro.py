#!/usr/bin/env python
"""Reproduce every headline number, offline, with no API key.

    python repro.py            # everything, from committed artifacts
    python repro.py --demo     # end-to-end agent on a few messages

Nothing here calls a network. Model outputs are REPLAYED from eval/cached_*.jsonl,
which is a weaker claim than re-running and is stated as such in the report.
"""
import argparse, io, os, subprocess, sys, time, pathlib
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
os.environ.setdefault("PYTHONUTF8", "1")
ROOT = pathlib.Path(__file__).parent
STEPS = [
    ("Intent classification", "scripts/run_eval_intent.py"),
    ("Reply generation",      "scripts/run_eval_generation.py"),
    ("Escalation",            "scripts/run_eval_escalation.py"),
]

def run(title, script):
    print("\n" + "#" * 100); print(f"# {title}"); print("#" * 100)
    t = time.time()
    r = subprocess.run([sys.executable, str(ROOT / script)], cwd=ROOT,
                       env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = "\n".join(l for l in (r.stdout or "").splitlines()
                    if "Warning" not in l and "warn" not in l.lower())
    print(out)
    if r.returncode:
        print((r.stderr or "")[-2000:]); sys.exit(r.returncode)
    return time.time() - t

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        run("Demo", "scripts/demo.py"); return
    print("Hiver take-home — @AmericanAir support agent")
    print("offline replay of committed artifacts; no network, no API key")
    total = 0.0
    for t, s in STEPS:
        total += run(t, s)
    print("\n" + "=" * 100)
    print(f"done in {total:.1f}s")
    print("""
Read these numbers with three caveats, all expanded in REPORT.md:
  * Golden labels were produced by an LLM applying the frozen codebook and are
    human-adjudicated only where the two blind annotators disagreed. They are a
    model-derived standard, not ground truth.
  * Generation scores are REPLAYED cached outputs, not a fresh run.
  * The escalation layer cannot be shown to beat random at this sample size:
    AURC delta vs random = -0.014, 95% CI [-0.058, +0.020].""")

if __name__ == "__main__":
    main()
