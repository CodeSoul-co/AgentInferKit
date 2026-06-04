# Stateless vs Stateful Comparison Report

## Overview
- Total cases: 9
- Stateful passed cases: 9
- Stateless passed cases: 9
- Stateful all-calls-succeeded count: 5
- Stateless all-calls-succeeded count: 9

## Overview Metrics
- Stateful success rate: 88.24%
- Stateless success rate: 100.00%
- Stateful invalid call rate: 0.00%
- Stateless invalid call rate: 0.00%
- Stateful recovery rate: 100.00%
- Stateless recovery rate: 0.00%
- Stateful average steps: 3.78
- Stateless average steps: 2.44
- Stateful final state correctness: 100.00%
- Stateless final state correctness: 100.00%
- Cases with step count difference: 8
- Cases with explicit dependency resolution: 3
- Cases with query before index: 1
- Cases with overwrite without re-index: 1
- Cases with trajectory divergence: 8
- Cases with snapshot semantics difference: 1
- Cases with retrieval outcome difference: 3

## Overall Conclusion
Across the evaluated cases, the stateful setting introduced explicit dependency-management steps that were absent or less prominent in the stateless baseline. The two settings also exhibited stable trajectory-level divergence, indicating that the stateful formulation changes the tool-use process rather than only the final outcome. The stateful environment preserved index-time snapshot semantics in cases involving overwrite without re-index, whereas the stateless baseline reflected only the latest file content.

## write_then_query

- Description: Stateful requires explicit indexing before search can hit; stateless searches current file content directly.
- Stateful outcome: Stateful completed 2 calls and returned no final query hits. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and returned 1 hit(s) for file(s): f1. Goals passed: True.
- Stateful steps: 2
- Stateless steps: 2
- Stateful sequence: file.write -> search.query
- Stateless sequence: file.write -> search.query
- Key difference: Stateful query missed because the file was not indexed, while stateless query directly searched current file content.
- Key process difference: Stateful trajectory queried before dependency completion, while stateless trajectory directly searched current file content.

## write_index_query

- Description: Both settings can hit the file, but stateful needs an explicit search.index step.
- Stateful outcome: Stateful completed 3 calls and returned 1 hit(s) for file(s): f1. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and returned 1 hit(s) for file(s): f1. Goals passed: True.
- Stateful steps: 3
- Stateless steps: 2
- Stateful sequence: file.write -> search.index -> search.query
- Stateless sequence: file.write -> search.query
- Key difference: Stateful system required explicit indexing before retrieval, while stateless query did not.
- Key process difference: Stateful trajectory included explicit indexing before retrieval, while stateless trajectory did not.

## overwrite_without_reindex

- Description: Stateful search can stay on the stale indexed snapshot, while stateless search reflects the latest file content.
- Stateful outcome: Stateful completed 4 calls and returned 1 hit(s) for file(s): f1. Goals passed: True.
- Stateless outcome: Stateless completed 3 calls and returned no final query hits. Goals passed: True.
- Stateful steps: 4
- Stateless steps: 3
- Stateful sequence: file.write -> search.index -> file.write -> search.query
- Stateless sequence: file.write -> file.write -> search.query
- Key difference: Stateful search used indexed snapshot and did not reflect overwritten content before re-index, while stateless query reflected the latest file content.
- Key process difference: Stateful trajectory preserved an overwrite-without-reindex structure, while stateless trajectory always followed the latest file content.

## issue_close_requires_assignment

- Description: Stateful issue closing enforces workflow dependency and recovery; stateless baseline closes directly.
- Stateful outcome: Stateful completed 4 calls and final issue state(s): iss1=closed. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and final issue state(s): iss1=closed. Goals passed: True.
- Stateful steps: 4
- Stateless steps: 2
- Stateful sequence: issue.create -> issue.close -> issue.assign -> issue.close
- Stateless sequence: issue.create -> issue.close
- Key difference: Stateful issue workflow rejected close-before-assignment and required recovery, while the stateless baseline accepted the direct close.
- Key process difference: Stateful trajectory exposed a failed close, dependency repair via assignment, and retry; stateless trajectory closed the issue directly.

## multi_file_partial_index

