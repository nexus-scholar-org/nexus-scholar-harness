import json, glob
from collections import defaultdict

def load_all(pattern):
    out = {}
    for f in glob.glob(pattern):
        for rec in json.loads(open(f, encoding='utf-8').read()):
            out[rec['workspace_id']] = rec
    return out

s1 = load_all('batch_*_decisions.json')
s2 = load_all('batch_*_decisions_screener2.json')

disputed = [w for w in s1 if s1[w]['decision'] != s2[w]['decision']]
print('total disputed:', len(disputed))

# group by batch (find which batch file contains each id)
bybatch = defaultdict(list)
for f in sorted(glob.glob('batch_[0-9][0-9][0-9].json')):
    b = json.loads(open(f, encoding='utf-8').read())
    ids = {p['workspace_id'] for p in b['papers']}
    inter = set(disputed) & ids
    if inter:
        bybatch[b['batch_index']] = sorted(inter)

tot = 0
for k in sorted(bybatch):
    n = len(bybatch[k])
    tot += n
    print('batch %s: %d disputed' % (k, n))
print('sum:', tot)

# save grouped registry
with open('_adjudication_registry.json', 'w', encoding='utf-8') as fh:
    json.dump({k: v for k, v in sorted(bybatch.items())}, fh, indent=2)
print('registry written -> _adjudication_registry.json')
