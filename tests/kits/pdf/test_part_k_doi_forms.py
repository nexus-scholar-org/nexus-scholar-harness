"""Part K (M12a): a DOI written as a link or with ``doi:`` is looked up as the bare DOI.

Found by the Part K build: ``download --input`` passed ``https://doi.org/10.…``
unchanged, so the OpenAlex and Unpaywall addresses held the prefix twice and
answered nothing useful. The library strips the prefix (its case is kept).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import aiohttp
import pytest
from scholar_search.http_client import AcademicHttpClient

from scholar_pdf.downloader import AsyncPDFDownloader, bare_doi


@pytest.mark.parametrize("written", [
    "10.7717/peerj.4375", "https://doi.org/10.7717/peerj.4375", "http://dx.doi.org/10.7717/peerj.4375",
    "doi:10.7717/peerj.4375", "  DOI: 10.7717/peerj.4375 ",
])
def test_every_written_form_is_the_bare_doi(written):
    assert bare_doi(written) == "10.7717/peerj.4375"


@pytest.mark.asyncio
async def test_the_lookups_ask_for_the_bare_doi(tmp_path):
    client = MagicMock(spec=AcademicHttpClient)
    answer = MagicMock()
    answer.status_code = 200
    answer.json.return_value = {}
    client.get = AsyncMock(return_value=answer)
    downloader = AsyncPDFDownloader(output_dir=tmp_path)
    result = await downloader.process_doi(AsyncMock(spec=aiohttp.ClientSession), client, "https://doi.org/10.7717/PeerJ.4375")
    urls = [call.args[0] for call in client.get.call_args_list]
    assert urls and all("doi.org/https" not in u and u.endswith("10.7717/PeerJ.4375") for u in urls), urls
    assert result.doi == "10.7717/PeerJ.4375"
