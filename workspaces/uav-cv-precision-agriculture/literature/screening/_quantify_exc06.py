import json, glob
from collections import Counter

adj = {}
for f in glob.glob('_adjudication_resolved_group_*.json'):
    for rec in json.loads(open(f, encoding='utf-8').read()):
        adj[rec['workspace_id']] = rec

def paper_has_abstract(wid):
    for f in sorted(glob.glob('batch_[0-9][0-9][0-9].json')):
        for p in json.loads(open(f, encoding='utf-8').read())['papers']:
            if p['workspace_id'] == wid:
                a = (p.get('abstract') or '').strip()
                return a not in ('', 'No abstract available.', 'NO ABSTRACT')
    return False

exc = {w: r for w, r in adj.items() if r['decision'] == 'EXCLUDE'}
print('adjudicated EXCLUDE:', len(exc))

codes = Counter()
for r in exc.values():
    for c in r['final_codes']:
        codes[c] += 1
print('\nMost common final codes among adjudicated EXCLUDEs:')
for c, n in codes.most_common():
    print('  %s: %d' % (c, n))

# EXC-06-driven exclusions
exc06 = {w: r for w, r in exc.items() if 'EXC-06' in r['final_codes']}
print('\nExcluded WITH EXC-06:', len(exc06))

# Of those, how many actually DO have an abstract (so EXC-06 was about 'no metric', not 'no abstract')?
no_abs = [w for w in exc06 if not paper_has_abstract(w)]
has_abs = [w for w in exc06 if paper_has_abstract(w)]
print('  ...no abstract present in batch:', len(no_abs))
print('  ...abstract IS present but EXC-06 used (no metric/unsupported):', len(has_abs))

# EXC-06 dedundant: restricted to in-scope-topic hint (crop/weed/segmentation/drone)
import re
hint = re.compile(r'(crop|weed|vegetation|segmentation|UAV|drone|wheat|maize|corn|rice|canola|soybean|field|row)', re.I)
in_scope_hint = []
for w in has_abs:
    for f in sorted(glob.glob('batch_[0-9][0-9][0-9].json')):
        for p in json.loads(open(f, encoding='utf-8').read())['papers']:
            if p['workspace_id'] == w:
                txt = (p.get('abstract') or '') + ' ' + (p.get('title') or '')
                if hint.search(txt):
                    in_scope_hint.append(w)
print('\n  EXC-06 w/abstract + in-scope-topic hint (contested):', len(in_scope_hint))