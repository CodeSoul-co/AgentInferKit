# Fault Robustness Report

## Overview
- Total cases: 136
- Success@1: 52.9%
- Pass^k: 100.0%
- Success rate: 100.0%
- Recovery rate: 100.0%
- Cost increase: 0.50 extra calls
- State corruption rate: 0.0%
- Average extra steps: 0.50
- Average latency increase ms: 3.41

## By Noise Type

| Noise | Cases | Success@1 | Pass^k | Recovery | Cost increase | State corruption | Latency increase ms |
|---|---:|---:|---:|---:|---:|---:|---:|
| schema_drift | 34 | 5.9% | 100.0% | 100.0% | 1.00 | 0.0% | 0.10 |
| stale_state | 34 | 100.0% | 100.0% | 100.0% | 0.00 | 0.0% | 0.81 |
| timeout | 34 | 5.9% | 100.0% | 100.0% | 1.00 | 0.0% | 12.55 |
| vague_observation | 34 | 100.0% | 100.0% | 100.0% | 0.00 | 0.0% | 0.16 |

## Cases

### experiment1_synthetic::write_then_query::timeout

- Description: Stateful requires explicit indexing before search can hit; stateless searches current file content directly. Noise type=timeout; target tool=file.write.
- Noise type: timeout
- Source: experiment1_synthetic
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 10.34
- Clean sequence: file.write -> search.query
- Fault sequence: file.write -> file.write -> search.query

### experiment1_synthetic::write_then_query::schema_drift

- Description: Stateful requires explicit indexing before search can hit; stateless searches current file content directly. Noise type=schema_drift; target tool=file.write.
- Noise type: schema_drift
- Source: experiment1_synthetic
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.04
- Clean sequence: file.write -> search.query
- Fault sequence: file.write -> file.write -> search.query

### experiment1_synthetic::write_then_query::stale_state

- Description: Stateful requires explicit indexing before search can hit; stateless searches current file content directly. Noise type=stale_state; target tool=search.query.
- Noise type: stale_state
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.06
- Clean sequence: file.write -> search.query
- Fault sequence: file.write -> search.query

### experiment1_synthetic::write_then_query::vague_observation

- Description: Stateful requires explicit indexing before search can hit; stateless searches current file content directly. Noise type=vague_observation; target tool=search.query.
- Noise type: vague_observation
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.04
- Clean sequence: file.write -> search.query
- Fault sequence: file.write -> search.query

### experiment1_synthetic::write_index_query::timeout

- Description: Both settings can hit the file, but stateful needs an explicit search.index step. Noise type=timeout; target tool=file.write.
- Noise type: timeout
- Source: experiment1_synthetic
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 10.70
- Clean sequence: file.write -> search.index -> search.query
- Fault sequence: file.write -> file.write -> search.index -> search.query

### experiment1_synthetic::write_index_query::schema_drift

- Description: Both settings can hit the file, but stateful needs an explicit search.index step. Noise type=schema_drift; target tool=file.write.
- Noise type: schema_drift
- Source: experiment1_synthetic
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.09
- Clean sequence: file.write -> search.index -> search.query
- Fault sequence: file.write -> file.write -> search.index -> search.query

### experiment1_synthetic::write_index_query::stale_state

- Description: Both settings can hit the file, but stateful needs an explicit search.index step. Noise type=stale_state; target tool=search.index.
- Noise type: stale_state
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.07
- Clean sequence: file.write -> search.index -> search.query
- Fault sequence: file.write -> search.index -> search.query

### experiment1_synthetic::write_index_query::vague_observation

- Description: Both settings can hit the file, but stateful needs an explicit search.index step. Noise type=vague_observation; target tool=search.index.
- Noise type: vague_observation
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.09
- Clean sequence: file.write -> search.index -> search.query
- Fault sequence: file.write -> search.index -> search.query

### experiment1_synthetic::overwrite_without_reindex::timeout

- Description: Stateful search can stay on the stale indexed snapshot, while stateless search reflects the latest file content. Noise type=timeout; target tool=file.write.
- Noise type: timeout
- Source: experiment1_synthetic
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 17.91
- Clean sequence: file.write -> search.index -> file.write -> search.query
- Fault sequence: file.write -> file.write -> search.index -> file.write -> search.query

