import pandas as pd, numpy as np, re, sys, os
from sklearn.feature_extraction.text import TfidfVectorizer
import sklearn.preprocessing as pp
P=lambda *a:(print(*a),sys.stdout.flush())
CACHE='data/raw/_rev_uber_first.pkl'
BRANDS=['Uber_Support','AmazonHelp','AppleSupport','Delta']
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
        f=f.merge(r,on='thread'); f['brand']=B; out.append(f)
    allf=pd.concat(out,ignore_index=True); allf.to_pickle(CACHE)
P("cached rows:",len(allf))
for B in BRANDS:
    f=allf[allf.brand==B].copy()
    P(f"\n===== {B}  threads-with-reply={len(f):,}")
    P("  span:",f.created_at.min(),"->",f.created_at.max())
    wk=f.created_at.dt.to_period('W').value_counts().sort_index()
    P("  weeks:"); 
    for k,v in wk.items(): P(f"    {k}  {v:6,}  {100*v/len(f):5.2f}%")
    pre=(f.created_at<pd.Timestamp('2017-10-01',tz='UTC')).sum()
    P(f"  threads before 2017-10-01: {pre} ({100*pre/len(f):.3f}%)")
