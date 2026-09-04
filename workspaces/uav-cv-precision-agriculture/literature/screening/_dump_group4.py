import json, glob, io

chunk = json.loads(open('_adjudication_chunk_4.json', encoding='utf-8').read())
batches = chunk['batches']
ids = set(chunk['disputed_ids'])

def load_all(pattern):
    out = {}
    for f in glob.glob(pattern):
        for rec in json.loads(open(f, encoding='utf-8').read()):
            out[rec['workspace_id']] = rec
    return out

s1 = load_all('batch_*_decisions.json')
s2 = load_all('batch_*_decisions_screener2.json')

# collect papers
papers = {}
for bn in batches:
    f = f'batch_{bn:03d}.json'
    b = json.loads(open(f, encoding='utf-8').read())
    for p in b['papers']:
        if p['workspace_id'] in ids:
            papers[p['workspace_id']] = p

with io.open('_adj_dump_group4.txt','w',encoding='utf-8') as out:
    for wid in sorted(ids):
        p = papers.get(wid)
        out.write('='*110+'\n')
        if not p:
            out.write(f'MISSING PAPER: {wid}\n')
            continue
        out.write(f"ID: {wid}\n")
        out.write(f"TITLE: {p.get('title','')}\n")
        out.write(f"VENUE: {p.get('venue','')} | YEAR: {p.get('year','')} | DOI: {p.get('doi','')}\n")
        out.write('ABS: '+(p.get('abstract') or 'NO ABSTRACT')+'\n')
        r1 = s1.get(wid,{})
        r2 = s2.get(wid,{})
        out.write(f"S1 DECISION: {r1.get('decision')} CONF:{r1.get('confidence')} CODES:{r1.get('matched_inclusion_criteria') or r1.get('violated_exclusion_criteria')}\n")
        out.write(f"S1 REASON: {r1.get('screening_reasoning','')}\n")
        out.write(f"S2 DECISION: {r2.get('decision')} CONF:{r2.get('confidence')} CODES:{r2.get('matched_inclusion_criteria') or r2.get('violated_exclusion_criteria')}\n")
        out.write(f"S2 REASON: {r2.get('screening_reasoning','')}\n")

missing_ids = ids - set(papers.keys())
print("disputed total:", len(ids))
print("papers found:", len(papers))
print("missing:", missing_ids)
