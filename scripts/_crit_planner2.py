import pandas as pd, re
df = pd.read_csv('data/raw/twcs.csv', usecols=['tweet_id','author_id','inbound','text','in_response_to_tweet_id'], dtype={'text':str})
b='Uber_Support'
out=df[df.author_id==b]; inb=df[df.inbound==True][['tweet_id','text']].rename(columns={'tweet_id':'pid','text':'ctext'})
m=out.merge(inb,left_on='in_response_to_tweet_id',right_on='pid')
t=m.text.fillna(''); c=m.ctext.fillna('')
url=t.str.contains(r'https?://t\.co')
dm=t.str.contains(r'(?i)(\bDM\b|direct message|private message)')
def pct(x): return 100*x.mean()
print('n=',len(m))
print('reply has link  : %.1f%%'%pct(url))
print('reply says DM   : %.1f%%'%pct(dm))
print('link or DM      : %.1f%%'%pct(url|dm))
print('neither         : %.1f%%'%pct(~(url|dm)))
oth=t[~(url|dm)]
print('\n--- 20 replies with NO deflection (the "auto-handleable" pool) ---')
for s in oth.sample(20,random_state=1): print(' *',s[:170].replace('\n',' '))
print('\n=== what customers actually put in public messages (n=%d) ==='%len(c))
ent={'email':r'[\w.+-]+@[\w-]+\.\w+','currency':r'[$£€]\s?\d|\b\d+\s?(usd|dollars|rs|inr)\b','date-ish':r'(?i)\b(yesterday|today|last night|\d{1,2}/\d{1,2}|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b','trip/order id':r'\b[0-9a-f]{8}-[0-9a-f]{4}\b|\b[A-Z0-9]{8,}\b','phone':r'\b\d{10}\b'}
for k,p in ent.items(): print('  %-14s %5.1f%%'%(k,pct(c.str.contains(p,case=False))))
