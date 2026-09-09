import pandas as pd, numpy as np, re
df = pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound']=df['inbound'].astype(bool)
df['in_response_to_tweet_id']=pd.to_numeric(df['in_response_to_tweet_id'],errors='coerce')
df['ts']=pd.to_datetime(df['created_at'],format='%a %b %d %H:%M:%S +0000 %Y',utc=True)
inb_ids=set(df.loc[df.inbound,'tweet_id'])

# --- Delta example of scrambling + id order sanity
END=r'\b(\d{1,2})\s?/\s?(\d{1,2})\b\s*(?:[\^~*\-][A-Za-z]{1,4})?\s*$'
d=df[(~df.inbound)&(df.author_id=='Delta')].dropna(subset=['in_response_to_tweet_id'])
sz=d.groupby('in_response_to_tweet_id').size()
shown=0
for pid in sz[sz>=3].index:
    g=d[d.in_response_to_tweet_id==pid]
    m=g['text'].str.extract(END)
    if m[0].notna().all():
        g2=g.assign(k=m[0].astype(int)).sort_values('ts',kind='stable')
        print(f"\nDelta burst parent={int(pid)} ts-sorted marker sequence -> {list(g2.k)}  ids {list(g2.tweet_id)}")
        for _,r in g2.iterrows(): print(f"   {r.ts.time()} id={r.tweet_id} k={r.k} :: {r.text[:95]}")
        shown+=1
    if shown>=3: break

# --- Uber: how much does burst-merge change anything?
u=df[(~df.inbound)&(df.author_id=='Uber_Support')].dropna(subset=['in_response_to_tweet_id']).copy()
u=u[u.in_response_to_tweet_id.isin(inb_ids)]
g=u.groupby('in_response_to_tweet_id')
sz=g.size(); span=(g['ts'].max()-g['ts'].min()).dt.total_seconds()
print(f"\nUber answered msgs={len(sz):,}")
for w in [60,300,900]:
    n=((sz>=2)&(span<=w)).sum()
    print(f"  2+ agent tweets within {w}s window: {n:,} ({100*n/len(sz):.2f}%)")
print("  examples of Uber 2+ within 300s:")
cand=sz[(sz>=2)&(span<=300)].index[:5]
for pid in cand:
    gg=u[u.in_response_to_tweet_id==pid].sort_values('ts')
    print(f"   parent {int(pid)}: "+" || ".join(t[:70] for t in gg.text))

# --- greeting-only first agent reply rate
GREET=re.compile(r'^\s*(hi|hey|hello|good (morning|evening|afternoon)|thanks|thank you|sorry)\b',re.I)
for B in ['Uber_Support','Delta']:
    b=df[(~df.inbound)&(df.author_id==B)].dropna(subset=['in_response_to_tweet_id'])
    b=b[b.in_response_to_tweet_id.isin(inb_ids)]
    first=b.sort_values('ts').groupby('in_response_to_tweet_id').first()
    short=first['text'].str.len()<60
    print(f"\n{B}: first-agent-reply <60 chars: {100*short.mean():.1f}%   starts w/ greeting word: {100*first['text'].str.contains(GREET).mean():.1f}%   greeting AND <60ch: {100*(short&first['text'].str.contains(GREET)).mean():.1f}%")