- Description: Stateful search only sees explicitly indexed files; stateless search scans all current file content.
- Stateful outcome: Stateful completed 4 calls and returned 1 hit(s) for file(s): f1. Goals passed: True.
- Stateless outcome: Stateless completed 3 calls and returned 2 hit(s) for file(s): f1, f2. Goals passed: True.
- Stateful steps: 4
- Stateless steps: 3
- Stateful sequence: file.write -> file.write -> search.index -> search.query
- Stateless sequence: file.write -> file.write -> search.query
- Key difference: Stateful search returned only explicitly indexed file snapshots, while stateless search scanned all current file content.
- Key process difference: Stateful trajectory included explicit indexing before retrieval, while stateless trajectory did not.

## reindex_after_overwrite

- Description: Stateful search reflects overwritten content only after a second index step; stateless search reflects it directly.
- Stateful outcome: Stateful completed 5 calls and returned 1 hit(s) for file(s): f1. Goals passed: True.
- Stateless outcome: Stateless completed 3 calls and returned 1 hit(s) for file(s): f1. Goals passed: True.
- Stateful steps: 5
- Stateless steps: 3
- Stateful sequence: file.write -> search.index -> file.write -> search.index -> search.query
- Stateless sequence: file.write -> file.write -> search.query
- Key difference: Stateful system required explicit indexing before retrieval, while stateless query did not.
- Key process difference: Stateful trajectory included explicit indexing before retrieval, while stateless trajectory did not.

## calendar_conflict_requires_reschedule

- Description: Stateful calendar creation rejects participant conflicts and requires rescheduling; stateless accepts the conflict directly.
- Stateful outcome: Stateful completed 3 calls and final event state(s): e1=confirmed@10.0, e2=confirmed@11.0. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and final event state(s): e1=confirmed@10.0, e2=confirmed@10.5. Goals passed: True.
- Stateful steps: 3
- Stateless steps: 2
- Stateful sequence: calendar.create_event -> calendar.create_event -> calendar.create_event
- Stateless sequence: calendar.create_event -> calendar.create_event
- Key difference: Stateful calendar workflow rejected a participant conflict and required a non-conflicting retry, while the stateless baseline accepted the conflicting mutation.
- Key process difference: Stateful trajectory exposed a calendar conflict and required a non-conflicting retry, while stateless trajectory accepted the conflicting mutation.

## calendar_update_conflict_requires_recovery

- Description: Stateful calendar update rejects moving an event into a conflict; stateless updates directly.
- Stateful outcome: Stateful completed 4 calls and final event state(s): e1=confirmed@9.0, e2=confirmed@11.0. Goals passed: True.
- Stateless outcome: Stateless completed 3 calls and final event state(s): e1=confirmed@9.0, e2=confirmed@9.5. Goals passed: True.
- Stateful steps: 4
- Stateless steps: 3
- Stateful sequence: calendar.create_event -> calendar.create_event -> calendar.update_event -> calendar.update_event
- Stateless sequence: calendar.create_event -> calendar.create_event -> calendar.update_event
- Key difference: Stateful calendar workflow rejected a participant conflict and required a non-conflicting retry, while the stateless baseline accepted the conflicting mutation.
- Key process difference: Stateful trajectory exposed a calendar conflict and required a non-conflicting retry, while stateless trajectory accepted the conflicting mutation.

## issue_reopen_requires_closed_state

- Description: Stateful issue reopening requires a closed issue and exposes recovery; stateless reopens directly.
- Stateful outcome: Stateful completed 5 calls and final issue state(s): iss2=open. Goals passed: True.
- Stateless outcome: Stateless completed 2 calls and final issue state(s): iss2=open. Goals passed: True.
- Stateful steps: 5
- Stateless steps: 2
- Stateful sequence: issue.create -> issue.reopen -> issue.assign -> issue.close -> issue.reopen
- Stateless sequence: issue.create -> issue.reopen
- Key difference: Stateful issue workflow rejected reopen-before-close and required a close-then-reopen recovery, while the stateless baseline accepted reopening directly.
- Key process difference: Stateful trajectory exposed a failed reopen, repaired the issue state through close-and-reopen, while stateless trajectory reopened directly.
