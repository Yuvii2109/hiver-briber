"""Build the generation inputs: for each golden message, retrieve evidence and
assemble the exact prompt that src/hiver/llm.py will hash and cache."""
import sys, json, pathlib
sys.path.insert(0,'src')
import numpy as np, pandas as pd
from hiver.retrieve.index import CaseIndex
from hiver.generate.responder import build_prompt, SYSTEM, NearestReplyGenerator
from hiver.classify.baselines import TemplateParrot
from hiver.classify.model import EmbeddingIntentClassifier
from hiver.taxonomy.intents import INTENTS

SEED=20260909; K=5
emb=np.load('artifacts/emb_all_fp16.npy').astype(np.float32)
meta=pd.read_parquet('artifacts/meta_all.parquet')
pos={int(t):i for i,t in enumerate(meta.tweet_id.values)}
tr=(meta.split=='train').values
idx=CaseIndex(emb[tr],meta[tr].copy(),exclude_deflections=True)

lab=json.load(open('data/interim/labels_raw.json',encoding='utf-8'))
teach={int(r['tweet_id']):r['intent'] for r in lab['teach'] if r['intent'] in INTENTS}
tr_ids=[t for t in teach if t in pos]
clf=EmbeddingIntentClassifier(seed=SEED).fit(emb[[pos[t] for t in tr_ids]],
                                             np.array([teach[t] for t in tr_ids]))
parrot=TemplateParrot().fit(meta[tr].reply_clean.dropna().tolist())
near=NearestReplyGenerator()

gr=pd.read_json('eval/golden_raw.jsonl',lines=True)
gr=gr[gr.A==gr.B].copy()                       # provisional gold
# judge budget: all of Set B (population) + a slice of Set A
sel=pd.concat([gr[gr.set=='B'], gr[gr.set=='A'].head(57)])
print(f"generating for {len(sel)} golden messages (SetB={int((sel.set=='B').sum())}, SetA={int((sel.set=='A').sum())})")

out=[]
for r in sel.itertuples():
    i=pos[int(r.tweet_id)]
    cases=idx.search(emb[i],k=K,before=meta.created.values[i])
    intent=clf.predict(emb[i:i+1])[0]
    prompt=build_prompt(r.text,intent,cases)
    out.append({
        'tweet_id':int(r.tweet_id),'set':r.set,'text':r.text,'gold_intent':r.A,
        'pred_intent':str(intent),
        'top_sim':float(cases.sim.max()) if len(cases) else 0.0,
        'mean_sim':float(cases.sim.mean()) if len(cases) else 0.0,
        'n_cases':int(len(cases)),
        'cases':[{'q':str(c.q),'reply':str(c.reply_clean),'sim':float(c.sim)} for c in cases.itertuples()],
        'prompt':prompt,
        'draft_human':str(r.human_reply),
        'draft_nearest':near.generate(r.text,intent,cases),
        'draft_parrot':parrot.generate(),
    })
pathlib.Path('data/interim').mkdir(exist_ok=True,parents=True)
json.dump({'system':SYSTEM,'items':out},open('data/interim/gen_inputs.json','w',encoding='utf-8'),ensure_ascii=False)
print(f"wrote data/interim/gen_inputs.json  ({len(out)} items)")
print(f"mean top-similarity {np.mean([o['top_sim'] for o in out]):.3f}; "
      f"items with no evidence above floor: {sum(1 for o in out if o['n_cases']==0)}")
