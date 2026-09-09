import pandas as pd, numpy as np, re, sys, collections
P=lambda *a:(print(*a),sys.stdout.flush())
df=pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
brand_of=df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s:s.iloc[0])
DIG=re.compile(r'@(\d+)')
for BRAND in ['Uber_Support','AmazonHelp','Delta']:
    th=set(brand_of[brand_of==BRAND].index); d=df[df.thread.isin(th)]
    inb=d[d.inbound]
    c=collections.Counter(); per_thread=collections.defaultdict(set)
    for t,thr in zip(inb['text'].astype(str), inb['thread']):
        for m in set(DIG.findall(t)):
            c[m]+=1; per_thread[m].add(thr)
    tot=sum(c.values())
    P(f"\n=== {BRAND}: {len(c):,} distinct mentioned-ids, {tot:,} mention instances in inbound")
    P("  top 10 mentioned ids (count, #threads, share of all mention instances):")
    for mid,n in c.most_common(10):
        P(f"    @{mid}: {n:,}  threads={len(per_thread[mid]):,}  {100*n/tot:.1f}% of mentions")
    top1=c.most_common(1)[0]
    P(f"  top-1 id covers {100*len(per_thread[top1[0]])/inb['thread'].nunique():.1f}% of threads")
    # how many mentioned-ids appear in >1 thread at all?
    multi=sum(1 for m in per_thread if len(per_thread[m])>1)
    inmulti=sum(c[m] for m in per_thread if len(per_thread[m])>1)
    P(f"  mentioned-ids appearing in >1 thread: {multi:,}/{len(c):,} ({100*multi/len(c):.1f}%), covering {100*inmulti/tot:.1f}% of mention instances")
    # excluding top-1
    rest={m:v for m,v in per_thread.items() if m!=top1[0]}
    multi2=sum(1 for m in rest if len(rest[m])>1)
    inm2=sum(c[m] for m in rest if len(rest[m])>1); tot2=tot-top1[1]
    P(f"  EXCLUDING top-1: >1-thread ids {multi2:,}/{len(rest):,} ({100*multi2/len(rest):.1f}%), {100*inm2/max(tot2,1):.1f}% of remaining mentions")
    # sample messages containing top-1
    ex=[t for t in inb['text'].astype(str) if '@'+top1[0] in t][:5]
    for e in ex: P("    EX:", e[:150].replace('\n',' '))
