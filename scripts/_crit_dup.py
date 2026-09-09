import pandas as pd, numpy as np, re, hashlib, collections
BRAND='Uber_Support'
df = pd.read_pickle('data/raw/twcs_threaded.pkl'); df['inbound']=df['inbound'].astype(bool)
brand_of = df.loc[~df.inbound].groupby('thread')['author_id'].agg(lambda s: s.iloc[0])
th = set(brand_of[brand_of==BRAND].index)
d = df[df.thread.isin(th)].copy()
print(f"{BRAND}: threads={len(th):,} rows={len(d):,} inbound={d.inbound.sum():,} outbound={(~d.inbound).sum():,}")

def norm(s):
    s = str(s).lower()
    s = re.sub(r'https?://\S+',' ', s)
    s = re.sub(r'@\w+',' ', s)
    s = re.sub(r'[\^~\-]\s?[a-z]{2}\s*$','',s.strip())   # agent signature
    s = re.sub(r'\d+',' ', s)                            # order/case numbers
    s = re.sub(r'[^a-z\s]',' ', s)
    return re.sub(r'\s+',' ',s).strip()

d['norm']=d['text'].map(norm)

# ---------- 1. agent-side boilerplate ----------
out = d[~d.inbound]
vc = out['norm'].value_counts()
dup_rows = int(len(out) - (vc>0).sum())
print(f"\n--- AGENT replies ({len(out):,}) ---")
print(f"unique normalized: {len(vc):,}  -> {100*dup_rows/len(out):.1f}% of agent replies are a normalized-exact repeat of another")
print(f"share of agent replies belonging to a template used >=10 times: {100*vc[vc>=10].sum()/len(out):.1f}%")
print(f"share belonging to a template used >=100 times: {100*vc[vc>=100].sum()/len(out):.1f}%")
print("\ntop 8 canned agent replies:")
for s,c in vc.head(8).items():
    print(f"  {c:6,}x  {s[:110]}")

# ---------- 2. customer-side: FIRST inbound of each thread = classification/retrieval target ----------
d = d.sort_values(['thread','created_at'])
first = d[d.inbound].groupby('thread', as_index=False).first()
print(f"\n--- CUSTOMER first-messages ({len(first):,} = one per thread) ---")
fvc = first['norm'].value_counts()
print(f"unique normalized: {len(fvc):,}  -> {100*(len(first)-len(fvc))/len(first):.1f}% are normalized-exact repeats")
print(f"share in a cluster of size >=5: {100*fvc[fvc>=5].sum()/len(first):.1f}%   >=20: {100*fvc[fvc>=20].sum()/len(first):.1f}%")
print("top 8 repeated customer openers:")
for s,c in fvc.head(8).items():
    print(f"  {c:6,}x  {s[:110]}")

# ---------- 3. leakage across a CONVERSATION-level split ----------
rng = np.random.default_rng(0)
thr = first['thread'].to_numpy(); perm = rng.permutation(len(thr))
n_te = int(0.2*len(thr)); te_idx=set(perm[:n_te].tolist())
first['split'] = ['test' if i in te_idx else 'train' for i in range(len(first))]
train_norms = set(first.loc[first.split=='train','norm'])
te = first[first.split=='test']
leak = te['norm'].isin(train_norms)
print(f"\n--- LEAKAGE under conversation-level split (80/20, seed 0) ---")
print(f"test first-messages: {len(te):,}")
print(f"with a NORMALIZED-EXACT twin in TRAIN: {leak.sum():,}  ({100*leak.mean():.1f}%)")
te_ne = te[te['norm'].str.split().str.len()>=5]
leak_ne = te_ne['norm'].isin(train_norms)
print(f"  restricted to >=5 content words: {leak_ne.sum():,}/{len(te_ne):,} ({100*leak_ne.mean():.1f}%)")
