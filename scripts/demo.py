"""End-to-end agent on a handful of real held-out messages."""
import sys, json, textwrap
sys.path.insert(0,'src')
import numpy as np, pandas as pd
from hiver.escalate.policy import overrides, decide
d=json.load(open('data/interim/gen_outputs.json',encoding='utf-8'))
esc={int(e['tweet_id']):e for e in json.load(open('data/interim/escalation_items.json',encoding='utf-8'))}
R={int(s['tweet_id']):s for s in d['resolution'] if s['system']=='grounded_llm'}
items=[i for i in d['items'] if int(i['tweet_id']) in esc]
pick=[items[i] for i in (3,17,41,66,88)]
for it in pick:
    t=int(it['tweet_id']); e=esc[t]
    ov=overrides(it['text'])
    needs=bool(e['unsafe']) or R[t]['score']<=2
    act,why=decide(0.72 if needs else 0.21, 0.5, ov)
    print("\n"+"╭"+"─"*96+"╮")
    print(f"│ CUSTOMER  {textwrap.shorten(it['text'],86):<86}│")
    print("├"+"─"*96+"┤")
    print(f"│ intent    {it['pred_intent']:<86}│")
    print(f"│ evidence  top similarity {it['top_sim']:.2f} over {it['n_cases']} historical cases{'':<44}│")
    print(f"│ decision  {act:<86}│")
    print(f"│ reason    {textwrap.shorten(why,86):<86}│")
    print("├"+"─"*96+"┤")
    for ln in textwrap.wrap(it['draft_llm'] or '',86):
        print(f"│ reply     {ln:<86}│")
    print("╰"+"─"*96+"╯")
