import json
chunk = json.loads(open('_adjudication_chunk_4.json', encoding='utf-8').read())
ids = chunk['disputed_ids']
print("list len:", len(ids))
print("unique:", len(set(ids)))
# find dupes
from collections import Counter
c = Counter(ids)
print("dupes:", [k for k,v in c.items() if v>1])
