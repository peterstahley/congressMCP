# congressMCP Live API Audit (auto-generated)

| Tool | Operation | Status | Endpoint | Live top-keys | Code keys | Key diff | Detail |
|---|---|---|---|---|---|---|---|
| bills | search_bills | EMPTY | /bill/119/hr | bills,pagination,request | bills |  |  |
| bills | get_bills | OK | /bill/119/hr | bills,pagination,request | - |  |  |
| bills | get_bill_details | OK | /bill/119/hr/1 | bill,request | - |  |  |
| bills | get_bill_text | OK | /bill/119/hr/1/text | pagination,request,textVersions | - |  |  |
| bills | get_bill_text_versions | OK | /bill/119/hr/1/text | pagination,request,textVersions | - |  |  |
| bills | get_bill_titles | OK | /bill/119/hr/1/titles | pagination,request,titles | - |  |  |
| bills | get_bill_content | OK | /bill/119/hr/1/text | pagination,request,textVersions | - |  |  |
| bills | get_bill_summaries | ERROR | /bill/119/hr/1/summaries | pagination,request,summaries | summaries |  |  |
| bills | get_recent_bills | OK | /bill/119/hr | bills,pagination,request | - |  |  |
| bills | get_bills_by_date_range | OK | /bill/119/hr | bills,pagination,request | - |  |  |
| bills | get_bill_actions | OK | /bill/119/hr/1/actions | actions,pagination,request | actions |  |  |
| bills | get_bill_amendments | OK | /bill/119/hr/1/amendments | amendments,pagination,request | amendments |  |  |
| bills | get_bill_committees | OK | /bill/119/hr/1/committees | committees,pagination,request | committees |  |  |
| bills | get_bill_cosponsors | EMPTY | /bill/119/hr/1/cosponsors | cosponsors,pagination,request | cosponsors |  |  |
| bills | get_bill_related_bills | OK | /bill/119/hr/1/relatedbills | pagination,relatedBills,request | - |  |  |
| bills | get_bill_subjects | OK | /bill/119/hr/1/subjects | pagination,request,subjects | - |  |  |
| amendments | get_amendments | OK | /amendment/119/samdt | amendments,pagination,request | - |  |  |
| amendments | search_amendments | OK | /amendment/119/samdt | amendments,pagination,request | - |  |  |
| amendments | get_amendment_details | OK | /amendment/119/samdt/1 | amendment,request | - |  |  |
| amendments | get_amendment_actions | OK | /amendment/119/samdt/1/actions | actions,pagination,request | actions |  |  |
| amendments | get_amendment_sponsors | EMPTY | /amendment/119/samdt/1/cosponsors | cosponsors,pagination,request | cosponsors |  |  |
| amendments | get_amendment_amendments | EMPTY | /amendment/119/samdt/1/amendments | amendments,pagination,request | - |  |  |
| amendments | get_amendment_text | OK | /amendment/119/samdt/1/text | pagination,request,textVersions | - |  |  |
| treaties_and_summaries | search_summaries | ERROR |  |  | - |  |  |
| treaties_and_summaries | search_treaties | API-ERROR | /treaty/119 | error,request | treaties |  |  |
| treaties_and_summaries | get_treaty_actions | OK | /treaty/119/1/actions | actions,pagination,request | - |  |  |
| treaties_and_summaries | get_treaty_committees | OK | /treaty/119/1/committees | request,treatyCommittees | - |  |  |
| treaties_and_summaries | get_treaty_text | OK | /treaty/119/1 | request,treaty | actions |  |  |
| committee_intelligence | get_latest_committee_reports | OK | /committee-report | pagination,reports,request | reports |  |  |
| committee_intelligence | get_committee_reports_by_congress | OK | /committee-report/119 | pagination,reports,request | reports |  |  |
| committee_intelligence | get_committee_reports_by_congress_and_type | OK | /committee-report/119/hrpt | pagination,reports,request | reports |  |  |
| committee_intelligence | get_committee_report_details | OK | /committee-report/119/hrpt/1 | committeeReports,request | - |  |  |
| committee_intelligence | get_committee_report_text_versions | OK | /committee-report/119/hrpt/1/text | pagination,request,text | - |  |  |
| committee_intelligence | get_committee_report_content | OK |  |  | - |  |  |
| committee_intelligence | search_committee_reports | OK |  |  | reports |  |  |
| committee_intelligence | get_latest_committee_prints | OK | /committee-print | committeePrints,pagination,request | - |  |  |
| committee_intelligence | get_committee_prints_by_congress | OK | /committee-print/119 | committeePrints,pagination,request | - |  |  |
| committee_intelligence | get_committee_prints_by_congress_and_chamber | OK | /committee-print/119/house | committeePrints,pagination,request | - |  |  |
| committee_intelligence | get_committee_print_details | OK | /committee-print/119/house/62718 | committeePrint,pagination,request | - |  |  |
| committee_intelligence | get_committee_print_text_versions | OK | /committee-print/119/house/62718/text | pagination,request,text | - |  |  |
| committee_intelligence | search_committee_prints | OK | /committee-print | committeePrints,pagination,request | - |  |  |
| committee_intelligence | get_latest_committee_meetings | OK | /committee-meeting | committeeMeetings,pagination,request | - |  |  |
| committee_intelligence | get_committee_meetings_by_congress | OK | /committee-meeting/119 | committeeMeetings,pagination,request | - |  |  |
| committee_intelligence | get_committee_meetings_by_congress_and_chamber | OK | /committee-meeting/119/house | committeeMeetings,pagination,request | - |  |  |
| committee_intelligence | get_committee_meetings_by_committee | OK |  |  | - |  |  |
| committee_intelligence | get_committee_meeting_details | OK | /committee-meeting/119/house/119425 | committeeMeeting,request | - |  |  |
| committee_intelligence | search_committee_meetings | OK | /committee-meeting/119/house | committeeMeetings,pagination,request | - |  |  |
| records_and_hearings | search_congressional_record | EMPTY | /congressional-record | Results,Status | - |  |  |
| records_and_hearings | search_daily_congressional_record | OK | /daily-congressional-record | dailyCongressionalRecord,pagination,request | - |  |  |
| records_and_hearings | search_bound_congressional_record | OK | /bound-congressional-record/1994/1/25 | boundCongressionalRecord,pagination,request | - |  |  |
| records_and_hearings | search_house_communications | OK | /house-communication/119/ec | houseCommunications,pagination,request | houseCommunications |  |  |
| records_and_hearings | get_house_communication_details | OK | /house-communication/119/ec/3948 | houseCommunication,request | houseCommunications |  |  |
| records_and_hearings | search_house_requirements | OK | /house-requirement | houseRequirements,pagination,request | - |  |  |
| records_and_hearings | get_house_requirement_details | OK | /house-requirement/12478 | houseRequirement,request | - |  |  |
| records_and_hearings | get_house_requirement_matching_communications | EMPTY | /house-requirement/12478/matching-communications | matchingCommunications,pagination,request | - |  |  |
| records_and_hearings | search_senate_communications | OK | /senate-communication/119/ec | pagination,request,senateCommunications | - |  |  |
| records_and_hearings | get_senate_communication_details | OK | /senate-communication/119/ec/3948 | request,senateCommunication | - |  |  |
| records_and_hearings | get_committee_communication_details | OK | /house-communication/119/ec/3948 | houseCommunication,request | - |  |  |
| records_and_hearings | search_hearings | OK | /hearing/119/house | hearings,pagination,request | hearings |  |  |
| records_and_hearings | get_hearings_by_congress | OK | /hearing/119 | hearings,pagination,request | hearings |  |  |
| records_and_hearings | get_hearings_by_congress_and_chamber | OK | /hearing/119/house | hearings,pagination,request | hearings |  |  |
| records_and_hearings | get_hearing_details | API-ERROR | /hearing/119/house/62718 | error,request | - |  |  |
| records_and_hearings | get_hearing_content | API-ERROR | /hearing/119/house/62718 | error,request | - |  |  |
| research_and_professional | get_congress_info | OK |  |  | - |  |  |
| research_and_professional | search_congresses | OK |  |  | - |  |  |
| research_and_professional | get_congress_info_enhanced | OK |  |  | - |  |  |
| research_and_professional | search_crs_reports | OK |  |  | - |  |  |
| voting_and_nominations | get_house_votes_by_congress | OK | house-vote/119 | houseRollCallVotes,pagination,request | - |  |  |
| voting_and_nominations | get_house_votes_by_session | OK | house-vote/119/1 | houseRollCallVotes,pagination,request | - |  |  |
| voting_and_nominations | get_house_vote_details | OK | house-vote/119/1/240 | houseRollCallVote,request | - |  |  |
| voting_and_nominations | get_house_vote_details_enhanced | OK | house-vote/119/1/240 | houseRollCallVote,request | - |  |  |
| voting_and_nominations | get_house_vote_member_votes | OK | house-vote/119/1/240 | houseRollCallVote,request | - |  |  |
| voting_and_nominations | get_house_vote_member_votes_xml | OK | house-vote/119/1/240 | houseRollCallVote,request | - |  |  |
| voting_and_nominations | search_nominations | OK |  |  | nominations |  |  |
| voting_and_nominations | get_latest_nominations | OK | nomination | nominations,pagination,request | nominations |  |  |
| voting_and_nominations | get_nomination_details | OK | nomination/119/786 | nomination,request | - |  |  |
| voting_and_nominations | get_nomination_actions | EMPTY | nomination/119/786/actions | actions,pagination,request | actions |  |  |
| voting_and_nominations | get_nomination_committees | EMPTY | nomination/119/786/committees | committees,request | committees |  |  |
| voting_and_nominations | get_nomination_hearings | EMPTY | nomination/119/786/hearings | hearings,pagination,request | hearings |  |  |
| voting_and_nominations | get_nomination_nominees | EMPTY | nomination/119/786/1 | nominees,pagination,request | - |  |  |
| voting_and_nominations | get_nominations_by_congress | OK | nomination/119 | nominations,pagination,request | nominations |  |  |
| search_members | search_members | EMPTY | /member/CA/1 | members,pagination,request | members |  |  |
| get_member_details | get_member_details | OK | /member/K000397 | member,request | - |  |  |
| get_member_sponsored_legislation | get_member_sponsored_legislation | OK | /member/K000397/sponsored-legislation | pagination,request,sponsoredLegislation | - |  |  |
| get_member_cosponsored_legislation | get_member_cosponsored_legislation | OK | /member/K000397/cosponsored-legislation | cosponsoredLegislation,pagination,request | - |  |  |
| get_members_by_congress | get_members_by_congress | OK | /member/congress/119 | members,pagination,request | members |  |  |
| get_members_by_state | get_members_by_state | OK | /member/CA | members,pagination,request | members |  |  |
| get_members_by_district | get_members_by_district | OK | /member/CA/1 | members,pagination,request | members |  |  |
| get_members_by_congress_state_district | get_members_by_congress_state_district | OK | /member/congress/119/CA/1 | members,pagination,request | members |  |  |
| search_committees | search_committees | OK | /committee/house | committees,pagination,request | committees |  |  |
| get_committee_bills | get_committee_bills | OK | /committee/house/hsju00/bills | committee-bills,pagination,request | bills,committee-bills | bills<-committee-bills.bills |  |
| get_committee_reports | get_committee_reports | OK | /committee/house/hsju00/reports | pagination,reports,request | reports |  |  |
| get_committee_communications | get_committee_communications | OK | /committee/house/hsju00/house-communication | houseCommunications,pagination,request | - |  |  |
| get_committee_nominations | get_committee_nominations | EMPTY | /committee/senate/hsju00/nominations | nominations,pagination,request | nominations |  |  |
| get_laws | get_laws | OK | /law/119/pub | bills,pagination,request | - |  |  |
| get_law_details | get_law_details | OK | /law/119/pub/1 | bill,request | - |  |  |

## Summary

- OK: 79
- EMPTY: 12
- API-ERROR: 3
- ERROR: 2