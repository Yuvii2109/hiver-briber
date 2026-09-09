import pandas as pd, numpy as np, re, sys, os
from sklearn.feature_extraction.text import TfidfVectorizer
import sklearn.preprocessing as pp
P=lambda *a:(print(*a),sys.stdout.flush())
CACHE='data/raw/_rev_cache.pkl'
BRANDS=['Uber_Support','AmazonHelp','Delta']
def norm(s):
    s=str(s).lower(); s=re.sub(r'https?://\S+',' ',s); s=re.sub(r'@\w+',' ',s)
    s=re.sub(r'\d+',' ',s); s=re.sub(r'[^a-z\s]',' ',s); return re.sub(r'\s+',' ',s).strip()
if os.path.exists(CACHE):
    allf=pd.read_pickle(CACHE)
else:
    df=pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
    brand_of=df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s:s.iloc[0])
    out=[]
    for B in BRANDS:
        th=set(brand_of[brand_of==B].index); d=df[df.thread.isin(th)].copy()
        d['created_at']=pd.to_datetime(d['created_at'],format='mixed',utc=True,errors='coerce')
        d['norm']=d['text'].map(norm); d=d.sort_values(['thread','created_at'])
        f=d[d.inbound].groupby('thread',as_index=False).first()
        r=d[~d.inbound].groupby('thread',as_index=False).first()[['thread','norm','text']]
        r.columns=['thread','rnorm','rtext']
        f=f.merge(r,on='thread'); f['brand']=B; out.append(f[['thread','brand','author_id','created_at','text','norm','rtext','rnorm']])
    allf=pd.concat(out,ignore_index=True); allf.to_pickle(CACHE)
P("cached:",len(allf))
for B in BRANDS:
    f=allf[allf.brand==B].copy()
    f=f[f['norm'].str.split().str.len()>=5].reset_index(drop=True)
    n=len(f)
    P(f"\n===== {B}  n={n:,}")
    wk=f.created_at.dt.to_period('W').value_counts()
    P(f"  in-window(>=2017-10-01): {100*(f.created_at>=pd.Timestamp('2017-10-01',tz='UTC')).mean():.2f}%   busiest week share={100*wk.max()/n:.2f}%  (uniform over {len(wk[wk>100])} wks = {100/len(wk[wk>100]):.1f}%)")
    # channel A: repeat customers across threads
    vc=f.author_id.value_counts()
    P(f"  CHANNEL A repeat-customer: {100*(1-vc.size/n):.2f}% of threads share an author with another thread; top author has {vc.iloc[0]} threads")
    # channel B: reply-side template collapse (split-invariant)
    P(f"  CHANNEL B reply template: distinct normalised first-replies = {f.rnorm.nunique():,} / {n:,} = {100*f.rnorm.nunique()/n:.1f}%")
    top=f.rnorm.value_counts().head(3)
    for t,c in top.items(): P(f"      x{c:5,} ({100*c/n:4.1f}%)  {t[:90]}")
    P(f"      top-10 reply strings cover {100*f.rnorm.value_counts().head(10).sum()/n:.1f}% of all threads")
