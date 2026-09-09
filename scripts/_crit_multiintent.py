import pandas as pd, numpy as np, re, itertools, collections, random
df = pd.read_pickle('C:/Users/Dell/dev/hiver-briber/data/raw/twcs_threaded.pkl')
df['inbound']=df['inbound'].astype(bool)

# opening customer msgs in threads that Uber_Support participated in
ub = set(df.loc[df['author_id']=='Uber_Support','thread'])
sub = df[df['thread'].isin(ub) & df['inbound']].copy()
sub['created_at']=pd.to_datetime(sub['created_at'],errors='coerce',format='mixed',utc=True)
sub = sub.sort_values('created_at')
first = sub.groupby('thread',as_index=False).first()
print("Uber threads:",len(ub)," opening customer msgs:",len(first))

def clean(t):
    t=re.sub(r'@\w+','',str(t)); t=re.sub(r'http\S+','',t); return t.lower()
first['c']=first['text'].map(clean)

FAM = {
 'payment_billing': r'\b(charg\w*|billed|bill|overcharg\w*|double.?charg|payment|card|invoice|receipt|price|fare|cost|surge|expensive|money)\b',
 'refund':          r'\b(refund\w*|reimburs\w*|money back|credit(ed)?\b|compensat\w*)\b',
 'driver_conduct':  r'\b(driver|rider|rude|unsafe|assault\w*|harass\w*|drunk|yell\w*|creep\w*|dangerous)\b',
 'trip_route':      r'\b(route|wrong (way|turn|address|location)|long(er)? way|detour|drop.?off|pick.?up|late|waiting|eta|cancel\w*)\b',
 'lost_item':       r'\b(lost|left (my|behind)|forgot|phone in the car|wallet|bag)\b',
 'account_access':  r'\b(account|log ?in|sign ?in|password|hack\w*|locked|suspend\w*|deactivat\w*|verif\w*|otp)\b',
 'app_technical':   r'\b(app|crash\w*|bug|glitch|error|won\'?t load|update|version|freez\w*|not working)\b',
 'promo_code':      r'\b(promo|coupon|code|discount|voucher|free ride|offer|referral)\b',
 'support_unresp':  r'\b(no (one|response|reply)|still waiting|days ago|ignor\w*|unresponsive|customer service|escalat\w*)\b',
}
pat = {k:re.compile(v) for k,v in FAM.items()}
hits = first['c'].map(lambda t: frozenset(k for k,p in pat.items() if p.search(t)))
first['nfam']=hits.map(len); first['fams']=hits

n=len(first)
print("\n--- keyword-family co-occurrence (crude proxy, upper bound) ---")
for k in range(0,5):
    m=(first['nfam']==k).sum()
    print(f"  {k} families: {m:6,} ({100*m/n:5.2f}%)")
print(f"  >=2 families: {(first['nfam']>=2).sum():,} ({100*(first['nfam']>=2).mean():.2f}%)")
print(f"  >=3 families: {(first['nfam']>=3).sum():,} ({100*(first['nfam']>=3).mean():.2f}%)")

print("\n--- most common CO-OCCURRING pairs ---")
c=collections.Counter()
for s in first.loc[first['nfam']>=2,'fams']:
    for a,b in itertools.combinations(sorted(s),2): c[(a,b)]+=1
for (a,b),v in c.most_common(12): print(f"  {v:6,}  {a:18s} + {b}")

# explicit conjunction / compound-request surface cues
CONJ = re.compile(r'\b(and also|also,|plus,? ?(i|my|the)|another (issue|thing|problem)|second(ly)?|on top of that|as well as|not only|,? and (i|my|now|then) )\b')
first['conj']=first['c'].str.contains(CONJ)
print(f"\nexplicit compound-cue phrases: {first['conj'].sum():,} ({100*first['conj'].mean():.2f}%)")
both = first['conj'] & (first['nfam']>=2)
print(f"conj AND >=2 families (high-precision compound): {both.sum():,} ({100*both.mean():.2f}%)")

print("\n--- 15 random examples with >=2 families (manual read) ---")
random.seed(7)
ex=first[first['nfam']>=2].sample(min(15,int((first['nfam']>=2).sum())),random_state=7)
for _,r in ex.iterrows():
    print(f"  [{'+'.join(sorted(r['fams']))}] {' '.join(str(r['text']).split())[:190]}")
