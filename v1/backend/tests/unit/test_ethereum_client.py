"""Etherscan client tests (HTTP layer mocked with respx)."""

from __future__ import annotations

import httpx
import pytest
import respx

from app.core.errors import ProviderError, RateLimitError
from app.services.ingestion.ethereum_client import EtherscanClient

BASE = "https://api.etherscan.io/v2/api"


def _envelope(result, *, status="1", message="OK") -> dict:
    return {"status": status, "message": message, "result": result}


def _record(hash_hex: str) -> dict:
    return {
        "blockNumber": "21000000",
        "timeStamp": "1710000000",
        "hash": hash_hex,
        "from": "0x" + "aa" * 20,
        "to": "0x" + "bb" * 20,
        "value": "1000",
        "gas": "21000",
        "gasUsed": "21000",
        "gasPrice": "20000000000",
        "input": "0x",
        "isError": "0",
        "txreceipt_status": "1",
    }


ADDR = "0x" + "aa" * 20


class TestEtherscanClient:
    async def test_fetch_includes_chainid_and_apikey(self) -> None:
        client = EtherscanClient(api_key="secret-key", base_url=BASE, chain_id=1, page_size=100)
        seen: dict = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen.update(dict(request.url.params))
            return httpx.Response(200, json=_envelope([]))

        with respx.mock(base_url=BASE) as mock:
            mock.get("").mock(side_effect=handler)
            await client.get_native_transactions(address=ADDR)

        assert seen["chainid"] == "1"
        assert seen["apikey"] == "secret-key"
        assert seen["action"] == "txlist"
        assert seen["module"] == "account"

    async def test_paginates_until_short_page(self) -> None:
        client = EtherscanClient(api_key="k", base_url=BASE, chain_id=1, page_size=2, max_pages=10)
        pages: dict[str, list[dict]] = {
            "1": [_record(f"0x{'11'*32}"), _record(f"0x{'22'*32}")],
            "2": [_record(f"0x{'33'*32}")],
        }

        def handler(request: httpx.Request) -> httpx.Response:
            p = request.url.params.get("page")
            return httpx.Response(200, json=_envelope(pages.get(p, [])))

        with respx.mock(base_url=BASE) as mock:
            mock.get("").mock(side_effect=handler)
            txs = await client.get_native_transactions(address=ADDR)

        assert len(txs) == 3
        assert txs[0]["hash"] == f"0x{'11'*32}"

    async def test_no_transactions_message_returns_empty(self) -> None:
        client = EtherscanClient(api_key="k", base_url=BASE, chain_id=1)
        with respx.mock(base_url=BASE) as mock:
            mock.get("").mock(
                return_value=httpx.Response(200, json=_envelope([], status="0", message="No transactions found"))
            )
            assert await client.get_native_transactions(address=ADDR) == []

    async def test_rate_limit_message_raises(self) -> None:
        client = EtherscanClient(api_key="k", base_url=BASE, chain_id=1)
        with respx.mock(base_url=BASE) as mock:
            mock.get("").mock(
                return_value=httpx.Response(
                    200, json=_envelope([], status="0", message="Max rate limit reached, please try again later.")
                )
            )
            with pytest.raises(RateLimitError):
                await client.get_native_transactions(address=ADDR)

    async def test_missing_api_key_raises_with_hint(self) -> None:
        # Realistic Etherscan NOTOK envelope with the key hint in `result`.
        client = EtherscanClient(api_key="", base_url=BASE, chain_id=1)
        with respx.mock(base_url=BASE) as mock:
            mock.get("").mock(
                return_value=httpx.Response(
                    200,
                    json=_envelope(
                        "Missing/Invalid API Key", status="0", message="NOTOK"
                    ),
                )
            )
            with pytest.raises(ProviderError, match="ETHERSCAN_API_KEY"):
                await client.get_native_transactions(address=ADDR)

    async def test_http_429_raises_rate_limit(self) -> None:
        client = EtherscanClient(api_key="k", base_url=BASE, chain_id=1)
        with respx.mock(base_url=BASE) as mock:
            mock.get("").mock(return_value=httpx.Response(429))
            with pytest.raises(RateLimitError):
                await client.get_native_transactions(address=ADDR)

    async def test_http_500_raises_provider_error(self) -> None:
        client = EtherscanClient(api_key="k", base_url=BASE, chain_id=1)
        with respx.mock(base_url=BASE) as mock:
            mock.get("").mock(return_value=httpx.Response(500, text="boom"))
            with pytest.raises(ProviderError, match="HTTP 500"):
                await client.get_native_transactions(address=ADDR)