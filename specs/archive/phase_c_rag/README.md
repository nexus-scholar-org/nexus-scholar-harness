# Phase C: Retrieval Augmented Generation (RAG)

**Specification Version:** 1.1.0  
**Status:** READY FOR IMPLEMENTATION (Post-Review)  
**Target System:** `nexus-scholar-harness` + `scholar-rag-kit`  
**Estimated Duration:** 5 days (Days 10–14)  
**Success Gates:** Schema-validated extraction with PII redaction; LLM extraction with heuristic fallback; Gemini embedding integration

---

## 1. Executive Summary

Phase C addresses **Retrieval Augmented Generation** through three high-value features that transform the RAG kit into a production-grade semantic search and extraction engine for scholarly literature.

### 1.1 Features Overview

| # | Feature | Kit | Impact | Effort |
|---|---------|-----|--------|--------|
| C1 | In-Memory Vector Backend | scholar-rag-kit | High | Medium |
| C2 | Structured Extraction with LLM | scholar-rag-kit | High | High |
| C3 | Gemini Embedding Integration | scholar-rag-kit | Medium | Medium |

### 1.2 Methodological Value

- **Semantic Search:** Vector embeddings enable concept-based retrieval beyond keyword matching
- **Schema Validation:** LLM extraction with Pydantic models ensures structured, validated output
- **PII Redaction:** Automated detection and masking of sensitive information in extracted data
- **Simplicity:** In-memory Numpy backend provides lightweight similarity search without heavy external dependencies

---

## 2. Feature Specifications

### 2.1 C1: In-Memory Vector Backend

**Goal:** Add a lightweight numpy-based vector backend for semantic similarity search without heavy external dependencies.

#### 2.1.1 Algorithm Specification

**Vector Similarity Search:**
- Embed documents using sentence transformers or Gemini embeddings
- Store vectors in memory using NumPy arrays
- Query with cosine similarity using vectorized dot products

**NumpyBackend Operations:**
```python
backend = NumpyBackend()
backend.add_documents(documents=texts, metadatas=metadatas, ids=ids)
results = backend.query(query_text=query, n_results=10)
```

#### 2.1.2 Files to Create/Modify

| File | Changes |
|------|---------|
| `tools/scholar-rag-kit/src/scholar_rag/backends.py` | **NEW** - `NumpyBackend` class (lower-level abstraction) |
| `tools/scholar-rag-kit/src/scholar_rag/cli.py` | No new commands - existing `index` and `query` already use the configured backend |

> **DESIGN NOTE:** The existing `index` command (line 33) already indexes via `ScholarIndexer`. The `NumpyBackend` class provides a lightweight alternative to heavy vector databases like ChromaDB, ensuring the harness remains portable and easy to install.

#### 2.1.3 Implementation Details

```python
# tools/scholar-rag-kit/src/scholar_rag/backends.py
"""Vector storage backends for RAG."""
from __future__ import annotations
from typing import Any, Protocol
from pathlib import Path


class VectorBackend(Protocol):
    """Protocol for vector storage backends."""
    
    def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ) -> None:
        """Add documents to the vector store."""
        ...
    
    def query(
        self,
        query_text: str,
        n_results: int = 10,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Query the vector store for similar documents."""
        ...
    
    def delete(self, ids: list[str]) -> None:
        """Delete documents by ID."""
        ...


class NumpyBackend:
    """In-memory Numpy vector storage backend."""
    
    def __init__(self):
        self._documents = []
        self._metadatas = []
        self._ids = []
        self._vectors = None
        self._embedder = None
    
    def set_embedder(self, embedder):
        self._embedder = embedder

    def add_documents(
        self,
        documents: list[str],
        metadatas: list[dict[str, Any]],
        ids: list[str],
    ) -> int:
        """Add documents to in-memory store."""
        import numpy as np
        if not self._embedder:
            raise ValueError("Embedder not set")
            
        embeddings = self._embedder.embed(documents)
        new_vectors = np.array(embeddings, dtype=np.float32)
        
        # Normalize for cosine similarity
        norms = np.linalg.norm(new_vectors, axis=1, keepdims=True)
        # Avoid division by zero
        norms[norms == 0] = 1e-10
        new_vectors = new_vectors / norms
        
        if self._vectors is None:
            self._vectors = new_vectors
        else:
            self._vectors = np.vstack([self._vectors, new_vectors])
            
        self._documents.extend(documents)
        self._metadatas.extend(metadatas)
        self._ids.extend(ids)
        
        return len(documents)
    
    def query(
        self,
        query_text: str,
        n_results: int = 10,
        where: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Query store for similar documents."""
        import numpy as np
        
        if self._vectors is None or len(self._documents) == 0:
            return {"documents": [], "metadatas": [], "distances": [], "ids": []}
            
        query_emb = self._embedder.embed([query_text])[0]
        q_vec = np.array(query_emb, dtype=np.float32)
        q_vec = q_vec / (np.linalg.norm(q_vec) or 1e-10)
        
        # Compute cosine similarities (dot product since normalized)
        similarities = np.dot(self._vectors, q_vec)
        
        # Sort indices by similarity descending
        top_indices = np.argsort(similarities)[::-1][:n_results]
        
        return {
            "documents": [self._documents[i] for i in top_indices],
            "metadatas": [self._metadatas[i] for i in top_indices],
            "distances": [(1.0 - similarities[i]) for i in top_indices], # Convert similarity to distance
            "ids": [self._ids[i] for i in top_indices],
        }
    
    def delete(self, ids: list[str]) -> None:
        """Delete documents by ID."""
        import numpy as np
        indices_to_keep = [i for i, doc_id in enumerate(self._ids) if doc_id not in ids]
        
        if len(indices_to_keep) < len(self._ids):
            self._documents = [self._documents[i] for i in indices_to_keep]
            self._metadatas = [self._metadatas[i] for i in indices_to_keep]
            self._ids = [self._ids[i] for i in indices_to_keep]
            
            if self._vectors is not None:
                self._vectors = self._vectors[indices_to_keep]
    
    def count(self) -> int:
        """Return number of documents in collection."""
        return len(self._documents)
```

