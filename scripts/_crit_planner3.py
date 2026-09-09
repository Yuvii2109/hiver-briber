import pandas as pd, re, collections
df=pd.read_csv('data/raw/twcs.csv',usecols=['author_id','inbound','text'],dtype={'text':str})
t=df[df.author_id=='Uber_Support'].text.fillna('')
links=[u for s in t for u in re.findall(r'https://t\.co/\w+',s)]
c=collections.Counter(links)
print('link tokens:',len(links),'distinct:',len(c))
tot=sum(c.values())
cum=0
for i,(u,n) in enumerate(c.most_common(10)):
    cum+=n; print('  %-26s %6d  cum %.1f%%'%(u,n,100*cum/tot))
top5=sum(n for _,n in c.most_common(5)); print('top5 share: %.1f%%'%(100*top5/tot))
