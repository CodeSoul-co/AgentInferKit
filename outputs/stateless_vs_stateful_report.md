# Stateless vs Stateful Comparison Report

## Overview
- Total cases: 3
- Stateful passed cases: 3
- Stateless passed cases: 3
- Stateful all-calls-succeeded count: 3
- Stateless all-calls-succeeded count: 3

## Overview Metrics
- Stateful average steps: 3.00
- Stateless average steps: 2.33
- Cases with step count difference: 2
- Cases with explicit dependency resolution: 1
- Cases with query before index: 1
- Cases with overwrite without re-index: 1
- Cases with trajectory divergence: 2
- Cases with snapshot semantics difference: 1
- Cases with retrieval outcome difference: 2

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


