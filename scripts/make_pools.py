import sys, re, json, numpy as np, pandas as pd
sys.path.insert(0,'src')
ex = pd.read_parquet('data/processed/examples.parquet')
def norm(s):
    s=re.sub(r'https?://\S+',' ',str(s)); s=re.sub(r'@\w+',' ',s)
    return re.sub(r'\s+',' ',s).strip()
ex['q']=ex['customer'].map(norm)
rng=np.random.default_rng(20260909)

# Training pool for the distilled classifier: TRAIN only, first-turn.
tr = ex[(ex.split=='train') & ex.is_first_turn]
tr_s = tr.iloc[rng.choice(len(tr), 3000, replace=False)]

# Golden pool: held-out only. Set B is drawn uniformly from TEST so that
# aggregate numbers (accuracy, coverage, escalation rate) estimate the real
# population; Set A is stratified later and may draw from DEV too.
te = ex[(ex.split=='test') & ex.is_first_turn]
dv = ex[(ex.split=='dev')  & ex.is_first_turn]
print(f"pools -> train first-turn {len(tr):,} | dev {len(dv):,} | test {len(te):,}")

setB = te.iloc[rng.choice(len(te), 100, replace=False)]           # population sample
rest = te[~te.tweet_id.isin(setB.tweet_id)]
poolA = pd.concat([dv, rest])                                      # stratify from here
poolA_s = poolA.iloc[rng.choice(len(poolA), 900, replace=False)]   # silver-label, then stratify

def dump(df, path, kind):
    recs=[{'tweet_id':int(r.tweet_id),'conv':str(r.conv),'split':r.split,'kind':kind,
           'text':r.q,'human_reply':str(r.reply_clean),'deflected':bool(r.deflection),
           'created':str(r.created)} for r in df.itertuples()]
    with open(path,'w',encoding='utf-8') as f:
        for r in recs: f.write(json.dumps(r,ensure_ascii=False)+'\n')
    print(f"  wrote {path}: {len(recs)}")
dump(tr_s,'data/interim/pool_train.jsonl','train')
dump(setB,'data/interim/pool_setB.jsonl','setB_population')
dump(poolA_s,'data/interim/pool_setA_candidates.jsonl','setA_candidates')
