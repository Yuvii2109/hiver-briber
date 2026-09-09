import pandas as pd, re
df=pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound']=df['inbound'].astype(str).isin(['True','true','1'])
for BRAND in ['AmericanAir','Uber_Support','Delta']:
    pat=re.compile(r'@'+BRAND+r'\b',re.I)
    ment=df[df['inbound'] & df['text'].astype(str).str.contains(pat,na=False)]
    bt=set(df[(~df['inbound'])&(df['author_id']==BRAND)]['thread'])
    engaged=ment['thread'].isin(bt)
    print(f"{BRAND}: inbound tweets @-mentioning brand = {len(ment):,}")
    print(f"   thread contains >=1 brand tweet (ENGAGED): {engaged.mean():.1%} ({engaged.sum():,})")
    print(f"   thread contains ZERO brand tweets (NEVER ENGAGED): {(~engaged).mean():.1%} ({(~engaged).sum():,})")
    ne=ment[~engaged]
    # are these openers?
    allids=set(df['tweet_id'].astype('int64'))
    op=ne['in_response_to_tweet_id'].map(lambda v: True if pd.isna(v) else int(v) not in allids)
    print(f"   of never-engaged: openers {op.mean():.1%}")
    MENT=re.compile(r'^(?:\s*@\w+)+\s*')
    cl=ne['text'].astype(str).str.replace(MENT,'',regex=True)
    print("   samples:", [s[:80] for s in cl.sample(4,random_state=7)])
