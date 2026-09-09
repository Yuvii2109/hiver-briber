import pandas as pd, re
df = pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound']=df['inbound'].astype(bool)
df['created']=pd.to_datetime(df['created_at'], format='%a %b %d %H:%M:%S %z %Y', errors='coerce', utc=True)
brand_of = df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s: s.iloc[0])
NARROW = re.compile(r"(?:\bdm\b|\bdms\b|direct message|private message|send us a (?:message|note|dm))", re.I)
BROAD  = re.compile(r"(?:\bdm\b|\bdms\b|direct message|private message|\bpm us\b|message us|send us a (?:message|note|dm)|meet you (?:there|here)|call us|give us a call|email us|contact us|reach out to us|fill out|web ?form|(?:visit|click|head (?:to|over)|check out|reach out|report it|submit)[^.!?]{0,45}https?://)", re.I)
for B in ['Uber_Support','AmericanAir']:
    th=set(brand_of[brand_of==B].index)
    sub=df[df['thread'].isin(th)].sort_values(['thread','created'],kind='mergesort')
    fo=sub[~sub.inbound].groupby('thread').head(1)['text'].fillna('')
    print(f"\n### {B}  n_first_replies={len(fo)}  narrow={100*fo.str.contains(NARROW).mean():.1f}%  broad={100*fo.str.contains(BROAD).mean():.1f}%")
    for t in fo.sample(12, random_state=0): print("   -", re.sub(r'\s+',' ',t)[:150])
