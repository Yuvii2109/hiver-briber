import pandas as pd, numpy as np, re
from sklearn.feature_extraction.text import TfidfVectorizer
import sklearn.preprocessing as pp
BRAND='Uber_Support'
df=pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
brand_of=df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s:s.iloc[0])
th=set(brand_of[brand_of==BRAND].index); d=df[df.thread.isin(th)].copy()
def norm(s):
    s=str(s).lower(); s=re.sub(r'https?://\S+',' ',s); s=re.sub(r'@\w+',' ',s)
    s=re.sub(r'[\^~\-]\s?[a-z]{2}\s*$','',s.strip()); s=re.sub(r'\d+',' ',s)
    s=re.sub(r'[^a-z\s]',' ',s); return re.sub(r'\s+',' ',s).strip()
d['norm']=d['text'].map(norm); d=d.sort_values(['thread','created_at'])
first=d[d.inbound].groupby('thread',as_index=False).first()
first=first[first['norm'].str.split().str.len()>=5]
rep=d[~d.inbound].sort_values(['thread','created_at']).groupby('thread',as_index=False).first()[['thread','norm','text']]
rep.columns=['thread','rnorm','rtext']
m=first.merge(rep,on='thread').reset_index(drop=True)
print(f"pairs: {len(m):,}")

DEFL=re.compile(r'(?:\bdm\b|direct message|private message|send us a (?:note|message|dm)|message us|follow up here|contact us|reach out|email us|link)',re.I)
m['is_defl']=m['rtext'].str.contains(DEFL)
print(f"agent first-replies that are a DM/route deflection: {100*m['is_defl'].mean():.1f}%")

# semantic clustering of the REPLY side: TF-IDF on replies, greedy cluster at cos>0.8
vr=TfidfVectorizer(analyzer='word',ngram_range=(1,2),min_df=2,sublinear_tf=True)
R=pp.normalize(vr.fit_transform(m['rnorm']))
vq=TfidfVectorizer(analyzer='word',ngram_range=(1,2),min_df=2,sublinear_tf=True)
Q=pp.normalize(vq.fit_transform(m['norm']))

rng=np.random.default_rng(0); qs=rng.choice(len(m),400,replace=False)
sem5=[];defl5=[];exact5=[]
for i in qs:
    S=(Q[i]@Q.T).toarray().ravel(); S[i]=-1
    top=np.argsort(-S)[:5]
    Rt=R[top]; C=(Rt@Rt.T).toarray()
    # greedy: count clusters at cos>0.8 among the 5 retrieved replies
    unassigned=set(range(5)); k=0
    while unassigned:
        a=unassigned.pop(); k+=1
        for b in list(unassigned):
            if C[a,b]>0.8: unassigned.discard(b)
    sem5.append(k)
    defl5.append(m['is_defl'].iloc[top].mean())
    exact5.append(m['rnorm'].iloc[top].nunique())
sem5=np.array(sem5); defl5=np.array(defl5); exact5=np.array(exact5)
print(f"\n--- top-5 grounding diversity (400 random queries) ---")
print(f"  distinct reply STRINGS      : {exact5.mean():.2f} / 5")
print(f"  distinct reply CLUSTERS(>.8): {sem5.mean():.2f} / 5   (<=2 clusters: {100*(sem5<=2).mean():.1f}% of queries)")
print(f"  queries where ALL 5 retrieved replies are deflections: {100*(defl5==1.0).mean():.1f}%")
print(f"  queries where >=4/5 are deflections: {100*(defl5>=0.8).mean():.1f}%")
print(f"  mean deflection share of top-5: {defl5.mean():.2f}")
