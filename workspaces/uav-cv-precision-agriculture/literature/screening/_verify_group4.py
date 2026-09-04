import json, io
chunk = json.loads(open('_adjudication_chunk_4.json', encoding='utf-8').read())
ids = set(chunk['disputed_ids'])
data = json.loads(open('_adjudication_resolved_group_4.json', encoding='utf-8').read())
rec_ids = set(r['workspace_id'] for r in data)
print("chunk count:", len(ids), "record count:", len(data))
print("all chunk ids present:", ids == rec_ids)
print("missing from output:", ids - rec_ids)
print("extra in output:", rec_ids - ids)
# check each record has required keys
required = ["workspace_id","decision","confidence","final_codes","adjudication_reasoning","s1_decision","s2_decision"]
bad = []
for r in data:
    for k in required:
        if k not in r:
            bad.append((r.get('workspace_id'), k))
print("missing keys:", bad)
print("file path OK, parses as JSON")
