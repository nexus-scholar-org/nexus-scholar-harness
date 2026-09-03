import json
from collections import Counter

ws = 'workspaces/uav-multispectral-weed-detection/literature'

def dos(d):
    return [x.get('external_ids', {}).get('doi', '') or x.get('provider_id', '') for x in d]

inc = json.load(open(ws + '/included.json'))
exc = json.load(open(ws + '/excluded.json'))

kw_inc = set(dos(inc))
kw_exc = set(dos(exc))

fin_inc = set(dos(json.load(open(ws + '/llm_included.json'))))
fin_exc = set(dos(json.load(open(ws + '/llm_excluded.json'))))

# Build per-paper annotation
# Annotator A = keyword screening (binary)
# Annotator B = final adjudicated (binary)
# A: 1=INCLUDE, 0=EXCLUDE ; B: 1=INCLUDE, 0=EXCLUDE
a = {}
for d in kw_inc: a[d] = 1
for d in kw_exc: a[d] = 0
b = {}
for d in fin_inc: b[d] = 1
for d in fin_exc: b[d] = 0

# Contingency
table = Counter()
all_keys = set(a) | set(b)
print('total papers:', len(all_keys))
missing = [d for d in all_keys if d not in a or d not in b]
print('papers missing a rating:', len(missing))
for d in all_keys:
    table[(a.get(d), b.get(d))] += 1

n11 = table.get((1,1),0)  # both include
n00 = table.get((0,0),0)  # both exclude
n10 = table.get((1,0),0)  # A include, B exclude
n01 = table.get((0,1),0)  # A exclude, B include
N = sum(table.values())

po = (n11 + n00) / N
# expected agreement
p_inc = (n11 + n10) / N   # A marginal include
p_exc = (n01 + n00) / N
# probability both include by chance
pa_inc = (n11 + n01) / N  # B marginal include
pb_inc = (n11 + n10) / N
pe = (pa_inc * pb_inc) + ((1-pa_inc) * (1-pb_inc))

kappa = (po - pe) / (1 - pe) if pe != 1 else 0

print()
print('=== Cohen kappa: keyword screening vs final adjudicated outcome ===')
print(f'both INCLUDE (a=1,b=1): {n11}')
print(f'both EXCLUDE (a=0,b=0): {n00}')
print(f'A INCLUDE / B EXCLUDE (disagree): {n10}')
print(f'A EXCLUDE / B INCLUDE (disagree): {n01}')
print(f'N = {N}')
print(f'Observed agreement po = {po:.4f}')
print(f'Expected agreement pe = {pe:.4f}')
print(f"Cohen's kappa = {kappa:.4f}")
print(f'Raw agreement = {po*100:.1f}%')

# Interpret
print()
if kappa >= 0.81: print('Interpretation (Landis & Koch): Almost perfect')
elif kappa >= 0.61: print('Interpretation (Landis & Koch): Substantial')
elif kappa >= 0.41: print('Interpretation (Landis & Koch): Moderate')
elif kappa >= 0.21: print('Interpretation (Landis & Koch): Fair')
elif kappa >= 0.0: print('Interpretation (Landis & Koch): Slight')
else: print('Interpretation (Landis & Koch): Poor')

# Save for report
Path = __import__('pathlib').Path
out = {
    'total_papers': N,
    'both_include': n11, 'both_exclude': n00,
    'A_include_B_exclude': n10, 'A_exclude_B_include': n01,
    'observed_agreement': round(po,4), 'expected_agreement': round(pe,4),
    'cohens_kappa': round(kappa,4),
}
Path('C:/Users/mouadh/AppData/Local/Temp/opencode/kappa.json').write_text(json.dumps(out, indent=2), encoding='utf-8')
print('\nsaved kappa.json')
