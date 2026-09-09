"""Assemble the golden evaluation set from the two blind annotation passes.

TWO SETS, never averaged -- this is the point:

  Set B (population, n=100): a UNIFORM RANDOM draw from held-out test threads.
    Every prior-dependent number is computed here and only here: accuracy,
    automation coverage, escalation rate, deflection rate. These are estimates of
    real traffic.

  Set A (stratified, n=150): oversamples rare and high-risk intents so that
    per-class diagnosis and failure analysis have anything to look at. macro-F1
    and per-class F1 come from here. Aggregates computed on Set A would be
    meaningless, because its class prior is manufactured.

Reporting a single accuracy over a stratified set is the most common way this
deliverable goes wrong: the number describes a distribution that does not exist.
"""
from __future__ import annotations
import json, sys, pathlib, collections
import numpy as np, pandas as pd
sys.path.insert(0, 'src')
from hiver.taxonomy.intents import INTENTS, RISK_TIER

RAW = pathlib.Path('data/interim/labels_raw.json')

def main():
    d = json.load(RAW.open(encoding='utf-8'))
    A = {int(r['tweet_id']): r for r in d['goldA']}
    B = {int(r['tweet_id']): r for r in d['goldB']}
    pools = {}
    for f, s in [('pool_setB.jsonl', 'B'), ('pool_setA_candidates.jsonl', 'A')]:
        for line in open(f'data/interim/{f}', encoding='utf-8'):
            r = json.loads(line); pools[int(r['tweet_id'])] = {**r, 'set': s}

    both = [t for t in pools if t in A and t in B]
    print(f"double-annotated: {len(both)} messages")

    # ---- Set B: uniform random population sample, take all of it
    setB = [t for t in both if pools[t]['set'] == 'B']
    # ---- Set A: stratify on the agreed label, oversampling rare + high-risk intents
    candA = [t for t in both if pools[t]['set'] == 'A']
    by_intent = collections.defaultdict(list)
    for t in candA:
        by_intent[A[t]['intent']].append(t)
    rng = np.random.default_rng(20260909)
    target, setA = 150, []
    per = max(1, target // max(len(INTENTS), 1))
    for it in INTENTS:
        pool = by_intent.get(it, [])
        rng.shuffle(pool)
        want = per + (4 if RISK_TIER.get(it) == 'high' else 0)   # boost risky classes
        setA += pool[:want]
    setA = setA[:target]

    rows = []
    for t in setB + setA:
        p, a, b = pools[t], A[t], B[t]
        rows.append({
            'tweet_id': t, 'conv': p['conv'], 'set': p['set'], 'split': p['split'],
            'text': p['text'], 'human_reply': p['human_reply'],
            'human_deflected': p['deflected'], 'created': p['created'],
            'A': a['intent'], 'B': b['intent'],
            'confA': a.get('confidence'), 'confB': b.get('confidence'),
            'ambigA': a.get('ambiguity', ''), 'ambigB': b.get('ambiguity', ''),
        })
    out = pathlib.Path('eval/golden_raw.jsonl')
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', encoding='utf-8') as f:
        for r in rows: f.write(json.dumps(r, ensure_ascii=False) + '\n')

    df = pd.DataFrame(rows)
    agree = (df.A == df.B).mean()
    print(f"\nSet B (population) n={(df.set=='B').sum()}   Set A (stratified) n={(df.set=='A').sum()}")
    print(f"raw annotator agreement: {agree:.1%}  ({int((df.A!=df.B).sum())} need human adjudication)")

    # Cohen's kappa -- raw agreement alone is inflated by the dominant class
    labs = sorted(set(df.A) | set(df.B))
    m = pd.crosstab(df.A, df.B).reindex(index=labs, columns=labs, fill_value=0).values
    n = m.sum(); po = np.trace(m) / n
    pe = ((m.sum(0) / n) * (m.sum(1) / n)).sum()
    print(f"Cohen's kappa: {(po-pe)/(1-pe):.3f}   (<0.60 would mean the taxonomy is not reliably applicable)")

    print("\nintent distribution, Set B = the real population prior:")
    vc = df[df.set=='B'].A.value_counts()
    for it in INTENTS:
        print(f"  {it:34} {vc.get(it,0):3d}  ({100*vc.get(it,0)/max((df.set=='B').sum(),1):4.1f}%)")
    print("\nworst disagreements (these are the taxonomy's real seams):")
    dis = df[df.A != df.B]
    for pair, c in collections.Counter(tuple(sorted([r.A, r.B])) for r in dis.itertuples()).most_common(6):
        print(f"  {c:3d}x  {pair[0]}  <->  {pair[1]}")
    print(f"\nwrote {out}  -> now run: python scripts/review_labels.py")

if __name__ == '__main__':
    main()
