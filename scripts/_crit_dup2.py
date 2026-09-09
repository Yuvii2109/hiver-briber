import pandas as pd, numpy as np, re
from sklearn.feature_extraction.text import TfidfVectorizer
BRAND='Uber_Support'
df = pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
brand_of = df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s: s.iloc[0])
th=set(brand_of[brand_of==BRAND].index); d=df[df.thread.isin(th)].copy()
def norm(s):
    s=str(s).lower(); s=re.sub(r'https?://\S+',' ',s); s=re.sub(r'@\w+',' ',s)
    s=re.sub(r'[\^~\-]\s?[a-z]{2}\s*$','',s.strip()); s=re.sub(r'\d+',' ',s)
    s=re.sub(r'[^a-z\s]',' ',s); return re.sub(r'\s+',' ',s).strip()
d['norm']=d['text'].map(norm); d=d.sort_values(['thread','created_at'])
first=d[d.inbound].groupby('thread',as_index=False).first()
first=first[first['norm'].str.split().str.len()>=5].reset_index(drop=True)   # real messages only
print(f"customer first-messages with >=5 content words: {len(first):,}")

rng=np.random.default_rng(0); perm=rng.permutation(len(first)); n_te=int(0.2*len(first))
first['split']=np.where(np.isin(np.arange(len(first)),perm[:n_te]),'test','train')
tr=first[first.split=='train'].reset_index(drop=True); te=first[first.split=='test'].reset_index(drop=True)

v=TfidfVectorizer(analyzer='word',ngram_range=(1,2),min_df=2,sublinear_tf=True)
Xtr=v.fit_transform(tr['norm']); Xte=v.transform(te['norm'])
import sklearn.preprocessing as pp
Xtr=pp.normalize(Xtr); Xte=pp.normalize(Xte)
best=np.zeros(Xte.shape[0]); arg=np.zeros(Xte.shape[0],dtype=int)
for i in range(0,Xte.shape[0],1000):
    S=(Xte[i:i+1000]@Xtr.T).toarray()
    best[i:i+1000]=S.max(1); arg[i:i+1000]=S.argmax(1)
print("\n--- CUSTOMER-side near-dup leakage (TF-IDF word 1-2gram cosine, test vs train) ---")
for t in [0.99,0.95,0.90,0.80,0.70]:
    print(f"  test msgs with max cos > {t}: {(best>t).sum():,} / {len(te):,}  ({100*(best>t).mean():.2f}%)")
print(f"  median max-cos = {np.median(best):.3f}   mean = {best.mean():.3f}")
print("\n examples at cos>0.95:")
idx=np.where(best>0.95)[0][:5]
for i in idx:
    print(f"  cos={best[i]:.3f}\n    TEST : {te['text'].iloc[i][:100]}\n    TRAIN: {tr['text'].iloc[arg[i]][:100]}")

# ---- agent side: how diverse is a top-5 retrieval really? ----
out=d[~d.inbound].copy()
pairs=[]
# link each first customer msg to the brand's first reply in that thread
rep=out.sort_values(['thread','created_at']).groupby('thread',as_index=False).first()[['thread','norm','text']]
rep.columns=['thread','rnorm','rtext']
m=first.merge(rep,on='thread',how='inner')
print(f"\n--- (customer,reply) pairs available for grounding: {len(m):,} ---")
Xall=pp.normalize(v.transform(m['norm']))
q=rng.choice(len(m),400,replace=False)
uniq5=[];uniq10=[]
for i in q:
    S=(Xall[i]@Xall.T).toarray().ravel(); S[i]=-1
    top=np.argsort(-S)[:10]
    uniq5.append(m['rnorm'].iloc[top[:5]].nunique()); uniq10.append(m['rnorm'].iloc[top].nunique())
print(f"  distinct agent replies among top-5 retrieved (mean over 400 queries): {np.mean(uniq5):.2f} / 5")
print(f"  distinct agent replies among top-10: {np.mean(uniq10):.2f} / 10")
print(f"  queries where top-5 collapses to <=2 distinct replies: {100*np.mean(np.array(uniq5)<=2):.1f}%")
