"""Escalation results: risk-coverage, overrides, and the honest baselines.

TARGET DEFINITION (stated because it is the least obvious choice in the project):

  NEEDS_HUMAN = the drafted reply should not be auto-sent, because it is either
    (a) unsafe to send publicly as the brand, or
    (b) fails to move the customer forward at all (resolution <= 2).

Judging only (a) yielded 1 positive in 150 -- too sparse to fit or evaluate anything.
That sparsity is itself a finding: on this brand the realistic failure is not a
dangerous reply, it is a useless one. Escalating a useless draft is what a support
desk actually does, so (b) belongs in the target. Base rate: 12.0%.

This label is derived from an LLM judge, so it is a model-derived standard, not
ground truth. It is reported as such.
"""
import sys, json
sys.path.insert(0,'src')
import numpy as np, pandas as pd
from hiver.escalate.policy import (Signals, RiskModel, overrides, anger_score,
                                   risk_coverage_curve, aurc, coverage_at_risk, decide)
from hiver.classify.model import EmbeddingIntentClassifier
from hiver.taxonomy.intents import RISK_TIER
from hiver.evaluate.stats import wilson
from hiver.paths import path, teacher_labels

SEED=20260909
esc=json.load(open(path('escalation'),encoding='utf-8'))
d=json.load(open(path('generation'),encoding='utf-8'))
R={int(s['tweet_id']):s for s in d['resolution'] if s['system']=='grounded_llm'}
for e in esc:
    r=R[int(e['tweet_id'])]
    e['needs_human']=bool(e['unsafe']) or int(r['score'])<=2

emb=np.load(path('embeddings')).astype(np.float32)
meta=pd.read_parquet(path('meta'))
pos={int(t):i for i,t in enumerate(meta.tweet_id.values)}
from hiver.taxonomy.intents import INTENTS
teach={k:v for k,v in teacher_labels().items() if v in INTENTS}
tr=[t for t in teach if t in pos]
clf=EmbeddingIntentClassifier(seed=SEED).fit(emb[[pos[t] for t in tr]],np.array([teach[t] for t in tr]))

TIER={'low':0.0,'medium':0.5,'high':1.0}
setB=np.array([e['set']=='B' for e in esc])
ytmp=np.array([e['needs_human'] for e in esc])
# Per-intent automatability, estimated ONLY on the dev half (Set A) and applied to the
# test half. Laplace-smoothed, because several intents have <10 dev examples.
import collections
num=collections.Counter(); den=collections.Counter()
for e,yy,isB in zip(esc,ytmp,setB):
    if isB: continue
    den[e['pred_intent']]+=1; num[e['pred_intent']]+=int(yy)
prior=ytmp[~setB].mean()
DIFF={k:(num[k]+2*prior)/(den[k]+2) for k in den}
print('per-intent difficulty estimated on Set A (dev half), applied to Set B:')
for k in sorted(DIFF,key=lambda k:-DIFF[k]): print(f'   {k:34}{DIFF[k]:.3f}  (n={den[k]})')
print()

sigs=[];y=[];forced=[];reasons=[]
for e in esc:
    i=pos[int(e['tweet_id'])]
    p=clf.predict_proba(emb[i:i+1])[0]; s=np.sort(p)
    ov=overrides(e['text'])
    sigs.append(Signals(intent_conf=float(s[-1]),intent_margin=float(s[-1]-s[-2]),
        top_sim=e['top_sim'],mean_sim=e['mean_sim'],neighbour_disagree=0.0,
        risk_tier=TIER.get(RISK_TIER.get(e['pred_intent'],'medium'),0.5),
        anger=anger_score(e['text']),msg_len=min(len(e['text'].split())/50,1.0),
        n_overrides=float(len(ov)),
        intent_difficulty=DIFF.get(e['pred_intent'],prior),
        draft_len=min(len((e['draft'] or '').split())/50,1.0)))
    y.append(e['needs_human']); forced.append(bool(ov)); reasons.append(ov)
y=np.array(y); forced=np.array(forced)
print(f"n={len(y)}  NEEDS_HUMAN base rate {y.mean():.1%}  (this is the error you ship at 100% automation)")
print(f"hard overrides fire on {forced.sum()} items; of those {int(y[forced].sum())} are truly NEEDS_HUMAN")

