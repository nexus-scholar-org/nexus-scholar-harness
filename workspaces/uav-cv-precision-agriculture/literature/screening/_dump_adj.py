import json, glob

chunk = json.load(open('_adjudication_chunk_1.json', encoding='utf-8'))
disputed = set(chunk['disputed_ids'])
batches = chunk['batches']

# map workspace_id -> paper info
papers = {}
for b in batches:
    fn = f'batch_{b:03d}.json'
    data = json.load(open(fn, encoding='utf-8'))
    for p in data['papers']:
        papers[p['workspace_id']] = p

# load decisions from both screeners
s1 = {}
for f in glob.glob('batch_*_decisions.json'):
    for rec in json.load(open(f, encoding='utf-8')):
        s1[rec['workspace_id']] = rec
s2 = {}
for f in glob.glob('batch_*_decisions_screener2.json'):
    for rec in json.load(open(f, encoding='utf-8')):
        s2[rec['workspace_id']] = rec

out = []
for wid in sorted(disputed):
    p = papers.get(wid, {})
    r1 = s1.get(wid, {})
    r2 = s2.get(wid, {})
    out.append({
        'workspace_id': wid,
        'title': p.get('title'),
        'year': p.get('year'),
        'venue': p.get('venue'),
        'abstract': p.get('abstract'),
        's1_decision': r1.get('decision'),
        's1_reason': r1.get('screening_reasoning'),
        's2_decision': r2.get('decision'),
        's2_reason': r2.get('screening_reasoning'),
    })

with open('_adj_dump_1.txt', 'w', encoding='utf-8') as f:
    for i, rec in enumerate(out):
        f.write(f"===== [{i}] {rec['workspace_id']} =====" + "\n")
        f.write(f"TITLE: {rec['title']} ({rec['year']}) [{rec['venue']}]" + "\n")
        f.write(f"S1_DECISION: {rec['s1_decision']} | S1_REASON: {rec['s1_reason']}" + "\n")
        f.write(f"S2_DECISION: {rec['s2_decision']} | S2_REASON: {rec['s2_reason']}" + "\n")
        f.write("ABSTRACT: " + (rec['abstract'] or 'NONE') + "\n")
        f.write("\n")

missing = [w for w in disputed if not papers.get(w)]
print("total disputed:", len(disputed))
print("missing in papers:", missing)
print("missing s1:", [w for w in disputed if w not in s1])
print("missing s2:", [w for w in disputed if w not in s2])
print("written records:", len(out))
