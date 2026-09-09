# -*- coding: utf-8 -*-
import pandas as pd, numpy as np, re, sys, collections, io
sys.stdout=io.TextIOWrapper(sys.stdout.buffer,encoding='utf-8',errors='replace')
P=lambda *a:(print(*a),sys.stdout.flush())
df=pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
brand_of=df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s:s.iloc[0])
STOP=set('''Hi Hey Hello Sorry Thanks Thank We If Please Send Can Could Would Team DM Our Your You This That The It Is Are Not No Yes Let Us Here There Have Has Had Will Should May Might Just Also Sure Happy Glad Apologies Oh Ok Okay Hope Feel Rest Support Help Trip Driver Account Payment Fare Ride App Email Reply Contact Kindly Follow For Stay Find Visit Connect Check Demand Keep Simply Get Supply Sign However But Uber Amazon Delta Please We'd We're I'm It's Don't Can't That's What When Where Why How Do Does Did Been Being More Most Some Any All One Two Prime Alexa Echo Kindle Fire'''.split())
VOC=re.compile(r'\b(?:Hi|Hey|Hello|Thanks|Thank you|Sorry(?:[^,.!?]{0,40})?|Apologies(?:[^,.!?]{0,30})?)[,! ]+\s*([A-Z][a-z]{2,12})\b')
TAIL=re.compile(r',\s*([A-Z][a-z]{2,12})\s*[!.]')
URL=re.compile(r'https?://\S+')
for BRAND in ['Uber_Support','AmazonHelp','Delta']:
    th=set(brand_of[brand_of==BRAND].index); d=df[df.thread.isin(th)]
    out=d[~d.inbound]['text'].astype(str)
    def nm(s):
        return [x for x in (VOC.findall(s)+TAIL.findall(s)) if x not in STOP]
    hit=out.map(lambda s: len(nm(s))>0)
    c=collections.Counter(x for s in out for x in nm(s))
    P(f"\n=== {BRAND} outbound n={len(out):,}")
    P(f"  replies with a vocative first-name: {hit.mean()*100:.2f}%  ({int(hit.sum()):,})")
    P("  top:", c.most_common(12))
    # link context
    lb=out[out.str.contains(URL)]
    ctx=collections.Counter()
    for s in lb:
        pre=s[:URL.search(s).start()][-45:].lower()
        ctx[re.sub(r'\s+',' ',pre).strip()[-32:]]+=1
    P(f"  link-bearing replies {len(lb):,} ({100*len(lb)/len(out):.1f}%); top pre-link context:")
    for k,v in ctx.most_common(8): P(f"     [{k}] x{v}")
    # DM-deeplink share: does reply also say DM/message?
    dm=lb.str.contains(r'(?i)\bDM\b|direct message|message us|dm us|send us a')
    P(f"  of link-bearing replies, {dm.mean()*100:.1f}% also contain DM/message wording (link = DM deep-link, not content)")
