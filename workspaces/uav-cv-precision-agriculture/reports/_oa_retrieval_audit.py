import json, glob, sys
from collections import Counter
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

inc = json.load(open('workspaces/uav-cv-precision-agriculture/literature/included.json', encoding='utf-8'))
got = json.load(open('workspaces/uav-cv-precision-agriculture/pdfs/download_summary.json', encoding='utf-8'))
got_doi = {r['doi'] for r in got}

def pub(doi):
    d = doi.lower()
    if d.startswith('10.3390'): return 'MDPI'
    if d.startswith('10.1016/j'): return 'Elsevier/ScienceDirect'
    if d.startswith('10.1016/') or d.startswith('10.1017/'): return 'Elsevier'
    if d.startswith('10.48550/'): return 'arXiv'
    if d.startswith('10.1007'): return 'Springer'
    if d.startswith('10.1109'): return 'IEEE'
    if d.startswith('10.3389'): return 'Frontiers'
    if d.startswith('10.1038') or d.startswith('10.1057') or d.startswith('10.21105'): return 'Springer/Nature'
    if d.startswith('10.1080'): return 'Taylor&Francis'
    if d.startswith('10.1371'): return 'PLOS'
    if d.startswith('10.1111') or d.startswith('10.1104') or d.startswith('10.1002'): return 'Wiley'
    return 'OTHER'

rows = []
status_counter = Counter()
pub_counter = Counter()
pub_fail = Counter()
for r in inc:
    wid = r['workspace_id']
    doi = (r.get('external_ids') or {}).get('doi') or r.get('doi')
    p = pub(doi or '')
    ok = doi in got_doi
    rows.append({'workspace_id': wid, 'doi': doi, 'publisher': p,
                 'retrieved': ok, 'screening_status': r['screening']['screening_status']})
    status_counter[(p, ok)] += 1
    pub_counter[p] += 1
    if not ok:
        pub_fail[p] += 1

json.dump(rows, open('workspaces/uav-cv-precision-agriculture/pdfs/oa_retrieval_status.csv.json', 'w', encoding='utf-8'), indent=2)

print('total candidate records:', len(rows), ' retrieved:', sum(1 for r in rows if r['retrieved']))
print()
print('%-24s %6s %6s' % ('PUBLISHER','total','retrieved'))
for p in sorted(pub_counter, key=lambda x: -pub_counter[x]):
    print('%-24s %6d %6d' % (p, pub_counter[p], pub_counter[p]-pub_fail[p]))
print()
# retrieval by screening cohort (confirmed vs provisional)
conf_tot = sum(1 for r in rows if r['screening_status']=='CONFIRMED_INCLUSION')
conf_ok = sum(1 for r in rows if r['screening_status']=='CONFIRMED_INCLUSION' and r['retrieved'])
prov_tot = sum(1 for r in rows if r['screening_status']!='CONFIRMED_INCLUSION')
prov_ok = sum(1 for r in rows if r['screening_status']!='CONFIRMED_INCLUSION' and r['retrieved'])
print('CONFIRMED cohort: %d/%d retrieved'%(conf_ok,conf_tot))
print('PROVISIONAL cohort: %d/%d retrieved'%(prov_ok,prov_tot))