import pandas as pd, numpy as np, re, sys
P='C:/Users/Dell/dev/hiver-briber/data/raw/twcs_threaded.pkl'
df = pd.read_pickle(P)
df['inbound']=df['inbound'].astype(bool)
df['created']=pd.to_datetime(df['created_at'], format='%a %b %d %H:%M:%S %z %Y', errors='coerce')
brand_of = df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s: s.iloc[0])

DM   = re.compile(r'(?:\bdm\b|\bdms\b|direct message|private message|\bpm us\b|message us|send us a (?:message|note|dm)|meet you (?:there|here)|follow (?:and|us and) )', re.I)
ROUTE= re.compile(r'(?:visit|follow up|click|head (?:to|over)|check out|reach out|contact us|fill out|report it|submit)[^.!?]{0,45}https?://', re.I)
ASK  = re.compile(r'(?:can you (?:please )?(?:send|share|provide|dm)|please (?:send|share|provide)|what(?:\'s| is) your|which (?:email|account)|email address (?:associated|linked|you))', re.I)

def strip(s):
    s = re.sub(r'https?://\S+','',s); s = re.sub(r'@\w+','',s)
    s = re.sub(r'[\^\-~]\s?[A-Za-z]{2,3}\s*$','',s.strip())
    return re.sub(r'\s+',' ',s).strip()

BRANDS = ['Uber_Support','AmazonHelp','hulu_support','GWRHelp','VirginTrains','SpotifyCares','Delta','AmericanAir','Tesco','AppleSupport']
rows=[]
for b in BRANDS:
    th = set(brand_of[brand_of==b].index)
    sub = df[df['thread'].isin(th)].sort_values(['thread','created'])
    out = sub[~sub.inbound].copy()
    t = out['text'].fillna('')
    out['dm']=t.str.contains(DM); out['route']=t.str.contains(ROUTE); out['ask']=t.str.contains(ASK)
    out['defl']= out['dm']|out['route']
    out['words']=t.map(strip).str.split().str.len()
    # last brand turn per thread
    last = out.groupby('thread').tail(1)
    # grounding pairs: inbound msg immediately followed (in time) by a brand reply in same thread
    sub2 = sub.copy(); sub2['nxt_in']=sub2.groupby('thread')['inbound'].shift(-1)
    sub2['nxt_txt']=sub2.groupby('thread')['text'].shift(-1)
    pairs = sub2[(sub2.inbound)&(sub2['nxt_in']==False)].copy()
    pt = pairs['nxt_txt'].fillna('')
    pairs['defl']= pt.str.contains(DM)|pt.str.contains(ROUTE)
    pairs['ask'] = pt.str.contains(ASK)
    pairs['words']=pt.map(strip).str.split().str.len()
    rows.append(dict(brand=b, threads=len(th),
      pct_thr_any_defl=round(100*out.groupby('thread')['defl'].any().mean(),1),
      pct_thr_LAST_defl=round(100*last['defl'].mean(),1),
      pct_pairs_defl=round(100*pairs['defl'].mean(),1),
      pct_pairs_defl_or_ask=round(100*(pairs['defl']|pairs['ask']).mean(),1),
      n_pairs=len(pairs), n_pairs_clean=int((~(pairs['defl']|pairs['ask'])).sum()),
      med_reply_words=float(pairs['words'].median()),
      med_clean_words=float(pairs.loc[~(pairs['defl']|pairs['ask']),'words'].median())))
r=pd.DataFrame(rows).sort_values('pct_pairs_defl')
print(r.to_string(index=False))