#### 2.1.4 CLI Integration

> **No new CLI commands needed.** The existing `index` and `query` commands provide vector storage and semantic search. The `NumpyBackend` class is used internally by `ScholarIndexer` and can be used directly for custom pipelines.

The existing commands that already use ChromaDB:
- `scholar-rag index <docs_path>` - Indexes markdown documents into ChromaDB
- `scholar-rag query <query_text>` - Performs hybrid vector search with graph PageRank boosting
- `scholar-rag stats` - Shows collection statistics

---

### 2.2 C2: Structured Extraction with LLM

**Goal:** Extract structured metadata from papers using LLMs with schema validation and PII redaction.

#### 2.2.1 Algorithm Specification

**Extraction Pipeline:**
1. Chunk documents into manageable segments
2. Send to LLM with extraction schema prompt
3. Parse JSON response
4. Validate against Pydantic model
5. Redact PII fields
6. Store with provenance metadata

**PII Detection:**
- Emails: `r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'`
- ORCIDs: `r'\b\d{4}-\d{4}-\d{4}-\d{3}[0-9X]\b'`
- Phone numbers: `r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'`

#### 2.2.2 Files to Create/Modify

| File | Changes |
|------|---------|
| `tools/scholar-rag-kit/src/scholar_rag/extractor.py` | **NEW** - `LLMExtractor` class |
| `tools/scholar-rag-kit/src/scholar_rag/schemas.py` | **NEW** - Extraction Pydantic models |
| `tools/scholar-rag-kit/src/scholar_rag/redactor.py` | **NEW** - PII detection and redaction |
| `tools/scholar-rag-kit/src/scholar_rag/cli.py` | Add `extract` command |

#### 2.2.3 Implementation Details

```python
# tools/scholar-rag-kit/src/scholar_rag/schemas.py
"""Pydantic schemas for structured extraction."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from .models import MethodologyMetadata  # REUSE existing model from models.py


class AuthorExtraction(BaseModel):
    """Extracted author information."""
    family_name: str = Field(description="Author family/last name")
    given_name: Optional[str] = Field(None, description="Author given/first name")
    orcid: Optional[str] = Field(None, description="ORCID identifier")
    affiliation: Optional[str] = Field(None, description="Institutional affiliation")
    email: Optional[str] = Field(None, description="Contact email")


class PaperExtraction(BaseModel):
    """Complete paper extraction schema. Aligns with existing MethodologyMetadata."""
    title: str = Field(description="Paper title")
    authors: list[AuthorExtraction] = Field(default_factory=list)
    abstract: Optional[str] = Field(None, description="Paper abstract")
    keywords: list[str] = Field(default_factory=list)
    doi: Optional[str] = Field(None, description="Digital Object Identifier")
    year: Optional[int] = Field(None, description="Publication year")
    publication_date: Optional[datetime] = Field(None, description="Publication date")
    journal: Optional[str] = Field(None, description="Journal name")
    venue: Optional[str] = Field(None, description="Conference/workshop name")
    language: str = Field("en", description="Paper language (ISO 639-1)")
    methodology: Optional[MethodologyMetadata] = None  # REUSE existing model
    key_findings: list[str] = Field(default_factory=list, description="Main findings")
    limitations: list[str] = Field(default_factory=list, description="Study limitations")
    funding: Optional[str] = Field(None, description="Funding source")
    competing_interests: Optional[str] = Field(None, description="Conflicts of interest")
    pdf_url: Optional[str] = Field(None, description="PDF download URL")
    open_access: Optional[bool] = Field(None, description="Open access status")


class ExtractionResult(BaseModel):
    """Result of extraction with provenance."""
    paper: PaperExtraction
    confidence: float = Field(ge=0.0, le=1.0, description="Extraction confidence")
    source_file: str = Field(description="Source document path")
    chunk_index: int = Field(description="Chunk index in document")
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    pii_redacted: bool = Field(False, description="Whether PII was redacted")
```

