import pandas as pd, numpy as np, re, math
from collections import defaultdict
BRAND='Uber_Support'
df = pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
brand_of = df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s: s.iloc[0])
th = set(brand_of[brand_of==BRAND].index)
d = df[df.thread.isin(th)].copy().sort_values(['thread','created_at'])
DM   = re.compile(r'(?:\bdm\b|direct message|private message|\bpm us\b|message us|send us a (?:message|note)|meet you there)', re.I)
ROUTE= re.compile(r'(?:visit|follow up|click|head (?:to|over)|check out|reach out|contact us|fill out|use|via|here)[^.!?]{0,40}https?://', re.I)
recs=[]
for t,g in d.groupby('thread',sort=False):
    inb=g['inbound'].values; tx=g['text'].fillna('').values
    if not (~inb).any(): continue
    fi=int(np.argmax(~inb)); txt=tx[fi]
    recs.append((bool(inb[fi+1:].any()), bool(DM.search(txt)), bool(ROUTE.search(txt))))
r=pd.DataFrame(recs,columns=['came_back','dm','route'])
print(f"n threads={len(r):,}")
print(f"first reply DM-only deflect : {100*r.dm.mean():.1f}%")
print(f"first reply link-route      : {100*r.route.mean():.1f}%")
print(f"first reply DM or link      : {100*(r.dm|r.route).mean():.1f}%")
print(f"customer replies again after first brand reply: {100*r.came_back.mean():.1f}%")
print(f"NOT DM-deflected AND no follow-up (loosest 'one-shot handled'): {100*((~r.dm)&(~r.came_back)).mean():.1f}%")
print(f"NOT DM/link AND no follow-up (strict)                        : {100*((~(r.dm|r.route))&(~r.came_back)).mean():.1f}%")
def norm(s):
    s=str(s).lower(); s=re.sub(r'https?://\S+',' ',s); s=re.sub(r'@\w+',' ',s)
    s=re.sub(r'\d+',' ',s); s=re.sub(r'[^a-z\s]',' ',s); return re.sub(r'\s+',' ',s).strip()
first = d[d.inbound].groupby('thread',as_index=False).first(); first['norm']=first['text'].map(norm)
rng=np.random.default_rng(0); idx=rng.permutation(len(first))
hold=first.iloc[idx[:200]]; train=first.iloc[idx[200:]]
print(f"\nheld-out 200 vs index {len(train):,}: normalized-EXACT twin in index: {100*hold['norm'].isin(set(train['norm'])).mean():.1f}%")
tr_tok=[set(x.split()) for x in train['norm']]
inv=defaultdict(list)
for i,ts_ in enumerate(tr_tok):
    for w in ts_: inv[w].append(i)
for THR in (0.6,0.8):
    hits=0
    for h in hold['norm']:
        hs=set(h.split())
        if not hs: continue
        cand=set()
        for w in hs: cand.update(inv.get(w,[])[:1500])
        best=0.0
        for i in cand:
            u=len(hs|tr_tok[i])
            if u: best=max(best,len(hs&tr_tok[i])/u)
            if best>=THR: break
        hits+= best>=THR
    print(f"held-out 200: token-Jaccard>={THR} near-twin in index: {100*hits/200:.1f}%")
def wilson(k,n,z=1.96):
    p=k/n; den=1+z*z/n; c=(p+z*z/(2*n))/den; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return (100*(c-h),100*(c+h))
print(f"\nWilson CI, 38% of n=150: {wilson(57,150)}")
print(f"Wilson CI, 82% of n=40 : {wilson(33,40)}")
print(f"Wilson CI, 82% of n=25 : {wilson(20,25)}")
