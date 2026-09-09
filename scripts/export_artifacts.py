"""Commit everything a grader needs, so nothing is gated on a 516MB CSV or an API key."""
import sys, json, hashlib, pathlib
sys.path.insert(0,'src')
import numpy as np, pandas as pd

pathlib.Path('eval').mkdir(exist_ok=True)
# 1) the brand slice -- a few MB, removes the download from the critical path
ex=pd.read_parquet('data/processed/examples.parquet')
ex.to_parquet('eval/americanair_examples.parquet',compression='zstd')
print(f"eval/americanair_examples.parquet  {pathlib.Path('eval/americanair_examples.parquet').stat().st_size/1e6:.1f}MB  ({len(ex):,} rows)")

# 2) embeddings (fp16) so no torch on the grader's path
emb=np.load('artifacts/emb_all_fp16.npy'); np.save('eval/embeddings_fp16.npy',emb)
print(f"eval/embeddings_fp16.npy           {emb.nbytes/1e6:.1f}MB  {emb.shape}")

# 3) LLM outputs, with provenance, because they are REPLAYED not re-run
d=json.load(open('data/interim/gen_outputs.json',encoding='utf-8'))
PROV={"produced_by":"claude-opus-5 via the Claude Code agent harness (subagents), not a direct API call",
      "temperature":0.0,"date_utc":"2026-09-10",
      "note":"These are cached model outputs. `python repro.py` REPLAYS them; it does not "
             "re-run the model. Re-running with HIVER_LIVE=1 and an API key may produce "
             "different text and therefore different scores."}
with open('eval/cached_generations.jsonl','w',encoding='utf-8') as f:
    for i in d['items']:
        f.write(json.dumps({"tweet_id":i['tweet_id'],
            "prompt_sha256":hashlib.sha256(i['prompt'].encode()).hexdigest(),
            "draft":i['draft_llm'],"provenance":PROV},ensure_ascii=False)+"\n")
with open('eval/cached_judgments.jsonl','w',encoding='utf-8') as f:
    for axis in ('faithfulness','resolution'):
        for s in d[axis]:
            f.write(json.dumps({"axis":axis,**s,"provenance":PROV},ensure_ascii=False)+"\n")
print(f"eval/cached_generations.jsonl      {len(d['items'])} drafts")
print(f"eval/cached_judgments.jsonl        {len(d['faithfulness'])+len(d['resolution'])} judgements")

# 4) teacher labels
lab=json.load(open('data/interim/labels_raw.json',encoding='utf-8'))
with open('eval/teacher_labels.jsonl','w',encoding='utf-8') as f:
    for r in lab['teach']: f.write(json.dumps(r,ensure_ascii=False)+"\n")
print(f"eval/teacher_labels.jsonl          {len(lab['teach'])} labels")
for p in ['eval/golden_raw.jsonl','eval/CODEBOOK.md']:
    print(f"{p:35}{pathlib.Path(p).stat().st_size/1024:.0f}KB")