```python
# tools/scholar-rag-kit/src/scholar_rag/redactor.py
"""PII detection and redaction."""
from __future__ import annotations
import re
from typing import Any


class PIIRedactor:
    """Detects and redacts personally identifiable information."""
    
    # PII patterns (corrected from v1.0)
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b')
    ORCID_PATTERN = re.compile(r'\b\d{4}-\d{4}-\d{4}-\d{3}[0-9X]\b')
    ORCID_URI_PATTERN = re.compile(r'https?://orcid\.org/\d{4}-\d{4}-\d{4}-\d{3}[0-9X]\b')
    PHONE_PATTERN = re.compile(r'(?:\+1[\s.\-]?)?\(?\d{3}\)?[\s.\-]?\d{3}[\s.\-]?\d{4}\b')
    GRANT_PATTERN = re.compile(
        r'\b(?:NIH|NSF|ERC|EU|EMA|FDA)\s*(?:Grant\s*)?[\s#:]*'
        r'[A-Z]?\d{2,}[A-Z]*[\-/]?\d{0,6}\b',
        re.IGNORECASE
    )
    
    def redact(self, text: str) -> tuple[str, bool]:
        """Redact PII from text.
        
        Returns:
            Tuple of (redacted_text, pii_found)
        """
        pii_found = False
        redacted = text
        
        # Redact ORCID URIs first (before numeric ORCIDs to avoid partial replacement)
        if self.ORCID_URI_PATTERN.search(redacted):
            redacted = self.ORCID_URI_PATTERN.sub("[ORCID REDACTED]", redacted)
            pii_found = True
        
        # Redact emails
        if self.EMAIL_PATTERN.search(redacted):
            redacted = self.EMAIL_PATTERN.sub("[EMAIL REDACTED]", redacted)
            pii_found = True
        
        # Redact ORCIDs (numeric)
        if self.ORCID_PATTERN.search(redacted):
            redacted = self.ORCID_PATTERN.sub("[ORCID REDACTED]", redacted)
            pii_found = True
        
        # Redact phone numbers
        if self.PHONE_PATTERN.search(redacted):
            redacted = self.PHONE_PATTERN.sub("[PHONE REDACTED]", redacted)
            pii_found = True
        
        # Redact grant numbers
        if self.GRANT_PATTERN.search(redacted):
            redacted = self.GRANT_PATTERN.sub("[GRANT REDACTED]", redacted)
            pii_found = True
        
        return redacted, pii_found
    
    def redact_dict(self, data: dict[str, Any]) -> tuple[dict[str, Any], bool]:
        """Recursively redact PII from a dictionary."""
        pii_found = False
        redacted = {}
        
        for key, value in data.items():
            if isinstance(value, str):
                redacted_value, found = self.redact(value)
                redacted[key] = redacted_value
                if found:
                    pii_found = True
            elif isinstance(value, dict):
                redacted_dict, found = self.redact_dict(value)
                redacted[key] = redacted_dict
                if found:
                    pii_found = True
            elif isinstance(value, list):
                redacted_list, found = self.redact_list(value)
                redacted[key] = redacted_list
                if found:
                    pii_found = True
            else:
                redacted[key] = value
        
        return redacted, pii_found
    
    def redact_list(self, items: list[Any]) -> tuple[list[Any], bool]:
        """Recursively redact PII from a list."""
        pii_found = False
        redacted = []
        
        for item in items:
            if isinstance(item, str):
                redacted_item, found = self.redact(item)
                redacted.append(redacted_item)
                if found:
                    pii_found = True
            elif isinstance(item, dict):
                redacted_dict, found = self.redact_dict(item)
                redacted.append(redacted_dict)
                if found:
                    pii_found = True
            elif isinstance(item, list):
                redacted_list, found = self.redact_list(item)
                redacted.append(redacted_list)
                if found:
                    pii_found = True
            else:
                redacted.append(item)
        
        return redacted, pii_found
```

