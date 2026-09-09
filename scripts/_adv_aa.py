import pandas as pd, numpy as np, re
df=pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound']=df['inbound'].astype(str).isin(['True','true','1'])
df['ts']=pd.to_datetime(df['created_at'],format='%a %b %d %H:%M:%S %z %Y',errors='coerce')
all_ids=set(df['tweet_id'].astype('int64'))
BRAND='AmericanAir'
bt=df[(~df['inbound'])&(df['author_id']==BRAND)]['thread'].unique()
sub=df[df['thread'].isin(bt)].copy().sort_values('ts')
inb=sub[sub['inbound']].copy(); ob=sub[(~sub['inbound'])&(sub['author_id']==BRAND)]
parents=set(ob['in_response_to_tweet_id'].dropna().astype('int64')); bid=set(ob['tweet_id'].astype('int64'))
rt=inb['response_tweet_id'].map(lambda v: False if pd.isna(v) else any(p.strip().isdigit() and int(p.strip()) in bid for p in str(v).split(',')))
inb['replied']=inb['tweet_id'].astype('int64').isin(parents).values | rt.values
opener=inb['in_response_to_tweet_id'].map(lambda v: True if pd.isna(v) else int(v) not in all_ids).values
lastbrand=ob.groupby('thread')['ts'].max(); inb['lb']=inb['thread'].map(lastbrand)
DM=re.compile(r'(?:\bdm\b|direct message|private message|send us a message)',re.I)
dmth=set(ob[ob['text'].str.contains(DM,na=False)]['thread'])
n=len(inb); nrm=~inb['replied'].values
print(f"AmericanAir inbound={n}")
print(f"  no-reply overall     : {nrm.mean():.1%} ({nrm.sum()})")
print(f"  openers = {opener.mean():.1%};  no-reply|opener {nrm[opener].mean():.1%} ({nrm[opener].sum()});  no-reply|followup {nrm[~opener].mean():.1%} ({nrm[~opener].sum()})")
nr=inb[nrm]
cov=(nr['lb']>nr['ts']).values; dm=nr['thread'].isin(dmth).values
MENT=re.compile(r'^(?:\s*@\w+)+\s*'); THX=re.compile(r'^\W*(thanks|thank you|thx|ty\b|cheers|ok\b|okay|got it|great|awesome|perfect|no worries|nvm|never ?mind|all good|👍|🙏)',re.I)
clean=nr['text'].astype(str).str.replace(MENT,'',regex=True); thx=clean.str.match(THX).values
print(f"  of no-reply: covered-by-later-brand-reply {cov.mean():.1%} | DM-deflected thread {dm.mean():.1%} | ack/thanks {thx.mean():.1%}")
resid=~(cov|dm|thx)
print(f"  residual 'genuine silence' = {resid.mean():.1%} of no-reply = {resid.sum()/n:.1%} of all inbound ({resid.sum()})")
r2=resid&opener[nrm]
print(f"  residual AND opener = {r2.sum()} = {r2.sum()/n:.2%} of inbound")
print("  residual samples:", [s[:90] for s in clean[resid].sample(5,random_state=3)])
