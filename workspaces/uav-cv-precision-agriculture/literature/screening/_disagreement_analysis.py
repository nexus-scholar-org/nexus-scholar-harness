import json, glob
from collections import Counter

def load_all(pattern):
    out = {}
    for f in glob.glob(pattern):
        for rec in json.loads(open(f, encoding='utf-8').read()):
            out[rec['workspace_id']] = rec
    return out

s1 = load_all('batch_*_decisions.json')
s2 = load_all('batch_*_decisions_screener2.json')

# S1=INCLUDE, S2=EXCLUDE disagreements: what codes did S2 assign?
s2_exc_codes = Counter()
for wid in s1:
    if s1[wid]['decision'] == 'INCLUDE' and s2[wid]['decision'] == 'EXCLUDE':
        for c in s2[wid]['violated_exclusion_criteria']:
            s2_exc_codes[c] += 1
print('S2 exclusion codes among the 682 S1-included/S2-excluded:')
for c, n in s2_exc_codes.most_common():
    print('  %s: %d' % (c, n))

# Of the S1=INCLUDE/S2=EXCLUDE, how many had abstracts?
def get_abs(wid):
    # find in batch file
    pass
# quick: count EXC-06 assignments (no/no retrievable quantitative results)
exc06 = [w for w in s1 if s1[w]['decision']=='INCLUDE' and s2[w]['decision']=='EXCLUDE' and 'EXC-06' in s2[w]['violated_exclusion_criteria']]
print('\nCount S1-inc/S2-exc with EXC-06 (no abstract / no quant results):', len(exc06))
