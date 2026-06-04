# Fault Robustness Report

## Overview
- Total cases: 4
- Success rate: 100.0%
- Recovery rate: 100.0%
- State corruption rate: 0.0%
- Average extra steps: 0.50
- Average latency increase ms: 1.34

## Cases

### latency_file_write

- Description: Artificial latency is injected into file.write without changing the final state.
- Clean success: True
- Fault success: True
- Recovery detected: False
- State corrupted: False
- Failed fault calls: 0
- Observation fault count: 0
- Extra steps: 0
- Latency increase ms: 5.19
- Clean sequence: file.write
- Fault sequence: file.write

### transient_file_write_recovery

- Description: The first file.write fails transiently; a retry recovers the final state.
- Clean success: True
- Fault success: True
- Recovery detected: True
- State corrupted: False
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.04
- Clean sequence: file.write
- Fault sequence: file.write -> file.write

### stale_search_observation

- Description: The second search.query replays a stale observation while the index state itself is current.
- Clean success: True
- Fault success: True
- Recovery detected: False
- State corrupted: False
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.02
- Clean sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query
- Fault sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query

### vague_issue_error_recovery

- Description: A close-before-assignment error is masked, then assignment and retry recover the workflow.
- Clean success: True
- Fault success: True
- Recovery detected: True
- State corrupted: False
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.12
- Clean sequence: issue.create -> issue.assign -> issue.close
- Fault sequence: issue.create -> issue.close -> issue.assign -> issue.close
