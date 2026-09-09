import pandas as pd, numpy as np, re, sys
from sklearn.feature_extraction.text import TfidfVectorizer
import sklearn.preprocessing as pp
BRAND='Uber_Support'
df=pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
brand_of=df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s:s.iloc[0])
th=set(brand_of[brand_of==BRAND].index); d=df[df.thread.isin(th)].copy()
d['created_at']=pd.to_datetime(d['created_at'],format='mixed',utc=True,errors='coerce')
def norm(s):
    s=str(s).lower(); s=re.sub(r'https?://\S+',' ',s); s=re.sub(r'@\w+',' ',s)
    s=re.sub(r'\d+',' ',s); s=re.sub(r'[^a-z\s]',' ',s); return re.sub(r'\s+',' ',s).strip()
d['norm']=d['text'].map(norm); d=d.sort_values(['thread','created_at'])
first=d[d.inbound].groupby('thread',as_index=False).first()
first=first[first['norm'].str.split().str.len()>=5].reset_index(drop=True)
n=len(first); print(f"threads(usable)={n:,}",flush=True)
# how many customers open >1 thread?
ac=first['author_id'].value_counts()
print(f"distinct customer authors={len(ac):,}; authors with >1 thread={int((ac>1).sum()):,} "
      f"covering {int(ac[ac>1].sum()):,} threads ({100*ac[ac>1].sum()/n:.1f}%)",flush=True)
rng=np.random.default_rng(0); perm=rng.permutation(n); n_te=int(0.2*n)
first['split']=np.where(np.isin(np.arange(n),perm[:n_te]),'test','train')
tr=first[first.split=='train'].reset_index(drop=True); te=first[first.split=='test'].reset_index(drop=True)
sa=te['author_id'].isin(set(tr['author_id']))
print(f"TEST threads whose SAME customer also has a TRAIN thread: {int(sa.sum()):,}/{len(te):,} ({100*sa.mean():.2f}%)",flush=True)
# max cosine restricted to same-author train threads
v=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=2,sublinear_tf=True)
Xtr=pp.normalize(v.fit_transform(tr['norm'])); Xte=pp.normalize(v.transform(te['norm']))
idx=np.where(sa.to_numpy())[0]
byauth={}
for j,a in enumerate(tr['author_id']): byauth.setdefault(a,[]).append(j)
hi=0; ex=[]
for i in idx:
    js=byauth[te['author_id'].iloc[i]]
    s=(Xte[i]@Xtr[js].T).toarray().ravel()
    if s.max()>0.9:
        hi+=1
        if len(ex)<5: ex.append((s.max(),te['text'].iloc[i][:90],tr['text'].iloc[js[int(s.argmax())]][:90]))
print(f"  of those, max same-author cosine > 0.9: {hi} ({100*hi/max(len(te),1):.2f}% of all test)",flush=True)
for c,a,b in ex: print(f"   cos={c:.3f}\n     TEST : {a}\n     TRAIN: {b}",flush=True)
