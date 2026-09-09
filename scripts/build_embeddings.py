import sys, re, numpy as np, pandas as pd
sys.path.insert(0,'src')
from hiver.retrieve.encode import encode

def norm(s):
    s = re.sub(r'https?://\S+',' ', str(s)); s = re.sub(r'@\w+',' ', s)
    return re.sub(r'\s+',' ', s).strip()

ex = pd.read_parquet('data/processed/examples.parquet')
ex['q'] = ex['customer'].map(norm)
print(f"encoding {len(ex):,} customer messages…")
v = encode(ex['q'].tolist())
np.save('artifacts/emb_all_fp16.npy', v)
ex[['conv','tweet_id','split','is_first_turn','created','deflection','q','reply_clean']].to_parquet('artifacts/meta_all.parquet')
print("saved artifacts/emb_all_fp16.npy", v.shape, v.dtype, f"{v.nbytes/1e6:.1f}MB")
