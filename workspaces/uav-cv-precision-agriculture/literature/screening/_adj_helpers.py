import json

# Emits a per-ID adjudication helper: for each disputed id, pull both screeners' reasoning
def load_all(pattern):
    out = {}
    for f in glob.glob(pattern):
        for rec in json.loads(open(f, encoding='utf-8').read()):
            out[rec['workspace_id']] = rec
    return out
