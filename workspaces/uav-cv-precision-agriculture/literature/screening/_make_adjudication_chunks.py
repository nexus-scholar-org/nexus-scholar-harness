import json

reg = json.load(open('_adjudication_registry.json', encoding='utf-8'))

# ordered batches with dispute counts
items = [(int(k), v) for k, v in reg.items()]
items.sort()

# partition into 6 balanced contiguous groups
target = len([i for _, v in items for i in v]) / 6.0
print('target per group ~', target)

groups = []
cur = []
curcount = 0
for k, v in items:
    cur.append((k, v))
    curcount += len(v)
    if curcount >= target:
        groups.append(cur)
        cur = []
        curcount = 0
if cur:
    groups.append(cur)

for gi, g in enumerate(groups, 1):
    ids = [i for _, v in g for i in v]
    batches = [k for k, _ in g]
    payload = {'group': gi, 'batches': batches, 'disputed_ids': ids}
    fn = '_adjudication_chunk_%d.json' % gi
    json.dump(payload, open(fn, 'w', encoding='utf-8'), indent=2)
    print('group %d: batches %s..%s, %d disputes -> %s' % (gi, batches[0], batches[-1], len(ids), fn))