# fit on Set A, evaluate on Set B (population) -- thresholds must not be tuned on the test half
rm=RiskModel(seed=SEED).fit([s for s,m in zip(sigs,~setB) if m], y[~setB])
risk=rm.risk(sigs)
print("\nfitted risk weights (linear, so they are inspectable):")
for k,v in sorted(rm.weights().items(),key=lambda kv:-abs(kv[1])): print(f"   {k:20}{v:+.3f}")

print("\n"+"="*92); print("RISK-COVERAGE on Set B (population sample; model fit on Set A)"); print("="*92)
cov,sel,taus=risk_coverage_curve(risk[setB],y[setB],forced[setB])
print(f"AURC {aurc(cov,sel):.4f}  (lower is better)")
base=y[setB].mean()
for r_ in [0.02,0.05,0.10,0.15]:
    c=coverage_at_risk(cov,sel,r_)
    if r_>=base:
        print(f"  coverage @ <={int(r_*100):2d}% bad-send rate : {c:5.1%}   "
              f"-- VACUOUS: the target exceeds the {base:.1%} base rate, so doing nothing already meets it")
    else:
        print(f"  coverage @ <={int(r_*100):2d}% bad-send rate : {c:5.1%}   "
              f"-> auto-send {c*100:.0f} of every 100 messages, escalate {100-c*100:.0f}")
print(f"  full automation           : 100.0%   -> ships the {base:.1%} base error rate")

# Does this beat random AT ALL at n=93? Bootstrap the AURC difference.
def _aurc(score,yy,rng_idx):
    c,s_,_=risk_coverage_curve(score[rng_idx],yy[rng_idx],np.zeros(len(rng_idx),bool))
    return aurc(c,s_)
yB=y[setB]; sB=risk[setB]
dB=np.array([s.intent_difficulty for s,m in zip(sigs,setB) if m])
rng=np.random.default_rng(SEED); rnd=rng.random(setB.sum())
diffs=[]
for _ in range(2000):
    idx=rng.integers(0,len(yB),len(yB))
    if yB[idx].sum()==0: continue
    diffs.append(_aurc(dB,yB,idx)-_aurc(rnd,yB,idx))
diffs=np.array(diffs); lo,hi=np.percentile(diffs,[2.5,97.5])
print("")
print(f"AURC(intent-difficulty) - AURC(random) = {np.mean(diffs):+.4f} [{lo:+.4f},{hi:+.4f}]"
      f"   (negative is better; interval spanning 0 means n={len(yB)} cannot resolve it)")

# baselines for the escalation layer itself
print("\n--- escalation baselines (an escalation layer must beat these to be worth anything) ---")
def rc(score,name):
    c,s,_=risk_coverage_curve(score,y[setB],np.zeros(setB.sum(),bool))
    print(f"  {name:26} AURC {aurc(c,s):.4f}  cov@5% {coverage_at_risk(c,s,0.05):5.1%}")
rng=np.random.default_rng(SEED)
rc(rng.random(setB.sum()),'random')
rc(1-np.array([s.intent_conf for s,m in zip(sigs,setB) if m]),'1 - intent confidence')
rc(1-np.array([s.top_sim for s,m in zip(sigs,setB) if m]),'1 - retrieval similarity')
rc(np.array([s.intent_difficulty for s,m in zip(sigs,setB) if m]),'intent difficulty alone')
rc(risk[setB],'full risk model')

print("\n--- worked decisions (the brief requires a stated reason) ---")
order=np.argsort(-risk)
tau=0.5
for j in list(order[:3])+list(order[-2:]):
    e=esc[j]; a,why=decide(float(risk[j]),tau,reasons[j])
    print(f"  [{a:9}] risk={risk[j]:.2f} needs_human={e['needs_human']}  {why}")
    print(f"      customer: {e['text'][:110]}")
import os; os.makedirs('artifacts',exist_ok=True)
json.dump({'coverage':cov.tolist(),'risk':sel.tolist()},open('artifacts/risk_coverage.json','w'))