### experiment1_synthetic::overwrite_without_reindex::schema_drift

- Description: Stateful search can stay on the stale indexed snapshot, while stateless search reflects the latest file content. Noise type=schema_drift; target tool=file.write.
- Noise type: schema_drift
- Source: experiment1_synthetic
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.08
- Clean sequence: file.write -> search.index -> file.write -> search.query
- Fault sequence: file.write -> file.write -> search.index -> file.write -> search.query

### experiment1_synthetic::overwrite_without_reindex::stale_state

- Description: Stateful search can stay on the stale indexed snapshot, while stateless search reflects the latest file content. Noise type=stale_state; target tool=search.index.
- Noise type: stale_state
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.17
- Clean sequence: file.write -> search.index -> file.write -> search.query
- Fault sequence: file.write -> search.index -> file.write -> search.query

### experiment1_synthetic::overwrite_without_reindex::vague_observation

- Description: Stateful search can stay on the stale indexed snapshot, while stateless search reflects the latest file content. Noise type=vague_observation; target tool=search.index.
- Noise type: vague_observation
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.33
- Clean sequence: file.write -> search.index -> file.write -> search.query
- Fault sequence: file.write -> search.index -> file.write -> search.query

### experiment1_synthetic::issue_close_requires_assignment::timeout

- Description: Stateful issue closing enforces workflow dependency and recovery; stateless baseline closes directly. Noise type=timeout; target tool=issue.create.
- Noise type: timeout
- Source: experiment1_synthetic
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 2
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 11.43
- Clean sequence: issue.create -> issue.close -> issue.assign -> issue.close
- Fault sequence: issue.create -> issue.create -> issue.close -> issue.assign -> issue.close

### experiment1_synthetic::issue_close_requires_assignment::schema_drift

- Description: Stateful issue closing enforces workflow dependency and recovery; stateless baseline closes directly. Noise type=schema_drift; target tool=issue.create.
- Noise type: schema_drift
- Source: experiment1_synthetic
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 2
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.29
- Clean sequence: issue.create -> issue.close -> issue.assign -> issue.close
- Fault sequence: issue.create -> issue.create -> issue.close -> issue.assign -> issue.close

### experiment1_synthetic::issue_close_requires_assignment::stale_state

- Description: Stateful issue closing enforces workflow dependency and recovery; stateless baseline closes directly. Noise type=stale_state; target tool=issue.create.
- Noise type: stale_state
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.09
- Clean sequence: issue.create -> issue.close -> issue.assign -> issue.close
- Fault sequence: issue.create -> issue.close -> issue.assign -> issue.close

### experiment1_synthetic::issue_close_requires_assignment::vague_observation

- Description: Stateful issue closing enforces workflow dependency and recovery; stateless baseline closes directly. Noise type=vague_observation; target tool=issue.create.
- Noise type: vague_observation
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.11
- Clean sequence: issue.create -> issue.close -> issue.assign -> issue.close
- Fault sequence: issue.create -> issue.close -> issue.assign -> issue.close

### experiment1_synthetic::multi_file_partial_index::timeout

- Description: Stateful search only sees explicitly indexed files; stateless search scans all current file content. Noise type=timeout; target tool=file.write.
- Noise type: timeout
- Source: experiment1_synthetic
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 16.93
- Clean sequence: file.write -> file.write -> search.index -> search.query
- Fault sequence: file.write -> file.write -> file.write -> search.index -> search.query

### experiment1_synthetic::multi_file_partial_index::schema_drift

- Description: Stateful search only sees explicitly indexed files; stateless search scans all current file content. Noise type=schema_drift; target tool=file.write.
- Noise type: schema_drift
- Source: experiment1_synthetic
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.13
- Clean sequence: file.write -> file.write -> search.index -> search.query
- Fault sequence: file.write -> file.write -> file.write -> search.index -> search.query

### experiment1_synthetic::multi_file_partial_index::stale_state

- Description: Stateful search only sees explicitly indexed files; stateless search scans all current file content. Noise type=stale_state; target tool=search.index.
- Noise type: stale_state
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.17
- Clean sequence: file.write -> file.write -> search.index -> search.query
- Fault sequence: file.write -> file.write -> search.index -> search.query

