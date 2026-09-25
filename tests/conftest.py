"""Test harness: every example runs against a fake Cerebrus Pulse API.

The examples reach the API through httpx.Client, both directly (the free /demo
and /health calls) and through the cerebrus-pulse SDK. The ``api`` fixture
swaps httpx.Client for one bound to an httpx.MockTransport, so no test touches
the network, and it records every path requested.

Responses come from fixtures/api_responses.json: real engine output captured on
2026-09-24 (see its ``_meta``).
"""

from __future__ import annotations

import base64
import importlib.util
import json
import pathlib

import httpx
import pytest
from cerebrus_pulse.payment import DEFAULT_ALLOWED_PAYTO

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESPONSES = json.loads((ROOT / "tests" / "fixtures" / "api_responses.json").read_text(encoding="utf-8"))

PAID_PREFIXES = (
    "/pulse/", "/sentiment", "/funding/", "/bundle/", "/screener", "/oi/", "/spread/",
    "/correlation", "/arb", "/cex-dex/", "/basis/", "/depeg", "/liquidations/",
)
FREE_PATHS = ("/health", "/demo/")

# What the gateway's paid routes cost, in atomic USDC (6 decimals).
PRICES = {"/pulse/": 25_000, "/sentiment": 10_000, "/funding/": 10_000,
          "/cex-dex/": 20_000, "/liquidations/": 30_000}
BASE_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
PAY_TO = DEFAULT_ALLOWED_PAYTO  # the SDK's default payee, so a payTo change is made once
DUMMY_KEY = "0x" + "11" * 32  # obviously fake, never funded: signs locally, can never settle


def load_example(relpath: str):
    """Import an example script by path (its folder name is not a package name)."""
    path = ROOT / relpath
    spec = importlib.util.spec_from_file_location(f"example_{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def payment_required(path: str) -> httpx.Response:
    """A 402 shaped like the gateway's: x402 v2 terms in the PAYMENT-REQUIRED header."""
    amount = next(v for k, v in PRICES.items() if path.startswith(k))
    terms = {"x402Version": 2, "accepts": [{
        "scheme": "exact", "network": "eip155:8453", "asset": BASE_USDC,
        "amount": str(amount), "payTo": PAY_TO, "maxTimeoutSeconds": 300,
        "extra": {"name": "USD Coin", "version": "2"},
    }]}
    header = base64.b64encode(json.dumps(terms).encode()).decode()
    return httpx.Response(402, headers={"PAYMENT-REQUIRED": header}, json={})


class FakeAPI:
    """Answers from the fixtures.

    ``unpaid`` makes every paid path answer 402. ``paying`` makes a paid path
    answer 402 until the request carries an x402 PAYMENT-SIGNATURE.
    """

    def __init__(self):
        self.routes: dict[str, object] = {k: v for k, v in RESPONSES.items() if k.startswith("/")}
        self.unpaid = False
        self.paying = False
        self.requests: list[httpx.Request] = []

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        path = request.url.path
        signed = bool(request.headers.get("PAYMENT-SIGNATURE"))
        if path.startswith(PAID_PREFIXES) and (self.unpaid or (self.paying and not signed)):
            return payment_required(path)
        body = self.routes.get(path)
        if isinstance(body, httpx.Response):
            return body
        if body is None:
            return httpx.Response(404, json={"detail": f"no fixture for {path}"})
        return httpx.Response(200, json=body)

    @property
    def paths(self) -> list[str]:
        return [r.url.path for r in self.requests]

    @property
    def paid_paths(self) -> list[str]:
        return [p for p in self.paths if p.startswith(PAID_PREFIXES)]


@pytest.fixture
def api(monkeypatch):
    fake = FakeAPI()
    transport = httpx.MockTransport(fake.handle)
    real_client = httpx.Client

    class Client(real_client):
        def __init__(self, *args, **kwargs):
            kwargs["transport"] = transport
            super().__init__(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", Client)
    # Never let a real wallet in the developer's environment reach a test.
    for name in ("CEREBRUS_WALLET_KEY", "CEREBRUS_MAX_PAYMENT_USD", "CEREBRUS_MAX_SPEND_USD",
                 "CEREBRUS_ALLOWED_PAYTO", "CEREBRUS_AGENT_MODEL", "OPENAI_API_KEY"):
        monkeypatch.delenv(name, raising=False)
    return fake


@pytest.fixture
def wallet(api, monkeypatch):
    """CEREBRUS_WALLET_KEY set to a fake key, and an API that wants payment first.

    The examples then pay for real with the x402 client: payments are signed
    locally and the fake API accepts them. Nothing can settle.
    """
    monkeypatch.setenv("CEREBRUS_WALLET_KEY", DUMMY_KEY)
    api.paying = True
    return api
