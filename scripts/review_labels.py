"""Adjudicate the golden set. Run:  python scripts/review_labels.py

Two annotators labelled every held-out message independently against the frozen
codebook. Where they AGREE the label is provisionally accepted; where they DISAGREE
a human must decide, because those are exactly the boundaries the codebook does not
settle. This is also what makes the reported inter-annotator agreement meaningful
rather than decorative.

Keys:  1-9,0 pick an intent   a/b accept annotator A or B   s skip   u undo   q save+quit
"""
from __future__ import annotations
import json, os, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))
from hiver.taxonomy.intents import INTENTS

GOLD = pathlib.Path('eval/golden_raw.jsonl')
OUT  = pathlib.Path('eval/golden_adjudicated.jsonl')

def load(p):
    return [json.loads(l) for l in p.open(encoding='utf-8') if l.strip()] if p.exists() else []

def main():
    items = load(GOLD)
    if not items:
        print(f"no {GOLD}; run scripts/build_golden.py first"); return
    done = {r['tweet_id']: r for r in load(OUT)}
    todo = [r for r in items if r['tweet_id'] not in done]
    dis = [r for r in todo if r['A'] != r['B']]
    agr = [r for r in todo if r['A'] == r['B']]
    print(f"{len(items)} golden items | {len(done)} already adjudicated")
    print(f"annotators disagree on {len(dis)} of {len(todo)} remaining "
          f"({100*len(dis)/max(len(todo),1):.0f}%) — those come first\n")

    order = dis + agr
    log = []
    for n, r in enumerate(order, 1):
        os.system('cls' if os.name == 'nt' else 'clear')
        tag = 'DISAGREEMENT' if r['A'] != r['B'] else 'both agree'
        print(f"[{n}/{len(order)}]  {tag}   set={r.get('set','?')}\n")
        print(f"  {r['text']}\n")
        print(f"  (the human agent actually replied: {r.get('human_reply','')[:160]})\n")
        for i, it in enumerate(INTENTS):
            k = str((i + 1) % 10)
            mark = ''
            if it == r['A']: mark += '  <- A'
            if it == r['B']: mark += '  <- B'
            print(f"   {k}) {it}{mark}")
        print(f"\n  A={r['A']} (conf {r.get('confA','?')})   B={r['B']} (conf {r.get('confB','?')})")
        if r.get('ambigA'): print(f"  A noted: {r['ambigA'][:110]}")
        c = input("\n  > ").strip().lower()
        if c == 'q': break
        if c == 's': continue
        if c == 'u' and log:
            done.pop(log.pop()['tweet_id'], None); continue
        lab = r['A'] if c == 'a' else r['B'] if c == 'b' else None
        if lab is None and c.isdigit():
            idx = (int(c) - 1) % 10
            if idx < len(INTENTS): lab = INTENTS[idx]
        if lab is None: continue
        rec = {**r, 'gold': lab, 'adjudicated': r['A'] != r['B']}
        done[r['tweet_id']] = rec; log.append(rec)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', encoding='utf-8') as f:
        for r in done.values(): f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f"\nsaved {len(done)} adjudicated labels -> {OUT}")

if __name__ == '__main__':
    main()