```python
# tools/scholar-rag-kit/src/scholar_rag/extractor.py
"""LLM-based structured extraction."""
from __future__ import annotations
from typing import Any
from pathlib import Path
from logging import getLogger
import json
import re

logger = getLogger(__name__)


class LLMExtractor:
    """Extracts structured metadata from documents using LLMs."""
    
    GEMINI_REST_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    
    EXTRACTION_PROMPT = """You are a scholarly metadata extraction expert performing structured extraction
for a systematic literature review. Extract information from the academic text below.

### Extraction Schema
The output must be a single JSON object with these fields:
- title (string, required): Paper title
- authors (array of objects): Each with family_name, given_name (if available), orcid, affiliation
- abstract (string or null): Full abstract if present
- keywords (array of strings): Author-supplied keywords
- doi (string or null): Digital Object Identifier
- year (integer or null): Publication year
- journal (string or null): Journal name
- venue (string or null): Conference or workshop name
- language (string): ISO 639-1 language code, default "en"
- methodology (object or null): study_design, paradigm, sample_size, dataset,
  evaluation_metrics, primary_results, declared_limitations
- key_findings (array of strings): Main empirical findings stated in the text
- limitations (array of strings): Explicit limitations stated by the authors
- funding (string or null): Funding source if mentioned
- competing_interests (string or null): Conflicts of interest if stated

### Rules
- If a field is not present in the text, set it to null (do NOT guess or hallucinate).
- For authors, extract family_name and given_name separately if possible.
- Return ONLY the JSON object. No markdown fences, no commentary.

### Source Section: {section_name}

### Text to extract from:
{text}
"""
    
    # Field weights for confidence calculation
    _FIELD_WEIGHTS = {
        "title": 2.0, "authors": 2.0, "abstract": 1.5, "doi": 1.5,
        "year": 1.5, "journal": 1.0, "venue": 1.0, "language": 0.5,
        "methodology": 2.0, "key_findings": 1.5, "limitations": 1.0,
        "keywords": 0.5, "funding": 0.5, "competing_interests": 0.5,
        "pdf_url": 0.3, "open_access": 0.3,
    }
    
    def __init__(
        self,
        api_key: str | None = None,
        model: str = "gemini-2.0-flash",
        temperature: float = 0.1,
        timeout: float = 120.0,
    ):
        import os
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        if not self.api_key:
            raise ValueError("No Gemini API key found. Set GEMINI_API_KEY env var or pass api_key=.")
        self.model = model
        self.temperature = temperature
        self.timeout = timeout
    
    async def extract_from_text(
        self,
        text: str,
        schema: type,
        chunk_index: int = 0,
        source_file: str = "",
        section_name: str = "unknown",
    ) -> dict[str, Any]:
        """Extract structured data from text using LLM with heuristic fallback."""
        from .redactor import PIIRedactor
        
        try:
            # Build prompt with section awareness
            prompt = self.EXTRACTION_PROMPT.format(
                section_name=section_name,
                text=text,
            )
            
            # Call LLM
            response = await self._call_llm(prompt)
            
            # Parse JSON
            extracted = self._parse_llm_json(response)
            
            # Validate with Pydantic
            validated = schema(**extracted)
        except Exception as exc:
            logger.warning("LLM extraction failed (%s). Falling back to heuristic.", exc)
            extracted = self._heuristic_extract(text, schema)
            validated = schema(**extracted)
        
        # Redact PII
        redactor = PIIRedactor()
        redacted_data, pii_found = redactor.redact_dict(validated.model_dump())
        
        return {
            "extraction": redacted_data,
            "confidence": self._calculate_confidence(extracted, schema),
            "source_file": source_file,
            "chunk_index": chunk_index,
            "pii_redacted": pii_found,
        }
    
    async def extract_from_file(
        self,
        file_path: Path,
        schema: type,
    ) -> list[dict[str, Any]]:
        """Extract structured data from a file, chunking as needed."""
        from .chunker import MarkdownChunker
        
        content = file_path.read_text(encoding="utf-8")
        chunker = MarkdownChunker()
        chunks = chunker.chunk(markdown_text=content)
        
        results = []
        for i, chunk in enumerate(chunks):
            section_name = chunk.metadata.section if hasattr(chunk.metadata, 'section') else "unknown"
            result = await self.extract_from_text(
                chunk.text,
                schema,
                chunk_index=i,
                source_file=str(file_path),
                section_name=section_name,
            )
            results.append(result)
        
        return results
    
    async def _call_llm(self, prompt: str) -> str:
        """Send prompt to Gemini REST API and return text response."""
        import httpx
        
        url = self.GEMINI_REST_URL.format(model=self.model)
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": self.temperature,
                "candidateCount": 1,
                "responseMimeType": "application/json",
            },
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                url, json=payload, params={"key": self.api_key},
            )
            resp.raise_for_status()
            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                raise ValueError("Gemini returned no candidates")
            parts = candidates[0].get("content", {}).get("parts", [])
            return "".join(p.get("text", "") for p in parts)
    
    def _parse_llm_json(self, response: str) -> dict[str, Any]:
        """Robustly extract JSON from LLM response, handling markdown fences."""
        stripped = response.strip()
        # Try to strip markdown code fences
        fence_match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", stripped)
        if fence_match:
            stripped = fence_match.group(1).strip()
        # Try bare JSON object
        obj_match = re.search(r"\{[\s\S]*\}", stripped)
        if obj_match:
            return json.loads(obj_match.group())
        raise ValueError(f"Failed to parse LLM response as JSON: {response[:200]}")
    
    def _heuristic_extract(self, text: str, schema: type) -> dict[str, Any]:
        """Rule-based fallback extraction from raw text."""
        result = {}
        fields = getattr(schema, 'model_fields', {})
        
        if 'title' in fields:
            title_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
            if title_match:
                result["title"] = title_match.group(1).strip()
        
        if 'doi' in fields:
            doi_match = re.search(r"\b10\.\d{4,9}/[^\s]+", text)
            if doi_match:
                result["doi"] = doi_match.group()
        
        if 'year' in fields:
            year_match = re.search(r"\b(19|20)\d{2}\b", text)
            if year_match:
                result["year"] = int(year_match.group())
        
        # Set null for missing optional fields
        for field_name in fields:
            if field_name not in result:
                result[field_name] = None
        
        return result
    
    def _calculate_confidence(self, extracted: dict[str, Any], schema: type) -> float:
        """Weighted confidence: required/important fields count more."""
        schema_fields = getattr(schema, 'model_fields', {})
        total_weight = 0.0
        filled_weight = 0.0
        
        for field_name in schema_fields:
            weight = self._FIELD_WEIGHTS.get(field_name, 0.5)
            total_weight += weight
            value = extracted.get(field_name)
            if value is not None and value != [] and value != "":
                filled_weight += weight
        
        return round(filled_weight / total_weight, 3) if total_weight > 0 else 0.0
```

