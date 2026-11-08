"""Deterministic document deduplication and non-destructive metadata fusion."""

import re
from difflib import SequenceMatcher

from .completeness import compute_total_score
from .models import Document, DocumentCluster


def _title_key(title: str) -> str:
    """Normalizes a title by removing non-alphanumeric characters and extra whitespace."""
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def _first_author_surname(doc: Document) -> str | None:
    """Extracts normalized first author surname if present."""
    if doc.authors:
        return doc.authors[0].family_name.lower().strip()
    return None


class Deduplicator:
    """
    Two-tier deterministic deduplication and non-destructive metadata fusion engine:
      Tier 1: Canonical Persistent Identifiers (DOI, arXiv ID, PMID, OpenAlex ID, S2 ID)
      Tier 2: Fuzzy lexical title normalization (>= 97%) + author surname match + year tolerance (+/- 1 year)

    The tier-2 values are parameters (M7-method, decision 2026-11-08): a
    protocol's ``method.dedup`` block may set them within checked limits. The
    defaults are the values above, and with them the result is unchanged.
    """

    def __init__(
        self,
        *,
        title_similarity: float = 0.97,
        first_author: bool = True,
        year_tolerance: int = 1,
    ) -> None:
        if not 0.90 <= float(title_similarity) <= 1.0:
            raise ValueError(f"title_similarity must be within [0.90, 1.00], got {title_similarity!r}")
        if isinstance(year_tolerance, bool) or not isinstance(year_tolerance, int) or not 0 <= year_tolerance <= 2:
            raise ValueError(f"year_tolerance must be 0, 1 or 2, got {year_tolerance!r}")
        self.title_similarity = float(title_similarity)
        self.first_author = bool(first_author)
        self.year_tolerance = year_tolerance
        # Length pre-filter for tier 2. Two strings can only reach a ratio t if
        # the shorter is at least t / (2 - t) of the longer. At the default (and
        # above) the historical 5 % window is kept, so default results never
        # move; a looser threshold widens it to that bound.
        self._length_window = (
            0.05 if self.title_similarity >= 0.97 else 1 - self.title_similarity / (2 - self.title_similarity)
        )

    def _authors_compatible(self, left: Document, right: Document) -> bool:
        if not self.first_author:
            return True
        left_author = _first_author_surname(left)
        right_author = _first_author_surname(right)
        if left_author and right_author:
            # Surnames should match or one contain the other (to handle prefixes like de/van/von)
            return (
                left_author == right_author
                or left_author in right_author
                or right_author in left_author
            )
        return True

    def deduplicate(self, documents: list[Document]) -> list[DocumentCluster]:
        clusters: list[DocumentCluster] = []
        id_index: dict[tuple[str, str], DocumentCluster] = {}
        exact_title_index: dict[str, DocumentCluster] = {}
        fuzzy_pool: list[tuple[str, Document, DocumentCluster]] = []

        def _register(doc: Document, cluster: DocumentCluster) -> None:
            ext = doc.external_ids
            if ext.doi:
                id_index[("doi", ext.doi.strip().lower())] = cluster
            if ext.arxiv_id:
                id_index[("arxiv", ext.arxiv_id.strip().lower())] = cluster
            if ext.pubmed_id:
                id_index[("pubmed", str(ext.pubmed_id).strip())] = cluster
            if ext.openalex_id:
                id_index[("openalex", ext.openalex_id.strip())] = cluster
            if ext.s2_id:
                id_index[("s2", ext.s2_id.strip())] = cluster

            tkey = _title_key(doc.title)
            if tkey:
                exact_title_index[tkey] = cluster
                fuzzy_pool.append((tkey, doc, cluster))

        for document in documents:
            match = None
            ext = document.external_ids

            # Tier 1: Canonical Persistent Identifiers in O(1)
            if ext.doi and ("doi", ext.doi.strip().lower()) in id_index:
                match = id_index[("doi", ext.doi.strip().lower())]
            elif ext.arxiv_id and ("arxiv", ext.arxiv_id.strip().lower()) in id_index:
                match = id_index[("arxiv", ext.arxiv_id.strip().lower())]
            elif ext.pubmed_id and ("pubmed", str(ext.pubmed_id).strip()) in id_index:
                match = id_index[("pubmed", str(ext.pubmed_id).strip())]
            elif ext.openalex_id and ("openalex", ext.openalex_id.strip()) in id_index:
                match = id_index[("openalex", ext.openalex_id.strip())]
            elif ext.s2_id and ("s2", ext.s2_id.strip()) in id_index:
                match = id_index[("s2", ext.s2_id.strip())]

            if match is not None and self._has_identifier_conflict(
                document, match.representative
            ):
                match = None

            # Tier 1b: Exact normalized title match in O(1)
            tkey = _title_key(document.title)
            if match is None and tkey and tkey in exact_title_index:
                exact_cluster = exact_title_index[tkey]
                if self._fuzzy_match(document, exact_cluster.representative):
                    match = exact_cluster

            # Tier 2: Fuzzy Lexical Title Match (pruned by length & author/year)
            if match is None and tkey:
                len_doc = len(tkey)
                for cand_tkey, cand_doc, cand_cluster in fuzzy_pool:
                    len_cand = len(cand_tkey)
                    if abs(len_doc - len_cand) / max(len_doc, len_cand) > self._length_window:
                        continue
                    if (
                        document.year
                        and cand_doc.year
                        and abs(document.year - cand_doc.year) > self.year_tolerance
                    ):
                        continue
                    if self._has_identifier_conflict(document, cand_doc):
                        continue
                    if not self._authors_compatible(document, cand_doc):
                        continue
                    if SequenceMatcher(None, tkey, cand_tkey).ratio() >= self.title_similarity:
                        match = cand_cluster
                        break

            if match is None:
                cluster_id = len(clusters) + 1
                document.workspace_id = f"SCI-{cluster_id:06d}"
                match = DocumentCluster(cluster_id, document, [document])
                clusters.append(match)
            else:
                # Score-based representative election
                candidate_score = compute_total_score(document)
                current_score = compute_total_score(match.representative)

                if candidate_score > current_score:
                    # Swap: candidate becomes representative
                    old_rep = match.representative
                    document.workspace_id = old_rep.workspace_id
                    document.cluster_id = old_rep.cluster_id
                    # Merge old rep metadata into new representative
                    self._merge_metadata(document, old_rep)
                    match.representative = document
                    match.members.append(document)
                else:
                    # Keep current representative
                    document.workspace_id = match.representative.workspace_id
                    document.cluster_id = match.representative.cluster_id
                    # Merge candidate metadata into representative
                    self._merge_metadata(match.representative, document)
                    match.members.append(document)

            _register(document, match)
            document.cluster_id = match.cluster_id
            document.workspace_id = match.representative.workspace_id

        return clusters

    def get_unique_documents(self, documents: list[Document]) -> list[Document]:
        return [cluster.representative for cluster in self.deduplicate(documents)]

    def get_statistics(self, clusters: list[DocumentCluster]) -> dict[str, int | float]:
        total = sum(cluster.size for cluster in clusters)
        unique = len(clusters)
        duplicates = total - unique
        return {
            "total_documents": total,
            "unique_documents": unique,
            "duplicates": duplicates,
            "duplicate_rate": duplicates / total if total else 0.0,
        }

    @staticmethod
    def _same_identifier(left: Document, right: Document) -> bool:
        left_ids = left.external_ids
        right_ids = right.external_ids
        return bool(
            (left_ids.doi and left_ids.doi == right_ids.doi)
            or (left_ids.arxiv_id and left_ids.arxiv_id == right_ids.arxiv_id)
            or (left_ids.pubmed_id and left_ids.pubmed_id == right_ids.pubmed_id)
            or (left_ids.openalex_id and left_ids.openalex_id == right_ids.openalex_id)
            or (left_ids.s2_id and left_ids.s2_id == right_ids.s2_id)
        )

    _PREPRINT_OR_REPO_DOI_PREFIXES = (
        "10.1101/",  # bioRxiv / medRxiv
        "10.48550/arxiv.",  # arXiv DataCite DOI
        "10.2139/ssrn.",  # SSRN
        "10.5281/zenodo.",  # Zenodo
        "10.21203/rs.",  # Research Square
    )

    _DOI_SCHEME_PREFIXES = (
        "https://doi.org/",
        "http://doi.org/",
        "https://dx.doi.org/",
        "http://dx.doi.org/",
        "doi:",
    )

    @staticmethod
    def _normalize_doi(value: str | None) -> str:
        """Normalize a DOI for identity comparison (scheme strip + lowercase).

        The DOI namespace is the one identifier namespace that legitimately
        arrives in several surface forms (``https://doi.org/10.x/y``,
        ``doi:10.x/y``, bare ``10.x/y``). Identity comparison must not depend
        on which surface form a provider happened to emit, so the comparison
        is done on the normalized bare DOI. ``models.ExternalIds`` already
        normalizes on construction, but the conflict check must not rely on
        that: documents can be constructed, mutated or imported from cached
        JSON without going through that constructor.
        """
        if not value:
            return ""
        normalized = str(value).strip().lower()
        for prefix in Deduplicator._DOI_SCHEME_PREFIXES:
            normalized = normalized.removeprefix(prefix)
        return normalized.strip()

    @staticmethod
    def _is_preprint_publisher_pair(left: Document, right: Document) -> bool:
        """True when the pair is exactly one preprint/repository DOI + one publisher DOI.

        The narrowness condition of the reviewed relaxation: a preprint (or any
        other repository-hosted record) and its published counterpart carry two
        DIFFERENT DOIs by construction, because the publisher minted a new DOI
        for the version of record. That single case is the only case in which
        two different non-empty DOIs may describe the same work.
        """
        d1 = Deduplicator._normalize_doi(left.external_ids.doi)
        d2 = Deduplicator._normalize_doi(right.external_ids.doi)
        if not (d1 and d2) or d1 == d2:
            return False
        is_d1_pre = d1.startswith(Deduplicator._PREPRINT_OR_REPO_DOI_PREFIXES)
        is_d2_pre = d2.startswith(Deduplicator._PREPRINT_OR_REPO_DOI_PREFIXES)
        return bool(is_d1_pre ^ is_d2_pre)

    @staticmethod
    def _has_identifier_conflict(left: Document, right: Document) -> bool:
        """Return true when the same persistent-ID namespace disagrees.

        A lexical match must never override contradictory identifier evidence.
        Missing identifiers remain compatible so DOI/arXiv bridge records can
        still connect otherwise equivalent provider records.

        NARROWNESS CONDITION (reviewed decision, kit PR for packet T-K0):
        the only tolerated disagreement is the preprint <-> publisher pair,
        computed ONCE by ``_is_preprint_publisher_pair`` (both DOIs present,
        different after normalization, and EXACTLY ONE of them a
        preprint/repository DOI). In that case:

        * the DOI disagreement is expected (the publisher minted a new DOI);
        * an OpenAlex/S2 id disagreement is expected too, because OpenAlex and
          Semantic Scholar assign DISTINCT ids to a preprint and to its
          published version. In every OTHER case a provider-id disagreement
          blocks the merge, so two records carrying contradictory persistent
          identifiers are never silently merged.
        """
        left_ids = left.external_ids
        right_ids = right.external_ids

        is_preprint_pair = Deduplicator._is_preprint_publisher_pair(left, right)

        d1 = Deduplicator._normalize_doi(left_ids.doi)
        d2 = Deduplicator._normalize_doi(right_ids.doi)
        if d1 and d2 and d1 != d2 and not is_preprint_pair:
            return True

        # Provider-assigned ids (OpenAlex, Semantic Scholar): a disagreement
        # blocks the merge unless the pair is the preprint <-> publisher case.
        for l_val, r_val in (
            (left_ids.openalex_id, right_ids.openalex_id),
            (left_ids.s2_id, right_ids.s2_id),
        ):
            if (
                l_val
                and r_val
                and str(l_val).strip().lower() != str(r_val).strip().lower()
                and not is_preprint_pair
            ):
                return True

        # arXiv and PubMed are single-version namespaces: strict conflict.
        for l_val, r_val in (
            (left_ids.arxiv_id, right_ids.arxiv_id),
            (left_ids.pubmed_id, right_ids.pubmed_id),
        ):
            if (
                l_val
                and r_val
                and str(l_val).strip().lower() != str(r_val).strip().lower()
            ):
                return True
        return False

    def _fuzzy_match(self, left: Document, right: Document) -> bool:
        if Deduplicator._has_identifier_conflict(left, right):
            return False

        left_title = _title_key(left.title)
        right_title = _title_key(right.title)
        if not left_title or not right_title:
            return False

        ratio = SequenceMatcher(None, left_title, right_title).ratio()
        if ratio < self.title_similarity:
            return False

        # Check year tolerance if both have publication year
        if left.year and right.year:
            if abs(left.year - right.year) > self.year_tolerance:
                return False

        # Check author surname match if both have authors (unless switched off)
        return self._authors_compatible(left, right)

    @staticmethod
    def _merge_metadata(rep: Document, source: Document) -> None:
        """Enrich the representative document with missing metadata and provenance from a duplicate."""
        # Merge Persistent Identifiers
        if not rep.external_ids.doi and source.external_ids.doi:
            rep.external_ids.doi = source.external_ids.doi
        if not rep.external_ids.arxiv_id and source.external_ids.arxiv_id:
            rep.external_ids.arxiv_id = source.external_ids.arxiv_id
        if not rep.external_ids.pubmed_id and source.external_ids.pubmed_id:
            rep.external_ids.pubmed_id = source.external_ids.pubmed_id
        if not rep.external_ids.openalex_id and source.external_ids.openalex_id:
            rep.external_ids.openalex_id = source.external_ids.openalex_id
        if not rep.external_ids.s2_id and source.external_ids.s2_id:
            rep.external_ids.s2_id = source.external_ids.s2_id

        # Merge Provenance Sources
        for src in source.sources:
            if src not in rep.sources:
                rep.sources.append(src)

        # Merge OA Locations
        for oa in source.oa_locations:
            if oa not in rep.oa_locations:
                rep.oa_locations.append(oa)

        # Text fields: Prefer longer / cleaner abstract
        if source.abstract:
            if not rep.abstract or len(source.abstract) > len(rep.abstract):
                rep.abstract = source.abstract

        if not rep.venue and source.venue:
            rep.venue = source.venue
        if not rep.url and source.url:
            rep.url = source.url
        if not rep.year and source.year:
            rep.year = source.year
        if not rep.tldr and source.tldr:
            rep.tldr = source.tldr

        # Authors: Prefer richer author list
        if len(source.authors) > len(rep.authors):
            rep.authors = list(source.authors)

        # Numerical fields (take maximum)
        if source.citations_count is not None:
            if (
                rep.citations_count is None
                or source.citations_count > rep.citations_count
            ):
                rep.citations_count = source.citations_count

        if source.references_count is not None:
            if (
                rep.references_count is None
                or source.references_count > rep.references_count
            ):
                rep.references_count = source.references_count

        # Lists (deduplicate union)
        for mesh in source.mesh_terms:
            if mesh not in rep.mesh_terms:
                rep.mesh_terms.append(mesh)

        for intent in source.citation_intents:
            if intent not in rep.citation_intents:
                rep.citation_intents.append(intent)
