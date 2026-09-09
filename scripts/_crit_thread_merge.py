import pandas as pd, numpy as np, collections
df = pd.read_pickle('data/raw/twcs_threaded.pkl')
df['inbound']=df['inbound'].astype(bool)
print("rows", len(df), "threads", df['thread'].nunique())

sizes = df.groupby('thread').size()
print("thread size dist:", sizes.describe().to_dict())
for k in [20,50,100,200,500]:
    print(f"  threads >{k} msgs: {(sizes>k).sum():,}")
print("  max size:", sizes.max(), "at thread", sizes.idxmax())

inb = df[df.inbound]
ncust = inb.groupby('thread')['author_id'].nunique()
print("\nthreads w/ >1 distinct customer:", (ncust>1).sum(), f"({100*(ncust>1).mean():.2f}% of threads having inbound)")
print("threads total:", df['thread'].nunique())
print("as pct of ALL threads:", 100*(ncust>1).sum()/df['thread'].nunique())

# message-level exposure: what fraction of INBOUND messages live in a multi-customer thread
bad = set(ncust[ncust>1].index)
print("\ninbound msgs in multi-customer threads:", inb['thread'].isin(bad).sum(), f"({100*inb['thread'].isin(bad).mean():.2f}% of inbound msgs)")

# thread 409
t = df[df.thread==409]
if len(t):
    print("\nthread 409: msgs", len(t), "distinct inbound authors", t[t.inbound]['author_id'].nunique())
    print(t.sort_values('tweet_id').head(4)[['tweet_id','author_id','inbound','text']].to_string()[:1200])
