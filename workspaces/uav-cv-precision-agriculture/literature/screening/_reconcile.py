import json, glob
from collections import Counter

def load(pattern):
    out = {}
    for f in glob.glob(pattern):
        for rec in json.loads(open(f, encoding='utf-8').read()):
            out[rec['workspace_id']] = rec
    return out

s1 = load('batch_*_decisions.json')
s2 = load('batch_*_decisions_screener2.json')

# adjudication resolutions (all groups)
adj = {}
for f in glob.glob('_adjudication_resolved_group_*.json'):
    for rec in json.loads(open(f, encoding='utf-8').read()):
        adj[rec['workspace_id']] = rec

print('screeners agreed:', sum(1 for w in s1 if s1[w]['decision']==s2[w]['decision']))
print('screeners disputed:', sum(1 for w in s1 if s1[w]['decision']!=s2[w]['decision']))
print('adjudicated (resolved):', len(adj))

# Final reconciled decision
final = {}
still_unresolved = []
for w in s1:
    if s1[w]['decision'] == s2[w]['decision']:
        final[w] = s1[w]['decision']
    else:
        if w in adj:
            final[w] = adj[w]['decision']
        else:
            still_unresolved.append(w)

print('\nFinal reconciled count:', len(final))
print('Still unresolved (in dispute, no adjudication):', len(still_unresolved))

fc = Counter(final.values())
print('Final INCLUDE:', fc.get('INCLUDE',0))
print('Final EXCLUDE:', fc.get('EXCLUDE',0))

# Breakdown of final includes
final_inc = [w for w,d in final.items() if d=='INCLUDE']
print('\nFinal INCLUDE count:', len(final_inc))

# Where did final includes come from?
agreed_inc = [w for w in s1 if s1[w]['decision']==s2[w]['decision']=='INCLUDE']
adjudicated_inc = [w for w in adj if adj[w]['decision']=='INCLUDE']
print('Agreed INCLUDE/INCLUDE by both screeners:', len(agreed_inc))
print('Adjudicated INCLUDE:', len(adjudicated_inc))
print('  of which also disputed:', sum(1 for w in adjudicated_inc if s1[w]['decision']!=s2[w]['decision']))

# Save final reconciled set for the deliverable
json.dump(sorted(final_inc), open('_final_reconciled_include.txt','w',encoding='utf-8'), indent=1)
print('\nWrote _final_reconciled_include.txt')
