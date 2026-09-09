import pandas as pd, re, numpy as np
df = pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
DM   = re.compile(r'(?:\bdm\b|direct message|private message|\bpm us\b|message us|send us a (?:message|note)|meet you there)', re.I)
ROUTE= re.compile(r'(?:visit|follow up|click|head (?:to|over)|check out|reach out|contact us|fill out|use|via|here)[^.!?]{0,40}https?://', re.I)
brand_of = df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s: s.iloc[0])
for B in ['Uber_Support','AmazonHelp','AppleSupport','SpotifyCares','Delta']:
    th = set(brand_of[brand_of==B].index)
    sub = df[df['thread'].isin(th)].copy()
    sub = sub.sort_values(['thread','created_at'])
    out = sub[~sub.inbound]
    first = out.groupby('thread').head(1)
    t = first['text'].fillna('')
    d1 = (t.str.contains(DM) | t.str.contains(ROUTE))
    anyd = out.assign(d=out['text'].fillna('').str.contains(DM)|out['text'].fillna('').str.contains(ROUTE)).groupby('thread')['d'].any()
    ntok = out.groupby('thread').size()
    print(f"{B:14s} threads={len(th):6d}  deflect_on_FIRST_reply={100*d1.mean():5.1f}%  deflect_anywhere={100*anyd.mean():5.1f}%  median_brand_turns={ntok.median():.0f}")
