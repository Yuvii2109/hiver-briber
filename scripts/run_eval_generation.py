"""Generation results. Two axes, never averaged, plus a hard non-LLM deflection rate."""
import sys, json, collections
sys.path.insert(0,'src')
import numpy as np, pandas as pd
from hiver.generate.responder import is_deflection
from hiver.evaluate.stats import bootstrap_metric, paired_bootstrap, wilson

d=json.load(open('data/interim/gen_outputs.json',encoding='utf-8'))
items={int(i['tweet_id']):i for i in d['items']}
SYS=['grounded_llm','nearest_reply','template_parrot','human']
KEY={'grounded_llm':'draft_llm','nearest_reply':'draft_nearest',
     'template_parrot':'draft_parrot','human':'draft_human'}

F=collections.defaultdict(dict); R=collections.defaultdict(dict)
for s in d['faithfulness']:
    if s.get('system') in SYS: F[s['system']][int(s['tweet_id'])]=s
for s in d['resolution']:
    if s.get('system') in SYS: R[s['system']][int(s['tweet_id'])]=s
ids=[t for t in items if all(t in F[s] and t in R[s] for s in SYS)]
print(f"complete judgements for {len(ids)}/{len(items)} items x {len(SYS)} systems\n")

def mean(v): return float(np.mean(v))
rows=[]
for s in SYS:
    f=np.array([F[s][t]['score'] for t in ids],float)
    r=np.array([R[s][t]['score'] for t in ids],float)
    uns=np.array([bool(R[s][t].get('send_unsafe')) for t in ids])
    ser=np.array([R[s][t].get('severity')=='serious' for t in ids])
    dfl=np.array([is_deflection(items[t].get(KEY[s]) or '') for t in ids])
    lo,hi=wilson(int(uns.sum()),len(ids))
    rows.append(dict(system=s,
        faithfulness=round(mean(f),2), resolution=round(mean(r),2),
        deflection_rate=f"{100*mean(dfl):.1f}%",
        unsafe_rate=f"{100*mean(uns):.1f}%", unsafe_ci=f"[{100*lo:.0f},{100*hi:.0f}]",
        serious=int(ser.sum())))
df=pd.DataFrame(rows)
print("="*104); print("REPLY GENERATION — the two axes are reported separately, never averaged"); print("="*104)
print(df.to_string(index=False))
print("""
Read the two axes together. FAITHFULNESS alone cannot separate a good agent from a
useless one: a reply that asserts nothing is faithful by construction. That is exactly
why the template parrot is on this table.""")

# paired: is the grounded system better than each alternative, on the same items?
print("\n--- paired bootstrap on mean RESOLUTION (same items, 2000 resamples) ---")
base=np.array([R['grounded_llm'][t]['score'] for t in ids],float)
for s in SYS[1:]:
    o=np.array([R[s][t]['score'] for t in ids],float)
    rng=np.random.default_rng(20260909); dif=[]
    for _ in range(2000):
        idx=rng.integers(0,len(ids),len(ids)); dif.append(base[idx].mean()-o[idx].mean())
    dif=np.array(dif); lo,hi=np.percentile(dif,[2.5,97.5])
    p=2*min((dif<=0).mean(),(dif>=0).mean())
    print(f"  grounded_llm - {s:16}: {base.mean()-o.mean():+.2f} [{lo:+.2f},{hi:+.2f}] p={p:.4f}")

print("\n--- same, for FAITHFULNESS ---")
basef=np.array([F['grounded_llm'][t]['score'] for t in ids],float)
for s in SYS[1:]:
    o=np.array([F[s][t]['score'] for t in ids],float)
    rng=np.random.default_rng(20260909); dif=[]
    for _ in range(2000):
        idx=rng.integers(0,len(ids),len(ids)); dif.append(basef[idx].mean()-o[idx].mean())
    dif=np.array(dif); lo,hi=np.percentile(dif,[2.5,97.5])
    p=2*min((dif<=0).mean(),(dif>=0).mean())
    print(f"  grounded_llm - {s:16}: {basef.mean()-o.mean():+.2f} [{lo:+.2f},{hi:+.2f}] p={p:.4f}")

json.dump({'ids':ids},open('artifacts/judged_ids.json','w'))
df.to_csv('artifacts/generation_results.csv',index=False)

# escalation inputs: the send-safety label per item for the grounded system
esc=[{'tweet_id':t,'unsafe':bool(R['grounded_llm'][t].get('send_unsafe')),
      'severity':R['grounded_llm'][t].get('severity'),
      'top_sim':items[t]['top_sim'],'mean_sim':items[t]['mean_sim'],
      'pred_intent':items[t]['pred_intent'],'gold_intent':items[t]['gold_intent'],
      'text':items[t]['text'],'draft':items[t]['draft_llm'],'set':items[t]['set']} for t in ids]
json.dump(esc,open('data/interim/escalation_items.json','w',encoding='utf-8'),ensure_ascii=False)
print(f"\nwrote escalation inputs ({sum(e['unsafe'] for e in esc)}/{len(esc)} drafts judged unsafe to send)")
