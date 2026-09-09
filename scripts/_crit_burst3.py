import pandas as pd, numpy as np, re
df = pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound']=df['inbound'].astype(bool)
df['in_response_to_tweet_id']=pd.to_numeric(df['in_response_to_tweet_id'],errors='coerce')
df['ts']=pd.to_datetime(df['created_at'],format='%a %b %d %H:%M:%S +0000 %Y',utc=True)
END=r'\b(\d{1,2})\s?/\s?(\d{1,2})\b\s*(?:[\^~*\-][A-Za-z]{1,4})?\s*$'
for B in ['Delta','AmazonHelp','British_Airways']:
    d=df[(~df.inbound)&(df.author_id==B)].dropna(subset=['in_response_to_tweet_id'])
    sz=d.groupby('in_response_to_tweet_id').size()
    big=set(sz[sz>=2].index)
    d=d[d.in_response_to_tweet_id.isin(big)].copy()
    m=d['text'].str.extract(END)
    d['k']=pd.to_numeric(m[0],errors='coerce')
    ok=asc=desc=tsn=tsdesc=0
    for pid,g in d.groupby('in_response_to_tweet_id'):
        if g['k'].isna().any() or len(g)<2 or g['k'].nunique()!=len(g): continue
        ok+=1
        tgt=list(g.sort_values('k').tweet_id)
        if list(g.sort_values('tweet_id').tweet_id)==tgt: asc+=1
        if list(g.sort_values('tweet_id',ascending=False).tweet_id)==tgt: desc+=1
        if list(g.sort_values(['ts','tweet_id']).tweet_id)==tgt: tsn+=1
        if list(g.sort_values(['ts'],kind='stable').sort_values('ts',kind='stable').tweet_id)==tgt: pass
        if list(g.sort_values(['ts']).sort_values('ts',kind='stable').tweet_id)==tgt: pass
        if list(g.assign(_n=-g.tweet_id).sort_values(['ts','_n']).tweet_id)==tgt: tsdesc+=1
    print(f"{B}: marked bursts={ok}  correct order by: tweet_id ASC {100*asc/ok:.1f}% | tweet_id DESC {100*desc/ok:.1f}% | (ts,id asc) {100*tsn/ok:.1f}% | (ts, id DESC) {100*tsdesc/ok:.1f}%")
