import json, glob, re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def load(pattern):
    out = {}
    for f in glob.glob(pattern):
        for rec in json.loads(open(f, encoding='utf-8').read()):
            out[rec['workspace_id']] = rec
    return out

adj = {}
for f in glob.glob('_adjudication_resolved_group_*.json'):
    for rec in json.loads(open(f, encoding='utf-8').read()):
        adj[rec['workspace_id']] = rec

def paper(wid):
    for f in sorted(glob.glob('batch_[0-9][0-9][0-9].json')):
        for p in json.loads(open(f, encoding='utf-8').read())['papers']:
            if p['workspace_id'] == wid:
                return p
    return None

# Audit candidates: adjudicated EXCLUDE where the abstract suggests in-scope UAV crop/weed
hint = re.compile(r'(crop|weed|vegetation|segmentation|UAV|drone|acre|field|row|maize|corn|wheat|rice|canola|soybean|sugar)', re.I)
cands = []
for wid, r in adj.items():
    if r['decision'] != 'EXCLUDE':
        continue
    p = paper(wid)
    if not p:
        continue
    txt = (p.get('abstract') or '') + ' ' + (p.get('title') or '')
    if hint.search(txt):
        cands.append((wid, r, p))

print('Adjudicated-EXCLUDE but abstract hints in-scope:', len(cands))
# sort to show those whose exclusion codes are the over-strict ones
def key(t):
    r=t[1]
    codes=r.get('final_codes') or []
    return (any(c.endswith('06') for c in codes), any(c.endswith('03') for c in codes), any(c.endswith('02') for c in codes), 0)
cands.sort(key=key, reverse=True)
for wid, r, p in cands[:25]:
    codes = r.get('final_codes') or []
    print('='*90)
    print(wid, p.get('title','')[:80], '|', p.get('venue'))
    print('  adj codes:', codes, 'conf:', r.get('confidence'))
    print('  adj reason:', r.get('adjudication_reasoning','')[:200])
    print('  ABS:', (p.get('abstract') or 'NO ABSTRACT')[:220])