"""Pytest config for the network-gated live conformance layer.

Registers the ``live`` marker and a ``live_ctx`` fixture. Live tests are skipped
unless ``CONGRESS_API_KEY`` is set, so the default ``pytest`` run (mocked, fast)
is unaffected. Run the live layer explicitly with ``pytest tests/live -m live``.
"""
import os
import sys

import pytest
import pytest_asyncio

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tests.live.live_context import live_context, get_api_key


def pytest_configure(config):
    config.addinivalue_line("markers", "live: marks tests that hit the real Congress.gov API (network + API key)")


@pytest_asyncio.fixture
async def live_ctx():
    if not get_api_key():
        pytest.skip("CONGRESS_API_KEY not set — skipping live API tests")
    async with live_context() as ctx:
        yield ctx
