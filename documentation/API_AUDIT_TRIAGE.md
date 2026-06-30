# congressMCP API Audit — Triage & Fix Plan (Phase 2 checkpoint)

Companion to the auto-generated `API_AUDIT.md` (raw harness output). This file is
the **human triage**: it separates confirmed code bugs from harness/fixture
artifacts, with the live evidence for each call, and proposes the Phase 3 fix
batches. Hand-verified by direct in-process probing against the live
Congress.gov API on 2026-06-30 (119th Congress).

## How to read the raw table
The harness (`scripts/audit_api.py`) calls each tool's **underlying impl** in
process against the live API and classifies the result. It is authoritative for
**endpoint correctness, response-key/nesting, and formatter crashes**. It is
**noisy** for two reasons that produce false EMPTY/ERROR rows:
1. **Over-fill** — it fills *every* optional filter param a search impl accepts
   (keywords + bill_type + date range + sort at once), over-constraining queries
   that then correctly return nothing. The real tool wrapper exposes fewer knobs.
2. **Blind spot** — it probes impls *directly with correct kwargs*, so it cannot
   see **wrapper↔impl signature mismatches** (the #28 / `search_committees`
   class). `search_summaries` was only caught by manually probing the wrapper.

→ Treat EMPTY/ERROR on multi-filter **search/list** ops as "verify manually,"
   not definitive. The confirmed bugs below were all hand-verified.

---

## Implementation status (Phase 3 — done 2026-06-30)

All 7 confirmed bugs below are **FIXED** on branch `production`, each with a mocked
regression test + a live shape test; the audit re-run shows every fixed surface OK.
A new **`laws` tool** was added (Part-A decision). Coverage dispositions (treaty /
CRS detail / daily-record articles / 4 filter variants → OMIT) are **final** — see
§B2. New tests: `test_wrapper_impl_signatures.py`, `test_signature_fixes.py`,
`test_formatter_fixes.py`, `test_endpoint_fixes.py`, `test_laws_tool.py`, plus live
regressions in `tests/live/test_live_conformance.py` (56 mocked + 11 live passing).

| Bug | Fix shipped |
|---|---|
| A1 get_committee_communications | endpoint → `house-communication`/`senate-communication` + matching key |
| A2 get_members_by_congress_state_district | endpoint → `/member/congress/{c}/{state}/{district}` |
| A3 search_committee_meetings | dropped invalid committee-code path segment |
| A4 search_committees | `keywords` optional; chamber via path; keyword/type filtered client-side; wrapper aligned |
| A5 search_summaries | `keywords` optional (browse mode) |
| A6 get_bills / formatters | guard null `latestAction` + null dict-valued fields |
| A7 get_bill_subjects | formatter handles the `{legislativeSubjects, policyArea}` dict shape |

## A. Confirmed code bugs (FIXED — detail retained for reference)

### Class 2 — Endpoint

**A1. `get_committee_communications` — wrong sub-resource path.** HIGH
- Builds `/committee/{chamber}/{code}/communications` → **404 for every committee**.
  The correct paths (per the official API + verified live) are chamber-specific:
  **`/committee/{chamber}/{committeeCode}/house-communication`** and
  **`/committee/{chamber}/{committeeCode}/senate-communication`** — both return
  data (`houseCommunications` / `senateCommunications`). The code just used the
  wrong path segment; `communications` is not a valid sub-resource.
- File: `congress_api/features/committees.py` (`get_committee_communications`).
- Fix: call `house-communication` for House committees and `senate-communication`
  for Senate (derive from the chamber/code), and read the matching response key.
  Straightforward endpoint fix — **no product decision needed** (earlier note
  retracted after live verification).

**A2. `get_members_by_congress_state_district` — wrong endpoint.** MEDIUM-HIGH
- Builds `/member/{state}/{district}` then filters by congress **client-side**.
  The dedicated `/member/congress/{congress}/{state}/{district}` **exists and
  returns the correct member** (verified: `/member/congress/119/CA/5` → 1 member).
- File: `congress_api/features/members.py` (`get_members_by_congress_state_district`,
  ~line 776; endpoint built ~826).
- Fix: use the congress-scoped path; drop the fragile client-side filter.

