import pandas as pd, numpy as np, re
df = pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
df['created']=pd.to_datetime(df['created_at'], format='%a %b %d %H:%M:%S %z %Y', errors='coerce')
brand_of = df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s: s.iloc[0])
out = df[~df.inbound].copy().sort_values('created')
first = out.groupby('thread').head(1).copy()          # brand's FIRST reply in thread
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
for b in ['GWRHelp','VirginTrains','British_Airways','AmericanAir','Delta','SouthwestAir','hulu_support','Uber_Support','SpotifyCares','Tesco','AppleSupport','comcastcares','TMobileHelp','AmazonHelp']:
    f=first[first.author_id==b]
    if len(f)<200: continue
    vc=f['pref'].value_counts()
    rows.append(dict(brand=b, first_replies=len(f),
        pct_defl_first=round(100*f['defl'].mean(),1),
        pct_dup8=round(100*(vc[vc>1].sum()/len(f)),1),
        top1_pref_share=round(100*vc.iloc[0]/len(f),1),
        top20_share=round(100*vc.head(20).sum()/len(f),1)))
r=pd.DataFrame(rows)
r['esc_evaluable']=np.where((r.pct_defl_first>=8)&(r.pct_defl_first<=60),'YES','no')
r['gen_ok']=np.where(r.pct_dup8<=25,'YES','no')
print(r.sort_values('pct_defl_first').to_string(index=False))
