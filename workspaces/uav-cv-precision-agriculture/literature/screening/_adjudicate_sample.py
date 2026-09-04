import json, glob, re

def load_all(pattern):
    out = {}
    for f in glob.glob(pattern):
        for rec in json.loads(open(f, encoding='utf-8').read()):
            out[rec['workspace_id']] = rec
    return out

s1 = load_all('batch_*_decisions.json')
s2 = load_all('batch_*_decisions_screener2.json')

def paper_batch(wid):
    # find batch file containing this wid
    for f in sorted(glob.glob('batch_[0-9][0-9][0-9].json')):
        b = json.loads(open(f, encoding='utf-8').read())
        for p in b['papers']:
            if p['workspace_id'] == wid:
                return p
    return None

# sample disagreements: S1=INCLUDE, S2=EXCLUDE, spread across S2 codes
target_codes = ['EXC-03','EXC-02','EXC-05','EXC-04','EXC-06','EXC-01']
sample = []
for wid in sorted(s1):
    if s1[wid]['decision']=='INCLUDE' and s2[wid]['decision']=='EXCLUDE':
        sample.append(wid)

# pick a spread: first 3 of each S2 code
seen = {}
for wid in sample:
    code = s2[wid]['violated_exclusion_criteria'][0] if s2[wid]['violated_exclusion_criteria'] else 'NONE'
    seen.setdefault(code, []).append(wid)

chosen = []
for code in target_codes:
    chosen.extend(seen.get(code, [])[:3])

for wid in chosen:
    p = paper_batch(wid)
    if not p: continue
    abs = (p.get('abstract') or 'NO ABSTRACT')[:400]
    print('='*100)
    print('ID', wid, '|', p.get('title','')[:90], '| venue:', p.get('venue'))
    print('ABS:', abs)
    print('S1 INCLUDE reason:', s1[wid].get('screening_reasoning',''))
    print('S2 EXCLUDE reason:', s2[wid].get('screening_reasoning',''))
    print()