### experiment1_synthetic::multi_file_partial_index::vague_observation

- Description: Stateful search only sees explicitly indexed files; stateless search scans all current file content. Noise type=vague_observation; target tool=search.index.
- Noise type: vague_observation
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 1.06
- Clean sequence: file.write -> file.write -> search.index -> search.query
- Fault sequence: file.write -> file.write -> search.index -> search.query

### experiment1_synthetic::reindex_after_overwrite::timeout

- Description: Stateful search reflects overwritten content only after a second index step; stateless search reflects it directly. Noise type=timeout; target tool=file.write.
- Noise type: timeout
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 17.53
- Clean sequence: file.write -> search.index -> file.write -> search.index -> search.query
- Fault sequence: file.write -> file.write -> search.index -> file.write -> search.index -> search.query

### experiment1_synthetic::reindex_after_overwrite::schema_drift

- Description: Stateful search reflects overwritten content only after a second index step; stateless search reflects it directly. Noise type=schema_drift; target tool=file.write.
- Noise type: schema_drift
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: -0.11
- Clean sequence: file.write -> search.index -> file.write -> search.index -> search.query
- Fault sequence: file.write -> file.write -> search.index -> file.write -> search.index -> search.query

### experiment1_synthetic::reindex_after_overwrite::stale_state

- Description: Stateful search reflects overwritten content only after a second index step; stateless search reflects it directly. Noise type=stale_state; target tool=search.index.
- Noise type: stale_state
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 2
- Extra steps: 0
- Latency increase ms: 0.10
- Clean sequence: file.write -> search.index -> file.write -> search.index -> search.query
- Fault sequence: file.write -> search.index -> file.write -> search.index -> search.query

### experiment1_synthetic::reindex_after_overwrite::vague_observation

- Description: Stateful search reflects overwritten content only after a second index step; stateless search reflects it directly. Noise type=vague_observation; target tool=search.index.
- Noise type: vague_observation
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 2
- Extra steps: 0
- Latency increase ms: 0.08
- Clean sequence: file.write -> search.index -> file.write -> search.index -> search.query
- Fault sequence: file.write -> search.index -> file.write -> search.index -> search.query

### experiment1_synthetic::calendar_conflict_requires_reschedule::timeout

- Description: Stateful calendar creation rejects participant conflicts and requires rescheduling; stateless accepts the conflict directly. Noise type=timeout; target tool=calendar.create_event.
- Noise type: timeout
- Source: experiment1_synthetic
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 2
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 22.74
- Clean sequence: calendar.create_event -> calendar.create_event -> calendar.create_event
- Fault sequence: calendar.create_event -> calendar.create_event -> calendar.create_event -> calendar.create_event

### experiment1_synthetic::calendar_conflict_requires_reschedule::schema_drift

- Description: Stateful calendar creation rejects participant conflicts and requires rescheduling; stateless accepts the conflict directly. Noise type=schema_drift; target tool=calendar.create_event.
- Noise type: schema_drift
- Source: experiment1_synthetic
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 2
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.07
- Clean sequence: calendar.create_event -> calendar.create_event -> calendar.create_event
- Fault sequence: calendar.create_event -> calendar.create_event -> calendar.create_event -> calendar.create_event

### experiment1_synthetic::calendar_conflict_requires_reschedule::stale_state

- Description: Stateful calendar creation rejects participant conflicts and requires rescheduling; stateless accepts the conflict directly. Noise type=stale_state; target tool=calendar.create_event.
- Noise type: stale_state
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 1
- Observation fault count: 3
- Extra steps: 0
- Latency increase ms: 0.39
- Clean sequence: calendar.create_event -> calendar.create_event -> calendar.create_event
- Fault sequence: calendar.create_event -> calendar.create_event -> calendar.create_event

### experiment1_synthetic::calendar_conflict_requires_reschedule::vague_observation

- Description: Stateful calendar creation rejects participant conflicts and requires rescheduling; stateless accepts the conflict directly. Noise type=vague_observation; target tool=calendar.create_event.
- Noise type: vague_observation
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 1
- Observation fault count: 3
- Extra steps: 0
- Latency increase ms: -0.01
- Clean sequence: calendar.create_event -> calendar.create_event -> calendar.create_event
- Fault sequence: calendar.create_event -> calendar.create_event -> calendar.create_event

