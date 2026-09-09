import json, pathlib, textwrap
rec = json.load(open('data/interim/taxonomy_raw.json', encoding='utf-8'))
ints = rec['final_intents']

# ---- machine-readable frozen taxonomy
py = ['"""FROZEN intent taxonomy for @AmericanAir.',
      '',
      'Induced by open coding 400 real conversation openers from the TRAIN split only',
      '(never dev/test). Four analysts coded the same sample independently from four',
      'angles -- action-first, topic-first, automatability-first, and a skeptic told to',
      'assume the obvious airline taxonomy was wrong -- and their proposals were then',
      'reconciled into this single taxonomy. 11 candidate intents were cut; the reasons',
      'are recorded in eval/CODEBOOK.md.',
      '',
      'The headline finding that shaped it: the generic airline taxonomy',
      '(baggage/delay/refund/seat/loyalty) accounts for only ~23% of this traffic, while',
      '~40% of inbound contains no answerable request at all. A taxonomy copied from',
      'domain intuition would have left the two largest masses invisible.',
      '',
      'See eval/CODEBOOK.md for the full annotation rules. This file is the frozen',
      'artifact the code imports; it must not drift from the codebook.',
      '"""',
      'from __future__ import annotations',
      '',
      'INTENTS: list[str] = [']
for it in ints:
    py.append(f'    "{it["name"]}",')
py.append(']')
py.append('')
py.append('# Harm if a bot auto-answers this wrongly. Drives the escalation override list.')
py.append('RISK_TIER: dict[str, str] = {')
for it in ints:
    py.append(f'    "{it["name"]}": "{it["risk_tier"]}",')
py.append('}')
py.append('')
py.append('# Prior share (%) estimated on the 400-message coding sample, for reference only.')
py.append('EST_SHARE: dict[str, float] = {')
for it in ints:
    py.append(f'    "{it["name"]}": {it["est_share_pct"]},')
py.append('}')
py.append('')
py.append('# Applied top-down; the FIRST match wins, which makes the label a deterministic')
py.append('# function of the message and keeps single-label evaluation defensible.')
py.append('PRECEDENCE: list[str] = [')
# OTHER appears TWICE by design: first as the safety route (anchorless legal
# threats, self-harm/violence language, medical crises -- these must never receive
# an automated empathy line, so they are caught before any topical rule), and last
# as the residual catch-all. Everything real is matched in between.
order = [p.split('(')[0].strip() for p in rec['precedence_order']]
mid = [n for n in order if n and n != 'OTHER']
seen = set()
py.append('    "OTHER_SAFETY",')
for n in mid:
    if n not in seen:
        seen.add(n); py.append(f'    "{n}",')
py.append('    "OTHER",')
py.append(']')
pathlib.Path('src/hiver/taxonomy/intents.py').write_text('\n'.join(py)+'\n', encoding='utf-8')

# ---- human-readable codebook
md = ['# Intent codebook — @AmericanAir', '',
      'Committed **before** any golden-set labelling, so the annotation rules could not be',
      'retro-fitted to whatever the model happened to do. Any second annotator should be',
      'able to apply this without talking to me.', '',
      '## How this taxonomy was built', '',
      'Four independent analysts open-coded the same 400 conversation openers, drawn from',
      'the **train split only**, each from a different angle (action-first, topic-first,',
      'automatability-first, and a deliberate skeptic instructed to assume the standard',
      'airline taxonomy was wrong). Their four taxonomies were then reconciled into one.', '',
      '**The finding that mattered:** the obvious airline taxonomy — baggage, delay,',
      'refund, seat, loyalty — covers only about 23% of this traffic. Refunds are ~3.5%,',
      'baggage ~2.5%. The two largest masses are things that taxonomy has no bucket for:',
      'social/praise traffic (~22%) and complaint with nothing filable in it (~11.5%).',
      'Roughly **40% of inbound contains no answerable request at all**.', '',
      '## Decision: venting is a first-class intent', '', textwrap.fill(rec['venting_decision'].split('\n')[0], 92), '',
      '## Precedence', '',
      'A message gets exactly **one** label. Rules are applied top-down and the first match',
      'wins, which makes the label a deterministic function of the text rather than an',
      "annotator's impression:", '']
for i, p in enumerate(rec['precedence_order'], 1):
    md.append(f'{i}. {p}')
md += ['', '## Intents', '']
for it in ints:
    md += [f'### {it["name"]}  ·  ~{it["est_share_pct"]}%  ·  risk: **{it["risk_tier"]}**', '',
           textwrap.fill(it['definition'], 92), '',
           f'**Support action.** {textwrap.fill(it["support_action"], 92)}', '',
           '**Include when**'] + [f'- {r}' for r in it['inclusion_rules']] + ['', '**Exclude when**'] + \
          [f'- {r}' for r in it['exclusion_rules']] + ['', '**Real examples**'] + \
          [f'- {e}' for e in it['positive_examples'][:4]] + ['', f'**Near miss (looks like this, is not).** {it["near_miss_negative"]}', '']
md += ['## Intents considered and cut', '']
for r in rec['rejected_intents']:
    md.append(f'- {r}')
md += ['', '## Where the analysts disagreed', '']
for d in rec['disagreements']:
    md.append(f'- {d}')
pathlib.Path('eval/CODEBOOK.md').write_text('\n'.join(md)+'\n', encoding='utf-8')
print('wrote src/hiver/taxonomy/intents.py and eval/CODEBOOK.md')