#### 2.2.4 CLI Integration

> **DESIGN NOTE:** The spec originally proposed `index-chroma` and `search-chroma` commands, but these duplicate the existing `index` and `query` commands. Instead, we add only the `extract` command to the existing CLI. The existing `index` and `query` commands already provide ChromaDB vector storage and semantic search.

```python
# tools/scholar-rag-kit/src/scholar_rag/cli.py
@app.command()
def extract(
    input_file: Path = typer.Argument(..., help="Input markdown file"),
    schema_name: str = typer.Option("paper", "--schema", "-s", help="Extraction schema: paper"),
    output: Path = typer.Option(None, "--output", "-o", help="Output JSON file"),
    api_key: str = typer.Option(None, "--api-key", envvar="GEMINI_API_KEY"),
):
    """Extract structured metadata from a document using LLM."""
    import asyncio
    from .extractor import LLMExtractor
    from .schemas import PaperExtraction
    
    schemas = {
        "paper": PaperExtraction,
    }
    
    if schema_name not in schemas:
        raise typer.BadParameter(f"Unknown schema: {schema_name}. Options: {list(schemas.keys())}")
    
    extractor = LLMExtractor(api_key=api_key)
    results = asyncio.run(extractor.extract_from_file(input_file, schemas[schema_name]))
    
    if output:
        output.write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
        typer.echo(f"✓ Extraction exported to {output}")
    else:
        typer.echo(json.dumps(results, indent=2, default=str))
```

---

### 2.3 C3: Gemini Embedding Integration

**Goal:** Add Gemini API embeddings as an alternative to sentence-transformers for vector storage.

#### 2.3.1 Algorithm Specification

**Gemini Embedding API:**
- Use `text-embedding-004` model for 768-dimensional embeddings
- Batch requests for efficiency
- Handle rate limits with exponential backoff

**API Integration:**
```python
import google.generativeai as genai  # Deferred
genai.configure(api_key=api_key)
model = genai.GenerativeModel("text-embedding-004")
result = model.embed_content(
    texts, 
    task_type="RETRIEVAL_DOCUMENT",
    title="Scholarly Article"
)
embeddings = result["embedding"]
```

