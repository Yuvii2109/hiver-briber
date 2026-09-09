import pandas as pd, numpy as np, re
df = pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
brand_of = df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s: s.iloc[0])
out = df[~df.inbound].copy()
t = out['text'].fillna('')

DM   = re.compile(r'(?:\bdm\b|direct message|private message|\bpm us\b|message us|send us a (?:message|note)|meet you there)', re.I)
ROUTE= re.compile(r'(?:visit|follow up|click|head (?:to|over)|check out|reach out|contact us|fill out|use|via|here)[^.!?]{0,40}https?://', re.I)
URL  = re.compile(r'https?://')
# strip the trailing agent signature (^AB / -AB) and mentions, then measure real content
def strip(s):
    s = re.sub(r'https?://\S+','',s); s = re.sub(r'@\w+','',s)
    s = re.sub(r'[\^\-~]\s?[A-Z]{2}\s*$','',s.strip())
    return re.sub(r'\s+',' ',s).strip()
core = t.map(strip)
out['dm']      = t.str.contains(DM)
out['route']   = t.str.contains(ROUTE)
out['hasurl']  = t.str.contains(URL)
out['deflect'] = out['dm'] | out['route']
out['words']   = core.str.split().str.len()
# non-ascii ratio -> proxy for non-English
out['nonascii']= t.map(lambda s: sum(ord(c)>127 and not (0x1F300<=ord(c)<=0x1FAFF) and ord(c) not in (0x2019,0x201C,0x201D,0x2018,0x2026,0x2014,0x2013) for c in s)/max(len(s),1))

g = out.groupby('thread')
agg = pd.DataFrame({'deflect':g['deflect'].any(),'hasurl':g['hasurl'].any(),'words':g['words'].mean()})
rows=[]
for b in out['author_id'].value_counts().head(18).index:
    th = brand_of[brand_of==b].index; a = agg.loc[agg.index.intersection(th)]
    ob = out[out.author_id==b]
    rows.append(dict(brand=b, threads=len(th),
        pct_deflect=round(100*a['deflect'].mean(),1),
        pct_url=round(100*a['hasurl'].mean(),1),
        med_reply_words=round(float(ob['words'].median()),1),
        pct_nonEN=round(100*float((ob['nonascii']>0.10).mean()),1)))
r=pd.DataFrame(rows).sort_values('pct_deflect')
print("=== REFINED deflection (DM-language OR link-routing) ===")
print(r.to_string(index=False))
