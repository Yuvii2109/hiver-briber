import csv, re, sys, collections
csv.field_size_limit(10**7)
BR={'Uber_Support','AppleSupport','SpotifyCares','AmazonHelp','Delta','AmericanAir','hulu_support','GWRHelp','British_Airways','TMobileHelp','comcastcares','Tesco','VirginTrains'}
roots=set()
with open('data/raw/twcs.csv',encoding='utf-8',newline='') as f:
    for r in csv.DictReader(f):
        if r['inbound']=='True' and not r['in_response_to_tweet_id']:
            roots.add(r['tweet_id'])
print(f"root inbound tweets: {len(roots):,}",flush=True)
def norm(s):
    s=s.lower(); s=re.sub(r'https?://\S+',' <url> ',s); s=re.sub(r'@\w+',' ',s)
    s=re.sub(r'[\^~\-]\s?[a-z]{2}\s*$','',s.strip()); s=re.sub(r'\d+',' ',s)
    s=re.sub(r'[^a-z<>\s]',' ',s); return re.sub(r'\s+',' ',s).strip()
DEFL=re.compile(r'(?:\bdm\b|direct message|private message|send us a (?:note|message|dm)|message us|follow up (?:here|with us)|contact us|reach out|email us|(?:visit|click|head (?:to|over)|fill out|complete)[^.!?]{0,40}https?://)',re.I)
pre=collections.defaultdict(collections.Counter); n=collections.Counter(); dfl=collections.Counter()
with open('data/raw/twcs.csv',encoding='utf-8',newline='') as f:
    for r in csv.DictReader(f):
        if r['inbound']=='True': continue
        a=r['author_id']
        if a not in BR: continue
        if r['in_response_to_tweet_id'] not in roots: continue
        t=r['text']; nn=norm(t)
        if len(nn.split())<3: continue
        n[a]+=1; pre[a][' '.join(nn.split()[:12])]+=1
        if DEFL.search(t): dfl[a]+=1
print(f"\n{'brand':<17}{'firstReplies':>13}{'neardup12%':>12}{'top20%':>8}{'top1%':>7}{'deflect%':>9}",flush=True)
rows=[]
for b in n:
    if n[b]<2000: continue
    c=pre[b]; tot=n[b]
    nd=100*sum(v for v in c.values() if v>=5)/tot
    rows.append((nd,b,tot,100*sum(v for _,v in c.most_common(20))/tot,100*c.most_common(1)[0][1]/tot,100*dfl[b]/tot))
for nd,b,tot,t20,t1,de in sorted(rows,reverse=True):
    print(f"{b:<17}{tot:>13,}{nd:>12.1f}{t20:>8.1f}{t1:>7.2f}{de:>9.1f}",flush=True)
print("\nUber top-6 templates:",flush=True)
for k,v in pre['Uber_Support'].most_common(6): print(f"  {100*v/n['Uber_Support']:5.2f}%  {k}",flush=True)
print("\nAmazonHelp top-6 templates:",flush=True)
for k,v in pre['AmazonHelp'].most_common(6): print(f"  {100*v/n['AmazonHelp']:5.2f}%  {k}",flush=True)
