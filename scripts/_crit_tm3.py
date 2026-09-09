import pandas as pd, numpy as np
df = pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound']=df['inbound'].astype(bool)
df['parent']=pd.to_numeric(df['in_response_to_tweet_id'],errors='coerce')
df['created']=pd.to_datetime(df['created_at'],format="%a %b %d %H:%M:%S %z %Y",utc=True,errors='coerce')
BRAND='AmericanAir'
owner = df.loc[~df.inbound].groupby('thread')['author_id'].first()
keep=set(owner[owner==BRAND].index)
b = df[df['thread'].isin(keep)].copy().sort_values(['thread','created'],kind='mergesort')

# replicate build_examples, tracking author identity
tot=0; merged_multi_author=0; reply_wrong_target=0; ctx_stranger=0
par = dict(zip(b['tweet_id'].astype('int64'), b['parent']))
auth = dict(zip(b['tweet_id'].astype('int64'), b['author_id']))
for tid,g in b.groupby('thread',sort=False):
    turns=[]
    for r in g.itertuples(index=False):
        if turns and turns[-1]['inbound']==bool(r.inbound):
            turns[-1]['authors'].add(r.author_id); turns[-1]['ids'].append(int(r.tweet_id))
        else:
            turns.append({'inbound':bool(r.inbound),'authors':{r.author_id},'ids':[int(r.tweet_id)]})
    for i,t in enumerate(turns):
        if not t['inbound']: continue
        if i+1>=len(turns) or turns[i+1]['inbound']: continue
        tot+=1
        if len(t['authors'])>1: merged_multi_author+=1
        # does the brand reply actually reply to one of this customer turn's tweets?
        rp = turns[i+1]['ids']
        parents = {par.get(x) for x in rp}
        if not (parents & set(t['ids'])):
            reply_wrong_target+=1
        # context contains a customer other than this one's author(s)
        prior_auth=set()
        for u in turns[:i]:
            if u['inbound']: prior_auth |= u['authors']
        if prior_auth - t['authors']: ctx_stranger+=1
print(f"{BRAND} examples built (current code): {tot:,}")
print(f"  customer turn is a MERGE of >1 distinct customer: {merged_multi_author:,} ({100*merged_multi_author/tot:.2f}%)")
print(f"  brand reply does NOT reply to that customer's tweet: {reply_wrong_target:,} ({100*reply_wrong_target/tot:.2f}%)")
print(f"  context contains a DIFFERENT customer's messages:   {ctx_stranger:,} ({100*ctx_stranger/tot:.2f}%)")
