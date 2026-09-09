import pandas as pd, numpy as np, re
df = pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound'] = df['inbound'].astype(str).isin(['True','true','1'])
df['ts']=pd.to_datetime(df['created_at'], format='%a %b %d %H:%M:%S %z %Y', errors='coerce')
all_ids=set(df['tweet_id'].astype('int64'))
DM=re.compile(r'\b(dm|direct message|pm us|send us a (dm|message)|private message)\b', re.I)

for BRAND in ['Uber_Support','Delta','AmazonHelp']:
    bt=df[(~df['inbound'])&(df['author_id']==BRAND)]['thread'].unique()
    sub=df[df['thread'].isin(bt)].copy().sort_values('ts')
    inb=sub[sub['inbound']].copy()
    ob=sub[(~sub['inbound'])&(sub['author_id']==BRAND)].copy()
    parents=set(ob['in_response_to_tweet_id'].dropna().astype('int64'))
    brand_ids=set(ob['tweet_id'].astype('int64'))
    def rt_hit(v):
        if pd.isna(v): return False
        return any(p.strip().isdigit() and int(p.strip()) in brand_ids for p in str(v).split(','))
    replied=inb['tweet_id'].astype('int64').isin(parents).values | inb['response_tweet_id'].map(rt_hit).values
    inb['replied']=replied
    # last brand reply time per thread
    lastbrand=ob.groupby('thread')['ts'].max()
    inb['last_brand_ts']=inb['thread'].map(lastbrand)
    nr=inb[~inb['replied']].copy()
    # covered-by-sibling: a brand reply exists LATER in the same thread
    covered=(nr['last_brand_ts']>nr['ts'])
    # thread contained DM deflection
    dmthreads=set(ob[ob['text'].str.contains(DM,na=False)]['thread'])
    indm=nr['thread'].isin(dmthreads)
    # customer burst: another inbound tweet by same author in same thread within 5 min after
    print(f"=== {BRAND} === no-reply inbound n={len(nr)} ({len(nr)/len(inb):.1%} of inbound)")
    print(f"   brand replied LATER in same thread (covered by sibling / fan-out): {covered.mean():.1%}")
    print(f"   thread contained a DM deflection                                : {indm.mean():.1%}")
    print(f"   covered-by-sibling OR DM-deflected                              : {(covered|indm).mean():.1%}")
    print(f"   neither (candidate 'genuine no action')                         : {(~(covered|indm)).mean():.1%}  -> {(~(covered|indm)).sum()} = {(~(covered|indm)).sum()/len(inb):.1%} of inbound")
    # short 'thanks' style
    THX=re.compile(r'^\W*(thanks|thank you|thx|ty|cheers|ok|okay|got it|great|awesome|nice|👍|🙏)', re.I)
    thx=nr['text'].str.contains(THX,na=False)
    print(f"   starts with thanks/ack token                                    : {thx.mean():.1%}")