**A3. `search_committee_meetings` — over-specified path.** MEDIUM
- Builds `/committee-meeting/{congress}/{chamber}/{committee_code}` → 404.
  Valid path is `/committee-meeting/{congress}/{chamber}` (verified works);
  committee-meeting has **no committee-code path segment**.
- File: `congress_api/features/committee_meetings.py` (`search_committee_meetings`).
- Fix: drop the committee-code segment; filter by committee client-side if needed.

### Class 1 — Signature (wrapper ↔ impl)

**A4. `search_committees` — wrapper/impl mismatch.** HIGH *(known, in-scope)*
- Wrapper `(chamber, committee_type, limit)` calls impl
  `(keywords[required], chamber, congress, limit)`: passes unexpected
  `committee_type` **and** omits required `keywords` → crash.
- Files: `members_committees_tools.py` (wrapper ~363) + `committees.py`
  (`search_committees`).
- Fix: align signatures — make `keywords` optional in the impl (browse all
  committees when absent) and reconcile `committee_type` (forward it or drop it).

**A5. `search_summaries` — required `keywords` crashes browse path.** HIGH
- Impl `search_summaries(ctx, keywords, congress, ...)` makes `keywords` a
  **required positional**. Calling the `treaties_and_summaries` tool with
  `operation="search_summaries"` and no keyword → `ToolError: search_summaries()
  missing 1 required positional argument: 'keywords'`. Works fine *with* a keyword
  (verified: `keywords="energy"` → 1 summary).
- File: `congress_api/features/summaries.py` (`search_summaries`).
- Fix: default `keywords=None` and handle the no-keyword case (list recent
  summaries). Same family as A4.

### Class 4b — Formatter (reads fields that don't exist / wrong type)

**A6. `get_bills` (and likely `get_bills_by_date_range`) — null-entry crash.** HIGH
- Output: repeated `Error formatting bill: 'NoneType' object has no attribute
  'get'`. The bill-list formatter calls `.get` on bill entries that are `None`.
- Files: `congress_api/features/buckets/bills/` (`formatters.py` / `api.py`).
- Fix: guard `None`/non-dict entries in the bill-list formatter. **Verify scope**:
  confirm which list ops share this formatter (`get_recent_bills` / `search_bills`
  classified OK in the sweep, so the fix may be entry-level guarding).

**A7. `get_bill_subjects` — treats subject string as dict.** HIGH
- Output: `Error formatting subjects: 'str' object has no attribute 'get'`.
  Live `/bill/119/hr/1/subjects` returns subjects whose items the formatter
  reads as dicts but at least one is a string.
- Files: `congress_api/features/buckets/bills/` (subjects formatter).
- Fix: handle str-vs-dict subject items.

---

## B. Not bugs — harness/fixture artifacts (no code change)

| Surface | Raw status | Why it's not a bug |
|---|---|---|
| `search_treaties` | API-ERROR | Over-fill (`topic`+dates). Base call `(congress, limit)` works. |
| `search_bills`, `get_bill_summaries` | EMPTY/ERROR | Over-fill (`bill_type`+`keywords`+dates). Both work at base; `get_bill_summaries` returns the OBBBA summary. |
| `get_hearing_details`, `get_hearing_content` | API-ERROR | Fixture chamber/jacket mismatch — discovery pulled a jacket whose chamber ≠ `house`. Path `/hearing/{congress}/{chamber}/{jacket}` is valid. |
| `get_committee_nominations` | EMPTY | Nominations are Senate-only; fixture passed a House code (`hsju00`). Works for Senate codes (`ssju00` → PN1127…). |
| `get_nomination_actions/committees/hearings/nominees` | EMPTY | Sparse fixture nomination (PN786 has no sub-data). `nominees` endpoint also needed `ordinal=1` fixture fix (was wrongly the congress). |
| `get_amendment_sponsors/amendments` | EMPTY | Sparse fixture amendment (SAMDT 1 has none). |
| `search_congressional_record` | EMPTY | Code reads the capitalized `Results`/`Issues` keys correctly; over-fill/param noise. |
| `get_house_requirement_matching_communications` | EMPTY | Requirement 12478 genuinely has no matches. |
| `search_bound_congressional_record` | (was ERROR) | Impl correctly restricts to 1873–1997 (bound record is historical-only); fixture year fixed to 1994. |
| `get_member_details` | (was EMPTY) | Classifier false positive on "No URL available"; now OK after classifier tightening. |
| `get_*_communication_details` (3) | FIXTURE-BLOCKED | Discovery field fixed (`number`); senate/committee detail still need committee-specific IDs. |

