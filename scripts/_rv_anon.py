import pandas as pd, numpy as np, re, sys, collections
P=lambda *a:(print(*a),sys.stdout.flush())
df=pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
brand_of=df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s:s.iloc[0])
MENT=re.compile(r'@(\w+)')
DIG=re.compile(r'@(\d+)')
TCO=re.compile(r'https?://t\.co/\S+')
URL=re.compile(r'https?://\S+')
for BRAND in ['Uber_Support','AmazonHelp','Delta']:
    th=set(brand_of[brand_of==BRAND].index); d=df[df.thread.isin(th)].copy()
    inb=d[d.inbound]; out=d[~d.inbound]
    txt=inb['text'].astype(str)
    has_dig=txt.str.contains(DIG)
    P(f"\n===== {BRAND}: inbound={len(inb):,} outbound={len(out):,} threads={len(th):,}")
    P(f" inbound containing @<digits>: {has_dig.mean()*100:.1f}%")
    # is the @digits the author's OWN id (self-mention)?
    own=0; other=0; n=0
    for a,t in zip(inb['author_id'].astype(str), txt):
        ds=DIG.findall(t)
        if not ds: continue
        n+=1
        if a in ds: own+=1
        else: other+=1
    P(f"  of those {n:,}: contains OWN author_id = {own:,} ({100*own/max(n,1):.1f}%), only-other-ids = {other:,} ({100*other/max(n,1):.1f}%)")
    # repeat customers
    cust=inb.groupby('author_id')['thread'].nunique()
    P(f" distinct customers={len(cust):,}; with >1 thread={int((cust>1).sum()):,} ({100*(cust>1).mean():.1f}%); msgs by repeat custs={100*inb['author_id'].map(cust).gt(1).mean():.1f}%")
    # url stats
    P(f" inbound with URL: {txt.str.contains(URL).mean()*100:.1f}%  (t.co: {txt.str.contains(TCO).mean()*100:.1f}%)")
    ot=out['text'].astype(str)
    P(f" OUTBOUND(agent) with URL: {ot.str.contains(URL).mean()*100:.1f}%  (t.co: {ot.str.contains(TCO).mean()*100:.1f}%)")
    # replies that are essentially a link
    strip=lambda s: re.sub(r'\s+',' ', MENT.sub(' ', URL.sub(' ', s))).strip()
    os_=ot.map(strip)
    P(f" OUTBOUND after strip: <3 chars {100*(os_.str.len()<3).mean():.2f}%  <=20 chars {100*(os_.str.len()<=20).mean():.2f}%")
    # link-bearing replies: how much text besides the link
    lb=ot[ot.str.contains(URL)]
    lbs=lb.map(strip)
    P(f"  link-bearing replies n={len(lb):,}: median residual chars={int(lbs.str.len().median())}; <=20 chars {100*(lbs.str.len()<=20).mean():.1f}% ; <=40 {100*(lbs.str.len()<=40).mean():.1f}%")
    is_=txt.map(strip)
    P(f" INBOUND after strip: <3 chars {100*(is_.str.len()<3).mean():.2f}%  <=20 chars {100*(is_.str.len()<=20).mean():.2f}%")
    # first customer message only (what actually gets classified)
    d2=d.sort_values(['thread','created_at'])
    f=d2[d2.inbound].groupby('thread',as_index=False).first()
    ft=f['text'].astype(str); fs=ft.map(strip)
    P(f" FIRST inbound msg only (n={len(f):,}): @digits {100*ft.str.contains(DIG).mean():.1f}%, URL {100*ft.str.contains(URL).mean():.1f}%, <3ch after strip {100*(fs.str.len()<3).mean():.2f}%, <=20ch {100*(fs.str.len()<=20).mean():.2f}%")
