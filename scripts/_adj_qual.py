import pandas as pd, numpy as np, re
df = pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound']=df['inbound'].astype(bool)
df['created']=pd.to_datetime(df['created_at'], format='%a %b %d %H:%M:%S %z %Y', errors='coerce')
brand_of = df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s: s.iloc[0])
rng=np.random.default_rng(11)
for b in ['Uber_Support','Delta']:
    th=brand_of[brand_of==b].index.values
    pick=rng.choice(th,size=10,replace=False)
    print(f"\n{'#'*90}\n## {b}\n{'#'*90}")
    for t in pick:
        sub=df[df.thread==t].sort_values('created')
        print(f"-- thread {t} ({len(sub)}) --")
        for _,r in sub.iterrows():
            print(("  C| " if r.inbound else "  B| ")+re.sub(r'\s+',' ',str(r.text))[:230])
