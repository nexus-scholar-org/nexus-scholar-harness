import json, glob, re

problems = []
tot_inc = 0
tot_exc = 0
tot_n = 0
files = sorted(glob.glob('batch_*_decisions_screener2.json'))
for f in files:
    idx = int(re.search(r'batch_(\d+)_decisions_screener2', f).group(1))
    try:
        d = json.loads(open(f, encoding='utf-8').read())
    except Exception as e:
        problems.append('PARSE %s: %s' % (f, e))
        continue
    if not isinstance(d, list):
        problems.append('NOTLIST %s' % f)
        continue
    try:
        b = json.loads(open(f.replace('_decisions_screener2.json', '.json'), encoding='utf-8').read())
        npapers = len(b['papers'])
    except Exception as e:
        npapers = None
        problems.append('BATCHREAD %s: %s' % (f, e))
        npapers = len(d)
    if len(d) != npapers:
        problems.append('COVERAGE %s: decisions=%d vs batch papers=%d' % (f, len(d), npapers))
    for i, rec in enumerate(d):
        if not all(k in rec for k in ['workspace_id', 'decision', 'confidence', 'matched_inclusion_criteria', 'violated_exclusion_criteria', 'relevant_rqs', 'screening_reasoning']):
            problems.append('KEYS %s[%d]' % (f, i))
            break
        if rec['decision'] not in ('INCLUDE', 'EXCLUDE'):
            problems.append('DEC %s[%d]: %s' % (f, i, rec['decision']))
        if rec['decision'] == 'INCLUDE':
            tot_inc += 1
        else:
            tot_exc += 1
        tot_n += 1

print('files ok/checked:', len(files))
print('total decisions:', tot_n, 'inc:', tot_inc, 'exc:', tot_exc)
print('problems:', problems if problems else 'NONE')
