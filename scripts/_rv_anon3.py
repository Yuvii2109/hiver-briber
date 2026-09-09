# -*- coding: utf-8 -*-
import pandas as pd, numpy as np, re, sys, collections, io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
P=lambda *a:(print(*a),sys.stdout.flush())
df=pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
brand_of=df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s:s.iloc[0])
BRAND='Uber_Support'
th=set(brand_of[brand_of==BRAND].index); d=df[df.thread.isin(th)].sort_values(['thread','created_at'])
f=d[d.inbound].groupby('thread',as_index=False).first()[['thread','author_id','text']]
o=d[~d.inbound].groupby('thread',as_index=False).first()[['thread','text']]
m=f.merge(o,on='thread',suffixes=('_q','_a'))
P(f"pairs={len(m):,} distinct customers={m.author_id.nunique():,}")
# examples of top mention ids
for mid in ['115873','115877','119983','116288']:
    ex=m[m.text_q.str.contains('@'+mid,regex=False)].text_q.head(3).tolist()
    P(f"\n--- @{mid} examples ---")
    for e in ex: P("   ", e[:130].replace('\n',' '))
raw=m.text_q.astype(str)
def nrm(s):
    s=re.sub(r'https?://\S+',' <LINK> ',str(s)); s=re.sub(r'@\d+',' <USER> ',s); s=re.sub(r'@\w+',' <BRAND> ',s)
    return re.sub(r'\s+',' ',s).strip()
nor=raw.map(nrm)
rng=np.random.default_rng(0); n=len(m); perm=rng.permutation(n); te=perm[:4000]; tr=perm[4000:]
auth=m.author_id.values
base=np.mean([ (auth[tr]==auth[i]).mean() for i in te[:1500] ])
P(f"\nbase rate P(random train item is same customer) = {base*100:.4f}%")
for lbl,corpus in [('RAW (mentions kept)',raw),('NORMALISED (@d->USER, url->LINK)',nor)]:
    V=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True)
    X=normalize(V.fit_transform(corpus))
    S=(X[te]@X[tr].T)
    S=np.asarray(S.todense())
    nn=tr[S.argmax(1)]
    same=(auth[nn]==auth[te]).mean()
    P(f"{lbl}: vocab={len(V.vocabulary_):,}  P(top-1 neighbour is SAME customer)={same*100:.2f}%  lift={same/base:.0f}x  mean max-cos={S.max(1).mean():.3f}")
# names in agent replies
NAMEPAT=re.compile(r'(?:^|[,!\.]\s|\bHi\b\s|\bHey\b\s|\bHello\b\s|\bSorry\b[^,]*,\s)([A-Z][a-z]{2,11})\b')
common=set('''Hi Hey Hello Sorry Thanks Thank We I If Please Send Can Could Would Team Uber Ubers DM Our Your You This That The It Is Are Not No Yes Let Us Here There Have Has Had Will Would Should May Might Just Also Sure Happy Glad Apologies Apologize Oh Ah Ok Okay Hope Hoping Feel Feels Rest Assured Support Help Helped Trip Trips Driver Drivers Account Payment Fare Ride Rides App Email Reply Replied Please'''.split())
def names(s):
    return [x for x in NAMEPAT.findall(str(s)) if x not in common]
hit=m.text_a.map(lambda s: len(names(s))>0)
P(f"\nagent replies with a name-like token: {hit.mean()*100:.1f}%")
cnt=collections.Counter(x for s in m.text_a for x in names(s))
P("top name-like tokens:", cnt.most_common(20))