### experiment1_synthetic::calendar_update_conflict_requires_recovery::timeout

- Description: Stateful calendar update rejects moving an event into a conflict; stateless updates directly. Noise type=timeout; target tool=calendar.create_event.
- Noise type: timeout
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 2
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 19.59
- Clean sequence: calendar.create_event -> calendar.create_event -> calendar.update_event -> calendar.update_event
- Fault sequence: calendar.create_event -> calendar.create_event -> calendar.create_event -> calendar.update_event -> calendar.update_event

### experiment1_synthetic::calendar_update_conflict_requires_recovery::schema_drift

- Description: Stateful calendar update rejects moving an event into a conflict; stateless updates directly. Noise type=schema_drift; target tool=calendar.create_event.
- Noise type: schema_drift
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 2
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.22
- Clean sequence: calendar.create_event -> calendar.create_event -> calendar.update_event -> calendar.update_event
- Fault sequence: calendar.create_event -> calendar.create_event -> calendar.create_event -> calendar.update_event -> calendar.update_event

### experiment1_synthetic::calendar_update_conflict_requires_recovery::stale_state

- Description: Stateful calendar update rejects moving an event into a conflict; stateless updates directly. Noise type=stale_state; target tool=calendar.create_event.
- Noise type: stale_state
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 1
- Observation fault count: 2
- Extra steps: 0
- Latency increase ms: 0.23
- Clean sequence: calendar.create_event -> calendar.create_event -> calendar.update_event -> calendar.update_event
- Fault sequence: calendar.create_event -> calendar.create_event -> calendar.update_event -> calendar.update_event

### experiment1_synthetic::calendar_update_conflict_requires_recovery::vague_observation

- Description: Stateful calendar update rejects moving an event into a conflict; stateless updates directly. Noise type=vague_observation; target tool=calendar.create_event.
- Noise type: vague_observation
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 1
- Observation fault count: 2
- Extra steps: 0
- Latency increase ms: 0.39
- Clean sequence: calendar.create_event -> calendar.create_event -> calendar.update_event -> calendar.update_event
- Fault sequence: calendar.create_event -> calendar.create_event -> calendar.update_event -> calendar.update_event

### experiment1_synthetic::issue_reopen_requires_closed_state::timeout

- Description: Stateful issue reopening requires a closed issue and exposes recovery; stateless reopens directly. Noise type=timeout; target tool=issue.create.
- Noise type: timeout
- Source: experiment1_synthetic
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 2
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 11.74
- Clean sequence: issue.create -> issue.reopen -> issue.assign -> issue.close -> issue.reopen
- Fault sequence: issue.create -> issue.create -> issue.reopen -> issue.assign -> issue.close -> issue.reopen

### experiment1_synthetic::issue_reopen_requires_closed_state::schema_drift

- Description: Stateful issue reopening requires a closed issue and exposes recovery; stateless reopens directly. Noise type=schema_drift; target tool=issue.create.
- Noise type: schema_drift
- Source: experiment1_synthetic
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 2
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.09
- Clean sequence: issue.create -> issue.reopen -> issue.assign -> issue.close -> issue.reopen
- Fault sequence: issue.create -> issue.create -> issue.reopen -> issue.assign -> issue.close -> issue.reopen

### experiment1_synthetic::issue_reopen_requires_closed_state::stale_state

- Description: Stateful issue reopening requires a closed issue and exposes recovery; stateless reopens directly. Noise type=stale_state; target tool=issue.create.
- Noise type: stale_state
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.27
- Clean sequence: issue.create -> issue.reopen -> issue.assign -> issue.close -> issue.reopen
- Fault sequence: issue.create -> issue.reopen -> issue.assign -> issue.close -> issue.reopen

### experiment1_synthetic::issue_reopen_requires_closed_state::vague_observation

- Description: Stateful issue reopening requires a closed issue and exposes recovery; stateless reopens directly. Noise type=vague_observation; target tool=issue.create.
- Noise type: vague_observation
- Source: experiment1_synthetic
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.43
- Clean sequence: issue.create -> issue.reopen -> issue.assign -> issue.close -> issue.reopen
- Fault sequence: issue.create -> issue.reopen -> issue.assign -> issue.close -> issue.reopen