---

## B2. Coverage vs. the official api.congress.gov list — decisions register

**Principle:** API completeness is *not* the goal. Coverage is driven by actual
use, and an endpoint we choose not to wrap is a **documented decision**, not a
silent gap. This register records each unwrapped/partial endpoint with a
recommended disposition so the omission is deliberate and auditable. The audit
itself probed **all 20 registered `@mcp.tool` functions and 92 operations** —
nothing missed at the tool layer; this section is about *what the MCP chooses to
expose*, not audit completeness. **Dispositions are recommendations for Peter to
confirm.**

Disposition key: **ADD** = implement (clear use-case value) · **OMIT** = decide
not to implement, documented here · **DEFER** = already in the `@mcp.resource`
layer, scheduled for the next pass · **DECIDE** = needs Peter's call.

| API endpoint(s) | MCP status | Recommended disposition & rationale |
|---|---|---|
| `/law/{congress}[/{lawType}[/{lawNumber}]]` | Not implemented | **DECIDE → lean ADD.** Querying *enacted laws* fits a policy/legislation tracker (leg-scan). `/law/119` verified live. Highest-value gap — but confirm it's in-scope for current workflows before building. |
| `/crsreport/{reportNumber}` (CRS detail) | Partial (search/latest only) | **OMIT (document).** Search + latest already cover discovery; per-report detail is niche. Revisit only if a workflow needs full CRS report bodies. |
| `/daily-congressional-record/{vol}/{issue}/articles` | Partial (search/latest only) | **OMIT (document).** Article-level drill-down is niche; the daily-record *search* covers the brief/scan needs. |
| `/treaty/*` detail + partitioned `/{suffix}` | In resource layer | **DEFER.** Treaty *search* exists as a tool; details live in `@mcp.resource`. NB: Peter flagged treaties may be out of scope for his use case — if so, mark the whole treaty surface **OMIT/low-priority** and don't invest in treaty-related fixes or the next-pass resource audit for it. |
| `/committee/{chamber}/{code}/house-communication` & `/senate-communication` | Wrapped but buggy | **FIX** — this is bug **A1**. |
| `/congress/current`, `/committee/{congress}[/{chamber}[/{code}]]`, top-level `/house-vote` | Filter variants of covered endpoints | **OMIT (document).** Reachable via existing list ops; dedicated variants add little. |

**Implemented-but-maybe-unneeded (don't over-invest):** some *existing* tool
surfaces may also be outside Peter's use case — e.g. the full treaty op set,
committee prints/meetings, nomination sub-ops. Where a surface is low-value for
current workflows, that's a reason to **deprioritize fixing its audit findings**,
not a reason to perfect it. Tag these during Phase 3 review so effort tracks use.

## C. Recommended harness improvement (Phase 3 prep)

Add a **static wrapper→impl signature diff** check: for each delegating wrapper,
compare the kwargs it passes to the impl's accepted parameters. This catches the
Class-1 signature bugs (A4, A5) **automatically** — the live harness is blind to
them. Cheap, no network, runs in the mocked suite.

---

## D. Proposed Phase 3 fix batches (after review)

Each batch: impl fix + a **mocked** regression test (plumbing) + a **live** test
(shape, in `tests/live/`), then refresh `documentation/CongressAPI_documentation.md`
for the touched endpoints (and `README.md` if a signature changes).

1. **Batch 1 — Signature (A4, A5):** make `keywords` optional in
   `search_committees` + `search_summaries`; reconcile `committee_type`. Add the
   static signature-diff check (Section C). Lowest risk, highest user impact.
2. **Batch 2 — Formatter (A6, A7):** guard null/str entries in the bills-list and
   bill-subjects formatters.
3. **Batch 3 — Endpoint (A2, A3):** switch to the correct paths
   (`/member/congress/{c}/{state}/{district}`, `/committee-meeting/{c}/{chamber}`).
4. **Batch 4 — Endpoint decision (A1):** `get_committee_communications` — confirm
   whether any committee-scoped communications endpoint exists; re-implement or
   retire. **Needs a product decision**, so isolate it.

Deploy once per batch via the documented venv reinstall flow; spot-check in cowork.
