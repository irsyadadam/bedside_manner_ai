"""NCBI E-utilities client with rate limiting and tenacity retry.

Endpoints implemented: ESearch, ESummary, EFetch. All accept either an
explicit `ids` list or a `webenv` + `query_key` pair from a prior
ESearch with `usehistory="y"`.

Rate limit is a simple sliding-window: the client never issues two
requests less than `1 / rate` seconds apart. NCBI's published limits
are 3 req/s without an API key and 10 req/s with one.
"""
from __future__ import annotations

import logging
import threading
import time
from typing import Any

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

log = logging.getLogger(__name__)

_RETRYABLE = (
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    requests.exceptions.HTTPError,
    requests.exceptions.ChunkedEncodingError,
)


class RateLimiter:
    """Thread-safe minimum-interval limiter."""

    def __init__(self, rate_per_sec: float) -> None:
        if rate_per_sec <= 0:
            raise ValueError("rate_per_sec must be > 0")
        self.min_interval = 1.0 / rate_per_sec
        self._last = 0.0
        self._lock = threading.Lock()

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            delta = now - self._last
            if delta < self.min_interval:
                time.sleep(self.min_interval - delta)
            self._last = time.monotonic()


class EUtilsError(RuntimeError):
    pass


class EUtilsClient:
    BASE = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(
        self,
        tool: str,
        email: str,
        api_key: str | None,
        rate_per_sec: float,
        timeout: float = 60.0,
    ) -> None:
        self.tool = tool
        self.email = email
        self.api_key = api_key
        self.timeout = timeout
        self.limiter = RateLimiter(rate_per_sec)
        self.session = requests.Session()

    # -- internal ---------------------------------------------------------

    def _common(self) -> dict[str, str]:
        p = {"tool": self.tool, "email": self.email}
        if self.api_key:
            p["api_key"] = self.api_key
        return p

    @retry(
        wait=wait_exponential(multiplier=1, min=1, max=30),
        stop=stop_after_attempt(6),
        retry=retry_if_exception_type(_RETRYABLE),
        before_sleep=before_sleep_log(log, logging.WARNING),
        reraise=True,
    )
    def _get(self, endpoint: str, params: dict[str, Any]) -> requests.Response:
        self.limiter.wait()
        merged = {**self._common(), **params}
        r = self.session.get(
            f"{self.BASE}/{endpoint}", params=merged, timeout=self.timeout
        )
        # Treat 429/5xx as retryable; raise so tenacity can catch.
        if r.status_code == 429 or r.status_code >= 500:
            r.raise_for_status()
        r.raise_for_status()
        return r

    # -- public endpoints -------------------------------------------------

    def esearch(
        self,
        db: str,
        term: str,
        retmax: int = 10000,
        retstart: int = 0,
        use_history: bool = True,
    ) -> dict:
        params: dict[str, Any] = {
            "db": db,
            "term": term,
            "retmax": retmax,
            "retstart": retstart,
            "retmode": "json",
        }
        if use_history:
            params["usehistory"] = "y"
        r = self._get("esearch.fcgi", params)
        payload = r.json()
        result = payload.get("esearchresult")
        if result is None or "ERROR" in result:
            raise EUtilsError(f"ESearch error: {payload}")
        return result

    def esummary(
        self,
        db: str,
        ids: list[str] | None = None,
        webenv: str | None = None,
        query_key: str | None = None,
        retstart: int = 0,
        retmax: int = 200,
    ) -> dict:
        params: dict[str, Any] = {"db": db, "retmode": "json"}
        if ids:
            params["id"] = ",".join(ids)
        elif webenv and query_key:
            params["WebEnv"] = webenv
            params["query_key"] = query_key
            params["retstart"] = retstart
            params["retmax"] = retmax
        else:
            raise ValueError("ESummary needs either ids or (webenv, query_key)")
        r = self._get("esummary.fcgi", params)
        payload = r.json()
        result = payload.get("result")
        if result is None:
            raise EUtilsError(f"ESummary error: {payload}")
        return result

    def efetch(
        self,
        db: str,
        ids: list[str] | None = None,
        webenv: str | None = None,
        query_key: str | None = None,
        retstart: int = 0,
        retmax: int = 50,
        rettype: str = "xml",
        retmode: str = "xml",
    ) -> str:
        params: dict[str, Any] = {"db": db, "rettype": rettype, "retmode": retmode}
        if ids:
            params["id"] = ",".join(ids)
        elif webenv and query_key:
            params["WebEnv"] = webenv
            params["query_key"] = query_key
            params["retstart"] = retstart
            params["retmax"] = retmax
        else:
            raise ValueError("EFetch needs either ids or (webenv, query_key)")
        r = self._get("efetch.fcgi", params)
        return r.text