### experiment1_toolsandbox_subset::toolsandbox::add_contact_with_name_and_phone_number::timeout

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=add_contact.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 12.49
- Clean sequence: add_contact -> end_conversation
- Fault sequence: add_contact -> add_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::add_contact_with_name_and_phone_number::schema_drift

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=add_contact.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: -0.08
- Clean sequence: add_contact -> end_conversation
- Fault sequence: add_contact -> add_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::add_contact_with_name_and_phone_number::stale_state

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=add_contact.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.18
- Clean sequence: add_contact -> end_conversation
- Fault sequence: add_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::add_contact_with_name_and_phone_number::vague_observation

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=add_contact.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.17
- Clean sequence: add_contact -> end_conversation
- Fault sequence: add_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::modify_contact_with_message_recency_alt::timeout

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=get_current_timestamp.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 14.36
- Clean sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation
- Fault sequence: get_current_timestamp -> get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::modify_contact_with_message_recency_alt::schema_drift

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=get_current_timestamp.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.08
- Clean sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation
- Fault sequence: get_current_timestamp -> get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::modify_contact_with_message_recency_alt::stale_state

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=get_current_timestamp.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.30
- Clean sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation
- Fault sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::modify_contact_with_message_recency_alt::vague_observation

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=get_current_timestamp.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: -0.07
- Clean sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation
- Fault sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::remove_contact_by_phone_ambiguous_alt::timeout

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=search_contacts.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 2
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 11.12
- Clean sequence: search_contacts -> remove_contact -> end_conversation
- Fault sequence: search_contacts -> search_contacts -> remove_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::remove_contact_by_phone_ambiguous_alt::schema_drift

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=search_contacts.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 2
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: -0.12
- Clean sequence: search_contacts -> remove_contact -> end_conversation
- Fault sequence: search_contacts -> search_contacts -> remove_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::remove_contact_by_phone_ambiguous_alt::stale_state

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=search_contacts.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.05
- Clean sequence: search_contacts -> remove_contact -> end_conversation
- Fault sequence: search_contacts -> remove_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::remove_contact_by_phone_ambiguous_alt::vague_observation

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=search_contacts.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.06
- Clean sequence: search_contacts -> remove_contact -> end_conversation
- Fault sequence: search_contacts -> remove_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::modify_contact_with_message_recency_multiple_user_turn_alt::timeout

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=get_current_timestamp.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 18.17
- Clean sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation
- Fault sequence: get_current_timestamp -> get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::modify_contact_with_message_recency_multiple_user_turn_alt::schema_drift

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=get_current_timestamp.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.09
- Clean sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation
- Fault sequence: get_current_timestamp -> get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::modify_contact_with_message_recency_multiple_user_turn_alt::stale_state

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=get_current_timestamp.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.09
- Clean sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation
- Fault sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::modify_contact_with_message_recency_multiple_user_turn_alt::vague_observation

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=get_current_timestamp.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.37
- Clean sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation
- Fault sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::remove_contact_by_phone_multiple_user_turn::timeout

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=search_contacts.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 2
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 10.78
- Clean sequence: search_contacts -> remove_contact -> end_conversation
- Fault sequence: search_contacts -> search_contacts -> remove_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::remove_contact_by_phone_multiple_user_turn::schema_drift

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=search_contacts.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 2
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.03
- Clean sequence: search_contacts -> remove_contact -> end_conversation
- Fault sequence: search_contacts -> search_contacts -> remove_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::remove_contact_by_phone_multiple_user_turn::stale_state

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=search_contacts.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.25
- Clean sequence: search_contacts -> remove_contact -> end_conversation
- Fault sequence: search_contacts -> remove_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::remove_contact_by_phone_multiple_user_turn::vague_observation

