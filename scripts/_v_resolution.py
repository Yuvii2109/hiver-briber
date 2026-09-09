import pandas as pd, numpy as np, re
df=pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
d=df.sort_values(['thread','created_at'])
DEFL=re.compile(r'(?:\bdm\b|direct message|private message|send us a (?:note|message|dm)|message us|follow up (?:here|with us)|contact us|reach out|email us|(?:visit|click|head (?:to|over)|fill out|complete)[^.!?]{0,40}https?://)',re.I)
ASK=re.compile(r'\?')
def strip(s):
    s=re.sub(r'https?://\S+','',str(s)); s=re.sub(r'@\w+','',s)
    s=re.sub(r'[\^\-~]\s?[A-Za-z]{2}\s*$','',s.strip()); return re.sub(r'\s+',' ',s).strip()
out=d[~d.inbound].copy()
out['core']=out['text'].map(strip); out['w']=out['core'].str.split().str.len()
out['defl']=out['text'].str.contains(DEFL); out['ask']=out['core'].str.contains(ASK)
out['subst']=(~out['defl'])&(~out['ask'])&(out['w']>=8)
brand_of=out.groupby('thread')['author_id'].first()
rows=[]
for b in ['Uber_Support','AppleSupport','SpotifyCares','AmazonHelp','Delta','AmericanAir','hulu_support','GWRHelp','TMobileHelp','comcastcares','British_Airways','Tesco','VirginTrains']:
    th=brand_of[brand_of==b].index
    g=out[out.thread.isin(set(th))]
    if len(th)<3000: continue
    per=g.groupby('thread').agg(any_subst=('subst','any'), n=('subst','size'))
    fr=g.groupby('thread').first()
    firstdefl=fr['defl']
    # of threads whose FIRST reply deflects, how many ever contain a substantive brand reply
    sub_pool=set(per[per.any_subst].index)
    dt=set(firstdefl[firstdefl].index)
    rows.append(dict(brand=b, threads=len(th),
        pct_msgs_subst=round(100*g['subst'].mean(),1),
        pct_threads_any_subst=round(100*per['any_subst'].mean(),1),
        pct_first_defl=round(100*firstdefl.mean(),1),
        rescue_rate=round(100*len(dt&sub_pool)/max(len(dt),1),1)))
print(pd.DataFrame(rows).sort_values('pct_threads_any_subst',ascending=False).to_string(index=False))
print("\nrescue_rate = of threads whose first brand reply is a deflection, % that later contain ANY substantive brand reply (i.e. resolution visible in public data)")
