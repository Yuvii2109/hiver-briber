import sys, yaml, pandas as pd
sys.path.insert(0, 'src')
from hiver.data.threads import load_raw, add_thread_ids, split_pileups, brand_threads
from hiver.data.examples import build_examples
from hiver.data.split import temporal_split, dedupe_corpus, template_key

cfg = yaml.safe_load(open('configs/config.yaml'))
brand = cfg['brand']
print(f"loading raw…"); df = load_raw(cfg['data']['raw_csv'])
print(f"  rows={len(df):,}  unparsed dates={df['created'].isna().sum():,}")
df = split_pileups(add_thread_ids(df))
th = brand_threads(df, brand)
print(f"{brand}: {th['conv'].nunique():,} conversations / {len(th):,} tweets")
ex = build_examples(th)
print(f"raw examples (cust-turn -> brand-reply): {len(ex):,}")
print(f"  deflection rate: {ex['deflection'].mean()*100:.1f}%")
print(f"  first-turn examples: {ex['is_first_turn'].sum():,}")

f = cfg['filters']
keep = (ex['cust_words'] >= f['min_customer_words'])
if f['drop_non_english']:
    keep &= (ex['nonascii'] <= f['max_nonascii_ratio'])
print(f"filtered out: {(~keep).sum():,}  ({(~keep).mean()*100:.1f}%)")
ex = ex[keep].copy()

ex = temporal_split(ex, cfg['split']['train_frac'], cfg['split']['dev_frac'])
print("\nsplit sizes:"); print(ex['split'].value_counts().to_string())
for s in ['train','dev','test']:
    sub=ex[ex.split==s]
    print(f"  {s:5} {sub['created'].min()} -> {sub['created'].max()}")

corpus = dedupe_corpus(ex[ex.split=='train'])
print(f"\nretrieval corpus: {len(ex[ex.split=='train']):,} -> {len(corpus):,} after template dedupe")
sub = ex[ex.split=='train'].copy(); sub['tkey']=sub['reply_clean'].map(template_key)
top = sub['tkey'].value_counts().head(5)
print("most-pasted templates in train:")
for k,c in top.items():
    print(f"  x{c:5}  {sub[sub.tkey==k]['reply_clean'].iloc[0][:110]}")
ex.to_parquet('data/processed/examples.parquet')
corpus.to_parquet('data/processed/corpus.parquet')
print("\nwrote data/processed/{examples,corpus}.parquet")
