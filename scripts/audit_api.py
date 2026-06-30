"""
Live API-conformance audit harness for congressMCP (Phase 1 infrastructure).

For every actively-called tool/operation this script:
  1. Resolves the underlying impl function (auto-parsed from each bucket's
     ``route_*_operation`` if/elif ladder + the direct member/committee wrappers).
  2. Introspects the impl signature and fills kwargs from ``tests/live/fixtures``
     (discovering live IDs where needed).
  3. Calls the impl IN-PROCESS against the live API through a recording httpx
     client (no MCP server, no redeploy).
  4. Classifies the outcome (OK / EMPTY / API-ERROR / CRASH / FIXTURE-BLOCKED)
     and records the *actual live response keys* vs the *keys the code reads*
     (static-extracted from the impl source) — surfacing the #30 response-key
     class where they differ.

Output: a markdown table to stdout (Phase 2 promotes it to
``documentation/API_AUDIT.md``). Requires ``CONGRESS_API_KEY``.

Usage:
    python scripts/audit_api.py            # full sweep
    python scripts/audit_api.py --smoke    # 3 representative surfaces only
"""
import argparse
import asyncio
import inspect
import json
import os
import re
import sys
import traceback

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Load CONGRESS_API_KEY from the plugin config if not already in env (avoids
# echoing the key on the command line / into transcripts).
if not os.getenv("CONGRESS_API_KEY"):
    import glob
    for cfg in glob.glob(os.path.expanduser(
            "~/AppData/Roaming/Claude/local-agent-mode-sessions/*/*/rpm/plugin_*/.mcp.json")):
        try:
            d = json.load(open(cfg))
            k = d.get("mcpServers", {}).get("congressmcp", {}).get("env", {}).get("CONGRESS_API_KEY")
            if k:
                os.environ["CONGRESS_API_KEY"] = k
                break
        except Exception:
            pass

from tests.live.live_context import live_context, get_api_key
from tests.live import fixtures

# ---------------------------------------------------------------------------
# 1. Build the surface inventory by parsing the route ladders.
# ---------------------------------------------------------------------------

# Routers/buckets whose route_* function maps operation -> impl.
_ROUTERS = [
    ("bills", "congress_api.features.bills_tool", "route_bills_operation"),
    ("amendments", "congress_api.features.amendments_tool", "route_amendments_operation"),
    ("treaties_and_summaries", "congress_api.features.treaties_and_summaries_tool", "route_treaties_summaries_operation"),
    ("committee_intelligence", "congress_api.features.buckets.committee_intelligence", "route_committee_intelligence_operation"),
    ("records_and_hearings", "congress_api.features.buckets.records_and_hearings", "route_records_and_hearings_operation"),
    ("research_and_professional", "congress_api.features.buckets.research_and_professional", "route_research_and_professional_operation"),
    ("voting_and_nominations", "congress_api.features.buckets.voting_and_nominations", "route_voting_and_nominations_operation"),
]

# Direct member/committee wrappers (tool == operation), impl lives in committees/members.
_DIRECT = [
    ("search_members", "congress_api.features.members", "search_members"),
    ("get_member_details", "congress_api.features.members", "get_member_details"),
    ("get_member_sponsored_legislation", "congress_api.features.members", "get_member_sponsored_legislation"),
    ("get_member_cosponsored_legislation", "congress_api.features.members", "get_member_cosponsored_legislation"),
    ("get_members_by_congress", "congress_api.features.members", "get_members_by_congress"),
    ("get_members_by_state", "congress_api.features.members", "get_members_by_state"),
    ("get_members_by_district", "congress_api.features.members", "get_members_by_district"),
    ("get_members_by_congress_state_district", "congress_api.features.members", "get_members_by_congress_state_district"),
    ("search_committees", "congress_api.features.committees", "search_committees"),
    ("get_committee_bills", "congress_api.features.committees", "get_committee_bills"),
    ("get_committee_reports", "congress_api.features.committees", "get_committee_reports"),
    ("get_committee_communications", "congress_api.features.committees", "get_committee_communications"),
    ("get_committee_nominations", "congress_api.features.committees", "get_committee_nominations"),
    ("get_laws", "congress_api.features.buckets.laws", "get_laws"),
    ("get_law_details", "congress_api.features.buckets.laws", "get_law_details"),
]

_LADDER_RE = re.compile(
    r'operation\s*==\s*"(?P<op>[^"]+)".*?from\s+(?P<mod>\.[\w.]+)\s+import\s+(?P<fn>\w+)',
    re.DOTALL,
)


def _resolve_relative(base_module: str, rel: str) -> str:
    """Resolve a relative import as Python would, relative to base_module.

    e.g. from 'congress_api.features.buckets.voting_and_nominations':
      '..nominations'   -> 'congress_api.features.nominations'
    from 'congress_api.features.bills_tool':
      '.buckets.bills'  -> 'congress_api.features.buckets.bills'
    """
    dots = len(rel) - len(rel.lstrip("."))
    tail = rel[dots:]
    pkg = base_module.split(".")[:-1]          # package containing the module
    up = dots - 1                              # one dot = same package
    target = pkg[: len(pkg) - up] if up else pkg
    return ".".join(target + ([tail] if tail else []))


def build_inventory():
    """Return list of surfaces: dict(tool, operation, impl_module, impl_func)."""
    surfaces = []
    for tool, mod_name, route_fn in _ROUTERS:
        mod = __import__(mod_name, fromlist=[route_fn])
        src = inspect.getsource(getattr(mod, route_fn))
        for m in _LADDER_RE.finditer(src):
            impl_mod = _resolve_relative(mod_name, m.group("mod"))
            surfaces.append({"tool": tool, "operation": m.group("op"),
                             "impl_module": impl_mod, "impl_func": m.group("fn")})
    for tool, impl_mod, impl_fn in _DIRECT:
        surfaces.append({"tool": tool, "operation": tool,
                         "impl_module": impl_mod, "impl_func": impl_fn})
    return surfaces


# ---------------------------------------------------------------------------
# 2. Static extraction of the response keys the code reads.
# ---------------------------------------------------------------------------

_KEY_RE = re.compile(r'(?:\.get\(\s*["\']([a-zA-Z][\w-]*)["\']|\[\s*["\']([a-zA-Z][\w-]*)["\']\s*\])')
# Generic container keys worth diffing against live top-level keys.
_INTEREST = {"bills", "reports", "communications", "nominations", "committees",
             "members", "amendments", "treaties", "summaries", "hearings",
             "meetings", "prints", "actions", "cosponsors", "sponsors",
             "committee-bills", "houseCommunications", "senateCommunications",
             "houseRollCallVotes", "results", "activities"}


def code_keys(fn) -> set:
    try:
        src = inspect.getsource(fn)
    except Exception:
        return set()
    keys = set()
    for m in _KEY_RE.finditer(src):
        keys.add(m.group(1) or m.group(2))
    return {k for k in keys if k in _INTEREST}


# ---------------------------------------------------------------------------
# 3. Probe a single surface live.
# ---------------------------------------------------------------------------

async def build_kwargs(ctx, fn):
    """Fill kwargs for impl `fn` from fixtures. Returns (kwargs, missing_required)."""
    kwargs = {}
    missing = []
    for p in inspect.signature(fn).parameters.values():
        if p.name in ("ctx", "args", "kwargs") or p.kind in (p.VAR_POSITIONAL, p.VAR_KEYWORD):
            continue
        required = p.default is inspect.Parameter.empty
        val, ok = await fixtures.resolve_param(ctx, p.name)
        if ok:
            kwargs[p.name] = val
        elif required:
            missing.append(p.name)
        # optional + unresolved -> just omit
    return kwargs, missing


def classify(result, recorded):
    """Classify the impl outcome from its return value + recorded API calls."""
    api_err = any(r["status"] >= 400 for r in recorded)
    text = result if isinstance(result, str) else getattr(result, "summary", str(result))
    low = (text or "").lower()
    if api_err:
        return "API-ERROR"
    if re.search(r"\berror\b", low) and ("retriev" in low or "failed" in low or low.startswith("error")
                                         or "formatting" in low or "processing" in low):
        return "ERROR"
    # EMPTY only when the *result set* is empty. Require "found/matching/results"
    # so incidental phrases like "No URL available" don't trip a false EMPTY.
    if re.search(r"\bno [\w ]{0,40}?(found|matching)\b", low) or "found 0 " in low or "0 results" in low:
        return "EMPTY"
    return "OK"


async def probe(ctx, surface):
    """Probe one surface; returns a result row dict."""
    row = {**surface, "status": "", "endpoint": "", "live_top_keys": "",
           "code_keys": "", "key_diff": "", "detail": ""}
    try:
        mod = __import__(surface["impl_module"], fromlist=[surface["impl_func"]])
        fn = getattr(mod, surface["impl_func"])
    except Exception as e:
        row["status"] = "IMPORT-FAIL"
        row["detail"] = f"{type(e).__name__}: {e}"
        return row

    row["code_keys"] = ",".join(sorted(code_keys(fn))) or "-"

    kwargs, missing = await build_kwargs(ctx, fn)
    if missing:
        row["status"] = "FIXTURE-BLOCKED"
        row["detail"] = "missing: " + ",".join(missing)
        return row

    ctx.client.calls.clear()
    try:
        result = await fn(ctx, **kwargs)
    except TypeError as e:
        row["status"] = "SIGNATURE-BUG"
        row["detail"] = str(e)
        return row
    except Exception as e:
        row["status"] = "CRASH"
        row["detail"] = f"{type(e).__name__}: {e}"
        return row

    recorded = list(ctx.client.calls)
    if recorded:
        last = recorded[-1]
        row["endpoint"] = last["path"].split("?")[0]
        row["live_top_keys"] = ",".join(last["top_keys"][:8])
        # diff: code reads a container key absent from live top-level but present nested
        ck = code_keys(fn)
        live_top = set().union(*[set(r["top_keys"]) for r in recorded])
        nested = {}
        for r in recorded:
            nested.update(r["nested_keys"])
        nested_all = set().union(*[set(v) for v in nested.values()]) if nested else set()
        diffs = []
        for k in ck:
            if k not in live_top:
                where = [parent for parent, kids in nested.items() if k in kids]
                if where:
                    diffs.append(f"{k}<-{where[0]}.{k}")
                elif k in nested:  # code key is itself a nesting parent present nested
                    pass
        row["key_diff"] = "; ".join(diffs)
    row["status"] = classify(result, recorded)
    if row["key_diff"] and row["status"] == "EMPTY":
        row["status"] = "RESPONSE-KEY-BUG?"
    return row


# ---------------------------------------------------------------------------
# 4. Run + emit.
# ---------------------------------------------------------------------------

_SMOKE = {"get_member_sponsored_legislation", "get_committee_bills", "get_nomination_details"}


def emit_markdown(rows):
    out = ["# congressMCP Live API Audit (auto-generated)", ""]
    out.append("| Tool | Operation | Status | Endpoint | Live top-keys | Code keys | Key diff | Detail |")
    out.append("|---|---|---|---|---|---|---|---|")
    for r in rows:
        out.append("| {tool} | {operation} | {status} | {endpoint} | {live_top_keys} | {code_keys} | {key_diff} | {detail} |".format(
            **{k: str(v).replace("|", "\\|")[:120] for k, v in r.items()}))
    # summary counts
    from collections import Counter
    c = Counter(r["status"] for r in rows)
    out += ["", "## Summary", ""]
    for k, v in c.most_common():
        out.append(f"- {k}: {v}")
    return "\n".join(out)


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="probe 3 representative surfaces only")
    ap.add_argument("--out", default=None, help="write markdown to this file")
    args = ap.parse_args()

    if not get_api_key():
        print("ERROR: CONGRESS_API_KEY not set", file=sys.stderr)
        return 2

    inventory = build_inventory()
    if args.smoke:
        inventory = [s for s in inventory if s["operation"] in _SMOKE]

    rows = []
    async with live_context() as ctx:
        for s in inventory:
            try:
                row = await probe(ctx, s)
            except Exception as e:
                row = {**s, "status": "HARNESS-ERROR", "endpoint": "", "live_top_keys": "",
                       "code_keys": "", "key_diff": "", "detail": traceback.format_exc(limit=1)}
            rows.append(row)
            print(f"  [{row['status']:>18}] {s['tool']}/{s['operation']}", file=sys.stderr)
            await asyncio.sleep(0.15)  # rate-limit hygiene

    md = emit_markdown(rows)
    if args.out:
        open(args.out, "w", encoding="utf-8").write(md)
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
