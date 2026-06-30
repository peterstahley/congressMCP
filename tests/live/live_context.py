"""
Live in-process Context for hitting the real Congress.gov API.

Every impl in congress_api flows API calls through
``core.client_handler.make_api_request(endpoint, ctx, params)``, which only
needs ``ctx.request_context.lifespan_context.{client, api_key}`` and a sync
``ctx.error(...)``. This module builds the smallest fake ``ctx`` that satisfies
that contract against a real ``httpx.AsyncClient``, so the audit harness and the
live test layer can call the underlying async functions directly — no MCP server,
no redeploy.

Usage::

    async with live_context() as ctx:
        data = await make_api_request("/bill/119/hr/1", ctx)
"""
import os
import logging
from contextlib import asynccontextmanager

import httpx

from congress_api.core.api_config import BASE_URL
from congress_api.core.client_handler import AppContext

logger = logging.getLogger(__name__)

# httpx logs full request URLs (including the api_key query param) at INFO.
# Silence it so the key never lands in test output / transcripts.
logging.getLogger("httpx").setLevel(logging.WARNING)


class _NoopReporter:
    """Tolerant stand-in for MCP Context logging methods.

    Accepts any args, is safe whether called or awaited (returns an awaitable
    no-op), so it covers ctx.error/info/warning/debug regardless of how an impl
    invokes them.
    """

    def __call__(self, *args, **kwargs):
        async def _coro():
            return None
        # Return an awaitable; sync callers that ignore the result are unaffected.
        return _coro()


class RecordingClient(httpx.AsyncClient):
    """httpx client that records every GET (endpoint + live response keys).

    Wrapping at the client layer captures *every* real API call regardless of
    which ``safe_*_request`` wrapper made it — no monkeypatching of app code.
    The audit harness clears ``calls`` before each surface and inspects it after.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.calls: list[dict] = []

    async def get(self, url, *args, **kwargs):
        response = await super().get(url, *args, **kwargs)
        record = {"path": str(url), "status": response.status_code,
                  "top_keys": [], "nested_keys": {}}
        try:
            data = response.json()
            if isinstance(data, dict):
                record["top_keys"] = list(data.keys())
                # capture one level of nesting for dict-valued keys (the #30 class)
                for k, v in data.items():
                    if isinstance(v, dict):
                        record["nested_keys"][k] = list(v.keys())
        except Exception:
            pass
        self.calls.append(record)
        return response


class _FakeRequestContext:
    def __init__(self, lifespan_context):
        self.lifespan_context = lifespan_context


class LiveContext:
    """Minimal duck-typed replacement for mcp ... Context."""

    def __init__(self, app_ctx: AppContext):
        self.request_context = _FakeRequestContext(app_ctx)
        # impls only call ctx.error today; provide the common set defensively.
        self.error = _NoopReporter()
        self.info = _NoopReporter()
        self.warning = _NoopReporter()
        self.warn = _NoopReporter()
        self.debug = _NoopReporter()

    async def report_progress(self, *args, **kwargs):  # pragma: no cover - unused
        return None


def get_api_key() -> str | None:
    """Return the live API key, loading it from the plugin config if not in env.

    Reads CONGRESS_API_KEY from env first; otherwise falls back to the installed
    plugin's .mcp.json so ``pytest tests/live`` works without exporting the key
    on the command line (which would echo it into transcripts).
    """
    key = os.getenv("CONGRESS_API_KEY")
    if key:
        return key
    import glob
    import json
    for cfg in glob.glob(os.path.expanduser(
            "~/AppData/Roaming/Claude/local-agent-mode-sessions/*/*/rpm/plugin_*/.mcp.json")):
        try:
            d = json.load(open(cfg))
            k = d.get("mcpServers", {}).get("congressmcp", {}).get("env", {}).get("CONGRESS_API_KEY")
            if k:
                os.environ["CONGRESS_API_KEY"] = k
                return k
        except Exception:
            pass
    return None


@asynccontextmanager
async def live_context():
    """Async context manager yielding a live LiveContext with a real httpx client."""
    api_key = get_api_key()
    timeout = httpx.Timeout(30.0, connect=10.0)
    async with RecordingClient(base_url=BASE_URL, timeout=timeout, follow_redirects=True) as client:
        app_ctx = AppContext(api_key=api_key or "MISSING_API_KEY", client=client)
        ctx = LiveContext(app_ctx)
        ctx.client = client  # expose the recorder to the harness
        yield ctx
