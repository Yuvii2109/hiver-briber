import pandas as pd, numpy as np, re, sys
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize
df=pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
d=df.sort_values(['thread','created_at'])
def norm(s):
    s=str(s).lower(); s=re.sub(r'https?://\S+',' url ',s); s=re.sub(r'@\w+',' ',s)
    s=re.sub(r'[\^~\-]\s?[a-z]{2}\s*$','',s.strip()); s=re.sub(r'\d+',' ',s)
    s=re.sub(r'[^a-z\s]',' ',s); return re.sub(r'\s+',' ',s).strip()
fi=d[d.inbound].groupby('thread',as_index=False).first()[['thread','text']]
fo=d[~d.inbound].groupby('thread',as_index=False).first()[['thread','text','author_id']]
m=fi.merge(fo,on='thread',suffixes=('_q','_a'))
m['qn']=m['text_q'].map(norm); m['an']=m['text_a'].map(norm)
m=m[(m.qn.str.split().str.len()>=4)&(m.an.str.split().str.len()>=3)]
def tokf1(a,b):
    A=a.split(); B=b.split()
    if not A or not B: return 0.0
    from collections import Counter
    ca,cb=Counter(A),Counter(B); ov=sum((ca&cb).values())
    if ov==0: return 0.0
    p=ov/len(B); r=ov/len(A); return 2*p*r/(p+r)
rng=np.random.default_rng(0)
print(f"{'brand':<16}{'n':>7}{'parrot':>9}{'1NN':>9}{'delta':>8}{'oracle5':>9}")
for b in ['Uber_Support','AppleSupport','SpotifyCares','AmazonHelp','Delta','AmericanAir','hulu_support','GWRHelp','TMobileHelp','comcastcares','British_Airways','Tesco','VirginTrains']:
    g=m[m.author_id==b]
    if len(g)<3000: continue
    g=g.reset_index(drop=True)
    idx=rng.choice(len(g),min(1500,len(g)),replace=False)
    pool=np.setdiff1d(np.arange(len(g)),idx)
    # parrot = modal normalized reply among pool (by 12-word prefix cluster -> pick its longest member)
    pre=g.loc[pool,'an'].str.split().str[:12].str.join(' ')
    top=pre.value_counts().index[0]
    cand=g.loc[pool[pre.values==top],'an']
    parrot=cand.iloc[np.argmax(cand.str.len().values)]
    V=TfidfVectorizer(ngram_range=(1,2),min_df=2,sublinear_tf=True)
    Q=normalize(V.fit_transform(g['qn']))
    S=(Q[idx]@Q[pool].T).toarray()
    nn=pool[S.argmax(1)]
    top5=pool[np.argsort(-S,1)[:,:5]]
    pp=np.mean([tokf1(g.an.iloc[i],parrot) for i in idx])
    nnv=np.mean([tokf1(g.an.iloc[i],g.an.iloc[j]) for i,j in zip(idx,nn)])
    orc=np.mean([max(tokf1(g.an.iloc[i],g.an.iloc[j]) for j in row) for i,row in zip(idx,top5)])
    print(f"{b:<16}{len(g):>7}{pp:>9.3f}{nnv:>9.3f}{nnv-pp:>8.3f}{orc:>9.3f}")
