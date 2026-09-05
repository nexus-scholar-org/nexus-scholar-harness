"""Phase 3: build synthesis matrix + descriptive statistics from merged records.json.

Outputs (all under synthesis/):
  synthesis_matrix.csv   — one row per study, verified values
  synthesis_matrix.json  — machine-readable
  synthesis_stats.json   — descriptive statistics (RQ1 + RQ2) for the review
"""
import csv, json, os, re, sys
import collections
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
WS = 'workspaces/uav-cv-precision-agriculture'
records = json.load(open(os.path.join(WS, 'literature/extraction/merged/records.json'), encoding='utf-8'))

SEG = ['mIoU', 'mPA', 'F1', 'Dice', 'PA', 'weed_F1', 'crop_F1']
EDGE = ['fps', 'latency_ms', 'power_w', 'params_M', 'gflops']

def dev_family(device):
    d = (device or '').lower()
    # Jetson only counts as the runtime device when it is the measured platform,
    # NOT an aspirational target ("targets Jetson", "argues feasibility on Jetson",
    # "for Jetson", "not performed on Jetson", "(consumer GPU; paper targets...)").
    aspirational = bool(re.search(r'(targets?|feasibility on|intended for|argues|for (the )?on.?board|not performed|left for future)[^.]*jetson', d))
    if not aspirational:
        if 'jetson orin' in d: return 'Jetson Orin'
        if 'orin nano super' in d: return 'Jetson Orin (Nano Super)'
        if 'orin' in d: return 'Jetson Orin'
        if 'agx xavier' in d: return 'Jetson AGX Xavier'
        if 'xavier nx' in d: return 'Jetson Xavier NX'
        if 'jetso' in d and 'tx2' in d: return 'Jetson TX2'
        if 'jetso' in d and 'nano' in d: return 'Jetson Nano'
        if 'jetso' in d: return 'Jetson (other)'
    if 'rk3588' in d or 'orange pi' in d: return 'Rockchip RK3588'
    if 'tinker board' in d: return 'Tinker Board S'
    if 'colab' in d or 't4' in d: return 'Cloud GPU (Colab)'
    if 'rtx 4090' in d or 'rtx 3090' in d or 'rtx 3080' in d or 'rtx 3070' in d or 'rtx 3050' in d or 'rtx 2080' in d or 'rtx 4060' in d or 'gtx 1660' in d or 'gtx' in d or 'titan' in d or 'quadro' in d or 'v100' in d or 'a100' in d or 'p100' in d: return 'Desktop/Server GPU'
    if 'cpu' in d or 'i7-1065g7' in d or 'i5' in d: return 'CPU'
    if d and 'none' in d or d and 'not specified' in d or d and 'no physical' in d: return 'None specified'
    if d == '': return 'Unknown / not stated'
    return 'Other'

# Each study row
CSV_FIELDS = ['workspace_id', 'title', 'year', 'venue', 'domain', 'task', 'best_model',
              'dataset_name', 'uav_collected', 'num_classes',
              'mIoU', 'mPA', 'F1', 'Dice', 'PA', 'weed_F1', 'crop_F1',
              'edge_runtime', 'device_family', 'device', 'precision', 'resolution_input',
              'fps', 'latency_ms', 'power_w', 'params_M', 'gflops']

def val_or_blank(rec, group, field):
    src = rec['segmentation']['metrics'] if group == 'seg' else rec['edge']
    o = src.get(field)
    if not o or not o.get('reported'):
        return ''
    v = o.get('value')
    return '' if v is None else ('%.4f' % v if isinstance(v, float) else str(v))

rows = []
for r in records:
    device = r['edge'].get('device') or ''
    fam = dev_family(device) if r['edge'].get('runtime_reported') else ('-None-' if not r['edge'].get('reported') else 'Efficiency-only')
    rows.append({
        'workspace_id': r['workspace_id'],
        'title': r['study']['title'],
        'year': r['study'].get('year') or '',
        'venue': r['study'].get('venue') or '',
        'domain': r['segmentation'].get('domain') or '',
        'task': r['segmentation'].get('task') or '',
        'best_model': r['segmentation'].get('best_model') or '',
        'dataset_name': (r['segmentation'].get('dataset') or {}).get('name') or '',
        'uav_collected': (r['segmentation'].get('dataset') or {}).get('uav_collected'),
        'num_classes': r['segmentation'].get('num_classes') or '',
        'mIoU': val_or_blank(r, 'seg', 'mIoU'),
        'mPA': val_or_blank(r, 'seg', 'mPA'),
        'F1': val_or_blank(r, 'seg', 'F1'),
        'Dice': val_or_blank(r, 'seg', 'Dice'),
        'PA': val_or_blank(r, 'seg', 'PA'),
        'weed_F1': val_or_blank(r, 'seg', 'weed_F1'),
        'crop_F1': val_or_blank(r, 'seg', 'crop_F1'),
        'edge_runtime': 'Y' if r['edge'].get('runtime_reported') else 'N',
        'device_family': fam,
        'device': device,
        'precision': r['edge'].get('precision') or '',
        'resolution_input': r['edge'].get('resolution_input') or '',
        'fps': val_or_blank(r, 'edge', 'fps'),
        'latency_ms': val_or_blank(r, 'edge', 'latency_ms'),
        'power_w': val_or_blank(r, 'edge', 'power_w'),
        'params_M': val_or_blank(r, 'edge', 'params_M'),
        'gflops': val_or_blank(r, 'edge', 'gflops'),
    })

