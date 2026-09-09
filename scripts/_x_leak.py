import pandas as pd, numpy as np, re, sys
from sklearn.feature_extraction.text import TfidfVectorizer
import sklearn.preprocessing as pp
P=lambda *a: (print(*a), sys.stdout.flush())
BRAND='Uber_Support'
df=pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
brand_of=df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s:s.iloc[0])
th=set(brand_of[brand_of==BRAND].index); d=df[df.thread.isin(th)].copy()
d['created_at']=pd.to_datetime(d['created_at'],format='mixed',utc=True,errors='coerce')
P("date span all rows:", d['created_at'].min(), "->", d['created_at'].max())
def norm(s):
    s=str(s).lower(); s=re.sub(r'https?://\S+',' ',s); s=re.sub(r'@\w+',' ',s)
    s=re.sub(r'\d+',' ',s); s=re.sub(r'[^a-z\s]',' ',s); return re.sub(r'\s+',' ',s).strip()
d['norm']=d['text'].map(norm); d=d.sort_values(['thread','created_at'])
first=d[d.inbound].groupby('thread',as_index=False).first()
first=first[first['norm'].str.split().str.len()>=5].reset_index(drop=True)
P(f"customer first-msgs (>=5 content words): {len(first):,}")
P("thread-start month distribution:")
P(first['created_at'].dt.to_period('W').value_counts().sort_index().to_string())

def leak(tr,te,analyzer,ngr,label):
    v=TfidfVectorizer(analyzer=analyzer,ngram_range=ngr,min_df=2,sublinear_tf=True)
    Xtr=pp.normalize(v.fit_transform(tr['norm'])); Xte=pp.normalize(v.transform(te['norm']))
    best=np.zeros(Xte.shape[0])
    for i in range(0,Xte.shape[0],500):
        best[i:i+500]=(Xte[i:i+500]@Xtr.T).toarray().max(1)
    P(f"\n[{label}] {analyzer} {ngr}  train={len(tr):,} test={len(te):,}")
    for t in [0.99,0.95,0.90,0.80,0.70,0.60]:
        P(f"   max-cos > {t}: {(best>t).sum():,}  ({100*(best>t).mean():.2f}%)")
    P(f"   median max-cos={np.median(best):.3f} mean={best.mean():.3f}")
    return best

rng=np.random.default_rng(0); perm=rng.permutation(len(first)); n_te=int(0.2*len(first))
first['rsplit']=np.where(np.isin(np.arange(len(first)),perm[:n_te]),'test','train')
tr=first[first.rsplit=='train']; te=first[first.rsplit=='test']
leak(tr,te,'char_wb',(3,5),'RANDOM conv split')

# temporal
cut=first['created_at'].quantile(0.8)
P(f"\ntemporal cutoff (80th pct of thread start) = {cut}")
trT=first[first.created_at<=cut]; teT=first[first.created_at>cut]
leak(trT,teT,'char_wb',(3,5),'TEMPORAL split')
