import json, glob, re
from collections import Counter

def load_all(pattern):
    out = {}
    for f in glob.glob(pattern):
        d = json.loads(open(f, encoding='utf-8').read())
        for rec in d:
            out[rec['workspace_id']] = rec
    return out

s1 = load_all('batch_*_decisions.json')
s2 = load_all('batch_*_decisions_screener2.json')

ids1 = set(s1)
ids2 = set(s2)
common = ids1 & ids2
print('screener1 papers:', len(ids1), 'screener2 papers:', len(ids2), 'common:', len(common))

# Confusion matrix on common decision labels
cm = Counter()
for wid in common:
    d1 = s1[wid]['decision']
    d2 = s2[wid]['decision']
    cm[(d1, d2)] += 1

inc_inc = cm[('INCLUDE','INCLUDE')]
inc_exc = cm[('INCLUDE','EXCLUDE')]
exc_inc = cm[('EXCLUDE','INCLUDE')]
exc_exc = cm[('EXCLUDE','EXCLUDE')]
total = inc_inc+inc_exc+exc_inc+exc_exc

print()
print('=== Confusion Matrix (S1 rows, S2 cols) ===')
print('                    S2=INCLUDE  S2=EXCLUDE')
print('  S1=INCLUDE        %6d     %6d' % (inc_inc, inc_exc))
print('  S1=EXCLUDE        %6d     %6d' % (exc_inc, exc_exc))

obs_agree = (inc_inc + exc_exc) / total
print()
print('Observed agreement: %.4f' % obs_agree)

# Cohen's kappa
# marginal proportions
p1i = (inc_inc + inc_exc) / total
p1e = (exc_inc + exc_exc) / total
p2i = (inc_inc + exc_inc) / total
p2e = (inc_exc + exc_exc) / total
pe = p1i*p2i + p1e*p2e
kappa = (obs_agree - pe) / (1 - pe) if (1 - pe) else 0.0
print('Expected agreement (chance): %.4f' % pe)
print('Cohen kappa: %.4f' % kappa)

# Direction of disagreement: how many S1 said INCLUDE but S2 EXCLUDE, and vice versa
print()
print('S1 INCLUDE / S2 EXCLUDE (potentially over-included by S1):', inc_exc)
print('S1 EXCLUDE / S2 INCLUDE (potentially over-excluded by S1):', exc_inc)

# Overall marginal incl rates
i1 = sum(1 for w in ids1 if s1[w]['decision']=='INCLUDE')/len(ids1)
i2 = sum(1 for w in ids2 if s2[w]['decision']=='INCLUDE')/len(ids2)
print()
print('S1 include rate: %.3f  S2 include rate: %.3f' % (i1, i2))