os.makedirs(os.path.join(WS, 'synthesis'), exist_ok=True)
with open(os.path.join(WS, 'synthesis', 'synthesis_matrix.csv'), 'w', newline='', encoding='utf-8') as f:
    w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
    w.writeheader()
    w.writerows(rows)

# write device_family back into the record for the stats section
for r, row in zip(records, rows):
    r['edge']['device_family'] = row['device_family']

json.dump(rows, open(os.path.join(WS, 'synthesis', 'synthesis_matrix.json'), 'w', encoding='utf-8'), indent=2, default=str)

# ---------- Descriptive statistics ----------
def frac_records(rec, field):
    """Return reported fraction values across the 82 RQ1 studies."""
    o = rec['segmentation']['metrics'].get(field)
    if o and o.get('reported') and o.get('value') is not None:
        return o['value']
    return None

def agg(field):
    vals = [v for v in (frac_records(r, field) for r in records) if v is not None]
    if not vals:
        return {'n': 0}
    return {'n': len(vals), 'min': min(vals), 'max': max(vals),
            'mean': sum(vals) / len(vals), 'median': sorted(vals)[len(vals)//2]}

stats = {
    'corpus': {'n_studies': len(records)},
    'rq1': {
        'n_with_any_metric': sum(1 for r in records if any(frac_records(r, f) is not None for f in ['mIoU', 'mPA', 'F1', 'Dice', 'PA'])),
        'metric_counts': {f: sum(1 for r in records if frac_records(r, f) is not None) for f in SEG},
        'metrics': {f: agg(f) for f in SEG},
        'domains': dict(Counter(r['segmentation'].get('domain') for r in records)),
        'tasks': dict(Counter(r['segmentation'].get('task') for r in records)),
        'years': dict(Counter(r['study'].get('year') for r in records if r['study'].get('year'))),
        'mIoU_by_domain': {},
    },
    'rq2': {
        'n_with_runtime': sum(1 for r in records if r['edge'].get('runtime_reported')),
        'n_with_efficiency_only': sum(1 for r in records if r['edge'].get('efficiency_reported') and not r['edge'].get('runtime_reported')),
        'device_families': dict(Counter(r['edge'].get('device_family') for r in records if r['edge'].get('runtime_reported'))),
        'precision': dict(Counter(r['edge'].get('precision') for r in records if r['edge'].get('runtime_reported'))),
        'fps': agg('fps') if False else {},
    },
}

for dom in ['crop-weed', 'crop-only', 'weed-only', 'crop-row', 'other-veg', 'crop-other']:
    vals = [frac_records(r, 'mIoU') for r in records if r['segmentation'].get('domain') == dom]
    vals = [v for v in vals if v is not None]
    stats['rq1']['mIoU_by_domain'][dom] = {
        'n': len(vals), 'mean': (sum(vals)/len(vals)) if vals else None,
        'min': min(vals) if vals else None, 'max': max(vals) if vals else None}

# runtime edge distributions
def edge_vals(field, sub=None):
    vals = []
    for r in records:
        o = r['edge'].get(field)
        if o and o.get('reported') and o.get('value') is not None:
            v = o['value']
            if sub is not None and not sub(r):
                continue
            vals.append(v)
    return vals

EDGE_FAM_KEYS = ['Jetson Nano', 'Jetson TX2', 'Jetson AGX Xavier', 'Jetson Xavier NX',
                 'Jetson Orin', 'Jetson Orin (Nano Super)', 'Jetson (other)',
                 'Rockchip RK3588', 'Tinker Board S']

def true_edge(r):
    return r['edge'].get('device_family') in EDGE_FAM_KEYS

def edge_summary(field, sub=None, label='all'):
    vals = edge_vals(field, sub)
    out = {}
    if vals:
        out[label] = {'n': len(vals), 'min': min(vals), 'max': max(vals),
                      'mean': sum(vals)/len(vals), 'median': sorted(vals)[len(vals)//2]}
    return out

for field in ['fps', 'latency_ms', 'power_w', 'params_M', 'gflops']:
    ent = {}
    ent.update(edge_summary(field, None, 'all'))
    ent.update(edge_summary(field, true_edge, 'true_edge'))
    ent.update(edge_summary(field, lambda r: not true_edge(r), 'desktop_cloud'))
    if ent:
        stats['rq2'][field] = ent

edge_studies = [r for r in records if r['edge'].get('runtime_reported')]
on_edge = [r for r in edge_studies if true_edge(r)]
stats['rq2']['n_with_true_edge_device'] = len(on_edge)
stats['rq2']['true_edge_by_family'] = dict(Counter(r['edge'].get('device_family') for r in on_edge))

json.dump(stats, open(os.path.join(WS, 'synthesis', 'synthesis_stats.json'), 'w', encoding='utf-8'), indent=2, default=str)

# ---- Architecture taxonomy + top datasets (derived, keyword-based) ----
def archfam(r):
    m = (r['segmentation'].get('best_model') or '').lower() + ' ' + ' '.join(r['segmentation'].get('models_tested') or [])
    if not m.strip():
        return 'unknown'
    hyb = bool(re.search(r'(transformer|vit|segformer|maskformer|swin|deit|attention|perceiver|focalnet)', m))
    cnn = bool(re.search(r'(unet|u-net|fcn|deeplab|pspnet|segnet|bisenet|enet|erfnet|mobilenet|resnet|resnext|efficientnet|cnn|dnn|encoder-decoder|linknet|fastscnn|squeezenet|shufflenet|yolo|mask.?rcnn|hrnet|panet|lraspp|gan)', m))
    if cnn and hyb:
        return 'hybrid (CNN+attention/transformer)'
    if hyb:
        return 'transformer/attention-based'
    if cnn:
        return 'CNN-based'
    return 'unknown'

stats['arch'] = dict(collections.Counter(archfam(r) for r in records))
stats['arch_with_metrics'] = dict(collections.Counter(
    archfam(r) for r in records
    if any(r['segmentation']['metrics'][f]['reported'] for f in ['mIoU', 'F1', 'Dice', 'PA', 'mPA'])))
dataset_counter = collections.Counter((r['segmentation'].get('dataset') or {}).get('name') or 'not stated' for r in records)
stats['top_datasets'] = dict(dataset_counter.most_common(15))

# Coarse venue type (keyword heuristic over study.venue)
def venue_class(v):
    v = (v or '').strip()
    if not v:
        return 'Other/unknown'
    vl = v.lower()
    if re.search(r'(arxiv|ssrn|biorxiv|preprint)', vl):
        return 'Preprint'
    if re.search(r'(conference|symposium|workshop|proceedings|international congress|\bconf\b|\bsymp\b)', vl):
        return 'Conference'
    if 'journal' in vl:
        return 'Journal'
    if re.search(r'\bIEEE\s+[A-Z]{3,}[\s,]*\d{4}', v) or re.search(r'\([A-Z0-9][A-Z0-9 .&\'\-]{1,}\)', v):
        # e.g. "IEEE HNICEM 2023" or parenthesized venue acronym (SYNCHROINFO)
        return 'Conference'
    return 'Journal'

stats['venue_types'] = dict(collections.Counter(venue_class(r['study'].get('venue')) for r in records))

# mIoU by architecture family (for review Section 1.3)
arch_miou = {}
for fam in collections.Counter(archfam(r) for r in records):
    vals = [v for v in (frac_records(r, 'mIoU') for r in records if archfam(r) == fam) if v is not None]
    arch_miou[fam] = {'n': len(vals)}
    if vals:
        arch_miou[fam].update({'min': min(vals), 'max': max(vals),
                               'mean': sum(vals) / len(vals), 'median': sorted(vals)[len(vals) // 2]})
stats['arch_miou'] = arch_miou

json.dump(stats, open(os.path.join(WS, 'synthesis', 'synthesis_stats.json'), 'w', encoding='utf-8'), indent=2, default=str)

print('rows written:', len(rows))
print()
print('== RQ1 ==')
print('n with any metric:', stats['rq1']['n_with_any_metric'])
print('metric counts:', stats['rq1']['metric_counts'])
print('mIoU agg:', stats['rq1']['metrics']['mIoU'])
for dom, v in stats['rq1']['mIoU_by_domain'].items():
    if v['n']: print('  mIoU by %s: n=%d mean=%.4f range=[%.4f,%.4f]' % (dom, v['n'], v['mean'], v['min'], v['max']))
for fam, v in stats['arch_miou'].items():
    if v['n']: print('  mIoU by arch %s: n=%d mean=%.4f median=%.4f range=[%.4f,%.4f]' % (fam, v['n'], v['mean'], v['median'], v['min'], v['max']))
print()
print('== RQ2 ==')
print('runtime:', stats['rq2']['n_with_runtime'], '| efficiency-only:', stats['rq2']['n_with_efficiency_only'])
print('device families:', stats['rq2']['device_families'])
print('true edge devices:', stats['rq2']['n_with_true_edge_device'], 'by family:', stats['rq2'].get('true_edge_by_family'))
for f in ['fps', 'latency_ms', 'params_M']:
    if f in stats['rq2']:
        for label in ['all', 'true_edge', 'desktop_cloud']:
            v = stats['rq2'][f].get(label)
            if v: print('%s[%s]: n=%d mean=%.2f median=%.2f range=[%.2f,%.2f]' % (f, label, v['n'], v['mean'], v['median'], v['min'], v['max']))