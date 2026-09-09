import pandas as pd, numpy as np, re, sys
BR=['GWRHelp','VirginTrains','British_Airways','AmericanAir','Delta','SouthwestAir','hulu_support','Uber_Support','SpotifyCares','Tesco','AppleSupport','comcastcares','TMobileHelp']
df = pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound']=df['inbound'].astype(bool)
out = df[~df.inbound][['thread','author_id','text','created_at']].copy()
del df
out = out[out.author_id.isin(BR)]
print("outbound rows for selected brands:", len(out), flush=True)
out['created']=pd.to_datetime(out['created_at'], format='%a %b %d %H:%M:%S %z %Y', errors='coerce', utc=True)
out=out.sort_values('created')
first = out.groupby('thread', sort=False).head(1).copy()
print("first replies:", len(first), flush=True)
DM   = re.compile(r'(?:\bdm\b|direct message|private message|\bpm us\b|message us|send us a (?:message|note)|meet you there)', re.I)
ROUTE= re.compile(r'(?:visit|follow up|click|head (?:to|over)|check out|reach out|contact us|fill out|use|via|here)[^.!?]{0,40}https?://', re.I)
def norm(s):
    s = re.sub(r'https?://\S+','',str(s)); s = re.sub(r'@\w+','',s)
    s = re.sub(r'[\^\-~]\s?[A-Z]{2}\s*$','',s.strip()); s = re.sub(r'[^a-z ]',' ',s.lower())
    return re.sub(r'\s+',' ',s).strip()
first['n']=first['text'].map(norm)
first['pref']=first['n'].str.split().str[:8].str.join(' ')
first['defl']=first['text'].str.contains(DM)|first['text'].str.contains(ROUTE)
rows=[]
for b in BR:
    f=first[first.author_id==b]
    if len(f)<200: continue
    vc=f['pref'].value_counts()
    rows.append(dict(brand=b, first_replies=len(f),
        defl_first_pct=round(100*f['defl'].mean(),1),
        dup8_pct=round(100*(vc[vc>1].sum()/len(f)),1),
        top1_pct=round(100*vc.iloc[0]/len(f),1),
        top20_pct=round(100*vc.head(20).sum()/len(f),1)))
r=pd.DataFrame(rows).sort_values('defl_first_pct')
print(r.to_string(index=False), flush=True)
r.to_csv('data/raw/brand_axis.csv', index=False)
