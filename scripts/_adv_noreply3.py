import pandas as pd, numpy as np, re
df = pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound']=df['inbound'].astype(str).isin(['True','true','1'])
df['ts']=pd.to_datetime(df['created_at'],format='%a %b %d %H:%M:%S %z %Y',errors='coerce')
MENT=re.compile(r'^(?:\s*@\w+)+\s*')
THX=re.compile(r'^\W*(thanks|thank you|thank u|thx|ty\b|cheers|ok\b|okay|got it|great|awesome|perfect|no worries|nvm|never ?mind|all good|sorted|resolved|👍|🙏|❤)',re.I)
for BRAND in ['Uber_Support','Delta','AmazonHelp']:
    bt=df[(~df['inbound'])&(df['author_id']==BRAND)]['thread'].unique()
    sub=df[df['thread'].isin(bt)].copy().sort_values('ts')
    inb=sub[sub['inbound']].copy(); ob=sub[(~sub['inbound'])&(sub['author_id']==BRAND)]
    parents=set(ob['in_response_to_tweet_id'].dropna().astype('int64')); bid=set(ob['tweet_id'].astype('int64'))
    rt=inb['response_tweet_id'].map(lambda v: False if pd.isna(v) else any(p.strip().isdigit() and int(p.strip()) in bid for p in str(v).split(',')))
    inb['replied']=inb['tweet_id'].astype('int64').isin(parents).values | rt.values
    nr=inb[~inb['replied']].copy()
    clean=nr['text'].astype(str).str.replace(MENT,'',regex=True)
    thx=clean.str.match(THX)
    short=clean.str.len()<40
    print(f"{BRAND}: no-reply n={len(nr)} | ack/thanks-lead {thx.mean():.1%} | <40 chars {short.mean():.1%} | ack OR short {(thx|short).mean():.1%}")
    print("   samples:", [s[:70] for s in clean[~(thx|short)].sample(3,random_state=1)])
