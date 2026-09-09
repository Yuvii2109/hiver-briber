import pandas as pd, numpy as np, sys
sys.path.insert(0,'src')
df = pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound']=df['inbound'].astype(bool)
df['parent']=pd.to_numeric(df['in_response_to_tweet_id'],errors='coerce')
df['created']=pd.to_datetime(df['created_at'],format="%a %b %d %H:%M:%S %z %Y",utc=True,errors='coerce')

BRAND='AmericanAir'
owner = df.loc[~df.inbound].groupby('thread')['author_id'].first()
keep=set(owner[owner==BRAND].index)
b = df[df['thread'].isin(keep)].copy()
print(f"{BRAND}: threads={b['thread'].nunique():,} msgs={len(b):,}")

inb=b[b.inbound]
nc=inb.groupby('thread')['author_id'].nunique()
multi=set(nc[nc>1].index)
print(f"  threads w/ >1 customer: {len(multi):,} ({100*len(multi)/b['thread'].nunique():.2f}%)")
print(f"  inbound msgs in those: {inb['thread'].isin(multi).sum():,} ({100*inb['thread'].isin(multi).mean():.2f}%)")
sz=b.groupby('thread').size()
print("  size dist:", {k:int((sz>k).sum()) for k in [10,20,50,100]}, "max", int(sz.max()))
print("  avg_turns ALL:", round(sz.mean(),3), "| avg_turns excluding multi-customer:", round(sz[~sz.index.isin(multi)].mean(),3))
print("  pct_multiturn(>2) ALL:", round(100*(sz>2).mean(),2), "| excl multi:", round(100*(sz[~sz.index.isin(multi)]>2).mean(),2))