#### 2.3.2 Files to Create/Modify

| File | Changes |
|------|---------|
| `tools/scholar-rag-kit/src/scholar_rag/embedder.py` | Add `GeminiEmbedding` class to existing `embedder.py` (which already has `get_embedder()` factory) |

> **DESIGN NOTE:** The existing `embedder.py` (115 lines) already has a `get_embedder()` factory function and `MockEmbeddingFunction`. The `GeminiEmbedding` class should be added to this existing module, not a new `embeddings.py` file. The `SentenceTransformerEmbedding` is already handled by the existing `get_embedder()` factory.

#### 2.3.3 Implementation Details

> **ADD TO EXISTING FILE:** `tools/scholar-rag-kit/src/scholar_rag/embedder.py` (not a new file)

```python
# ADD TO: tools/scholar-rag-kit/src/scholar_rag/embedder.py
# ... existing code (get_embedder, MockEmbeddingFunction, etc.) ...


class GeminiEmbedding:
    """Gemini API embedding model. Add to existing embedder.py."""
    
    def __init__(self, api_key: str | None = None, model: str = "text-embedding-004"):
        import os
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model = model
        self._client = None
    
    def _ensure_initialized(self) -> None:
        if self._client is None:
            import google.generativeai as genai  # Deferred
            genai.configure(api_key=self.api_key)
            self._client = genai
    
    def embed(self, texts: list[str]) -> list[list[float]]:
        self._ensure_initialized()
        
        batch_size = 100
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            model = self._client.GenerativeModel(self.model)
            result = model.embed_content(
                batch,
                task_type="RETRIEVAL_DOCUMENT",
                title="Scholarly Article"
            )
            
            all_embeddings.extend(result["embedding"])
        
        return all_embeddings
    
    @property
    def dimension(self) -> int:
        return 768  # text-embedding-004 dimension
```

#### 2.3.4 CLI Integration

> **No new CLI commands needed.** The existing `index` command already accepts an `--embedder` option that can be set to `gemini` when the `GeminiEmbedding` class is registered in the `get_embedder()` factory.

The existing command that will use Gemini embeddings:
```bash
# Use sentence-transformers (default)
uv run scholar-rag index ./extracted/

# Use Gemini embeddings (after registration in get_embedder())
uv run scholar-rag index ./extracted/ --embedder gemini
```

---

## 3. Testing Strategy

### 3.1 Testing Principles

1. **Hermetic Tests:** No network calls, no real API invocations
2. **Isolated Workspaces:** Use `tmp_path` fixture for all file I/O
3. **Contract-Driven:** Verify data schemas, not implementation details
4. **Deterministic:** Mock LLM responses for consistent results

### 3.2 Test Categories

#### 3.2.1 Unit Tests

| Feature | Test File | Test Cases |
|---------|-----------|------------|
| Numpy Backend | `test_backends.py` | Add, query, delete, count |
| Structured Extraction | `test_extractor.py` | Schema validation, confidence calculation |
| PII Redaction | `test_redactor.py` | Email, ORCID, phone detection |
| Embeddings | `test_embeddings.py` | Dimension, batch embedding |

#### 3.2.2 Integration Tests

| Feature | Test File | Test Cases |
|---------|-----------|------------|
| CLI index-chroma | `test_cli.py` | End-to-end indexing |
| CLI search-chroma | `test_cli.py` | End-to-end search |
| CLI extract | `test_cli.py` | End-to-end extraction |

### 3.3 Test Fixtures

```python
# tests/fixtures.py
import pytest
from pathlib import Path


@pytest.fixture
def sample_documents():
    """Sample markdown documents for testing."""
    return {
        "paper1.md": """# Methodology

We conducted a randomized controlled trial with 500 participants.
The intervention group received the treatment while the control group received placebo.

## Results

The primary outcome showed significant improvement (p < 0.001).
""",
        "paper2.md": """# Abstract

This meta-analysis examined 15 studies on the topic.
Results indicate a moderate effect size (d = 0.45).

## Limitations

- Small sample sizes in included studies
- Publication bias detected
""",
    }


@pytest.fixture
def sample_extraction_schema():
    """Sample extraction schema for testing."""
    from scholar_rag.schemas import PaperExtraction
    return PaperExtraction
```

### 3.4 Test Execution Commands

```bash
# Run all Phase C tests
uv run pytest tests/ -k "backend or extractor or redactor or embedding" -v

# Run specific feature tests
uv run pytest tests/test_backends.py -v
uv run pytest tests/test_extractor.py -v
uv run pytest tests/test_redactor.py -v

# Run with coverage
uv run pytest tests/ --cov=scholar_rag --cov-report=html
```

