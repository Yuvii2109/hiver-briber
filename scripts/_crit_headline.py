import pandas as pd, numpy as np, re, math
BRAND='Uber_Support'
df = pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
brand_of = df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s: s.iloc[0])
th = set(brand_of[brand_of==BRAND].index)
d = df[df.thread.isin(th)].copy().sort_values(['thread','created_at'])
print(f"{BRAND}: threads={len(th):,}")

DM   = re.compile(r'(?:\bdm\b|direct message|private message|\bpm us\b|message us|send us a (?:message|note)|meet you there)', re.I)
ROUTE= re.compile(r'(?:visit|follow up|click|head (?:to|over)|check out|reach out|contact us|fill out|use|via|here)[^.!?]{0,40}https?://', re.I)

# first brand reply per thread + whether a customer message follows it
recs=[]
for t,g in d.groupby('thread',sort=False):
    inb=g['inbound'].values; ts=g['created_at'].values; tx=g['text'].fillna('').values
    fi=np.argmax(~inb) if (~inb).any() else None
    if fi is None: continue
    after_customer = bool(inb[fi+1:].any())
    txt=tx[fi]
    recs.append((t, after_customer, bool(DM.search(txt) or ROUTE.search(txt)), int(inb.sum()), len(g)))
r=pd.DataFrame(recs,columns=['thread','customer_came_back','first_reply_deflect','n_inbound','n_msgs'])
n=len(r)
def wilson(k,n,z=1.96):
    p=k/n; den=1+z*z/n; c=(p+z*z/(2*n))/den; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return (100*(c-h),100*(c+h))
print(f"threads with a brand reply: {n:,}")
print(f"customer sends ANOTHER message after the first brand reply: {100*r.customer_came_back.mean():.1f}%")
print(f"first brand reply is a DM/link deflection:                  {100*r.first_reply_deflect.mean():.1f}%")
ct=pd.crosstab(r.first_reply_deflect,r.customer_came_back,normalize=True).round(3)*100
print("\n%% of threads, rows=first_reply_deflect, cols=customer_came_back:\n",ct)
print(f"\nfirst reply DEFLECTS *and* customer comes back anyway: {100*((r.first_reply_deflect)&(r.customer_came_back)).mean():.1f}%")
print(f"first reply neither deflects nor gets a follow-up (best case 'one-shot resolved'): {100*((~r.first_reply_deflect)&(~r.customer_came_back)).mean():.1f}%")

# --- near-duplicate leakage between a held-out slice and the index ---
def norm(s):
    s=str(s).lower(); s=re.sub(r'https?://\S+',' ',s); s=re.sub(r'@\w+',' ',s)
    s=re.sub(r'\d+',' ',s); s=re.sub(r'[^a-z\s]',' ',s); return re.sub(r'\s+',' ',s).strip()
first = d[d.inbound].groupby('thread',as_index=False).first()
first['norm']=first['text'].map(norm)
rng=np.random.default_rng(0); idx=rng.permutation(len(first)); hold=first.iloc[idx[:200]]; train=first.iloc[idx[200:]]
tr=set(train['norm'])
exact=hold['norm'].isin(tr).mean()
print(f"\nheld-out n=200 first-messages: normalized-EXACT twin already in index: {100*exact:.1f}%")
# token-jaccard >=0.8 near-dup via inverted index on rare-ish tokens (sampled train for speed)
tr_s=train.sample(60000,random_state=1)
from collections import defaultdict
inv=defaultdict(list)
tr_tok=[set(x.split()) for x in tr_s['norm']]
for i,ts_ in enumerate(tr_tok):
    for w in list(ts_)[:12]: inv[w].append(i)
hits=0
for h in hold['norm']:
    hs=set(h.split())
    if not hs: continue
    cand=set()
    for w in hs: cand.update(inv.get(w,[])[:400])
    best=0.0
    for i in cand:
        u=len(hs|tr_tok[i]); 
        if u: best=max(best,len(hs&tr_tok[i])/u)
        if best>=0.8: break
    hits+= best>=0.8
print(f"held-out n=200: token-Jaccard>=0.8 near-twin in a 60k sample of the index: {100*hits/200:.1f}%")
for k,lab in [(int(0.38*150),'38% of n=150'),(int(0.82*40),'82% of n=40')]:
    nn=150 if 'n=150' in lab else 40
    lo,hi=wilson(k,nn); print(f"Wilson 95% CI for {lab}: [{lo:.0f}%, {hi:.0f}%]")
