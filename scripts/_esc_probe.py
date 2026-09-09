import pandas as pd, numpy as np, re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, roc_auc_score, precision_recall_fscore_support

df = pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound']=df['inbound'].astype(bool)
df['created']=pd.to_datetime(df['created_at'], format='%a %b %d %H:%M:%S %z %Y', errors='coerce', utc=True)
brand_of = df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s: s.iloc[0])

HANDOFF = re.compile(r"(?:\bdm\b|\bdms\b|direct message|private message|\bpm us\b|message us|send us a (?:message|note|dm)|meet you (?:there|here)|call us|give us a call|email us|contact us|reach out to us|fill out|web ?form|(?:visit|click|head (?:to|over)|check out|reach out|report it|submit)[^.!?]{0,45}https?://)", re.I)
RISKKW  = re.compile(r"\b(?:fraud|stolen|steal|hack(?:ed|ing)?|unauthori[sz]ed|assault|attack|threat|unsafe|safety|police|lawyer|legal|sue|lawsuit|accident|crash|injur|emergency|911|harass|racist|refund|charged twice|double charge)\b", re.I)

def strip_(s):
    s = re.sub(r'@\w+','',str(s)); s = re.sub(r'https?://\S+',' URL ',s)
    return re.sub(r'\s+',' ',s).strip()

for B in ['Uber_Support','AmericanAir','Delta','hulu_support']:
    th = set(brand_of[brand_of==B].index)
    sub = df[df['thread'].isin(th)].sort_values(['thread','created'], kind='mergesort')
    # first inbound msg of thread, and the first brand reply after it
    first_in = sub[sub.inbound].groupby('thread').head(1)[['thread','text','created']].rename(columns={'text':'cust','created':'t0'})
    out = sub[~sub.inbound]
    first_out = out.groupby('thread').head(1)[['thread','text','created']].rename(columns={'text':'reply','created':'t1'})
    m = first_in.merge(first_out, on='thread')
    m = m[m.t1>=m.t0]
    m['y'] = m['reply'].fillna('').str.contains(HANDOFF).astype(int)
    m['cust_s'] = m['cust'].map(strip_)
    m = m[m.cust_s.str.split().str.len()>=3]
    m = m.sort_values('t0')
    n=len(m); cut=int(n*0.8)
    tr, te = m.iloc[:cut], m.iloc[cut:]
    base = te.y.mean()
    # baseline: risk keyword
    kw = te['cust_s'].str.contains(RISKKW).astype(int)
    p,r,f,_ = precision_recall_fscore_support(te.y, kw, average='binary', zero_division=0)
    # simple model on customer text ONLY
    v = TfidfVectorizer(ngram_range=(1,2), min_df=3, max_features=60000, sublinear_tf=True)
    Xtr=v.fit_transform(tr.cust_s); Xte=v.transform(te.cust_s)
    clf=LogisticRegression(max_iter=1000, C=1.0, class_weight='balanced').fit(Xtr, tr.y)
    s=clf.predict_proba(Xte)[:,1]
    ap=average_precision_score(te.y,s); auc=roc_auc_score(te.y,s)
    yh=(s>=0.5).astype(int)
    p2,r2,f2,_=precision_recall_fscore_support(te.y,yh,average='binary',zero_division=0)
    print(f"{B:14s} n={n:6d} test={len(te):5d} base_rate={base:.3f} | never-esc acc={1-base:.3f} "
          f"| kw P={p:.3f} R={r:.3f} F1={f:.3f} | tfidf-LR PR-AUC={ap:.3f} (lift x{ap/base:.2f}) ROC-AUC={auc:.3f} P={p2:.3f} R={r2:.3f} F1={f2:.3f}")
