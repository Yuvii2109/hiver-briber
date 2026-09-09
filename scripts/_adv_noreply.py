import pandas as pd, numpy as np
df = pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound'] = df['inbound'].astype(str).isin(['True','true','1'])

# brand threads: threads containing >=1 outbound tweet by BRAND
for BRAND in ['Uber_Support','Delta','AmazonHelp']:
    bt = df[(~df['inbound']) & (df['author_id']==BRAND)]['thread'].unique()
    sub = df[df['thread'].isin(bt)].copy()
    inb = sub[sub['inbound']]
    out_brand = sub[(~sub['inbound']) & (sub['author_id']==BRAND)]

    # replied set: inbound tweet ids that a BRAND outbound tweet points at via in_response_to
    parents = set(out_brand['in_response_to_tweet_id'].dropna().astype('int64'))
    inb_ids = inb['tweet_id'].astype('int64')
    replied = inb_ids.isin(parents)

    # also honour response_tweet_id field on the inbound row (fan-out list)
    brand_ids = set(out_brand['tweet_id'].astype('int64'))
    def rt_hits_brand(v):
        if pd.isna(v): return False
        for p in str(v).split(','):
            p=p.strip()
            if p and p.isdigit() and int(p) in brand_ids: return True
        return False
    rt = inb['response_tweet_id'].map(rt_hits_brand)
    replied_any = replied | rt.values

    # opener = inbound whose in_response_to is NaN or points to a tweet not in dataset
    all_ids = set(df['tweet_id'].astype('int64'))
    def is_opener(v):
        if pd.isna(v): return True
        return int(v) not in all_ids
    opener = inb['in_response_to_tweet_id'].map(is_opener).values

    n=len(inb)
    print(f"=== {BRAND} ===  inbound in brand threads: {n}")
    print(f"  no-reply overall            : {(~replied_any).mean():.1%}  ({(~replied_any).sum()})")
    print(f"  openers                     : {opener.mean():.1%} of inbound ({opener.sum()})")
    print(f"  no-reply | OPENER           : {(~replied_any[opener]).mean():.1%}  ({(~replied_any[opener]).sum()})")
    print(f"  no-reply | FOLLOW-UP        : {(~replied_any[~opener]).mean():.1%}  ({(~replied_any[~opener]).sum()})")
    # is the no-reply inbound the LAST message in its thread (by created_at)?
    sub['ts']=pd.to_datetime(sub['created_at'], format='%a %b %d %H:%M:%S %z %Y', errors='coerce')
    last = sub.sort_values('ts').groupby('thread')['tweet_id'].last()
    lastset=set(last.astype('int64'))
    is_last = inb_ids.isin(lastset).values
    nr = (~replied_any).values
    print(f"  of no-reply inbound, share that are the LAST tweet in thread: {is_last[nr].mean():.1%}")
    print(f"  of no-reply OPENERS, count: {(nr & opener).sum()}  ({(nr&opener).sum()/n:.1%} of all inbound)")
