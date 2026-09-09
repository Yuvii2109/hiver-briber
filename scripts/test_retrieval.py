import sys, numpy as np, pandas as pd
sys.path.insert(0,'src')
from hiver.retrieve.index import CaseIndex
emb=np.load('artifacts/emb_all_fp16.npy'); meta=pd.read_parquet('artifacts/meta_all.parquet')
tr=meta.split=='train'
idx=CaseIndex(emb[tr.values], meta[tr].copy(), exclude_deflections=True)
print(f"corpus {len(meta[tr]):,} train examples -> {len(idx.pool):,} non-deflection cases usable as evidence")
print(f"  ({100*(1-len(idx.pool)/len(meta[tr])):.1f}% of the corpus is a deflection and is excluded)\n")

te=meta[(meta.split=='test')&(meta.is_first_turn)].reset_index(drop=True)
qe=emb[meta.index.get_indexer(te.index)] if False else None
# recompute: need embeddings aligned to test rows
te_pos=np.flatnonzero((meta.split=='test').values & meta.is_first_turn.values)
rng=np.random.default_rng(3); pick=rng.choice(te_pos,3,replace=False)
for p in pick:
    q=meta.iloc[p]
    res=idx.search(emb[p].astype(np.float32), k=3, before=q['created'])
    print("="*95); print("QUERY:", q['q'][:150]); print("  (true human reply:", str(q['reply_clean'])[:110],")")
    for _,r in res.iterrows():
        print(f"   sim={r.sim:.3f} | {r['q'][:88]}")
        print(f"            -> {str(r.reply_clean)[:110]}")
# temporal guard check
p=pick[0]; q=meta.iloc[p]
allres=idx.search(emb[p].astype(np.float32),k=50,before=None)
guarded=idx.search(emb[p].astype(np.float32),k=50,before=q['created'])
print("\n"+"="*95)
print(f"temporal guard: unguarded top-50 include {int((allres['created']>=q['created']).sum())} future cases; guarded include {int((guarded['created']>=q['created']).sum())}")
