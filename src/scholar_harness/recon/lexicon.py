"""Pluggable domain lexicons for the distiller (M0.4, T4.5; broadened by P6).

The distiller's metric/dataset/school pattern tables were hard-coded for the
computer-vision/LLM domain.  :class:`DomainLexicon` externalizes them so any
research field (oncology, education, robotics, chemistry, ...) can register
its own patterns.  Each field maps a regex pattern (source string) to the
canonical label it emits, matching the shape ``distill_pool`` consumes and
the terms-file schema carries (spec 04_memory_and_cache.md section 6).

``DEFAULT_LEXICON`` ships today's CV/LLM tables **plus** a curated cross-domain
core (climate/geoscience, health, finance/economics, education/social science,
materials/chemistry) so a non-tech pool gets ``schools``/``metrics``/``datasets``
signal on day one (P6, 16_inception_improvements.md F.6).  It stays a keyword
heuristic: specialized registries still come from the domain lexicon merge.
``merge_lexicons`` overlays a field's patterns onto a base lexicon without
mutating it, which is how a niche domain is plugged in.

No named-field registry is shipped: M0.4 keeps exactly one shipped lexicon
(the default) and proves genericity through the merge hook and the tests.
"""

from __future__ import annotations

from dataclasses import dataclass

_DEFAULT_METRICS: dict[str, str] = {
    r"\bmap(?:@[\d.:]+|\d[\d.]*)\b": "mAP",
    r"\bf1\b": "F1",
    r"\bfps\b": "FPS",
    r"\biou\b": "IoU",
    r"\bprecision\b": "precision",
    r"\brecall\b": "recall",
    r"\bbleu\b": "BLEU",
    r"\bpass(?:@|_?at)[\s_]*(?:\d+|k)\b": "pass@",
    r"\baccuracy\b": "accuracy",
    r"exact\s+match": "exact match",
    r"\bcodebleu\b": "codebleu",
    r"\brmse\b": "RMSE",
    r"\bmae\b": "MAE",
    r"\bauc\b": "AUC",
    r"\br2\b": "R2",
    r"\bmcc\b": "MCC",
    r"\bp[- ]?value\b": "p-value",
    r"\b(?:95% )?confidence interval\b": "confidence interval",
    r"\bodds ratio\b": "odds ratio",
}

_DEFAULT_DATASETS: dict[str, str] = {
    r"\bplant[ -]?village\b": "PlantVillage",
    r"\brocole\b": "RoCoLe",
    r"\bmbpp\b": "MBPP",
    r"\bhumaneval\b": "HumanEval",
    r"\bswe[ -]?bench\b": "SWE-bench",
    r"\bcodetransocean\b": "CodeTransOcean",
    r"\bimagenet\b": "ImageNet",
    r"\bcoco\b": "COCO",
    r"\bmnist\b": "MNIST",
    r"\bcifar(?:-?\d+)?\b": "CIFAR",
    r"\bgsm8?k\b": "GSM8K",
    r"\bmmmlu\b": "MMLU",
    r"\bsquad\b": "SQuAD",
    r"\bmedmnist\b": "MedMNIST",
    r"\bcityscapes\b": "Cityscapes",
    r"\bpascal[ -]?voc\b": "Pascal VOC",
    r"\bera5\b": "ERA5",
    r"\bcmip\d?\b": "CMIP",
    r"\btcga\b": "TCGA",
    r"\bmimic(?:-iii|-iv)?\b": "MIMIC",
}

_DEFAULT_SCHOOLS: dict[str, str] = {
    r"\bdeep[- ]?learning\b": "deep learning",
    r"\b(?:uavs?|unmanned aerial vehicles?|drones?)\b": "UAV/drone",
    r"\b(?:llms?|large[- ]?language[- ]?models?|language[- ]?models?)\b": "language model/LLM",
    r"\bedge[- ]?inference\b": "edge inference",
    r"\b(?:multi|hyper)[- ]?spectral\b": "multispectral/hyperspectral",
    r"\bsegmentations?\b": "segmentation",
    r"\btransformers?\b": "transformer",
    r"\bclimate[- ]?change\b": "climate science",
    r"\bglobal[- ]?warming\b": "global warming",
    r"\b(?:precipitation|rainfall)\b": "precipitation",
    r"\bdroughts?\b": "drought",
    r"\bhydrolog(?:y|ical)\b": "hydrology",
    r"\b(?:oncology|oncologic|cancers?|tumou?rs?)\b": "oncology",
    r"\bimmunotherapy\b": "immunotherapy",
    r"\b(?:clinical|randomi[sz]ed controlled) trials?\b": "clinical trial",
    r"\b(?:magnetic resonance imaging|mri)\b": "MRI",
    r"\bcredit (?:risk|scoring)\b": "credit risk",
    r"\bcausal inference\b": "causal inference",
    r"\beconometrics?\b": "econometrics",
    r"\blearning analytics\b": "learning analytics",
    r"\bself[- ]?regulated learning\b": "self-regulated learning",
    r"\bqualitative (?:research|content analysis|analysis)\b": "qualitative research",
    r"\b(?:density functional|first[- ]principles?|dft)\b": "DFT",
    r"\bmolecular dynamics\b": "molecular dynamics",
    r"\binteratomic potentials?\b": "interatomic potentials",
}


@dataclass(frozen=True)
class DomainLexicon:
    """Per-field pattern configuration: regex pattern -> emitted label.

    ``metrics``, ``datasets``, and ``schools`` each map a regex source string
    to the canonical label the distiller emits for a matching pool doc.
    Instances are frozen; the contained mappings are ordinary (mutable)
    dicts, so a field may build its lexicon from any dict-like inputs.
    """

    metrics: dict[str, str]
    datasets: dict[str, str]
    schools: dict[str, str]


DEFAULT_LEXICON = DomainLexicon(
    metrics=_DEFAULT_METRICS,
    datasets=_DEFAULT_DATASETS,
    schools=_DEFAULT_SCHOOLS,
)


def merge_lexicons(base: DomainLexicon, extra: DomainLexicon) -> DomainLexicon:
    """Merge ``extra`` into ``base`` field-wise; ``extra`` wins per key.

    Returns a NEW lexicon; neither ``base`` nor ``extra`` is mutated.  A key
    present only in ``base`` survives unchanged; a key present in both
    resolves to ``extra``'s label; keys present only in ``extra`` are added.
    Every field is merged independently, so a field can override just the
    tables it cares about (e.g. only ``metrics``) and inherit the rest.
    """
    merged_metrics = dict(base.metrics or {})
    merged_metrics.update(extra.metrics or {})
    merged_datasets = dict(base.datasets or {})
    merged_datasets.update(extra.datasets or {})
    merged_schools = dict(base.schools or {})
    merged_schools.update(extra.schools or {})
    return DomainLexicon(
        metrics=merged_metrics,
        datasets=merged_datasets,
        schools=merged_schools,
    )