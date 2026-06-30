"""
Network-gated live conformance tests (Phase 1 seed).

These hit the real Congress.gov API and are skipped unless CONGRESS_API_KEY is
set. They are the shape-checking counterpart to the mocked plumbing suite: they
catch response-key/param/endpoint drift the mocks structurally cannot. The full
per-surface sweep is driven by ``scripts/audit_api.py`` (Phase 2); this module
asserts the harness's core invariants and a few representative surfaces.

Run with:  pytest tests/live -m live
"""
import pytest

from congress_api.core.client_handler import make_api_request

pytestmark = pytest.mark.live


@pytest.mark.asyncio
async def test_bill_envelope_shape(live_ctx):
    """A known bill returns the 'bill' envelope (sanity that live wiring works)."""
    data = await make_api_request("/bill/119/hr/1", live_ctx)
    assert "bill" in data, f"unexpected top-level keys: {list(data)}"


@pytest.mark.asyncio
async def test_committee_bills_nested_key(live_ctx):
    """Regression for the #30 class: committee bills nest under committee-bills.bills."""
    data = await make_api_request("/committee/senate/sseg00/bills", live_ctx)
    assert "committee-bills" in data
    assert "bills" in data["committee-bills"]


@pytest.mark.asyncio
async def test_get_committee_bills_impl_returns_data(live_ctx):
    """End-to-end: the impl must surface bills (not 'No bills found')."""
    from congress_api.features.committees import get_committee_bills
    result = await get_committee_bills(live_ctx, committee_code="hsju00", chamber="house", limit=5)
    assert "No bills found" not in result
    assert "Error" not in result[:20]


@pytest.mark.asyncio
async def test_member_sponsored_legislation_impl(live_ctx):
    """End-to-end member impl returns sponsored legislation for a known bioguide."""
    from congress_api.features.members import get_member_sponsored_legislation
    result = await get_member_sponsored_legislation(live_ctx, bioguide_id="K000397", limit=5)
    assert "Error" not in result[:20]


# --- Phase 3 fix regressions (live shape) ---

@pytest.mark.asyncio
async def test_search_summaries_browse_without_keywords(live_ctx):
    """Batch 1: search_summaries must not crash when called without a keyword."""
    from congress_api.features.summaries import search_summaries
    result = await search_summaries(live_ctx, congress=119, limit=3)
    assert "cannot be empty" not in result.lower()
    assert "ToolError" not in result


@pytest.mark.asyncio
async def test_search_committees_browse_and_filter(live_ctx):
    """Batch 1: browse (no keyword) + real client-side keyword filter."""
    from congress_api.features.committees import search_committees
    browse = await search_committees(live_ctx, chamber="house", limit=3)
    assert "Error" not in browse[:20]
    kw = await search_committees(live_ctx, keywords="judiciary", limit=5)
    assert "Judiciary" in kw


@pytest.mark.asyncio
async def test_get_bills_and_subjects_no_formatter_error(live_ctx):
    """Batch 2: bill-list and subjects formatters must not crash on live data."""
    from congress_api.features.buckets.bills import api as bills_api
    bills = await bills_api.get_bills(live_ctx, congress=119, bill_type="hr", limit=5)
    assert "Error formatting" not in bills
    subjects = await bills_api.get_bill_subjects(live_ctx, congress=119, bill_type="hr", bill_number=1)
    assert "Error formatting" not in subjects
    assert "Policy Area" in subjects


@pytest.mark.asyncio
async def test_committee_communications_correct_endpoint(live_ctx):
    """Batch 3: committee communications resolve via house/senate-communication."""
    from congress_api.features.committees import get_committee_communications
    house = await get_committee_communications(live_ctx, committee_code="hspw00", chamber="house", limit=3)
    assert "Communications for House Committee" in house
    senate = await get_committee_communications(live_ctx, committee_code="ssga00", chamber="senate", limit=3)
    assert "Communications for Senate Committee" in senate


@pytest.mark.asyncio
async def test_members_by_congress_state_district_returns_member(live_ctx):
    """Batch 3: dedicated /member/congress/{c}/{state}/{district} endpoint works."""
    from congress_api.features.members import get_members_by_congress_state_district
    result = await get_members_by_congress_state_district(live_ctx, congress=119, state_code="CA", district=5)
    assert "No members found" not in result
    assert "119th Congress" in result


@pytest.mark.asyncio
async def test_search_committee_meetings_no_404(live_ctx):
    """Batch 3: committee-meeting search no longer appends an invalid path segment."""
    from congress_api.features.committee_meetings import search_committee_meetings
    result = await search_committee_meetings(live_ctx, congress=119, chamber="house", limit=3)
    assert "Committee Meetings" in result
    assert "Error" not in result[:20]


@pytest.mark.asyncio
async def test_laws_tool_live(live_ctx):
    """Part C: laws tool lists and details enacted laws."""
    from congress_api.features.buckets import laws
    listed = await laws.get_laws(live_ctx, congress=119, law_type="pub", limit=3)
    assert "Error" not in listed[:20]
    assert "119th Congress" in listed
    detail = await laws.get_law_details(live_ctx, congress=119, law_type="pub", law_number=1)
    assert "Error" not in detail[:20]
    assert "Public Law" in detail
