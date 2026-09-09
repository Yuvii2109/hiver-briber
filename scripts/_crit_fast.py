import pandas as pd, numpy as np, re
P='C:/Users/Dell/dev/hiver-briber/data/raw/twcs_threaded.pkl'
df = pd.read_pickle(P)
df['inbound']=df['inbound'].astype(bool)
df['created']=pd.to_datetime(df['created_at'], format='%a %b %d %H:%M:%S %z %Y', errors='coerce')
brand_of = df.loc[~df.inbound].groupby('thread')['author_id'].first()
df['brand']=df['thread'].map(brand_of)
df=df.dropna(subset=['brand'])
df=df.sort_values(['thread','created'])

DM   = re.compile(r'(?:\bdm\b|\bdms\b|direct message|private message|\bpm us\b|message us|send us a (?:message|note|dm)|meet you (?:there|here)|follow (?:and|us and) )', re.I)
ROUTE= re.compile(r'(?:visit|follow up|click|head (?:to|over)|check out|reach out|contact us|fill out|report it|submit|more info|details)[^.!?]{0,45}https?://', re.I)
ASK  = re.compile(r'(?:can you (?:please )?(?:send|share|provide|dm|confirm)|please (?:send|share|provide|confirm)|what(?:\'s| is) your|which (?:email|account)|email address (?:associated|linked|you))', re.I)

df['nxt_in']=df.groupby('thread')['inbound'].shift(-1)
df['nxt_txt']=df.groupby('thread')['text'].shift(-1)
pairs = df[(df.inbound)&(df['nxt_in']==False)].copy()
pt = pairs['nxt_txt'].fillna('')
pairs['defl']= pt.str.contains(DM)|pt.str.contains(ROUTE)
pairs['ask'] = pt.str.contains(ASK)
def strip(s):
    s=re.sub(r'https?://\S+','',s); s=re.sub(r'@\w+','',s)
    s=re.sub(r'[\^\-~]\s?[A-Za-z]{2,3}\s*$','',s.strip()); return re.sub(r'\s+',' ',s).strip()
pairs['words']=pt.map(strip).str.split().str.len()
pairs['bad']=pairs['defl']|pairs['ask']

B=['Uber_Support','AmazonHelp','hulu_support','GWRHelp','VirginTrains','SpotifyCares','Delta','AmericanAir','British_Airways','Tesco','AppleSupport','SouthwestAir']
g=pairs[pairs.brand.isin(B)].groupby('brand')
r=pd.DataFrame({
 'n_pairs':g.size(),
 'pct_pair_defl':(100*g['defl'].mean()).round(1),
 'pct_pair_defl_or_ask':(100*g['bad'].mean()).round(1),
 'n_usable':g['bad'].apply(lambda s:int((~s).sum())),
 'med_words_all':g['words'].median(),
})
r['med_words_usable']=pairs[pairs.brand.isin(B)&~pairs.bad].groupby('brand')['words'].median()
print(r.sort_values('pct_pair_defl_or_ask').to_string())

# last brand turn per thread
lastb = df[~df.inbound].groupby('thread').tail(1)
lt=lastb['text'].fillna('')
lastb=lastb.assign(defl=lt.str.contains(DM)|lt.str.contains(ROUTE))
print("\n=== % threads whose FINAL brand turn is a deflection ===")
print((100*lastb[lastb.brand.isin(B)].groupby('brand')['defl'].mean()).round(1).sort_values().to_string())