- Description: ToolSandbox contacts case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=search_contacts.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: -0.00
- Clean sequence: search_contacts -> remove_contact -> end_conversation
- Fault sequence: search_contacts -> remove_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::add_contact_with_name_and_phone_number_10_distraction_tools::timeout

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=add_contact.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 10.71
- Clean sequence: add_contact -> end_conversation
- Fault sequence: add_contact -> add_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::add_contact_with_name_and_phone_number_10_distraction_tools::schema_drift

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=add_contact.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.15
- Clean sequence: add_contact -> end_conversation
- Fault sequence: add_contact -> add_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::add_contact_with_name_and_phone_number_10_distraction_tools::stale_state

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=add_contact.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.42
- Clean sequence: add_contact -> end_conversation
- Fault sequence: add_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::add_contact_with_name_and_phone_number_10_distraction_tools::vague_observation

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=add_contact.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.03
- Clean sequence: add_contact -> end_conversation
- Fault sequence: add_contact -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_date_and_time_multiple_user_turn_alt_all_tools::timeout

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=datetime_info_to_timestamp.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 10.53
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Fault sequence: datetime_info_to_timestamp -> datetime_info_to_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_date_and_time_multiple_user_turn_alt_all_tools::schema_drift

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=datetime_info_to_timestamp.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.05
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Fault sequence: datetime_info_to_timestamp -> datetime_info_to_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_date_and_time_multiple_user_turn_alt_all_tools::stale_state

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=datetime_info_to_timestamp.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.03
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Fault sequence: datetime_info_to_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_date_and_time_multiple_user_turn_alt_all_tools::vague_observation

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=datetime_info_to_timestamp.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.13
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Fault sequence: datetime_info_to_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_week_delta_and_time_multiple_user_turn_alt_10_distraction_tools::timeout

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=get_current_timestamp.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 10.88
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_week_delta_and_time_multiple_user_turn_alt_10_distraction_tools::schema_drift

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=get_current_timestamp.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: -0.05
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_week_delta_and_time_multiple_user_turn_alt_10_distraction_tools::stale_state

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=get_current_timestamp.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.04
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_week_delta_and_time_multiple_user_turn_alt_10_distraction_tools::vague_observation

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=get_current_timestamp.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.01
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_weekday_delta_and_time_multiple_user_turn_alt_10_distraction_tools::timeout

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=get_current_timestamp.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 11.36
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_weekday_delta_and_time_multiple_user_turn_alt_10_distraction_tools::schema_drift

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=get_current_timestamp.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.27
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_weekday_delta_and_time_multiple_user_turn_alt_10_distraction_tools::stale_state

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=get_current_timestamp.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.28
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_weekday_delta_and_time_multiple_user_turn_alt_10_distraction_tools::vague_observation

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=get_current_timestamp.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.07
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_week_delta_and_time_and_location_low_battery_mode_multiple_user_turn_alt::timeout

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=set_low_battery_mode_status.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 11.18
- Clean sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon -> get_current_timestamp -> add_reminder
- Fault sequence: set_low_battery_mode_status -> set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon -> get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_week_delta_and_time_and_location_low_battery_mode_multiple_user_turn_alt::schema_drift

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=set_low_battery_mode_status.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 1.29
- Clean sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon -> get_current_timestamp -> add_reminder
- Fault sequence: set_low_battery_mode_status -> set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon -> get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_week_delta_and_time_and_location_low_battery_mode_multiple_user_turn_alt::stale_state

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=search_location_around_lat_lon.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.04
- Clean sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon -> get_current_timestamp -> add_reminder
- Fault sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon -> get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_week_delta_and_time_and_location_low_battery_mode_multiple_user_turn_alt::vague_observation