---

## 4. Task List

### 4.1 Feature C1: ChromaDB Vector Backend

| # | Task | Dependencies | Est. Hours |
|---|------|--------------|------------|
| C1.1 | Create `backends.py` module with `ChromaDBBackend` | None | 2 |
| C1.2 | Integrate `ChromaDBBackend` with existing `ScholarIndexer` | C1.1 | 1 |
| C1.3 | Write unit tests for backend | C1.1 | 1.5 |
| C1.4 | Verify existing `index`/`query` commands still work | C1.2 | 0.5 |
| **Total** | | | **5** |

### 4.2 Feature C2: Structured Extraction with LLM

| # | Task | Dependencies | Est. Hours |
|---|------|--------------|------------|
| C2.1 | Create `schemas.py` module (align with existing `MethodologyMetadata`) | None | 0.5 |
| C2.2 | Create `redactor.py` module (fix PII patterns) | None | 1 |
| C2.3 | Create `extractor.py` module | C2.1, C2.2 | 2 |
| C2.4 | Implement `_call_llm()` with Gemini REST API | C2.3 | 1.5 |
| C2.5 | Implement `_heuristic_extract()` fallback | C2.3 | 1 |
| C2.6 | Add `extract` CLI command (with `asyncio.run()`) | C2.3 | 1 |
| C2.7 | Write unit tests for redactor | C2.2 | 1 |
| C2.8 | Write unit tests for extractor | C2.3, C2.4, C2.5 | 1.5 |
| C2.9 | Write CLI integration test | C2.6 | 0.5 |
| **Total** | | | **10** |

### 4.3 Feature C3: Gemini Embedding Integration

| # | Task | Dependencies | Est. Hours |
|---|------|--------------|------------|
| C3.1 | Add `GeminiEmbedding` class to existing `embedder.py` | None | 1 |
| C3.2 | Register `gemini` in `get_embedder()` factory | C3.1 | 0.5 |
| C3.3 | Write unit tests for Gemini embedding | C3.1, C3.2 | 1.5 |
| C3.4 | Verify existing `index` command works with `--embedder gemini` | C3.2 | 0.5 |
| **Total** | | | **3.5** |

### 4.4 Total Estimated Effort

| Feature | Hours |
|---------|-------|
| C1: ChromaDB Vector Backend | 5 |
| C2: Structured Extraction with LLM | 10 |
| C3: Gemini Embedding Integration | 3.5 |
| C4: Monorepo Sync (post-implementation) | 1.5 |
| **Total** | **20** |

---

## 4.5 Monorepo Governance (Post-Implementation)

> **CRITICAL:** Per AGENTS.md, changes to kit files must be synced to external repos.

### 4.5.1 Kit Sync Requirements

After implementing features in kit directories, run:

```bash
# Sync kit changes to external repos
python scripts/push_tools.py

# Update plugins.json with new commit SHAs
# (manual step after push)

# Regenerate metapackage pins
python scripts/generate_nexus_scholar_pins.py --check  # Verify freshness
python scripts/generate_nexus_scholar_pins.py          # Regenerate if needed
```

### 4.5.2 Conformance Test Updates

When adding the new `extract` CLI command, ensure it is registered in the Typer app so conformance tests pass:

```bash
# Run conformance tests
uv run pytest tests/conformance/test_actions_cli_parity.py -v
uv run pytest tests/conformance/test_mcp_tool_parity.py -v
```

### 4.5.3 Skill Updates

Update the relevant SKILL.md files to document new capabilities:

- `.agents/skills/scholar-rag-kit/SKILL.md` - Add ChromaDB, extraction, Gemini embeddings docs

---

## 5. Definition of Done (DoD)

### 5.1 Feature-Level DoD

For each feature to be considered complete:

- [ ] **Code Complete:** All implementation tasks finished
- [ ] **Tests Passing:** All unit and integration tests pass (`uv run pytest`)
- [ ] **Code Coverage:** New code has ≥90% test coverage
- [ ] **Lint Clean:** `uv run ruff check scripts/` passes (CI scope)
- [ ] **Type Clean:** No type errors in new code
- [ ] **Documentation:** Docstrings for all public functions/classes
- [ ] **CLI Integration:** Feature accessible via `scholar-rag` CLI
- [ ] **Backward Compatible:** No breaking changes to existing APIs

### 5.2 Feature-Specific DoD

#### C1: ChromaDB Vector Backend
- [ ] `ChromaDBBackend` class created and tested
- [ ] Integrates with existing `ScholarIndexer` without breaking it
- [ ] Existing `index` and `query` commands still work
- [ ] Batch indexing handles large document collections

