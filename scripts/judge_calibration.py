"""Score replies yourself, so judge-vs-human agreement is MEASURED, not asserted.

The brief requires "evidence of how well your judge agrees with a human". That
evidence cannot be produced by the model. This tool shows you drafts with the system
identity hidden and in shuffled order, takes your 1-5 scores, and writes them next to
the judge's for the agreement analysis.

~50 items is enough to be worth reporting and takes about half an hour. Note up front
that Pearson r at n=50 carries a 95% CI roughly [0.52, 0.82] around r=0.70 -- wide.
The analysis therefore reports Krippendorff's ordinal alpha and exact-agreement rate
alongside it, because r is blind to a judge that is uniformly one point generous.

Keys: 1-5 score   s skip   u undo   q save+quit
"""
from __future__ import annotations
import json, os, pathlib, random, sys

GEN = pathlib.Path('data/interim/gen_outputs.json')
OUT = pathlib.Path('eval/human_judge_scores.jsonl')
AXIS = sys.argv[1] if len(sys.argv) > 1 else 'resolution'
N = int(sys.argv[2]) if len(sys.argv) > 2 else 50

RUBRIC = {
 'resolution': ["5  answers it / states the concrete next step - customer can act now",
                "4  substantially helpful, minor gap",
                "3  partially useful; acknowledges + some direction (asking for needed info = 3)",
                "2  acknowledges but defers; customer knows nothing new",
                "1  pure deflection ('DM us', 'we'll look into it') or off-topic"],
 'faithfulness': ["5  every claim supported by the evidence; invents nothing",
                  "4  minor unsupported detail, no risk",
                  "3  one unsupported but plausible claim",
                  "2  asserts a policy/fee/timeline the evidence does not establish",
                  "1  contradicts evidence, or claims an action the agent cannot perform"],
}

def main():
    if not GEN.exists():
        print(f"missing {GEN}; run the generate+judge step first"); return
    d = json.load(GEN.open(encoding='utf-8'))
    items = {int(i['tweet_id']): i for i in d['items']}
    pairs = []
    for tid, it in items.items():
        for sysname, key in [('grounded_llm', 'draft_llm'), ('nearest_reply', 'draft_nearest'),
                             ('template_parrot', 'draft_parrot'), ('human', 'draft_human')]:
            if it.get(key):
                pairs.append({'tweet_id': tid, 'system': sysname, 'draft': it[key],
                              'text': it['text'], 'cases': it.get('cases', [])})
    random.Random(20260909).shuffle(pairs)          # identity hidden AND order shuffled
    done = {}
    if OUT.exists():
        for l in OUT.open(encoding='utf-8'):
            r = json.loads(l); done[(r['tweet_id'], r['system'], r['axis'])] = r
    todo = [p for p in pairs if (p['tweet_id'], p['system'], AXIS) not in done][:N]
    print(f"axis={AXIS}  scoring {len(todo)} drafts ({len(done)} already scored)\n")
    input("  enter to start > ")
    log = []
    for n, p in enumerate(todo, 1):
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"[{n}/{len(todo)}]  axis: {AXIS.upper()}   (system identity hidden)\n")
        print(f"CUSTOMER:\n  {p['text']}\n")
        if AXIS == 'faithfulness':
            print("EVIDENCE THE DRAFTER SAW:")
            for c in p['cases'][:3]:
                print(f"  - customer: {c['q'][:130]}")
                print(f"    replied : {c['reply'][:130]}")
            print()
        print(f"DRAFTED REPLY:\n  {p['draft']}\n")
        print("  " + "\n  ".join(RUBRIC[AXIS]))
        c = input("\n  score > ").strip().lower()
        if c == 'q': break
        if c == 's': continue
        if c == 'u' and log:
            done.pop(log.pop(), None); continue
        if c in '12345':
            k = (p['tweet_id'], p['system'], AXIS)
            done[k] = {'tweet_id': p['tweet_id'], 'system': p['system'], 'axis': AXIS,
                       'human_score': int(c)}
            log.append(k)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open('w', encoding='utf-8') as f:
        for r in done.values(): f.write(json.dumps(r, ensure_ascii=False) + '\n')
    print(f"\nsaved {len(done)} human scores -> {OUT}")

if __name__ == '__main__':
    main()
