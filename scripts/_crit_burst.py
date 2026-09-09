import pandas as pd, numpy as np, re, collections
df = pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound']=df['inbound'].astype(bool)
df['in_response_to_tweet_id']=pd.to_numeric(df['in_response_to_tweet_id'],errors='coerce')
df['ts']=pd.to_datetime(df['created_at'],format='%a %b %d %H:%M:%S +0000 %Y',errors='coerce',utc=True)
print('ts parse fail:', df['ts'].isna().sum())

MARK = re.compile(r'(?<![\d/])(\d{1,2})\s?/\s?(\d{1,2})(?![\d/])')

for BRAND in ['Uber_Support','Delta','AmazonHelp','AppleSupport','British_Airways','SpotifyCares','TMobileHelp']:
    out = df[(~df.inbound)&(df.author_id==BRAND)].copy()
    if len(out)==0: print(BRAND,'MISSING'); continue
    # inbound parents answered by this brand
    g = out.dropna(subset=['in_response_to_tweet_id']).groupby('in_response_to_tweet_id')
    sizes = g.size()
    # restrict to parents that are inbound customer tweets
    inb_ids = set(df.loc[df.inbound,'tweet_id'])
    sizes = sizes[[i in inb_ids for i in sizes.index]]
    n=len(sizes)
    multi = (sizes>=2).mean()*100
    # marker share among agent tweets
    mk = out['text'].str.contains(MARK)
    print(f"\n=== {BRAND}: agent tweets={len(out):,} answered-customer-msgs={n:,}")
    print(f"  2+ agent tweets to same customer msg: {multi:.1f}%  max={sizes.max()}  mean={sizes.mean():.2f}")
    print(f"  share of agent tweets containing k/n-like marker (loose regex): {100*mk.mean():.1f}%")
    # tighter: marker at end of text
    mk2 = out['text'].str.contains(r'\b\d{1,2}\s?/\s?\d{1,2}\b\s*(?:[\^~*\-][A-Za-z]{1,4})?\s*$')
    print(f"  marker at END of tweet: {100*mk2.mean():.1f}%")
    # among multi-part bursts only
    big = set(sizes[sizes>=2].index)
    ob = out[out['in_response_to_tweet_id'].isin(big)]
    print(f"  among tweets in 2+ bursts ({len(ob):,}): end-marker {100*ob['text'].str.contains(r'\b\d{1,2}\s?/\s?\d{1,2}\b\s*(?:[\^~*\-][A-Za-z]{1,4})?\s*$').mean():.1f}%")
    # timestamp span & ordering disagreement
    disagree_ts=0; disagree_id=0; tot=0; spans=[]
    for pid, grp in ob.groupby('in_response_to_tweet_id'):
        m = grp['text'].str.extract(r'\b(\d{1,2})\s?/\s?(\d{1,2})\b\s*(?:[\^~*\-][A-Za-z]{1,4})?\s*$')
        spans.append((grp['ts'].max()-grp['ts'].min()).total_seconds())
        if m[0].notna().all() and len(grp)>1:
            tot+=1
            order_mark = list(np.argsort(m[0].astype(float).values, kind='stable'))
            order_ts = list(np.argsort(grp['ts'].values, kind='stable'))
            order_id = list(np.argsort(grp['tweet_id'].values, kind='stable'))
            if order_mark!=order_ts: disagree_ts+=1
            if order_mark!=order_id: disagree_id+=1
    if spans: print(f"  burst span sec: median={np.median(spans):.0f} p90={np.percentile(spans,90):.0f}")
    if tot: print(f"  bursts w/ full markers={tot}: ts-order WRONG {100*disagree_ts/tot:.1f}%  id-order WRONG {100*disagree_id/tot:.1f}%")