- Description: ToolSandbox device_settings case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=search_location_around_lat_lon.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.18
- Clean sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon -> get_current_timestamp -> add_reminder
- Fault sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon -> get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::find_days_till_holiday::timeout

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=get_current_timestamp.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 11.20
- Clean sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Fault sequence: get_current_timestamp -> get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_days_till_holiday::schema_drift

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=get_current_timestamp.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.08
- Clean sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Fault sequence: get_current_timestamp -> get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_days_till_holiday::stale_state

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=get_current_timestamp.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.39
- Clean sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Fault sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_days_till_holiday::vague_observation

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=get_current_timestamp.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.22
- Clean sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Fault sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_days_till_holiday_alt::timeout

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=get_current_timestamp.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 10.99
- Clean sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Fault sequence: get_current_timestamp -> get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_days_till_holiday_alt::schema_drift

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=get_current_timestamp.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: -0.08
- Clean sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Fault sequence: get_current_timestamp -> get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_days_till_holiday_alt::stale_state

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=get_current_timestamp.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: -0.07
- Clean sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Fault sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_days_till_holiday_alt::vague_observation

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=get_current_timestamp.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.34
- Clean sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Fault sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_address_with_lat_lon::timeout

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=search_lat_lon.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 11.00
- Clean sequence: search_lat_lon -> end_conversation
- Fault sequence: search_lat_lon -> search_lat_lon -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_address_with_lat_lon::schema_drift

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=search_lat_lon.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.05
- Clean sequence: search_lat_lon -> end_conversation
- Fault sequence: search_lat_lon -> search_lat_lon -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_address_with_lat_lon::stale_state

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=search_lat_lon.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.10
- Clean sequence: search_lat_lon -> end_conversation
- Fault sequence: search_lat_lon -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_address_with_lat_lon::vague_observation

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=search_lat_lon.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: -0.03
- Clean sequence: search_lat_lon -> end_conversation
- Fault sequence: search_lat_lon -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_stock_symbol_with_company_name::timeout

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=search_stock.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 10.48
- Clean sequence: search_stock -> end_conversation
- Fault sequence: search_stock -> search_stock -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_stock_symbol_with_company_name::schema_drift

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=search_stock.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: -0.44
- Clean sequence: search_stock -> end_conversation
- Fault sequence: search_stock -> search_stock -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_stock_symbol_with_company_name::stale_state

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=search_stock.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.10
- Clean sequence: search_stock -> end_conversation
- Fault sequence: search_stock -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_stock_symbol_with_company_name::vague_observation

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=search_stock.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.18
- Clean sequence: search_stock -> end_conversation
- Fault sequence: search_stock -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_temperature::timeout

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=search_weather_around_lat_lon.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 11.01
- Clean sequence: search_weather_around_lat_lon -> end_conversation
- Fault sequence: search_weather_around_lat_lon -> search_weather_around_lat_lon -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_temperature::schema_drift

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=search_weather_around_lat_lon.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.03
- Clean sequence: search_weather_around_lat_lon -> end_conversation
- Fault sequence: search_weather_around_lat_lon -> search_weather_around_lat_lon -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_temperature::stale_state

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=search_weather_around_lat_lon.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.05
- Clean sequence: search_weather_around_lat_lon -> end_conversation
- Fault sequence: search_weather_around_lat_lon -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::find_temperature::vague_observation

- Description: ToolSandbox external_search case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=search_weather_around_lat_lon.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: -0.04
- Clean sequence: search_weather_around_lat_lon -> end_conversation
- Fault sequence: search_weather_around_lat_lon -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_latest_multiple_user_turn::timeout

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=search_messages.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 10.93
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Fault sequence: search_messages -> search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_latest_multiple_user_turn::schema_drift

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=search_messages.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.27
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Fault sequence: search_messages -> search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_latest_multiple_user_turn::stale_state

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=search_messages.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 22.07
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Fault sequence: search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_latest_multiple_user_turn::vague_observation

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=search_messages.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.05
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Fault sequence: search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_latest_multiple_user_turn_alt::timeout

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=search_messages.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 11.24
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Fault sequence: search_messages -> search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_latest_multiple_user_turn_alt::schema_drift

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=search_messages.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: -0.01
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Fault sequence: search_messages -> search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_latest_multiple_user_turn_alt::stale_state

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=search_messages.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.13
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Fault sequence: search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_latest_multiple_user_turn_alt::vague_observation

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=search_messages.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.09
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Fault sequence: search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_latest_alt::timeout

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=search_messages.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 10.78
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Fault sequence: search_messages -> search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_latest_alt::schema_drift

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=search_messages.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.16
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Fault sequence: search_messages -> search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_latest_alt::stale_state

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=search_messages.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.17
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Fault sequence: search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_latest_alt::vague_observation

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=search_messages.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.20
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Fault sequence: search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_latest::timeout

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=search_messages.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 10.88
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Fault sequence: search_messages -> search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_latest::schema_drift

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=search_messages.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.06
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Fault sequence: search_messages -> search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_latest::stale_state

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=search_messages.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.52
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Fault sequence: search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_latest::vague_observation

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=search_messages.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.10
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Fault sequence: search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_oldest::timeout

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=get_current_timestamp.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 11.02
- Clean sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation
- Fault sequence: get_current_timestamp -> get_current_timestamp -> search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_oldest::schema_drift

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=get_current_timestamp.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.20
- Clean sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation
- Fault sequence: get_current_timestamp -> get_current_timestamp -> search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_oldest::stale_state

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=get_current_timestamp.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.23
- Clean sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation
- Fault sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::search_message_with_recency_oldest::vague_observation

