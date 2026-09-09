"""Implements the proposed fix and measures its effect on AmericanAir."""
import pandas as pd, numpy as np
df = pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound']=df['inbound'].astype(bool)
df['parent']=pd.to_numeric(df['in_response_to_tweet_id'],errors='coerce')
df['created']=pd.to_datetime(df['created_at'],format="%a %b %d %H:%M:%S %z %Y",utc=True,errors='coerce')
BRAND='AmericanAir'
owner = df.loc[~df.inbound].groupby('thread')['author_id'].first()
keep=set(owner[owner==BRAND].index)
b = df[df['thread'].isin(keep)].copy()

ids=set(b['tweet_id'].astype('int64'))
par={int(t):(int(p) if pd.notna(p) and int(p) in ids else None) for t,p in zip(b['tweet_id'],b['parent'])}
auth=dict(zip(b['tweet_id'].astype('int64'),b['author_id']))
inb=dict(zip(b['tweet_id'].astype('int64'),b['inbound']))

# conv key = nearest inbound ancestor-or-self's author; None => pure broadcast segment
memo={}
def cust(t):
    if t in memo: return memo[t]
    path=[]; n=t
    while n is not None and not inb[n] and n not in memo:
        path.append(n); n=par[n]
    if n is None: r=None
    elif n in memo: r=memo[n]
    else: r=auth[n]           # n is inbound
    for p in path: memo[p]=r
    if n is not None: memo[n]=r
    return r
b['cust']=[cust(int(t)) for t in b['tweet_id']]
b['conv']=list(zip(b['thread'],b['cust'].fillna('__BROADCAST__')))

nb = b[b['cust'].notna()].copy()
print(f"messages dropped as pure-broadcast (no customer ancestor): {len(b)-len(nb):,} of {len(b):,}")
csz=nb.groupby('conv').size()
print(f"conversations after partition: {len(csz):,}  (was {b['thread'].nunique():,} components)")
print(f"  avg size {csz.mean():.3f}  max {csz.max()}  >20: {(csz>20).sum()}  >30: {(csz>30).sum()}")
chk=nb[nb.inbound].groupby('conv')['author_id'].nunique()
print(f"  convs with >1 customer author: {(chk>1).sum()}  (must be 0)")
print(f"  pct_multiturn(>2): {100*(csz>2).mean():.2f}")
split=nb.groupby('thread')['conv'].nunique()
print(f"  components split into >1 conv: {(split>1).sum():,} ({100*(split>1).mean():.2f}%)")
