import pandas as pd, numpy as np, re, collections, json

df = pd.read_pickle('data/raw/twcs.pkl')
df['inbound'] = df['inbound'].astype(bool)
df['in_response_to_tweet_id'] = pd.to_numeric(df['in_response_to_tweet_id'], errors='coerce')

# ---- branching check: response_tweet_id may hold a comma-separated list
rt = df['response_tweet_id'].fillna('')
multi = rt.str.contains(',')
print(f"tweets whose response_tweet_id lists MULTIPLE replies (branching): {multi.sum():,} "
      f"({100*multi.mean():.2f}%)  -> a thread is a TREE, not a chain")

# ---- chronology trap
d2 = df.dropna(subset=['in_response_to_tweet_id']).copy()
d2['parent'] = d2['in_response_to_tweet_id'].astype('int64')
print(f"replies whose parent has a HIGHER tweet_id: "
      f"{(d2['parent'] > d2['tweet_id']).mean()*100:.1f}%  -> tweet_id is NOT chronological")

# ---- build threads by walking parent pointers to a root
parent = dict(zip(d2['tweet_id'], d2['parent']))
ids = set(df['tweet_id'])
root_of = {}
def find_root(t):
    path=[]
    while t in parent and parent[t] in ids:
        if t in root_of:
            r=root_of[t]; break
        path.append(t); t=parent[t]
        if len(path)>200: break
    else:
        r=t
    r = root_of.get(t, t if t not in root_of else root_of[t])
    for p in path: root_of[p]=r
    root_of[t]=r
    return r
for t in df['tweet_id'].values:
    find_root(t)
df['thread'] = df['tweet_id'].map(root_of)
print(f"threads reconstructed: {df['thread'].nunique():,}")
df.to_pickle('data/raw/twcs_threaded.pkl')

# ---- per-brand thread stats
brand_of = df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s: s.iloc[0])
sizes = df.groupby('thread').size()
has_brand = df.groupby('thread')['inbound'].apply(lambda s: (~s).any())
DEFLECT = re.compile(r'\b(dm|direct message|private message|pm us|send us a message|link in bio|call us|email us)\b', re.I)
df['deflect'] = (~df.inbound) & df['text'].fillna('').str.contains(DEFLECT)
defl_by_thread = df.groupby('thread')['deflect'].any()

rows=[]
for b in df.loc[~df.inbound,'author_id'].value_counts().head(20).index:
    th = brand_of[brand_of==b].index
    n = len(th)
    rows.append(dict(brand=b, threads=n,
        inbound_msgs=int(df[(df.thread.isin(th))&(df.inbound)].shape[0]),
        avg_turns=round(float(sizes.loc[th].mean()),2),
        pct_multiturn=round(100*float((sizes.loc[th]>2).mean()),1),
        pct_deflect_to_dm=round(100*float(defl_by_thread.loc[th].mean()),1)))
r = pd.DataFrame(rows).sort_values('threads', ascending=False)
print("\n--- per-brand thread stats (top 20 by volume) ---")
print(r.to_string(index=False))
r.to_csv('data/raw/brand_stats.csv', index=False)
