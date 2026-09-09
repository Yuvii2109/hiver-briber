import pandas as pd, numpy as np, re, collections, sys, time
t0=time.time()
df=pd.read_pickle('data/raw/twcs_threaded.pkl')
print("loaded",len(df),time.time()-t0,flush=True)
df['inbound']=df['inbound'].astype(bool)
BRANDS=['Uber_Support','AmericanAir','Delta','AmazonHelp','AppleSupport','SpotifyCares','TMobileHelp','comcastcares','VirginTrains','GWRHelp','Tesco','hulu_support']
ob=df.loc[~df.inbound,['thread','author_id']]
brand_of=ob.groupby('thread')['author_id'].first()
df['brand']=df['thread'].map(brand_of)
d=df[df['brand'].isin(BRANDS)].sort_values(['thread','created_at'])
print("subset",len(d),time.time()-t0,flush=True)
rep=d[~d.inbound].groupby('thread',as_index=False).first()
cust=d[d.inbound].groupby('thread',as_index=False).first()
print("grouped",time.time()-t0,flush=True)

def norm(s):
    s=str(s).lower()
    s=re.sub(r'https?://\S+',' ',s); s=re.sub(r'@\w+',' ',s)
    s=re.sub(r'[\^~\-*]\s?[a-z]{2,3}\s*$','',s.strip())
    s=re.sub(r'\d+',' ',s); s=re.sub(r'[^a-z\s]',' ',s)
    return re.sub(r'\s+',' ',s).strip()
rep['n']=rep['text'].map(norm)
DEFL=re.compile(r'\b(dm|d\.m\.|direct message|private message|pm us|send us a (note|message|dm)|message us|email us|call us)\b',re.I)
rep['defl']=rep['text'].str.contains(DEFL)
def na(s):
    return any(ord(c)>127 and not(0x1F000<=ord(c)<=0x1FAFF or 0x2190<=ord(c)<=0x27BF or ord(c) in (0x2019,0x201C,0x201D,0x2018,0x2013,0x2014,0x2026)) for c in str(s))
cust['na']=cust['text'].map(na)
rows=[]
for B in BRANDS:
    r=rep[(rep.brand==B)&(rep['n'].str.split().str.len()>=3)]
    c=cust[cust.brand==B]
    cnt=collections.Counter(r['n'])
    rows.append(dict(brand=B,n=len(r),
        dup_pct=round(sum(v for v in cnt.values() if v>=2)/len(r)*100,1),
        top20_pct=round(sum(v for _,v in cnt.most_common(20))/len(r)*100,1),
        top1_pct=round(cnt.most_common(1)[0][1]/len(r)*100,1),
        defl_pct=round(rep[rep.brand==B]['defl'].mean()*100,1),
        cust_nonascii=round(c['na'].mean()*100,1),
        reply_words=round(r['n'].str.split().str.len().mean(),1)))
print(pd.DataFrame(rows).to_string(index=False),flush=True)
print("\n=== top 6 first-reply templates ===")
for B in ['Uber_Support','AmericanAir','Delta']:
    r=rep[(rep.brand==B)&(rep['n'].str.split().str.len()>=3)]
    print(f"\n--{B}--")
    for k,v in collections.Counter(r['n']).most_common(6):
        print(f"  {v:6d} ({100*v/len(r):4.1f}%) {k[:120]}")
print("DONE",time.time()-t0)
