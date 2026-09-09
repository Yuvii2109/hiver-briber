"""Intent-classification results: baselines, distilled model, CIs, paired tests."""
import sys, json, pathlib, collections
sys.path.insert(0,'src')
import numpy as np, pandas as pd
from sklearn.metrics import f1_score, accuracy_score, confusion_matrix, classification_report
from hiver.taxonomy.intents import INTENTS
from hiver.classify.baselines import KeywordBaseline, MajorityBaseline, tfidf_logreg
from hiver.classify.model import EmbeddingIntentClassifier, reliability
from hiver.evaluate.stats import bootstrap_metric, paired_bootstrap, mcnemar, wilson

SEED=20260909
emb=np.load('artifacts/emb_all_fp16.npy').astype(np.float32)
meta=pd.read_parquet('artifacts/meta_all.parquet')
pos={int(t):i for i,t in enumerate(meta.tweet_id.values)}

lab=json.load(open('data/interim/labels_raw.json',encoding='utf-8'))
teach={int(r['tweet_id']):r['intent'] for r in lab['teach'] if r['intent'] in INTENTS}

# gold: adjudicated file if the human has run the review tool, else A/B agreement
adj=pathlib.Path('eval/golden_adjudicated.jsonl')
gr=pd.read_json('eval/golden_raw.jsonl',lines=True)
if adj.exists():
    a={r['tweet_id']:r['gold'] for r in map(json.loads,adj.open(encoding='utf-8'))}
    gr['gold']=gr.tweet_id.map(a)
    print(f"using {len(a)} human-adjudicated labels")
else:
    gr['gold']=np.where(gr.A==gr.B, gr.A, None)
    print("NOTE: eval/golden_adjudicated.jsonl absent -> using A/B agreement as provisional gold;")
    print(f"      {int((gr.A!=gr.B).sum())} disagreements are DROPPED until a human adjudicates them.")
gr=gr[gr.gold.notna()].copy()

tr_ids=[t for t in teach if t in pos]
Xtr=emb[[pos[t] for t in tr_ids]]; ytr=np.array([teach[t] for t in tr_ids])
txt_tr=meta.q.values[[pos[t] for t in tr_ids]]
print(f"\ntrain (teacher-labelled): {len(tr_ids)}   golden: {len(gr)}  (SetA {int((gr.set=='A').sum())} / SetB {int((gr.set=='B').sum())})")

def ev(name,setname,ytrue,ypred,groups):
    mf,lo,hi=bootstrap_metric(ytrue,ypred,groups=groups,seed=SEED)
    acc=accuracy_score(ytrue,ypred)
    return dict(system=name,set=setname,n=len(ytrue),macro_f1=round(mf,3),
                ci=f"[{lo:.3f},{hi:.3f}]",accuracy=round(acc,3))

models={}
models['majority']=MajorityBaseline().fit(txt_tr,ytr)
models['keyword']=KeywordBaseline().fit(txt_tr,ytr)
tf=tfidf_logreg(SEED).fit(txt_tr,ytr); models['tfidf_lr']=tf
clf=EmbeddingIntentClassifier(seed=SEED).fit(Xtr,ytr); models['emb_lr']=clf

rows=[];preds={}
for setname in ['A','B']:
    g=gr[gr.set==setname]
    if not len(g): continue
    idx=[pos[t] for t in g.tweet_id]; X=emb[idx]; T=meta.q.values[idx]
    y=g.gold.values; grp=g.conv.values
    p={}
    p['majority']=models['majority'].predict(T)
    p['keyword'] =models['keyword'].predict(T)
    p['tfidf_lr']=models['tfidf_lr'].predict(T)
    p['emb_lr']  =models['emb_lr'].predict(X)
    # CIRCULAR BY CONSTRUCTION, printed only so the circularity is visible rather
    # than hidden: gold is defined as the A/B agreement, so annotator A scores 1.00
    # on every item that survived into the set. It is NOT a result and must never be
    # quoted as "the LLM ceiling". Breaking this needs human adjudication.
    p['llm_annotator(CIRCULAR)']=g.A.values
    for k,v in p.items(): rows.append(ev(k,setname,y,v,grp))
    preds[setname]=(y,p,grp,g)

df=pd.DataFrame(rows)
print("\n"+"="*88); print("INTENT CLASSIFICATION"); print("="*88)
for s,title in [('A','Set A — STRATIFIED (macro-F1, per-class diagnosis; aggregates here are meaningless)'),
                ('B','Set B — POPULATION (accuracy/coverage estimate real traffic)')]:
    d=df[df.set==s]
    if not len(d): continue
    print(f"\n{title}")
    print(d[['system','n','macro_f1','ci','accuracy']].to_string(index=False))

y,p,grp,g=preds['A']
print("\n--- paired comparisons on Set A (the marginal CIs above overlap; these do not) ---")
for base in ['keyword','tfidf_lr']:
    d=paired_bootstrap(y,p['emb_lr'],p[base],groups=grp,seed=SEED)
    mc=mcnemar(y,p['emb_lr'],p[base])
    print(f"  emb_lr - {base:9}: delta {d['delta']:+.3f} [{d['lo']:+.3f},{d['hi']:+.3f}] "
          f"p={d['p_two_sided']:.4f} | McNemar n10={mc['n10']} n01={mc['n01']} p={mc['p']:.4f}")

print("\n--- per-class on Set A (n and Wilson CI shown so a 13-example estimate cannot be misread) ---")
rep=classification_report(y,p['emb_lr'],output_dict=True,zero_division=0)
print(f"{'intent':34}{'n':>4}{'F1':>7}   recall 95% CI")
for it in INTENTS:
    if it not in rep: continue
    n=int(rep[it]['support']); r=rep[it]['recall']
    lo,hi=wilson(int(round(r*n)),n) if n else (0,0)
    print(f"{it:34}{n:4d}{rep[it]['f1-score']:7.2f}   [{lo:.2f},{hi:.2f}]")

pr=models['emb_lr'].predict_proba(emb[[pos[t] for t in g.tweet_id]])
conf=pr.max(1); corr=(p['emb_lr']==y)
bins,ece=reliability(conf,corr)
print(f"\ncalibration ECE = {ece:.3f}  (the escalation threshold is a threshold on THIS number)")
for b in bins: print(f"   {b['bin']:12} n={b['n']:3d} conf={b['confidence']:.2f} acc={b['accuracy']:.2f}")

cm=confusion_matrix(y,p['emb_lr'],labels=INTENTS)
print("\nconfusion matrix, RAW COUNTS (Set A):")
print(pd.DataFrame(cm,index=[i[:16] for i in INTENTS],columns=[i[:9] for i in INTENTS]).to_string())
df.to_csv('artifacts/intent_results.csv',index=False)
