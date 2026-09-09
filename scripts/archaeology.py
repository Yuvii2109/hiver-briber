import pandas as pd, numpy as np, collections, re, sys

df = pd.read_csv('data/raw/twcs.csv', dtype={'tweet_id':'int64','author_id':'str','inbound':'str',
    'created_at':'str','text':'str','response_tweet_id':'str','in_response_to_tweet_id':'str'})
print(f"rows={len(df):,}  cols={list(df.columns)}")
df['inbound'] = df['inbound'].str.strip().str.lower().eq('true')
print(f"inbound(customer)={df.inbound.sum():,}   outbound(brand)={(~df.inbound).sum():,}")

# brand accounts = authors of outbound tweets
brands = df.loc[~df.inbound,'author_id']
bc = brands.value_counts()
print(f"\ndistinct brand accounts = {bc.nunique()} ({len(bc)})")
print("\n--- top 25 brands by outbound volume ---")
print(bc.head(25).to_string())

# customers who are also non-numeric? sanity
cust = df.loc[df.inbound,'author_id']
nonnum = cust[~cust.str.fullmatch(r'\d+')].unique()
print(f"\ninbound authors that are NOT numeric IDs: {len(nonnum)} -> {nonnum[:15]}")
df.to_pickle('data/raw/twcs.pkl')
print("\nsaved pickle")
