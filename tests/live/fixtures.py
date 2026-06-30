"""
Curated known-valid sample IDs + a param-name -> value resolver for live probing.

Two halves:

1. ``FIXTURES`` — static, known-good values keyed by the *parameter name* used
   across the impls (collected from the union of impl signatures). The audit
   harness introspects each impl's signature and pulls values from here by name,
   so we don't hand-author kwargs for every one of ~80 operations.

2. ``discover_*`` — async helpers that hit live *list* endpoints to fill IDs we
   can't safely hard-code (a current nomination/treaty/amendment/vote/report
   number), so the audit never probes a guessed ID that 404s. Results are cached
   for the run.

Committee codes intentionally carry the numeric suffix (``hsju00`` not ``hsju``):
the live API rejects bare codes with "Data not found" (confirmed).
"""
from typing import Any, Dict, Optional

from congress_api.core.client_handler import make_api_request

# 119th Congress is the current one as of 2026.
CURRENT_CONGRESS = 119

# Static, known-valid sample values keyed by impl parameter name.
FIXTURES: Dict[str, Any] = {
    # paging / shaping — kept small so probes are cheap
    "limit": 5,
    "offset": 0,
    "sort": "updateDate+desc",
    "format": "json",
    "format_type": "formatted",
    # congress / chamber / session
    "congress": CURRENT_CONGRESS,
    "chamber": "house",
    "session": 1,
    # The bound congressional record only covers 1873-1997 in the API, so a
    # current year correctly validation-fails. Use a historical date.
    "year": 1994,
    "month": 1,
    "day": 25,
    "ordinal": 1,   # nominee position index (NOT the congress number)
    "start_year": 2023,
    "end_year": 2024,
    # members
    "bioguide_id": "K000397",   # proven live in prior smoke test
    "state": "CA",
    "state_code": "CA",
    "district": 1,
    "party": "D",
    "name": "Smith",
    "current_member": True,
    "current": True,
    # committees
    "committee_code": "hsju00",  # House Judiciary, valid live
    "committee_type": "standing",
    # bills / amendments / laws
    "bill_type": "hr",
    "bill_number": 1,
    "amendment_type": "samdt",
    "law_type": "pub",
    "law_number": 1,
    # search
    "keywords": "energy",
    "topic": "energy",
    # dates (both snake and camel variants appear across impls).
    # Range must fall INSIDE the 119th Congress (Jan 2025 - Jan 2027), else
    # date-filtered searches correctly return nothing and look falsely "empty".
    "from_date": "2025-01-01",
    "to_date": "2026-06-30",
    "from_date_time": "2025-01-01T00:00:00Z",
    "to_date_time": "2026-06-30T23:59:59Z",
    "fromDateTime": "2025-01-01T00:00:00Z",
    "toDateTime": "2026-06-30T23:59:59Z",
    "scheduled_from": "2025-01-01T00:00:00Z",
    "scheduled_to": "2026-06-30T23:59:59Z",
    # communications
    "communication_type": "ec",
    "report_type": "hrpt",
    # congressional record chunking
    "chunk_number": 1,
    "chunk_size": 5,
    "detailed": False,
    "conference": False,
}

# IDs that must be discovered live (no safe static default). Filled by discover_*.
_DISCOVERY_CACHE: Dict[str, Any] = {}

# Maps a parameter name to the discovery coroutine that can fill it.
# (name) -> (discover_fn_key)
_DISCOVERABLE = {
    "nomination_number": "nomination",
    "treaty_number": "treaty",
    "treaty_suffix": "treaty_suffix",
    "amendment_number": "amendment",
    "vote_number": "house_vote",
    "report_number": "committee_report",
    "communication_number": "house_communication",
    "requirement_number": "house_requirement",
    "jacket_number": "hearing",
    "event_id": "committee_meeting",
    "volume_number": "bound_record_volume",
    "issue_number": "daily_record_issue",
}


async def _list_first(ctx, endpoint: str, container: str, item_key: str,
                      params: Optional[Dict[str, Any]] = None):
    """Fetch a list endpoint and return item_key of the first element, or None."""
    data = await make_api_request(endpoint, ctx, params or {"limit": 1})
    if not isinstance(data, dict) or "error" in data:
        return None, data
    items = data.get(container)
    # container can be a list directly or nested
    if isinstance(items, dict):
        # e.g. {"committee-bills": {"bills": [...]}}
        for v in items.values():
            if isinstance(v, list):
                items = v
                break
    if not isinstance(items, list) or not items:
        return None, data
    return items[0].get(item_key), data


async def discover(ctx, fn_key: str):
    """Discover a single live ID by key, caching the result for the run."""
    if fn_key in _DISCOVERY_CACHE:
        return _DISCOVERY_CACHE[fn_key]

    c = CURRENT_CONGRESS
    val = None
    if fn_key == "nomination":
        val, _ = await _list_first(ctx, f"/nomination/{c}", "nominations", "number")
    elif fn_key == "treaty":
        val, _ = await _list_first(ctx, f"/treaty/{c}", "treaties", "number")
    elif fn_key == "treaty_suffix":
        val = None  # most treaties have no suffix; leave unset
    elif fn_key == "amendment":
        val, _ = await _list_first(ctx, f"/amendment/{c}/samdt", "amendments", "number")
    elif fn_key == "house_vote":
        val, _ = await _list_first(ctx, f"/house-vote/{c}/1", "houseRollCallVotes", "rollCallNumber")
    elif fn_key == "committee_report":
        val, _ = await _list_first(ctx, f"/committee-report/{c}/hrpt", "reports", "number")
    elif fn_key == "house_communication":
        val, _ = await _list_first(ctx, f"/house-communication/{c}/ec", "houseCommunications", "number")
    elif fn_key == "house_requirement":
        val, _ = await _list_first(ctx, "/house-requirement", "houseRequirements", "number")
    elif fn_key == "hearing":
        val, _ = await _list_first(ctx, f"/hearing/{c}", "hearings", "jacketNumber")
    elif fn_key == "committee_meeting":
        val, _ = await _list_first(ctx, f"/committee-meeting/{c}", "committeeMeetings", "eventId")
    elif fn_key == "bound_record_volume":
        val = None
    elif fn_key == "daily_record_issue":
        val = None

    # Numeric IDs come back as JSON strings; coerce so impls that do integer
    # comparisons (e.g. ``amendment_number <= 0``) get the int they expect —
    # FastMCP would coerce these in real MCP usage from the int type hint.
    if isinstance(val, str) and val.isdigit():
        val = int(val)
    _DISCOVERY_CACHE[fn_key] = val
    return val


async def resolve_param(ctx, name: str):
    """Resolve a single parameter name to a live-valid value.

    Returns (value, ok). ok=False means we could not supply this param (caller
    should record the surface as fixture-blocked rather than crash on it).
    """
    if name in FIXTURES:
        return FIXTURES[name], True
    if name in _DISCOVERABLE:
        val = await discover(ctx, _DISCOVERABLE[name])
        return val, val is not None
    return None, False
