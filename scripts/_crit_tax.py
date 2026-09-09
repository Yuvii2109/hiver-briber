import pandas as pd, numpy as np, re
BRAND='Uber_Support'
df = pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
brand_of = df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s: s.iloc[0])
th = set(brand_of[brand_of==BRAND].index)
d = df[df.thread.isin(th)].copy().sort_values(['thread','created_at'])
inb = d[d.inbound]
n_inb_per_thread = inb.groupby('thread').size()
print(f"threads={len(th):,}  inbound={len(inb):,}  mean inbound/thread={n_inb_per_thread.mean():.2f}")
print(f"threads with exactly 1 inbound msg: {100*(n_inb_per_thread==1).mean():.1f}%")
print(f"threads with >=2 inbound msgs     : {100*(n_inb_per_thread>=2).mean():.1f}%")

first = inb.groupby('thread', as_index=False).first()
def clean(s):
    s=str(s)
    s=re.sub(r'https?://\S+',' ',s); s=re.sub(r'@\w+',' ',s)
    s=re.sub(r'__\w+__',' ',s)                      # masked PII
    s=re.sub(r'[^A-Za-z0-9\']+',' ',s)
    return re.sub(r'\s+',' ',s).strip()
first['c']=first['text'].map(clean)
first['ntok']=first['c'].str.split().str.len()
print(f"\nfirst-customer-msg token length (after stripping urls/@/PII): "
      f"median={first.ntok.median():.0f} p25={first.ntok.quantile(.25):.0f} p75={first.ntok.quantile(.75):.0f}")
for k in (0,3,5,8):
    print(f"  <= {k} content tokens: {100*(first.ntok<=k).mean():5.1f}%")

# "contentless opener": no problem noun at all
PROB = re.compile(r'\b(charg|refund|fare|driver|ride|trip|account|app|card|payment|pay|cancel|'
                  r'promo|code|credit|money|price|surge|rate|lost|left|phone|item|bag|'
                  r'login|log|password|email|uberpool|pool|eats|food|order|address|route|'
                  r'wait|late|rude|accident|safe|safety|police|complain|issue|problem|error|'
                  r'help|support|charge|bank|receipt|invoice|tip|rating|star|deactivat)', re.I)
PING = re.compile(r'^\s*(hi|hey|hello|yo|please|pls|plz|can|could|someone|anyone|need|'
                  r'dm|dmd|sent|i\'?ve|ive|responded|replied|following|follow|update|any|'
                  r'still|what|why|how|when|where|thanks|thank|ok|okay|k)\b', re.I)
first['has_prob'] = first['c'].str.contains(PROB)
print(f"\nopeners with NO problem-keyword at all: {100*(~first.has_prob).mean():.1f}%")
# strictest 'pure ping': short AND no problem keyword
pure = (~first.has_prob) & (first.ntok<=12)
print(f"'pure ping' (no problem kw AND <=12 tokens): {100*pure.mean():.1f}%")
print(f"of THOSE, threads where customer sends >=2 inbound: "
      f"{100*first.loc[pure,'thread'].map(n_inb_per_thread).ge(2).mean():.1f}%")
print("\n--- 20 random 'pure ping' openers ---")
for s in first.loc[pure,'text'].sample(20, random_state=1): print("  *", str(s)[:130].replace('\n',' '))
print("\n--- 15 random openers WITH problem kw ---")
for s in first.loc[first.has_prob,'text'].sample(15, random_state=1): print("  *", str(s)[:130].replace('\n',' '))