#### C2: Structured Extraction with LLM
- [ ] Extraction schema aligns with existing `MethodologyMetadata` model
- [ ] PII redaction correctly identifies emails, ORCIDs, phones, grant numbers
- [ ] `_call_llm()` implements Gemini REST API with `responseMimeType: "application/json"`
- [ ] Heuristic fallback activates on LLM failure
- [ ] Confidence score uses weighted field importance
- [ ] CLI command uses `asyncio.run()` for async/sync compatibility

#### C3: Gemini Embedding Integration
- [ ] `GeminiEmbedding` class added to existing `embedder.py`
- [ ] Registered in `get_embedder()` factory
- [ ] Existing `index` command works with `--embedder gemini`
- [ ] Extraction results include provenance metadata

#### C3: Gemini Embedding Integration
- [ ] Sentence-transformers embeddings work correctly
- [ ] Gemini API embeddings work correctly
- [ ] Batch embedding handles rate limits
- [ ] Embedding dimension matches backend expectations

### 5.3 Phase-Level DoD

For Phase C to be considered complete:

- [ ] All 3 features implemented and tested
- [ ] All feature-specific DoD criteria met
- [ ] All unit tests pass: `uv run pytest tests/ -v`
- [ ] All integration tests pass
- [ ] No regressions in existing functionality
- [ ] Documentation updated (README, CLI help text)
- [ ] Changes committed with descriptive commit messages
- [ ] Code reviewed by at least one other agent/person
- [ ] Monorepo sync completed (kit repos updated, pins regenerated)

### 5.4 Acceptance Criteria

| Criteria | Measurement | Target |
|----------|-------------|--------|
| Extraction Accuracy | Test with known papers | ≥90% field accuracy |
| PII Redaction | Test with documents containing PII | 100% PII detected (email, ORCID, phone, grant) |
| LLM Fallback | Test with mocked API failure | Heuristic extraction activates |
| ChromaDB Integration | Existing `index`/`query` commands | 0 regressions |
| No Regressions | Existing test suite | 0 failures |

---

## 6. Dependencies & Constraints

### 6.1 External Dependencies

| Dependency | Version | Used By | Notes |
|------------|---------|---------|-------|
| `chromadb` | >=0.4.0 | C1 | Vector storage backend |
| `sentence-transformers` | >=2.2.0 | C3 | Default embedding model |
| `google-generativeai` | >=0.3.0 | C3 | Gemini embedding API |

### 6.2 Internal Dependencies

| Dependency | Kit | Notes |
|------------|-----|-------|
| `MarkdownChunker` | scholar-rag-kit | Existing chunker (NOT `chunk_document`) |
| `ScholarIndexer` | scholar-rag-kit | Existing indexer that wraps ChromaDB |
| `MethodologyMetadata` | scholar-rag-kit | Reuse in extraction schema |
| `get_embedder()` | scholar-rag-kit | Register `GeminiEmbedding` here |
| `LLMBatchScreener` | scholar-search-kit | Reference pattern for `_call_llm()` |
| `AcademicHttpClient` | scholar-search-kit | LLM API calls (if reusing pattern) |

### 6.3 Constraints

1. **No breaking changes:** All existing APIs must remain backward compatible
2. **P7.7 lazy imports:** All heavy dependencies must remain deferred inside function/method bodies
3. **Windows compatibility:** All file paths must handle Windows path separators
4. **UTF-8 encoding:** All file I/O must use UTF-8 encoding
5. **No network in tests:** All tests must be hermetic (mocked HTTP)

---

## 7. Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LLM extraction quality | Medium | High | Implement heuristic fallback |
| Gemini API rate limits | Medium | Medium | Implement exponential backoff |
| PII false positives | Low | Low | Use conservative patterns, manual review |
| ChromaDB integration breaking existing commands | Low | High | Test existing `index`/`query` commands after changes |
| Schema mismatch with existing `MethodologyMetadata` | Medium | Medium | Align schemas before implementation |

---

*Specification created by opencode (mimo-v2.5-free) on 2026-09-15*
*Source: Phase C requirements from ecosystem analysis documents*
*Lessons learned: Phase A, B specifications (attribute verification, P7.7 constraints, monorepo governance)*
*Post-review fixes (v1.1.0): Aligned schemas with existing MethodologyMetadata, fixed PII regex bugs, implemented _call_llm() with Gemini REST API, added heuristic fallback, fixed chunk_document→MarkdownChunker, removed duplicate CLI commands, fixed async/sync mismatch*