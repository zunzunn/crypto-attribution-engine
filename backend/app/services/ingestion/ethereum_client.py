"""Low-level Etherscan (Etherscan API V2) HTTP client.

This class only talks HTTP and returns raw JSON payloads. It never normalizes
(that's the normalizer's job) and never touches the database. Rate-limit and
API-key errors surface as typed exceptions (see app/core/errors.py).
"""

from __future__ import annotations

import json

import httpx

from app.core.errors import ProviderError, RateLimitError

_EMPTY_MESSAGES = {
    "no transactions found",
    "no records found",
    "transactions not found",
    "not found",
    "no blocks found",
}


class EtherscanClient:
    def __init__(
        self,
        *,
        api_key: str,
        base_url: str,
        chain_id: int,
        timeout_seconds: float = 30.0,
        page_size: int = 1000,
        max_pages: int = 20,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._api_key = api_key
        self._base_url = base_url
        self._chain_id = chain_id
        self._timeout = timeout_seconds
        self._page_size = page_size
        self._max_pages = max_pages
        self._transport = transport

    # ------------------------------------------------------------------ #
    # Public-API
    # ------------------------------------------------------------------ #
    async def get_native_transactions(self, address: str) -> list[dict]:
        """Fetch ALL native (ETH) transactions for ``address`` (paginated,
        oldest-first). Returns a list of raw Etherscan JSON records."""
        collected: list[dict] = []
        page = 1
        while True:
            page_items = await self._fetch_page(address, page)
            collected.extend(page_items)
            if (
                not page_items
                or len(page_items) < self._page_size
                or page >= self._max_pages
            ):
                break
            page += 1
        return collected

    # ------------------------------------------------------------------ #
    # Internals
    # ------------------------------------------------------------------ #
    async def _fetch_page(self, address: str, page: int) -> list[dict]:
        params = {
            "chainid": str(self._chain_id),
            "module": "account",
            "action": "txlist",
            "address": address,
            "startblock": "0",
            "endblock": "99999999",
            "page": str(page),
            "offset": str(self._page_size),
            "sort": "asc",
            "apikey": self._api_key,
        }
        body = await self._get_json(params)
        return self._unwrap(body)

    async def _get_json(self, params: dict) -> dict:
        async with httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            transport=self._transport,
        ) as client:
            response = await client.get("", params=params)
        if response.status_code == 429:
            raise RateLimitError("Etherscan rate limit exceeded (HTTP 429)")
        if response.status_code != 200:
            raise ProviderError(
                f"Etherscan returned HTTP {response.status_code}: {response.text[:200]}"
            )
        try:
            return response.json()
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise ProviderError("Etherscan returned non-JSON response") from exc

    @staticmethod
    def _unwrap(body: dict) -> list[dict]:
        status = str(body.get("status", ""))
        message = str(body.get("message", "")).lower()
        result = body.get("result")
        result_text = str(result)[:200].lower() if result is not None else ""

        if status == "1" and isinstance(result, list):
            return result

        if message in _EMPTY_MESSAGES or "no transactions" in message:
            return []
        if "rate limit" in message or "rate limit" in result_text:
            raise RateLimitError(f"Etherscan rate limit exceeded: {body.get('message')}")
        if "api key" in message or "api key" in result_text:
            raise ProviderError(
                "Etherscan rejected the API key. Set ETHERSCAN_API_KEY in backend/.env. "
                f"(provider: {body.get('result')})"
            )
        raise ProviderError(f"Etherscan API error ({body.get('message')}). Raw: {str(result)[:300]}")