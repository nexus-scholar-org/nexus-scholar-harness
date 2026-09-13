import asyncio
from scholar_search.providers.arxiv import ArxivProvider
from scholar_search.providers.crossref import CrossrefProvider
from scholar_search.providers.pubmed import PubMedProvider
from scholar_search.providers.semanticscholar import SemanticScholarProvider
from scholar_search.models import Query

async def test():
    # Core query
    q_arxiv = Query(
        text='(ti:"literature review" OR abs:"literature review" OR abs:"systematic review" OR abs:"evidence synthesis" OR abs:"scholarly") AND (abs:"large language model" OR abs:LLM OR abs:"agentic" OR abs:"multi-agent" OR abs:RAG)',
        year_min=2023,
        year_max=2026,
        max_results=20
    )
    p_arxiv = ArxivProvider()
    docs_arxiv = [d async for d in p_arxiv.search(q_arxiv)]
    print(f"arXiv results: {len(docs_arxiv)}")
    for d in docs_arxiv[:5]:
        print(" [arxiv]", d.year, d.title)

    # S2 query
    p_s2 = SemanticScholarProvider()
    q_s2 = Query(
        text='"systematic review" + ("large language model" | LLM | "agentic")',
        year_min=2023,
        year_max=2026,
        max_results=20
    )
    docs_s2 = [d async for d in p_s2.search(q_s2)]
    print(f"\nS2 results: {len(docs_s2)}")
    for d in docs_s2[:5]:
        print(" [s2]", d.year, d.title)

asyncio.run(test())
