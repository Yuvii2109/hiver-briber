import pandas as pd, numpy as np, re, collections
df=pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
brand_of=df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s:s.iloc[0])
d=df.sort_values(['thread','created_at'])

def norm(s):
    s=str(s).lower()
    s=re.sub(r'https?://\S+',' ',s); s=re.sub(r'@\w+',' ',s)
    s=re.sub(r'[\^~\-*]\s?[a-z]{2,3}\s*$','',s.strip())   # agent initials sig
    s=re.sub(r'\d+',' ',s); s=re.sub(r'[^a-z\s]',' ',s)
    return re.sub(r'\s+',' ',s).strip()

DEFL=re.compile(r'\b(dm|d\.m\.|direct message|private message|pm us|send us a (note|message|dm)|message us|email us|call us|follow (us )?(back|and dm))\b',re.I)

rows=[]
for BRAND in ['Uber_Support','AmericanAir','Delta','AmazonHelp','AppleSupport','SpotifyCares','TMobileHelp','comcastcares','VirginTrains','GWRHelp','Tesco','hulu_support']:
    th=set(brand_of[brand_of==BRAND].index)
    sub=d[d.thread.isin(th)]
    rep=sub[~sub.inbound].groupby('thread',as_index=False).first()
    cust=sub[sub.inbound].groupby('thread',as_index=False).first()
    rep['n']=rep['text'].map(norm)
    r=rep[rep['n'].str.split().str.len()>=3]
    cnt=collections.Counter(r['n'])
    dup=sum(c for k,c in cnt.items() if c>=2)/len(r)*100
    top20=sum(c for k,c in cnt.most_common(20))/len(r)*100
    top1=cnt.most_common(1)[0][1]/len(r)*100
    defl=rep['text'].str.contains(DEFL).mean()*100
    nonascii=cust['text'].map(lambda s: any(ord(ch)>127 and not (0x1F000<=ord(ch)<=0x1FAFF or 0x2190<=ord(ch)<=0x27BF) for ch in str(s))).mean()*100
    meanlen=r['n'].str.split().str.len().mean()
    rows.append(dict(brand=BRAND,firstreplies=len(r),exact_dup_pct=round(dup,1),top20_pct=round(top20,1),
                     top1_pct=round(top1,1),defl_pct=round(defl,1),cust_nonascii_pct=round(nonascii,1),mean_reply_words=round(meanlen,1)))
print(pd.DataFrame(rows).to_string(index=False))
