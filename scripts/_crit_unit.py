import pandas as pd, numpy as np
df = pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound']=df['inbound'].astype(bool)
BR='AmericanAir'
th = set(df.loc[(~df.inbound)&(df.author_id==BR),'thread'])
d = df[df.thread.isin(th)].copy()
d['ts'] = pd.to_datetime(d['created_at'], format='%a %b %d %H:%M:%S %z %Y', errors='coerce')
print("unparsed created_at:", int(d['ts'].isna().sum()))
d = d.sort_values(['thread','ts','tweet_id'])
inb = d[d.inbound]
print(f"threads={len(th):,}")
n_inb = inb.groupby('thread').size()
print(f"TURN-LEVEL rows (every customer turn)      = {len(inb):,}")
print(f"OPENING-ONLY rows (1 per thread)           = {n_inb.index.nunique():,}")
print(f"ratio turn/opening = {len(inb)/n_inb.index.nunique():.2f}x")
print(f"threads with >=2 customer turns: {100*(n_inb>=2).mean():.1f}%  (they carry "
      f"{100*(n_inb[n_inb>=2].sum()/len(inb)):.1f}% of turn-level rows)")

# does the thread's FIRST message belong to the customer?
first_msg = d.groupby('thread').head(1)
print(f"threads whose earliest msg is inbound(customer): {100*first_msg.inbound.mean():.1f}%")

# brand reply that FOLLOWS the opening customer msg: how many consecutive brand tweets?
recs=[]
for t,g in d.groupby('thread'):
    inb_i = np.where(g.inbound.values)[0]
    if len(inb_i)==0: continue
    i0 = inb_i[0]
    rest = g.iloc[i0+1:]
    if len(rest)==0 or rest.inbound.values[0]:
        recs.append((t,0,0)); continue
    k=0
    for v in rest.inbound.values:
        if v: break
        k+=1
    recs.append((t,k,1))
r = pd.DataFrame(recs, columns=['thread','n_brand_tweets_in_first_reply','has_reply'])
print(f"\nthreads where opening customer msg gets NO brand reply before next customer msg: "
      f"{100*(1-r.has_reply.mean()):.1f}%  (no target -> must be excluded or handled)")
rr=r[r.has_reply==1]
print("brand tweets in that first reply block:")
print((rr.n_brand_tweets_in_first_reply.value_counts(normalize=True).head(5)*100).round(1).to_string())
print(f"first reply is SPLIT across >=2 brand tweets: {100*(rr.n_brand_tweets_in_first_reply>=2).mean():.1f}%")

# created_at tie rate within thread
ties = d.groupby(['thread','ts']).size()
print(f"\nmessages sharing an identical created_at within the same thread: {100*(ties[ties>1].sum()/len(d)):.1f}%")