- Description: ToolSandbox messaging case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=get_current_timestamp.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.11
- Clean sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation
- Fault sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_date_and_time_multiple_user_turn_alt::timeout

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=datetime_info_to_timestamp.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 11.03
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Fault sequence: datetime_info_to_timestamp -> datetime_info_to_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_date_and_time_multiple_user_turn_alt::schema_drift

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=datetime_info_to_timestamp.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.10
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Fault sequence: datetime_info_to_timestamp -> datetime_info_to_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_date_and_time_multiple_user_turn_alt::stale_state

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=datetime_info_to_timestamp.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.07
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Fault sequence: datetime_info_to_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_date_and_time_multiple_user_turn_alt::vague_observation

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=datetime_info_to_timestamp.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.04
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Fault sequence: datetime_info_to_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_week_delta_and_time_multiple_user_turn_alt::timeout

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=get_current_timestamp.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 11.51
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_week_delta_and_time_multiple_user_turn_alt::schema_drift

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=get_current_timestamp.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.05
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_week_delta_and_time_multiple_user_turn_alt::stale_state

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=get_current_timestamp.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.23
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_week_delta_and_time_multiple_user_turn_alt::vague_observation

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=get_current_timestamp.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.30
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_weekday_delta_and_time_multiple_user_turn_alt::timeout

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=get_current_timestamp.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 11.27
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_weekday_delta_and_time_multiple_user_turn_alt::schema_drift

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=get_current_timestamp.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.03
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_weekday_delta_and_time_multiple_user_turn_alt::stale_state

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=get_current_timestamp.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.22
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_weekday_delta_and_time_multiple_user_turn_alt::vague_observation

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=get_current_timestamp.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.26
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_date_and_time_alt::timeout

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=datetime_info_to_timestamp.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 11.34
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Fault sequence: datetime_info_to_timestamp -> datetime_info_to_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_date_and_time_alt::schema_drift

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=datetime_info_to_timestamp.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: -0.07
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Fault sequence: datetime_info_to_timestamp -> datetime_info_to_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_date_and_time_alt::stale_state

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=datetime_info_to_timestamp.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.11
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Fault sequence: datetime_info_to_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_date_and_time_alt::vague_observation

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=datetime_info_to_timestamp.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.08
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Fault sequence: datetime_info_to_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_weekday_delta_and_time_alt::timeout

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=timeout; target tool=get_current_timestamp.
- Noise type: timeout
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 11.69
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_weekday_delta_and_time_alt::schema_drift

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=schema_drift; target tool=get_current_timestamp.
- Noise type: schema_drift
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- State corrupted: False
- Cost increase: 1
- Failed fault calls: 1
- Observation fault count: 1
- Extra steps: 1
- Latency increase ms: 0.35
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_weekday_delta_and_time_alt::stale_state

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=stale_state; target tool=get_current_timestamp.
- Noise type: stale_state
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.03
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> add_reminder

### experiment1_toolsandbox_subset::toolsandbox::add_reminder_content_and_weekday_delta_and_time_alt::vague_observation

- Description: ToolSandbox reminders case. Stateful follows the full oracle trajectory; stateless evaluates a compact final-state trajectory. Noise type=vague_observation; target tool=get_current_timestamp.
- Noise type: vague_observation
- Source: experiment1_toolsandbox_subset
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- State corrupted: False
- Cost increase: 0
- Failed fault calls: 0
- Observation fault count: 1
- Extra steps: 0
- Latency increase ms: 0.17
- Clean sequence: get_current_timestamp -> add_reminder
- Fault sequence: get_current_timestamp -> add_reminder
