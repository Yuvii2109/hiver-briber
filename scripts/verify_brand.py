import pandas as pd, numpy as np, re
pd.set_option('display.width',200)
df = pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound']=df['inbound'].astype(bool)
df['created']=pd.to_datetime(df['created_at'], format='%a %b %d %H:%M:%S %z %Y', errors='coerce')

brand_of = df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s: s.iloc[0])

def show(brand, n=4, seed=7):
    th = brand_of[brand_of==brand].index
    rng=np.random.default_rng(seed)
    pick = rng.choice(th, size=n, replace=False)
    print(f"\n{'='*100}\n### {brand}   ({len(th):,} threads)\n{'='*100}")
    for t in pick:
        sub = df[df.thread==t].sort_values('created')
        print(f"--- thread {t} ({len(sub)} msgs) ---")
        for _,r in sub.iterrows():
            who = 'CUST ' if r.inbound else 'BRAND'
            txt = re.sub(r'\s+',' ', str(r.text))[:210]
            print(f"  {who}| {txt}")
        print()

for b in ['AmericanAir','Delta','GWRHelp']:
    show(b)
