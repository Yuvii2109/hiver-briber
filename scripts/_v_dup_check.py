import pandas as pd, numpy as np, re, collections
df=pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
brand_of=df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s:s.iloc[0])
d=df.sort_values(['thread','created_at'])
def norm(s):
    s=str(s).lower(); s=re.sub(r'https?://\S+',' <url> ',s); s=re.sub(r'@\w+',' ',s)
    s=re.sub(r'[\^~\-]\s?[a-z]{2}\s*$','',s.strip()); s=re.sub(r'\d+',' ',s)
    s=re.sub(r'[^a-z<>\s]',' ',s); return re.sub(r'\s+',' ',s).strip()
DEFL=re.compile(r'(?:\bdm\b|direct message|private message|send us a (?:note|message|dm)|message us|follow up (?:here|with us)|contact us|reach out|email us|(?:visit|click|head (?:to|over)|fill out|complete)[^.!?]{0,40}https?://)',re.I)
first_in = d[d.inbound].groupby('thread',as_index=False).first()[['thread','text']]
first_out= d[~d.inbound].groupby('thread',as_index=False).first()[['thread','text','author_id']]
m=first_in.merge(first_out,on='thread',suffixes=('_q','_a'))
m['n']=m['text_a'].map(norm)
m['p12']=m['n'].str.split().str[:12].str.join(' ')
m['defl']=m['text_a'].str.contains(DEFL)
rows=[]
for b,g in m.groupby('author_id'):
    if len(g)<3000: continue
    c=g['p12'].value_counts()
    dupkeys=set(c[c>=5].index)
    neardup=100*g['p12'].isin(dupkeys).mean()
    top20=100*c.head(20).sum()/len(g)
    top1=100*c.iloc[0]/len(g)
    exactfull=100*(g['n'].map(g['n'].value_counts())>=5).mean()
    rows.append(dict(brand=b,n=len(g),neardup12=round(neardup,1),top20=round(top20,1),top1=round(top1,1),
                     fulldup=round(exactfull,1),pct_defl=round(100*g['defl'].mean(),1)))
r=pd.DataFrame(rows).sort_values('neardup12',ascending=False)
print("=== FIRST-REPLY template collapse, per brand (>=3000 threads) ===")
print(r.to_string(index=False))
u=m[m.author_id=='Uber_Support']
print("\nUber top-8 12-word prefixes:")
for k,v in u['p12'].value_counts().head(8).items(): print(f"  {100*v/len(u):5.2f}%  {k}")
