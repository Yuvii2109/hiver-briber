import pandas as pd, numpy as np, re, sys
sys.path.insert(0,'src')
df = pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
df['created']=pd.to_datetime(df['created_at'], format='%a %b %d %H:%M:%S %z %Y', utc=True, errors='coerce')
owner = df.loc[~df.inbound].groupby('thread')['author_id'].first()
aa = df[df.thread.isin(set(owner[owner=='AmericanAir'].index))].copy()

# 1) over-merge: threads containing >1 distinct CUSTOMER author
cust_per = aa[aa.inbound].groupby('thread')['author_id'].nunique()
print(f"AmericanAir threads: {aa.thread.nunique():,}")
print(f"  with >1 distinct customer author: {(cust_per>1).sum():,} ({(cust_per>1).mean()*100:.1f}%)")
print(f"  max customers in one thread: {cust_per.max()}   max thread size: {aa.groupby('thread').size().max()}")
print(f"  threads >30 msgs: {(aa.groupby('thread').size()>30).sum():,}")

# 2) multi-tweet agent bursts replying to the SAME parent
ag = aa[~aa.inbound].copy()
ag['parent']=pd.to_numeric(ag['in_response_to_tweet_id'],errors='coerce')
burst = ag.dropna(subset=['parent']).groupby(['thread','parent']).size()
print(f"\nagent replies to same parent: mean={burst.mean():.2f} max={burst.max()}")
print(f"  parents with >=2 agent replies: {(burst>=2).sum():,} ({(burst>=2).mean()*100:.1f}%)")
# k/n continuation markers
mk = ag['text'].fillna('').str.contains(r'\b\d\s?/\s?\d\b', regex=True)
print(f"  agent replies containing a 'k/n' marker: {mk.sum():,} ({mk.mean()*100:.2f}%)")
# 3) signatures on AmericanAir
sig = ag['text'].fillna('').str.contains(r'[\^\*]\s?[A-Z]{2}\s*$', regex=True)
print(f"  agent replies with ^XX/*XX signature: {sig.sum():,} ({sig.mean()*100:.2f}%)")
# 4) embedded newlines in raw csv text
nl = aa['text'].fillna('').str.contains('\n')
print(f"  texts containing embedded newline: {nl.sum():,} ({nl.mean()*100:.2f}%)")
