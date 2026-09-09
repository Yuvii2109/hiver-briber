import pandas as pd, numpy as np, re, collections
df = pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
# masked PII tokens across whole corpus
toks = collections.Counter()
for s in df['text'].fillna('').sample(400000, random_state=0):
    for m in re.findall(r'__\w+__', s): toks[m]+=1
print("masked PII tokens (400k sample):", dict(toks.most_common(10)))

brand_of = df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s: s.iloc[0])
th = set(brand_of[brand_of=='AmericanAir'].index)
aa = df[df.thread.isin(th)]
inb = aa[aa.inbound]
print(f"\nAmericanAir: {len(th):,} threads | {len(inb):,} inbound msgs")
# first customer message per thread = the "incoming message" to classify
first = inb.sort_values('created_at').groupby('thread').head(1)
print(f"first-customer-message per thread: {len(first):,}")

KW = {
 'BAGGAGE':r'\b(bag|bags|baggage|luggage|suitcase|carry.?on|checked bag|lost bag|gate check)\b',
 'DELAY_CANCEL':r'\b(delay|delayed|cancel|cancelled|canceled|diverted|missed connection|rebook|stuck|stranded)\b',
 'REFUND_COMP':r'\b(refund|reimburse|compensat|voucher|credit|money back|charge)\b',
 'SEAT_UPGRADE':r'\b(seat|seats|upgrade|first class|main cabin|exit row|assign)\b',
 'LOYALTY':r'\b(aadvantage|miles|elite|platinum|executive|status|award|points)\b',
 'CHECKIN_BOARD':r'\b(check.?in|boarding|board|gate|kiosk|standby|priority)\b',
 'BOOKING_CHANGE':r'\b(book|booking|reservation|change my flight|record locator|itinerary|confirmation)\b',
 'SPECIAL_ASSIST':r'\b(wheelchair|disab|service animal|assistance|medical|unaccompanied|minor|special)\b',
 'STAFF_COMPLAINT':r'\b(rude|attitude|unprofessional|disrespect|agent was|crew was|flight attendant)\b',
 'WEB_APP':r'\b(website|app|online|error|login|log in|site|crash)\b',
}
txt = first['text'].fillna('')
print("\n--- keyword hit-rate on FIRST customer message (overlapping, indicative only) ---")
for k,v in KW.items():
    print(f"  {k:16} {txt.str.contains(v,case=False,regex=True).mean()*100:5.1f}%")
none = ~pd.concat([txt.str.contains(v,case=False,regex=True) for v in KW.values()],axis=1).any(axis=1)
print(f"  {'NO KEYWORD':16} {none.mean()*100:5.1f}%   <- needs OTHER / real classifier")
print(f"\nmedian first-msg words: {txt.str.split().str.len().median():.0f}")
