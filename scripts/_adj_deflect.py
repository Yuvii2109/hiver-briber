import pandas as pd, numpy as np, re
pd.set_option('display.width',250)
df = pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound']=df['inbound'].astype(bool)
brand_of = df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s: s.iloc[0])

# --- NARROW deflection: explicit channel-switch only. No "contains a link" catch-all.
DM = re.compile(r"(dm us|send (us )?a (dm|direct message|private message|note)|send us a message|"
                r"\bdm\b (us|me|your|the)|via dm|in a dm|by dm|drop us a (dm|note|message)|"
                r"direct message|private message|shoot us a (dm|message)|"
                r"here to help[^.!?]{0,40}(link|note|team can connect)|"
                r"so (our|the) team can connect|meet you (there|in the dms)|"
                r"follow (us )?(and|so) (we|our team) can (dm|message)|"
                r"help\.uber\.com|t\.uber\.com/[a-z0-9]+)", re.I)
def strip(s):
    s = re.sub(r'https?://\S+',' ',str(s)); s = re.sub(r'@\w+',' ',s)
    s = re.sub(r'[\^\-~]\s?[A-Za-z]{2,3}\s*$','',s.strip())
    return re.sub(r'[^a-z0-9 ]',' ',s.lower())

BR=['Uber_Support','AppleSupport','Delta','AmazonHelp','AmericanAir','British_Airways','VirginTrains','GWRHelp','hulu_support','SpotifyCares','Tesco','comcastcares','TMobileHelp','XboxSupport']
rows=[]
for b in BR:
    th=set(brand_of[brand_of==b].index)
    out=df[(df.thread.isin(th))&(~df.inbound)].copy()
    t=out['text'].fillna('')
    out['defl']=t.str.contains(DM)
    norm=t.map(strip).str.replace(r'\s+',' ',regex=True).str.strip()
    out['norm']=norm
    vc=norm.value_counts()
    tpl10 = norm.map(vc).ge(10)
    thr=out.groupby('thread')['defl']
    rows.append(dict(brand=b,n_agent=len(out),
      pct_msg_defl=round(100*out['defl'].mean(),1),
      pct_thr_ALL_defl=round(100*thr.all().mean(),1),
      pct_thr_ANY_defl=round(100*thr.any().mean(),1),
      uniq_ratio=round(norm.nunique()/len(out),3),
      pct_tpl10=round(100*tpl10.mean(),1),
      med_words=int(norm.str.split().str.len().median())))
r=pd.DataFrame(rows).sort_values('pct_msg_defl')
print(r.to_string(index=False))
print()
# top templates for Uber + Delta
for b in ['Uber_Support','Delta','AmazonHelp']:
    th=set(brand_of[brand_of==b].index)
    out=df[(df.thread.isin(th))&(~df.inbound)]
    n=out['text'].fillna('').map(strip).str.replace(r'\s+',' ',regex=True).str.strip()
    print(f"### {b} top6 normalized replies (n={len(out)})")
    for s,c in n.value_counts().head(6).items(): print(f"  {c:6d}  {s[:120]}")
    print()
