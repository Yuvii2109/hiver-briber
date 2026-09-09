import pandas as pd, numpy as np, re, math
BRAND='Uber_Support'
df = pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
brand_of = df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s: s.iloc[0])
th=set(brand_of[brand_of==BRAND].index)
d=df[df.thread.isin(th)].copy().sort_values(['thread','created_at'])
first=d[d.inbound].groupby('thread',as_index=False).first()
print("first customer msgs:",len(first))
print("date range:",first.created_at.min(),"->",first.created_at.max())

# crude proxy taxonomy purely to measure CONCENTRATION (not a real taxonomy)
BUCK=[('safety',r'\b(assault|attack|unsafe|danger|police|crash|accident|harass|threat|kidnap|weapon|drunk driver)\b'),
      ('lost_item',r'\b(left|lost|forgot)\b.{0,30}\b(phone|bag|wallet|purse|laptop|keys|jacket|item|backpack)\b|\blost item\b'),
      ('fare_charge',r'\b(charg|overcharg|fare|price|surge|receipt|invoice|refund|money back|double charg|billed?)\b'),
      ('payment',r'\b(card|payment|paypal|bank|declin|cash|wallet|promo ?code|credit|coupon|voucher)\b'),
      ('account',r'\b(account|log ?in|login|password|sign ?in|verify|verification|suspend|deactivat|hack|email|phone number)\b'),
      ('driver',r'\b(driver|rude|cancel(l?ed)? on me|rating|star|no ?show|didn.?t (show|arrive)|waiting)\b'),
      ('trip',r'\b(trip|ride|route|pickup|drop ?off|destination|address|late|wrong (way|route|address))\b'),
      ('app_tech',r'\b(app|crash|error|bug|update|version|glitch|not working|won.?t (open|load)|loading)\b'),
      ('eats',r'\b(eats|order|food|restaurant|courier|delivery)\b'),
     ]
def clean(s):
    s=str(s); s=re.sub(r'https?://\S+',' ',s); s=re.sub(r'@\w+',' ',s); s=re.sub(r'__\w+__',' ',s)
    return re.sub(r'\s+',' ',s).strip()
first['c']=first['text'].map(clean)
pats=[(n,re.compile(p,re.I)) for n,p in BUCK]
def lab(t):
    for n,p in pats:
        if p.search(t): return n
    return 'OTHER'
first['b']=first['c'].map(lab)
vc=first['b'].value_counts(normalize=True)*100
print("\nproxy-intent prevalence (first-match priority order), %:")
print(vc.round(1).to_string())
print(f"\ntop-2 share: {vc.iloc[:2].sum():.1f}%   top-3: {vc.iloc[:3].sum():.1f}%   tail(<5%) classes: {(vc<5).sum()}, total tail mass {vc[vc<5].sum():.1f}%")

# multi-bucket hits = proxy for multi-intent / ambiguity
hits=np.zeros(len(first),dtype=int)
for n,p in pats: hits += first['c'].str.contains(p).values
print(f"\nmsgs matching >=2 buckets (multi-intent proxy): {100*(hits>=2).mean():.1f}%")
print(f"msgs matching 0 buckets (unclassifiable proxy) : {100*(hits==0).mean():.1f}%")

# what a stratified-uniform golden set implies vs prevalence
K=len(vc)
w_unif=np.full(K,1/K); w_prev=(vc/100).values
print(f"\nstratified-uniform weight per class = {1/K:.3f}; true prevalence range {w_prev.min():.3f}..{w_prev.max():.3f}")
print(f"head class up-weighted by factor {w_prev.max()/(1/K):.2f}x under prevalence weighting; rarest down-weighted {w_prev.min()/(1/K):.2f}x")

# simulate: per-class accuracy typically higher on head classes. Show accuracy gap under plausible per-class acc.
rng=np.random.default_rng(0)
# plausible: acc scales with log support
sup=w_prev; acc=0.55+0.35*(np.log(sup)-np.log(sup.min()))/(np.log(sup.max())-np.log(sup.min()))
print("\nsimulated per-class acc (head-favouring):", dict(zip(vc.index, acc.round(2))))
print(f"  macro (uniform / stratified set) = {acc.mean():.3f}")
print(f"  prevalence-weighted (production) = {(acc*w_prev).sum():.3f}")
print(f"  GAP = {100*((acc*w_prev).sum()-acc.mean()):+.1f} pp")

def wilson(k,n,z=1.96):
    p=k/n; den=1+z*z/n; c=(p+z*z/(2*n))/den; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return (100*(c-h),100*(c+h))
for n in (100,150,200):
    for p in (0.75,0.85):
        lo,hi=wilson(int(round(p*n)),n); print(f"random panel n={n}, acc={p:.0%}: 95% CI {lo:.1f}-{hi:.1f} (+/-{(hi-lo)/2:.1f}pp)")

# expected per-class support in a n=100 SIMPLE RANDOM sample
print("\nexpected count in n=100 simple-random sample:")
print((vc*1.0).round(1).to_string())
print("classes expected <3 examples:", int(((vc)<3).sum()))
