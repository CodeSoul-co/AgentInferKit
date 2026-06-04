# Agent-Policy Noise Robustness Report

## By Strategy and Noise

| Strategy | Noise | Cases | Success@1 | Pass^k | Recovery | Cost increase | State corruption |
|---|---|---:|---:|---:|---:|---:|---:|
| direct | misleading_observation | 23 | 4.3% | 4.3% | 0.0% | 0.00 | 95.7% |
| direct | schema_drift | 23 | 0.0% | 0.0% | 0.0% | 0.00 | 100.0% |
| direct | stale_state | 23 | 30.4% | 30.4% | 0.0% | 0.00 | 69.6% |
| direct | timeout | 23 | 0.0% | 0.0% | 0.0% | 0.00 | 100.0% |
| direct | vague_observation | 23 | 4.3% | 4.3% | 0.0% | 0.00 | 95.7% |
| cot | misleading_observation | 23 | 4.3% | 100.0% | 100.0% | 0.00 | 0.0% |
| cot | schema_drift | 23 | 0.0% | 78.3% | 78.3% | 1.35 | 21.7% |
| cot | stale_state | 23 | 30.4% | 30.4% | 0.0% | 0.00 | 69.6% |
| cot | timeout | 23 | 0.0% | 65.2% | 65.2% | 1.30 | 34.8% |
| cot | vague_observation | 23 | 4.3% | 91.3% | 90.9% | 0.00 | 8.7% |
| react | misleading_observation | 23 | 4.3% | 69.6% | 68.2% | 1.35 | 30.4% |
| react | schema_drift | 23 | 0.0% | 78.3% | 78.3% | 1.35 | 21.7% |
| react | stale_state | 23 | 30.4% | 95.7% | 93.8% | 0.65 | 4.3% |
| react | timeout | 23 | 0.0% | 65.2% | 65.2% | 1.30 | 34.8% |
| react | vague_observation | 23 | 4.3% | 73.9% | 72.7% | 1.35 | 26.1% |
| self_refine | misleading_observation | 23 | 4.3% | 100.0% | 100.0% | 0.00 | 0.0% |
| self_refine | schema_drift | 23 | 0.0% | 78.3% | 78.3% | 1.35 | 21.7% |
| self_refine | stale_state | 23 | 30.4% | 95.7% | 93.8% | 0.65 | 4.3% |
| self_refine | timeout | 23 | 0.0% | 65.2% | 65.2% | 1.30 | 34.8% |
| self_refine | vague_observation | 23 | 4.3% | 91.3% | 90.9% | 0.00 | 8.7% |

## Noise Intensity Curve

| Strategy | Noise | Intensity | Cases | Success@1 | Pass^k | Recovery | Cost increase | State corruption |
|---|---|---|---:|---:|---:|---:|---:|---:|
| direct | misleading_observation | level_1 | 13 | 7.7% | 7.7% | 0.0% | 0.00 | 92.3% |
| direct | misleading_observation | level_2 | 5 | 0.0% | 0.0% | 0.0% | 0.00 | 100.0% |
| direct | misleading_observation | level_3 | 5 | 0.0% | 0.0% | 0.0% | 0.00 | 100.0% |
| direct | schema_drift | level_1 | 13 | 0.0% | 0.0% | 0.0% | 0.00 | 100.0% |
| direct | schema_drift | level_2 | 5 | 0.0% | 0.0% | 0.0% | 0.00 | 100.0% |
| direct | schema_drift | level_3 | 5 | 0.0% | 0.0% | 0.0% | 0.00 | 100.0% |
| direct | stale_state | level_1 | 13 | 53.8% | 53.8% | 0.0% | 0.00 | 46.2% |
| direct | stale_state | level_2 | 5 | 0.0% | 0.0% | 0.0% | 0.00 | 100.0% |
| direct | stale_state | level_3 | 5 | 0.0% | 0.0% | 0.0% | 0.00 | 100.0% |
| direct | timeout | level_1 | 13 | 0.0% | 0.0% | 0.0% | 0.00 | 100.0% |
| direct | timeout | level_2 | 5 | 0.0% | 0.0% | 0.0% | 0.00 | 100.0% |
| direct | timeout | level_3 | 5 | 0.0% | 0.0% | 0.0% | 0.00 | 100.0% |
| direct | vague_observation | level_1 | 13 | 7.7% | 7.7% | 0.0% | 0.00 | 92.3% |
| direct | vague_observation | level_2 | 5 | 0.0% | 0.0% | 0.0% | 0.00 | 100.0% |
| direct | vague_observation | level_3 | 5 | 0.0% | 0.0% | 0.0% | 0.00 | 100.0% |
| cot | misleading_observation | level_1 | 13 | 7.7% | 100.0% | 100.0% | 0.00 | 0.0% |
| cot | misleading_observation | level_2 | 5 | 0.0% | 100.0% | 100.0% | 0.00 | 0.0% |
| cot | misleading_observation | level_3 | 5 | 0.0% | 100.0% | 100.0% | 0.00 | 0.0% |
| cot | schema_drift | level_1 | 13 | 0.0% | 61.5% | 61.5% | 0.46 | 38.5% |
| cot | schema_drift | level_2 | 5 | 0.0% | 100.0% | 100.0% | 2.00 | 0.0% |
| cot | schema_drift | level_3 | 5 | 0.0% | 100.0% | 100.0% | 3.00 | 0.0% |
| cot | stale_state | level_1 | 13 | 53.8% | 53.8% | 0.0% | 0.00 | 46.2% |
| cot | stale_state | level_2 | 5 | 0.0% | 0.0% | 0.0% | 0.00 | 100.0% |
| cot | stale_state | level_3 | 5 | 0.0% | 0.0% | 0.0% | 0.00 | 100.0% |
| cot | timeout | level_1 | 13 | 0.0% | 38.5% | 38.5% | 0.38 | 61.5% |
| cot | timeout | level_2 | 5 | 0.0% | 100.0% | 100.0% | 2.00 | 0.0% |
| cot | timeout | level_3 | 5 | 0.0% | 100.0% | 100.0% | 3.00 | 0.0% |
| cot | vague_observation | level_1 | 13 | 7.7% | 84.6% | 83.3% | 0.00 | 15.4% |
| cot | vague_observation | level_2 | 5 | 0.0% | 100.0% | 100.0% | 0.00 | 0.0% |
| cot | vague_observation | level_3 | 5 | 0.0% | 100.0% | 100.0% | 0.00 | 0.0% |
| react | misleading_observation | level_1 | 13 | 7.7% | 46.2% | 41.7% | 0.46 | 53.8% |
| react | misleading_observation | level_2 | 5 | 0.0% | 100.0% | 100.0% | 2.00 | 0.0% |
| react | misleading_observation | level_3 | 5 | 0.0% | 100.0% | 100.0% | 3.00 | 0.0% |
| react | schema_drift | level_1 | 13 | 0.0% | 61.5% | 61.5% | 0.46 | 38.5% |
| react | schema_drift | level_2 | 5 | 0.0% | 100.0% | 100.0% | 2.00 | 0.0% |
| react | schema_drift | level_3 | 5 | 0.0% | 100.0% | 100.0% | 3.00 | 0.0% |
| react | stale_state | level_1 | 13 | 53.8% | 92.3% | 83.3% | 0.38 | 7.7% |
| react | stale_state | level_2 | 5 | 0.0% | 100.0% | 100.0% | 1.00 | 0.0% |
| react | stale_state | level_3 | 5 | 0.0% | 100.0% | 100.0% | 1.00 | 0.0% |
| react | timeout | level_1 | 13 | 0.0% | 38.5% | 38.5% | 0.38 | 61.5% |
| react | timeout | level_2 | 5 | 0.0% | 100.0% | 100.0% | 2.00 | 0.0% |
| react | timeout | level_3 | 5 | 0.0% | 100.0% | 100.0% | 3.00 | 0.0% |
| react | vague_observation | level_1 | 13 | 7.7% | 53.8% | 50.0% | 0.46 | 46.2% |
| react | vague_observation | level_2 | 5 | 0.0% | 100.0% | 100.0% | 2.00 | 0.0% |
| react | vague_observation | level_3 | 5 | 0.0% | 100.0% | 100.0% | 3.00 | 0.0% |
| self_refine | misleading_observation | level_1 | 13 | 7.7% | 100.0% | 100.0% | 0.00 | 0.0% |
| self_refine | misleading_observation | level_2 | 5 | 0.0% | 100.0% | 100.0% | 0.00 | 0.0% |
| self_refine | misleading_observation | level_3 | 5 | 0.0% | 100.0% | 100.0% | 0.00 | 0.0% |
| self_refine | schema_drift | level_1 | 13 | 0.0% | 61.5% | 61.5% | 0.46 | 38.5% |
| self_refine | schema_drift | level_2 | 5 | 0.0% | 100.0% | 100.0% | 2.00 | 0.0% |
| self_refine | schema_drift | level_3 | 5 | 0.0% | 100.0% | 100.0% | 3.00 | 0.0% |
| self_refine | stale_state | level_1 | 13 | 53.8% | 92.3% | 83.3% | 0.38 | 7.7% |
| self_refine | stale_state | level_2 | 5 | 0.0% | 100.0% | 100.0% | 1.00 | 0.0% |
| self_refine | stale_state | level_3 | 5 | 0.0% | 100.0% | 100.0% | 1.00 | 0.0% |
| self_refine | timeout | level_1 | 13 | 0.0% | 38.5% | 38.5% | 0.38 | 61.5% |
| self_refine | timeout | level_2 | 5 | 0.0% | 100.0% | 100.0% | 2.00 | 0.0% |
| self_refine | timeout | level_3 | 5 | 0.0% | 100.0% | 100.0% | 3.00 | 0.0% |
| self_refine | vague_observation | level_1 | 13 | 7.7% | 84.6% | 83.3% | 0.00 | 15.4% |
| self_refine | vague_observation | level_2 | 5 | 0.0% | 100.0% | 100.0% | 0.00 | 0.0% |
| self_refine | vague_observation | level_3 | 5 | 0.0% | 100.0% | 100.0% | 0.00 | 0.0% |

## Cases

### synthetic_policy::file_write::timeout::level_1 / direct

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write

### synthetic_policy::file_write::timeout::level_1 / cot

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write -> file.write

### synthetic_policy::file_write::timeout::level_1 / react

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write -> file.write

### synthetic_policy::file_write::timeout::level_1 / self_refine

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write -> file.write

### synthetic_policy::issue_create::timeout::level_1 / direct

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create

### synthetic_policy::issue_create::timeout::level_1 / cot

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create -> issue.create

### synthetic_policy::issue_create::timeout::level_1 / react

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create -> issue.create

### synthetic_policy::issue_create::timeout::level_1 / self_refine

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create -> issue.create

### synthetic_policy::calendar_create::timeout::level_1 / direct

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event

### synthetic_policy::calendar_create::timeout::level_1 / cot

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event -> calendar.create_event

### synthetic_policy::calendar_create::timeout::level_1 / react

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event -> calendar.create_event

### synthetic_policy::calendar_create::timeout::level_1 / self_refine

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event -> calendar.create_event

### synthetic_policy::contact_add::timeout::level_1 / direct

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact

### synthetic_policy::contact_add::timeout::level_1 / cot

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact

### synthetic_policy::contact_add::timeout::level_1 / react

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact

### synthetic_policy::contact_add::timeout::level_1 / self_refine

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact

### synthetic_policy::wifi_setting::timeout::level_1 / direct

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status

### synthetic_policy::wifi_setting::timeout::level_1 / cot

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status -> set_wifi_status

### synthetic_policy::wifi_setting::timeout::level_1 / react

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status -> set_wifi_status

### synthetic_policy::wifi_setting::timeout::level_1 / self_refine

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status -> set_wifi_status

### synthetic_policy::file_write::timeout::level_2 / direct

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write

### synthetic_policy::file_write::timeout::level_2 / cot

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write -> file.write -> file.write

### synthetic_policy::file_write::timeout::level_2 / react

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write -> file.write -> file.write

### synthetic_policy::file_write::timeout::level_2 / self_refine

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write -> file.write -> file.write

### synthetic_policy::issue_create::timeout::level_2 / direct

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create

### synthetic_policy::issue_create::timeout::level_2 / cot

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create -> issue.create -> issue.create

### synthetic_policy::issue_create::timeout::level_2 / react

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create -> issue.create -> issue.create

### synthetic_policy::issue_create::timeout::level_2 / self_refine

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create -> issue.create -> issue.create

### synthetic_policy::calendar_create::timeout::level_2 / direct

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event

### synthetic_policy::calendar_create::timeout::level_2 / cot

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event -> calendar.create_event -> calendar.create_event

### synthetic_policy::calendar_create::timeout::level_2 / react

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event -> calendar.create_event -> calendar.create_event

### synthetic_policy::calendar_create::timeout::level_2 / self_refine

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event -> calendar.create_event -> calendar.create_event

### synthetic_policy::contact_add::timeout::level_2 / direct

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact

### synthetic_policy::contact_add::timeout::level_2 / cot

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact -> add_contact

### synthetic_policy::contact_add::timeout::level_2 / react

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact -> add_contact

### synthetic_policy::contact_add::timeout::level_2 / self_refine

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact -> add_contact

### synthetic_policy::wifi_setting::timeout::level_2 / direct

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status

### synthetic_policy::wifi_setting::timeout::level_2 / cot

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status -> set_wifi_status -> set_wifi_status

### synthetic_policy::wifi_setting::timeout::level_2 / react

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status -> set_wifi_status -> set_wifi_status

### synthetic_policy::wifi_setting::timeout::level_2 / self_refine

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status -> set_wifi_status -> set_wifi_status

### synthetic_policy::file_write::timeout::level_3 / direct

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write

### synthetic_policy::file_write::timeout::level_3 / cot

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write -> file.write -> file.write -> file.write

### synthetic_policy::file_write::timeout::level_3 / react

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write -> file.write -> file.write -> file.write

### synthetic_policy::file_write::timeout::level_3 / self_refine

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write -> file.write -> file.write -> file.write

### synthetic_policy::issue_create::timeout::level_3 / direct

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create

### synthetic_policy::issue_create::timeout::level_3 / cot

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create -> issue.create -> issue.create -> issue.create

### synthetic_policy::issue_create::timeout::level_3 / react

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create -> issue.create -> issue.create -> issue.create

### synthetic_policy::issue_create::timeout::level_3 / self_refine

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create -> issue.create -> issue.create -> issue.create

### synthetic_policy::calendar_create::timeout::level_3 / direct

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event

### synthetic_policy::calendar_create::timeout::level_3 / cot

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event -> calendar.create_event -> calendar.create_event -> calendar.create_event

### synthetic_policy::calendar_create::timeout::level_3 / react

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event -> calendar.create_event -> calendar.create_event -> calendar.create_event

### synthetic_policy::calendar_create::timeout::level_3 / self_refine

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event -> calendar.create_event -> calendar.create_event -> calendar.create_event

### synthetic_policy::contact_add::timeout::level_3 / direct

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact

### synthetic_policy::contact_add::timeout::level_3 / cot

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact -> add_contact -> add_contact

### synthetic_policy::contact_add::timeout::level_3 / react

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact -> add_contact -> add_contact

### synthetic_policy::contact_add::timeout::level_3 / self_refine

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact -> add_contact -> add_contact

### synthetic_policy::wifi_setting::timeout::level_3 / direct

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status

### synthetic_policy::wifi_setting::timeout::level_3 / cot

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status -> set_wifi_status -> set_wifi_status -> set_wifi_status

### synthetic_policy::wifi_setting::timeout::level_3 / react

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status -> set_wifi_status -> set_wifi_status -> set_wifi_status

### synthetic_policy::wifi_setting::timeout::level_3 / self_refine

- Noise type: timeout
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status -> set_wifi_status -> set_wifi_status -> set_wifi_status

### synthetic_policy::file_write::schema_drift::level_1 / direct

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write

### synthetic_policy::file_write::schema_drift::level_1 / cot

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write -> file.write

### synthetic_policy::file_write::schema_drift::level_1 / react

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write -> file.write

### synthetic_policy::file_write::schema_drift::level_1 / self_refine

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write -> file.write

### synthetic_policy::issue_create::schema_drift::level_1 / direct

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create

### synthetic_policy::issue_create::schema_drift::level_1 / cot

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create -> issue.create

### synthetic_policy::issue_create::schema_drift::level_1 / react

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create -> issue.create

### synthetic_policy::issue_create::schema_drift::level_1 / self_refine

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create -> issue.create

### synthetic_policy::calendar_create::schema_drift::level_1 / direct

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event

### synthetic_policy::calendar_create::schema_drift::level_1 / cot

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event -> calendar.create_event

### synthetic_policy::calendar_create::schema_drift::level_1 / react

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event -> calendar.create_event

### synthetic_policy::calendar_create::schema_drift::level_1 / self_refine

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event -> calendar.create_event

### synthetic_policy::contact_add::schema_drift::level_1 / direct

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact

### synthetic_policy::contact_add::schema_drift::level_1 / cot

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact

### synthetic_policy::contact_add::schema_drift::level_1 / react

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact

### synthetic_policy::contact_add::schema_drift::level_1 / self_refine

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact

### synthetic_policy::wifi_setting::schema_drift::level_1 / direct

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status

### synthetic_policy::wifi_setting::schema_drift::level_1 / cot

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status -> set_wifi_status

### synthetic_policy::wifi_setting::schema_drift::level_1 / react

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status -> set_wifi_status

### synthetic_policy::wifi_setting::schema_drift::level_1 / self_refine

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status -> set_wifi_status

### synthetic_policy::file_write::schema_drift::level_2 / direct

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write

### synthetic_policy::file_write::schema_drift::level_2 / cot

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write -> file.write -> file.write

### synthetic_policy::file_write::schema_drift::level_2 / react

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write -> file.write -> file.write

### synthetic_policy::file_write::schema_drift::level_2 / self_refine

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write -> file.write -> file.write

### synthetic_policy::issue_create::schema_drift::level_2 / direct

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create

### synthetic_policy::issue_create::schema_drift::level_2 / cot

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create -> issue.create -> issue.create

### synthetic_policy::issue_create::schema_drift::level_2 / react

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create -> issue.create -> issue.create

### synthetic_policy::issue_create::schema_drift::level_2 / self_refine

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create -> issue.create -> issue.create

### synthetic_policy::calendar_create::schema_drift::level_2 / direct

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event

### synthetic_policy::calendar_create::schema_drift::level_2 / cot

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event -> calendar.create_event -> calendar.create_event

### synthetic_policy::calendar_create::schema_drift::level_2 / react

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event -> calendar.create_event -> calendar.create_event

### synthetic_policy::calendar_create::schema_drift::level_2 / self_refine

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event -> calendar.create_event -> calendar.create_event

### synthetic_policy::contact_add::schema_drift::level_2 / direct

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact

### synthetic_policy::contact_add::schema_drift::level_2 / cot

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact -> add_contact

### synthetic_policy::contact_add::schema_drift::level_2 / react

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact -> add_contact

### synthetic_policy::contact_add::schema_drift::level_2 / self_refine

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact -> add_contact

### synthetic_policy::wifi_setting::schema_drift::level_2 / direct

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status

### synthetic_policy::wifi_setting::schema_drift::level_2 / cot

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status -> set_wifi_status -> set_wifi_status

### synthetic_policy::wifi_setting::schema_drift::level_2 / react

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status -> set_wifi_status -> set_wifi_status

### synthetic_policy::wifi_setting::schema_drift::level_2 / self_refine

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status -> set_wifi_status -> set_wifi_status

### synthetic_policy::file_write::schema_drift::level_3 / direct

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write

### synthetic_policy::file_write::schema_drift::level_3 / cot

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write -> file.write -> file.write -> file.write

### synthetic_policy::file_write::schema_drift::level_3 / react

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write -> file.write -> file.write -> file.write

### synthetic_policy::file_write::schema_drift::level_3 / self_refine

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: file.write
- Success@1 sequence: file.write
- Pass^k sequence: file.write -> file.write -> file.write -> file.write

### synthetic_policy::issue_create::schema_drift::level_3 / direct

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create

### synthetic_policy::issue_create::schema_drift::level_3 / cot

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create -> issue.create -> issue.create -> issue.create

### synthetic_policy::issue_create::schema_drift::level_3 / react

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create -> issue.create -> issue.create -> issue.create

### synthetic_policy::issue_create::schema_drift::level_3 / self_refine

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: issue.create
- Success@1 sequence: issue.create
- Pass^k sequence: issue.create -> issue.create -> issue.create -> issue.create

### synthetic_policy::calendar_create::schema_drift::level_3 / direct

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event

### synthetic_policy::calendar_create::schema_drift::level_3 / cot

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event -> calendar.create_event -> calendar.create_event -> calendar.create_event

### synthetic_policy::calendar_create::schema_drift::level_3 / react

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event -> calendar.create_event -> calendar.create_event -> calendar.create_event

### synthetic_policy::calendar_create::schema_drift::level_3 / self_refine

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: calendar.create_event
- Success@1 sequence: calendar.create_event
- Pass^k sequence: calendar.create_event -> calendar.create_event -> calendar.create_event -> calendar.create_event

### synthetic_policy::contact_add::schema_drift::level_3 / direct

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact

### synthetic_policy::contact_add::schema_drift::level_3 / cot

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact -> add_contact -> add_contact

### synthetic_policy::contact_add::schema_drift::level_3 / react

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact -> add_contact -> add_contact

### synthetic_policy::contact_add::schema_drift::level_3 / self_refine

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: add_contact
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact -> add_contact -> add_contact

### synthetic_policy::wifi_setting::schema_drift::level_3 / direct

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status

### synthetic_policy::wifi_setting::schema_drift::level_3 / cot

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status -> set_wifi_status -> set_wifi_status -> set_wifi_status

### synthetic_policy::wifi_setting::schema_drift::level_3 / react

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status -> set_wifi_status -> set_wifi_status -> set_wifi_status

### synthetic_policy::wifi_setting::schema_drift::level_3 / self_refine

- Noise type: schema_drift
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: set_wifi_status
- Success@1 sequence: set_wifi_status
- Pass^k sequence: set_wifi_status -> set_wifi_status -> set_wifi_status -> set_wifi_status

### synthetic_policy::contact_search_update::vague_observation::level_1 / direct

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts

### synthetic_policy::contact_search_update::vague_observation::level_1 / cot

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> modify_contact

### synthetic_policy::contact_search_update::vague_observation::level_1 / react

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> search_contacts -> modify_contact

### synthetic_policy::contact_search_update::vague_observation::level_1 / self_refine

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> modify_contact

### synthetic_policy::reminder_search_update::vague_observation::level_1 / direct

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder

### synthetic_policy::reminder_search_update::vague_observation::level_1 / cot

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> modify_reminder

### synthetic_policy::reminder_search_update::vague_observation::level_1 / react

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> search_reminder -> modify_reminder

### synthetic_policy::reminder_search_update::vague_observation::level_1 / self_refine

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> modify_reminder

### synthetic_policy::message_search_send::vague_observation::level_1 / direct

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages

### synthetic_policy::message_search_send::vague_observation::level_1 / cot

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> send_message_with_phone_number

### synthetic_policy::message_search_send::vague_observation::level_1 / react

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages -> send_message_with_phone_number

### synthetic_policy::message_search_send::vague_observation::level_1 / self_refine

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> send_message_with_phone_number

### synthetic_policy::setting_get_then_set::vague_observation::level_1 / direct

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status

### synthetic_policy::setting_get_then_set::vague_observation::level_1 / cot

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status -> set_wifi_status

### synthetic_policy::setting_get_then_set::vague_observation::level_1 / react

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status -> get_wifi_status -> set_wifi_status

### synthetic_policy::setting_get_then_set::vague_observation::level_1 / self_refine

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status -> set_wifi_status

### synthetic_policy::calendar_search_update::vague_observation::level_1 / direct

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events

### synthetic_policy::calendar_search_update::vague_observation::level_1 / cot

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events -> calendar.update_event

### synthetic_policy::calendar_search_update::vague_observation::level_1 / react

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events -> calendar.search_events -> calendar.update_event

### synthetic_policy::calendar_search_update::vague_observation::level_1 / self_refine

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events -> calendar.update_event

### synthetic_policy::contact_search_update::vague_observation::level_2 / direct

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts

### synthetic_policy::contact_search_update::vague_observation::level_2 / cot

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> modify_contact

### synthetic_policy::contact_search_update::vague_observation::level_2 / react

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> search_contacts -> search_contacts -> modify_contact

### synthetic_policy::contact_search_update::vague_observation::level_2 / self_refine

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> modify_contact

### synthetic_policy::reminder_search_update::vague_observation::level_2 / direct

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder

### synthetic_policy::reminder_search_update::vague_observation::level_2 / cot

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> modify_reminder

### synthetic_policy::reminder_search_update::vague_observation::level_2 / react

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> search_reminder -> search_reminder -> modify_reminder

### synthetic_policy::reminder_search_update::vague_observation::level_2 / self_refine

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> modify_reminder

### synthetic_policy::message_search_send::vague_observation::level_2 / direct

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages

### synthetic_policy::message_search_send::vague_observation::level_2 / cot

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> send_message_with_phone_number

### synthetic_policy::message_search_send::vague_observation::level_2 / react

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages -> search_messages -> send_message_with_phone_number

### synthetic_policy::message_search_send::vague_observation::level_2 / self_refine

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> send_message_with_phone_number

### synthetic_policy::setting_get_then_set::vague_observation::level_2 / direct

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status

### synthetic_policy::setting_get_then_set::vague_observation::level_2 / cot

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status -> set_wifi_status

### synthetic_policy::setting_get_then_set::vague_observation::level_2 / react

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status -> get_wifi_status -> get_wifi_status -> set_wifi_status

### synthetic_policy::setting_get_then_set::vague_observation::level_2 / self_refine

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status -> set_wifi_status

### synthetic_policy::calendar_search_update::vague_observation::level_2 / direct

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events

### synthetic_policy::calendar_search_update::vague_observation::level_2 / cot

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events -> calendar.update_event

### synthetic_policy::calendar_search_update::vague_observation::level_2 / react

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events -> calendar.search_events -> calendar.search_events -> calendar.update_event

### synthetic_policy::calendar_search_update::vague_observation::level_2 / self_refine

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events -> calendar.update_event

### synthetic_policy::contact_search_update::vague_observation::level_3 / direct

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts

### synthetic_policy::contact_search_update::vague_observation::level_3 / cot

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> modify_contact

### synthetic_policy::contact_search_update::vague_observation::level_3 / react

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> search_contacts -> search_contacts -> search_contacts -> modify_contact

### synthetic_policy::contact_search_update::vague_observation::level_3 / self_refine

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> modify_contact

### synthetic_policy::reminder_search_update::vague_observation::level_3 / direct

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder

### synthetic_policy::reminder_search_update::vague_observation::level_3 / cot

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> modify_reminder

### synthetic_policy::reminder_search_update::vague_observation::level_3 / react

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> search_reminder -> search_reminder -> search_reminder -> modify_reminder

### synthetic_policy::reminder_search_update::vague_observation::level_3 / self_refine

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> modify_reminder

### synthetic_policy::message_search_send::vague_observation::level_3 / direct

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages

### synthetic_policy::message_search_send::vague_observation::level_3 / cot

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> send_message_with_phone_number

### synthetic_policy::message_search_send::vague_observation::level_3 / react

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages -> search_messages -> search_messages -> send_message_with_phone_number

### synthetic_policy::message_search_send::vague_observation::level_3 / self_refine

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> send_message_with_phone_number

### synthetic_policy::setting_get_then_set::vague_observation::level_3 / direct

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status

### synthetic_policy::setting_get_then_set::vague_observation::level_3 / cot

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status -> set_wifi_status

### synthetic_policy::setting_get_then_set::vague_observation::level_3 / react

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status -> get_wifi_status -> get_wifi_status -> get_wifi_status -> set_wifi_status

### synthetic_policy::setting_get_then_set::vague_observation::level_3 / self_refine

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status -> set_wifi_status

### synthetic_policy::calendar_search_update::vague_observation::level_3 / direct

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events

### synthetic_policy::calendar_search_update::vague_observation::level_3 / cot

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events -> calendar.update_event

### synthetic_policy::calendar_search_update::vague_observation::level_3 / react

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events -> calendar.search_events -> calendar.search_events -> calendar.search_events -> calendar.update_event

### synthetic_policy::calendar_search_update::vague_observation::level_3 / self_refine

- Noise type: vague_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events -> calendar.update_event

### synthetic_policy::contact_search_update::misleading_observation::level_1 / direct

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts

### synthetic_policy::contact_search_update::misleading_observation::level_1 / cot

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> modify_contact

### synthetic_policy::contact_search_update::misleading_observation::level_1 / react

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> search_contacts -> modify_contact

### synthetic_policy::contact_search_update::misleading_observation::level_1 / self_refine

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> modify_contact

### synthetic_policy::reminder_search_update::misleading_observation::level_1 / direct

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder

### synthetic_policy::reminder_search_update::misleading_observation::level_1 / cot

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> modify_reminder

### synthetic_policy::reminder_search_update::misleading_observation::level_1 / react

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> search_reminder -> modify_reminder

### synthetic_policy::reminder_search_update::misleading_observation::level_1 / self_refine

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> modify_reminder

### synthetic_policy::message_search_send::misleading_observation::level_1 / direct

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages

### synthetic_policy::message_search_send::misleading_observation::level_1 / cot

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> send_message_with_phone_number

### synthetic_policy::message_search_send::misleading_observation::level_1 / react

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages -> send_message_with_phone_number

### synthetic_policy::message_search_send::misleading_observation::level_1 / self_refine

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> send_message_with_phone_number

### synthetic_policy::setting_get_then_set::misleading_observation::level_1 / direct

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status

### synthetic_policy::setting_get_then_set::misleading_observation::level_1 / cot

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status -> set_wifi_status

### synthetic_policy::setting_get_then_set::misleading_observation::level_1 / react

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status -> get_wifi_status -> set_wifi_status

### synthetic_policy::setting_get_then_set::misleading_observation::level_1 / self_refine

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status -> set_wifi_status

### synthetic_policy::calendar_search_update::misleading_observation::level_1 / direct

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events

### synthetic_policy::calendar_search_update::misleading_observation::level_1 / cot

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events -> calendar.update_event

### synthetic_policy::calendar_search_update::misleading_observation::level_1 / react

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events -> calendar.search_events -> calendar.update_event

### synthetic_policy::calendar_search_update::misleading_observation::level_1 / self_refine

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events -> calendar.update_event

### synthetic_policy::contact_search_update::misleading_observation::level_2 / direct

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts

### synthetic_policy::contact_search_update::misleading_observation::level_2 / cot

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> modify_contact

### synthetic_policy::contact_search_update::misleading_observation::level_2 / react

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> search_contacts -> search_contacts -> modify_contact

### synthetic_policy::contact_search_update::misleading_observation::level_2 / self_refine

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> modify_contact

### synthetic_policy::reminder_search_update::misleading_observation::level_2 / direct

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder

### synthetic_policy::reminder_search_update::misleading_observation::level_2 / cot

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> modify_reminder

### synthetic_policy::reminder_search_update::misleading_observation::level_2 / react

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> search_reminder -> search_reminder -> modify_reminder

### synthetic_policy::reminder_search_update::misleading_observation::level_2 / self_refine

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> modify_reminder

### synthetic_policy::message_search_send::misleading_observation::level_2 / direct

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages

### synthetic_policy::message_search_send::misleading_observation::level_2 / cot

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> send_message_with_phone_number

### synthetic_policy::message_search_send::misleading_observation::level_2 / react

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages -> search_messages -> send_message_with_phone_number

### synthetic_policy::message_search_send::misleading_observation::level_2 / self_refine

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> send_message_with_phone_number

### synthetic_policy::setting_get_then_set::misleading_observation::level_2 / direct

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status

### synthetic_policy::setting_get_then_set::misleading_observation::level_2 / cot

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status -> set_wifi_status

### synthetic_policy::setting_get_then_set::misleading_observation::level_2 / react

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status -> get_wifi_status -> get_wifi_status -> set_wifi_status

### synthetic_policy::setting_get_then_set::misleading_observation::level_2 / self_refine

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status -> set_wifi_status

### synthetic_policy::calendar_search_update::misleading_observation::level_2 / direct

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events

### synthetic_policy::calendar_search_update::misleading_observation::level_2 / cot

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events -> calendar.update_event

### synthetic_policy::calendar_search_update::misleading_observation::level_2 / react

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 2
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events -> calendar.search_events -> calendar.search_events -> calendar.update_event

### synthetic_policy::calendar_search_update::misleading_observation::level_2 / self_refine

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events -> calendar.update_event

### synthetic_policy::contact_search_update::misleading_observation::level_3 / direct

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts

### synthetic_policy::contact_search_update::misleading_observation::level_3 / cot

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> modify_contact

### synthetic_policy::contact_search_update::misleading_observation::level_3 / react

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> search_contacts -> search_contacts -> search_contacts -> modify_contact

### synthetic_policy::contact_search_update::misleading_observation::level_3 / self_refine

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> modify_contact

### synthetic_policy::reminder_search_update::misleading_observation::level_3 / direct

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder

### synthetic_policy::reminder_search_update::misleading_observation::level_3 / cot

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> modify_reminder

### synthetic_policy::reminder_search_update::misleading_observation::level_3 / react

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> search_reminder -> search_reminder -> search_reminder -> modify_reminder

### synthetic_policy::reminder_search_update::misleading_observation::level_3 / self_refine

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> modify_reminder

### synthetic_policy::message_search_send::misleading_observation::level_3 / direct

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages

### synthetic_policy::message_search_send::misleading_observation::level_3 / cot

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> send_message_with_phone_number

### synthetic_policy::message_search_send::misleading_observation::level_3 / react

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages -> search_messages -> search_messages -> send_message_with_phone_number

### synthetic_policy::message_search_send::misleading_observation::level_3 / self_refine

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_messages -> send_message_with_phone_number
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> send_message_with_phone_number

### synthetic_policy::setting_get_then_set::misleading_observation::level_3 / direct

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status

### synthetic_policy::setting_get_then_set::misleading_observation::level_3 / cot

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status -> set_wifi_status

### synthetic_policy::setting_get_then_set::misleading_observation::level_3 / react

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status -> get_wifi_status -> get_wifi_status -> get_wifi_status -> set_wifi_status

### synthetic_policy::setting_get_then_set::misleading_observation::level_3 / self_refine

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status
- Success@1 sequence: get_wifi_status
- Pass^k sequence: get_wifi_status -> set_wifi_status

### synthetic_policy::calendar_search_update::misleading_observation::level_3 / direct

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events

### synthetic_policy::calendar_search_update::misleading_observation::level_3 / cot

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events -> calendar.update_event

### synthetic_policy::calendar_search_update::misleading_observation::level_3 / react

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 3
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events -> calendar.search_events -> calendar.search_events -> calendar.search_events -> calendar.update_event

### synthetic_policy::calendar_search_update::misleading_observation::level_3 / self_refine

- Noise type: misleading_observation
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event
- Success@1 sequence: calendar.search_events
- Pass^k sequence: calendar.search_events -> calendar.update_event

### synthetic_policy::contact_stale_message::stale_state::level_1 / direct

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Success@1 sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Pass^k sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number

### synthetic_policy::contact_stale_message::stale_state::level_1 / cot

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Success@1 sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Pass^k sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number

### synthetic_policy::contact_stale_message::stale_state::level_1 / react

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Success@1 sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Pass^k sequence: search_contacts -> modify_contact -> search_contacts -> search_contacts -> send_message_with_phone_number

### synthetic_policy::contact_stale_message::stale_state::level_1 / self_refine

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Success@1 sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Pass^k sequence: search_contacts -> modify_contact -> search_contacts -> search_contacts -> send_message_with_phone_number

### synthetic_policy::reminder_stale_message::stale_state::level_1 / direct

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Success@1 sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Pass^k sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number

### synthetic_policy::reminder_stale_message::stale_state::level_1 / cot

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Success@1 sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Pass^k sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number

### synthetic_policy::reminder_stale_message::stale_state::level_1 / react

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Success@1 sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Pass^k sequence: search_reminder -> modify_reminder -> search_reminder -> search_reminder -> send_message_with_phone_number

### synthetic_policy::reminder_stale_message::stale_state::level_1 / self_refine

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Success@1 sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Pass^k sequence: search_reminder -> modify_reminder -> search_reminder -> search_reminder -> send_message_with_phone_number

### synthetic_policy::calendar_stale_message::stale_state::level_1 / direct

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Success@1 sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Pass^k sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number

### synthetic_policy::calendar_stale_message::stale_state::level_1 / cot

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Success@1 sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Pass^k sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number

### synthetic_policy::calendar_stale_message::stale_state::level_1 / react

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Success@1 sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Pass^k sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> calendar.search_events -> send_message_with_phone_number

### synthetic_policy::calendar_stale_message::stale_state::level_1 / self_refine

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Success@1 sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Pass^k sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> calendar.search_events -> send_message_with_phone_number

### synthetic_policy::file_index_stale_message::stale_state::level_1 / direct

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Success@1 sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Pass^k sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number

### synthetic_policy::file_index_stale_message::stale_state::level_1 / cot

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Success@1 sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Pass^k sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number

### synthetic_policy::file_index_stale_message::stale_state::level_1 / react

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Success@1 sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Pass^k sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> search.query -> send_message_with_phone_number

### synthetic_policy::file_index_stale_message::stale_state::level_1 / self_refine

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Success@1 sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Pass^k sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> search.query -> send_message_with_phone_number

### synthetic_policy::setting_stale_message::stale_state::level_1 / direct

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Success@1 sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Pass^k sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number

### synthetic_policy::setting_stale_message::stale_state::level_1 / cot

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Success@1 sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Pass^k sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number

### synthetic_policy::setting_stale_message::stale_state::level_1 / react

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Success@1 sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Pass^k sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> get_wifi_status -> send_message_with_phone_number

### synthetic_policy::setting_stale_message::stale_state::level_1 / self_refine

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Success@1 sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Pass^k sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> get_wifi_status -> send_message_with_phone_number

### synthetic_policy::contact_stale_message::stale_state::level_2 / direct

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Success@1 sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Pass^k sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number

### synthetic_policy::contact_stale_message::stale_state::level_2 / cot

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Success@1 sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Pass^k sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number

### synthetic_policy::contact_stale_message::stale_state::level_2 / react

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Success@1 sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Pass^k sequence: search_contacts -> modify_contact -> search_contacts -> search_contacts -> send_message_with_phone_number

### synthetic_policy::contact_stale_message::stale_state::level_2 / self_refine

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Success@1 sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Pass^k sequence: search_contacts -> modify_contact -> search_contacts -> search_contacts -> send_message_with_phone_number

### synthetic_policy::reminder_stale_message::stale_state::level_2 / direct

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Success@1 sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Pass^k sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number

### synthetic_policy::reminder_stale_message::stale_state::level_2 / cot

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Success@1 sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Pass^k sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number

### synthetic_policy::reminder_stale_message::stale_state::level_2 / react

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Success@1 sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Pass^k sequence: search_reminder -> modify_reminder -> search_reminder -> search_reminder -> send_message_with_phone_number

### synthetic_policy::reminder_stale_message::stale_state::level_2 / self_refine

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Success@1 sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Pass^k sequence: search_reminder -> modify_reminder -> search_reminder -> search_reminder -> send_message_with_phone_number

### synthetic_policy::calendar_stale_message::stale_state::level_2 / direct

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Success@1 sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Pass^k sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number

### synthetic_policy::calendar_stale_message::stale_state::level_2 / cot

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Success@1 sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Pass^k sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number

### synthetic_policy::calendar_stale_message::stale_state::level_2 / react

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Success@1 sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Pass^k sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> calendar.search_events -> send_message_with_phone_number

### synthetic_policy::calendar_stale_message::stale_state::level_2 / self_refine

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Success@1 sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Pass^k sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> calendar.search_events -> send_message_with_phone_number

### synthetic_policy::file_index_stale_message::stale_state::level_2 / direct

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Success@1 sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Pass^k sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number

### synthetic_policy::file_index_stale_message::stale_state::level_2 / cot

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Success@1 sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Pass^k sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number

### synthetic_policy::file_index_stale_message::stale_state::level_2 / react

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Success@1 sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Pass^k sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> search.query -> send_message_with_phone_number

### synthetic_policy::file_index_stale_message::stale_state::level_2 / self_refine

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Success@1 sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Pass^k sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> search.query -> send_message_with_phone_number

### synthetic_policy::setting_stale_message::stale_state::level_2 / direct

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Success@1 sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Pass^k sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number

### synthetic_policy::setting_stale_message::stale_state::level_2 / cot

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Success@1 sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Pass^k sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number

### synthetic_policy::setting_stale_message::stale_state::level_2 / react

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Success@1 sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Pass^k sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> get_wifi_status -> send_message_with_phone_number

### synthetic_policy::setting_stale_message::stale_state::level_2 / self_refine

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_2
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Success@1 sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Pass^k sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> get_wifi_status -> send_message_with_phone_number

### synthetic_policy::contact_stale_message::stale_state::level_3 / direct

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Success@1 sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Pass^k sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number

### synthetic_policy::contact_stale_message::stale_state::level_3 / cot

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Success@1 sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Pass^k sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number

### synthetic_policy::contact_stale_message::stale_state::level_3 / react

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Success@1 sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Pass^k sequence: search_contacts -> modify_contact -> search_contacts -> search_contacts -> send_message_with_phone_number

### synthetic_policy::contact_stale_message::stale_state::level_3 / self_refine

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Success@1 sequence: search_contacts -> modify_contact -> search_contacts -> send_message_with_phone_number
- Pass^k sequence: search_contacts -> modify_contact -> search_contacts -> search_contacts -> send_message_with_phone_number

### synthetic_policy::reminder_stale_message::stale_state::level_3 / direct

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Success@1 sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Pass^k sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number

### synthetic_policy::reminder_stale_message::stale_state::level_3 / cot

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Success@1 sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Pass^k sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number

### synthetic_policy::reminder_stale_message::stale_state::level_3 / react

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Success@1 sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Pass^k sequence: search_reminder -> modify_reminder -> search_reminder -> search_reminder -> send_message_with_phone_number

### synthetic_policy::reminder_stale_message::stale_state::level_3 / self_refine

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Success@1 sequence: search_reminder -> modify_reminder -> search_reminder -> send_message_with_phone_number
- Pass^k sequence: search_reminder -> modify_reminder -> search_reminder -> search_reminder -> send_message_with_phone_number

### synthetic_policy::calendar_stale_message::stale_state::level_3 / direct

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Success@1 sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Pass^k sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number

### synthetic_policy::calendar_stale_message::stale_state::level_3 / cot

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Success@1 sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Pass^k sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number

### synthetic_policy::calendar_stale_message::stale_state::level_3 / react

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Success@1 sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Pass^k sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> calendar.search_events -> send_message_with_phone_number

### synthetic_policy::calendar_stale_message::stale_state::level_3 / self_refine

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Success@1 sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> send_message_with_phone_number
- Pass^k sequence: calendar.search_events -> calendar.update_event -> calendar.search_events -> calendar.search_events -> send_message_with_phone_number

### synthetic_policy::file_index_stale_message::stale_state::level_3 / direct

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Success@1 sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Pass^k sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number

### synthetic_policy::file_index_stale_message::stale_state::level_3 / cot

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Success@1 sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Pass^k sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number

### synthetic_policy::file_index_stale_message::stale_state::level_3 / react

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Success@1 sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Pass^k sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> search.query -> send_message_with_phone_number

### synthetic_policy::file_index_stale_message::stale_state::level_3 / self_refine

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Success@1 sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> send_message_with_phone_number
- Pass^k sequence: file.write -> search.index -> search.query -> file.write -> search.index -> search.query -> search.query -> send_message_with_phone_number

### synthetic_policy::setting_stale_message::stale_state::level_3 / direct

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Success@1 sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Pass^k sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number

### synthetic_policy::setting_stale_message::stale_state::level_3 / cot

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Success@1 sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Pass^k sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number

### synthetic_policy::setting_stale_message::stale_state::level_3 / react

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Success@1 sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Pass^k sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> get_wifi_status -> send_message_with_phone_number

### synthetic_policy::setting_stale_message::stale_state::level_3 / self_refine

- Noise type: stale_state
- Source: synthetic_policy
- Intensity: level_3
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Success@1 sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> send_message_with_phone_number
- Pass^k sequence: get_wifi_status -> set_wifi_status -> get_wifi_status -> get_wifi_status -> send_message_with_phone_number

### toolsandbox_policy::add_contact_with_name_and_phone_number::timeout / direct

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: add_contact -> end_conversation
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact

### toolsandbox_policy::add_contact_with_name_and_phone_number::timeout / cot

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: add_contact -> end_conversation
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact

### toolsandbox_policy::add_contact_with_name_and_phone_number::timeout / react

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: add_contact -> end_conversation
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact

### toolsandbox_policy::add_contact_with_name_and_phone_number::timeout / self_refine

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: add_contact -> end_conversation
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact

### toolsandbox_policy::modify_contact_with_message_recency_alt::schema_drift / direct

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp

### toolsandbox_policy::modify_contact_with_message_recency_alt::schema_drift / cot

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp -> search_messages -> modify_contact -> end_conversation

### toolsandbox_policy::modify_contact_with_message_recency_alt::schema_drift / react

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp -> search_messages -> modify_contact -> end_conversation

### toolsandbox_policy::modify_contact_with_message_recency_alt::schema_drift / self_refine

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp -> search_messages -> modify_contact -> end_conversation

### toolsandbox_policy::remove_contact_by_phone_ambiguous_alt::vague_observation / direct

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: False
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> remove_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts

### toolsandbox_policy::remove_contact_by_phone_ambiguous_alt::vague_observation / cot

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: False
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> remove_contact -> remove_contact -> remove_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> remove_contact -> remove_contact -> remove_contact

### toolsandbox_policy::remove_contact_by_phone_ambiguous_alt::vague_observation / react

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: False
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_contacts -> remove_contact -> remove_contact -> remove_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> search_contacts -> end_conversation

### toolsandbox_policy::remove_contact_by_phone_ambiguous_alt::vague_observation / self_refine

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: False
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> remove_contact -> remove_contact -> remove_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> remove_contact -> remove_contact -> remove_contact

### toolsandbox_policy::modify_contact_with_message_recency_multiple_user_turn_alt::misleading_observation / direct

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp

### toolsandbox_policy::modify_contact_with_message_recency_multiple_user_turn_alt::misleading_observation / cot

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation

### toolsandbox_policy::modify_contact_with_message_recency_multiple_user_turn_alt::misleading_observation / react

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp -> search_messages -> modify_contact -> end_conversation

### toolsandbox_policy::modify_contact_with_message_recency_multiple_user_turn_alt::misleading_observation / self_refine

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> search_contacts -> search_messages -> modify_contact -> end_conversation

### toolsandbox_policy::remove_contact_by_phone_multiple_user_turn::stale_state / direct

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: False
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> remove_contact
- Success@1 sequence: search_contacts -> remove_contact
- Pass^k sequence: search_contacts -> remove_contact

### toolsandbox_policy::remove_contact_by_phone_multiple_user_turn::stale_state / cot

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: False
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> remove_contact -> remove_contact -> remove_contact
- Success@1 sequence: search_contacts -> remove_contact
- Pass^k sequence: search_contacts -> remove_contact -> remove_contact -> remove_contact

### toolsandbox_policy::remove_contact_by_phone_multiple_user_turn::stale_state / react

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: False
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> remove_contact -> remove_contact -> remove_contact
- Success@1 sequence: search_contacts -> remove_contact
- Pass^k sequence: search_contacts -> remove_contact -> remove_contact -> remove_contact

### toolsandbox_policy::remove_contact_by_phone_multiple_user_turn::stale_state / self_refine

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: False
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> remove_contact -> remove_contact -> remove_contact
- Success@1 sequence: search_contacts -> remove_contact
- Pass^k sequence: search_contacts -> remove_contact -> remove_contact -> remove_contact

### toolsandbox_policy::update_contact_relationship_with_relationship::timeout / direct

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> modify_contact -> modify_contact -> end_conversation
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts

### toolsandbox_policy::update_contact_relationship_with_relationship::timeout / cot

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> modify_contact -> modify_contact -> end_conversation
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> search_contacts -> modify_contact -> end_conversation

### toolsandbox_policy::update_contact_relationship_with_relationship::timeout / react

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> modify_contact -> modify_contact -> end_conversation
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> search_contacts -> modify_contact -> end_conversation

### toolsandbox_policy::update_contact_relationship_with_relationship::timeout / self_refine

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> modify_contact -> modify_contact -> end_conversation
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> search_contacts -> modify_contact -> end_conversation

### toolsandbox_policy::remove_contact_by_phone_ambiguous::schema_drift / direct

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: False
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_contacts -> remove_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts

### toolsandbox_policy::remove_contact_by_phone_ambiguous::schema_drift / cot

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: False
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_contacts -> remove_contact -> remove_contact -> remove_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> search_contacts -> end_conversation

### toolsandbox_policy::remove_contact_by_phone_ambiguous::schema_drift / react

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: False
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_contacts -> remove_contact -> remove_contact -> remove_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> search_contacts -> end_conversation

### toolsandbox_policy::remove_contact_by_phone_ambiguous::schema_drift / self_refine

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: False
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_contacts -> remove_contact -> remove_contact -> remove_contact
- Success@1 sequence: search_contacts
- Pass^k sequence: search_contacts -> search_contacts -> end_conversation

### toolsandbox_policy::remove_contact_with_id::vague_observation / direct

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: False
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: remove_contact
- Success@1 sequence: remove_contact
- Pass^k sequence: remove_contact

### toolsandbox_policy::remove_contact_with_id::vague_observation / cot

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: False
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: remove_contact -> remove_contact -> remove_contact
- Success@1 sequence: remove_contact
- Pass^k sequence: remove_contact -> remove_contact -> remove_contact

### toolsandbox_policy::remove_contact_with_id::vague_observation / react

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: False
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: remove_contact -> remove_contact -> remove_contact
- Success@1 sequence: remove_contact
- Pass^k sequence: remove_contact -> remove_contact -> remove_contact

### toolsandbox_policy::remove_contact_with_id::vague_observation / self_refine

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: False
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: remove_contact -> remove_contact -> remove_contact
- Success@1 sequence: remove_contact
- Pass^k sequence: remove_contact -> remove_contact -> remove_contact

### toolsandbox_policy::add_contact_with_name_and_phone_number_10_distraction_tools::misleading_observation / direct

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: add_contact -> end_conversation
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact

### toolsandbox_policy::add_contact_with_name_and_phone_number_10_distraction_tools::misleading_observation / cot

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: add_contact -> end_conversation
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> end_conversation

### toolsandbox_policy::add_contact_with_name_and_phone_number_10_distraction_tools::misleading_observation / react

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: add_contact -> end_conversation
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> add_contact

### toolsandbox_policy::add_contact_with_name_and_phone_number_10_distraction_tools::misleading_observation / self_refine

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: add_contact -> end_conversation
- Success@1 sequence: add_contact
- Pass^k sequence: add_contact -> end_conversation

### toolsandbox_policy::add_reminder_content_and_date_and_time_multiple_user_turn_alt_all_tools::stale_state / direct

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Success@1 sequence: datetime_info_to_timestamp -> add_reminder
- Pass^k sequence: datetime_info_to_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_date_and_time_multiple_user_turn_alt_all_tools::stale_state / cot

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Success@1 sequence: datetime_info_to_timestamp -> add_reminder
- Pass^k sequence: datetime_info_to_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_date_and_time_multiple_user_turn_alt_all_tools::stale_state / react

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Success@1 sequence: datetime_info_to_timestamp -> add_reminder
- Pass^k sequence: datetime_info_to_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_date_and_time_multiple_user_turn_alt_all_tools::stale_state / self_refine

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Success@1 sequence: datetime_info_to_timestamp -> add_reminder
- Pass^k sequence: datetime_info_to_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_multiple_user_turn_alt_10_distraction_tools::timeout / direct

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_multiple_user_turn_alt_10_distraction_tools::timeout / cot

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_multiple_user_turn_alt_10_distraction_tools::timeout / react

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_multiple_user_turn_alt_10_distraction_tools::timeout / self_refine

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_weekday_delta_and_time_multiple_user_turn_alt_10_distraction_tools::schema_drift / direct

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_weekday_delta_and_time_multiple_user_turn_alt_10_distraction_tools::schema_drift / cot

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_weekday_delta_and_time_multiple_user_turn_alt_10_distraction_tools::schema_drift / react

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_weekday_delta_and_time_multiple_user_turn_alt_10_distraction_tools::schema_drift / self_refine

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_and_location_low_battery_mode_multiple_user_turn_alt::vague_observation / direct

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon -> get_current_timestamp -> add_reminder
- Success@1 sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon
- Pass^k sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_and_location_low_battery_mode_multiple_user_turn_alt::vague_observation / cot

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon -> get_current_timestamp -> add_reminder
- Success@1 sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon
- Pass^k sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon -> get_current_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_and_location_low_battery_mode_multiple_user_turn_alt::vague_observation / react

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon -> get_current_timestamp -> add_reminder
- Success@1 sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon
- Pass^k sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon -> search_location_around_lat_lon -> add_reminder

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_and_location_low_battery_mode_multiple_user_turn_alt::vague_observation / self_refine

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon -> get_current_timestamp -> add_reminder
- Success@1 sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon
- Pass^k sequence: set_low_battery_mode_status -> set_wifi_status -> search_location_around_lat_lon -> get_current_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_and_location_multiple_user_turn_alt::misleading_observation / direct

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_location_around_lat_lon -> get_current_timestamp -> add_reminder
- Success@1 sequence: search_location_around_lat_lon
- Pass^k sequence: search_location_around_lat_lon

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_and_location_multiple_user_turn_alt::misleading_observation / cot

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_location_around_lat_lon -> get_current_timestamp -> add_reminder
- Success@1 sequence: search_location_around_lat_lon
- Pass^k sequence: search_location_around_lat_lon -> get_current_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_and_location_multiple_user_turn_alt::misleading_observation / react

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_location_around_lat_lon -> get_current_timestamp -> add_reminder
- Success@1 sequence: search_location_around_lat_lon
- Pass^k sequence: search_location_around_lat_lon -> search_location_around_lat_lon -> add_reminder

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_and_location_multiple_user_turn_alt::misleading_observation / self_refine

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_location_around_lat_lon -> get_current_timestamp -> add_reminder
- Success@1 sequence: search_location_around_lat_lon
- Pass^k sequence: search_location_around_lat_lon -> get_current_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_date_and_time_alt_all_tools::stale_state / direct

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Success@1 sequence: datetime_info_to_timestamp -> add_reminder
- Pass^k sequence: datetime_info_to_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_date_and_time_alt_all_tools::stale_state / cot

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Success@1 sequence: datetime_info_to_timestamp -> add_reminder
- Pass^k sequence: datetime_info_to_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_date_and_time_alt_all_tools::stale_state / react

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Success@1 sequence: datetime_info_to_timestamp -> add_reminder
- Pass^k sequence: datetime_info_to_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_date_and_time_alt_all_tools::stale_state / self_refine

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Success@1 sequence: datetime_info_to_timestamp -> add_reminder
- Pass^k sequence: datetime_info_to_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_weekday_delta_and_time_alt_10_distraction_tools::timeout / direct

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_weekday_delta_and_time_alt_10_distraction_tools::timeout / cot

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_weekday_delta_and_time_alt_10_distraction_tools::timeout / react

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_weekday_delta_and_time_alt_10_distraction_tools::timeout / self_refine

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp

### toolsandbox_policy::find_days_till_holiday::schema_drift / direct

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp

### toolsandbox_policy::find_days_till_holiday::schema_drift / cot

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation

### toolsandbox_policy::find_days_till_holiday::schema_drift / react

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation

### toolsandbox_policy::find_days_till_holiday::schema_drift / self_refine

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation

### toolsandbox_policy::convert_currency_canonicalize::vague_observation / direct

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: convert_currency
- Success@1 sequence: convert_currency
- Pass^k sequence: convert_currency

### toolsandbox_policy::convert_currency_canonicalize::vague_observation / cot

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: convert_currency
- Success@1 sequence: convert_currency
- Pass^k sequence: convert_currency

### toolsandbox_policy::convert_currency_canonicalize::vague_observation / react

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 1
- State corrupted: False
- Clean sequence: convert_currency
- Success@1 sequence: convert_currency
- Pass^k sequence: convert_currency -> convert_currency

### toolsandbox_policy::convert_currency_canonicalize::vague_observation / self_refine

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: convert_currency
- Success@1 sequence: convert_currency
- Pass^k sequence: convert_currency

### toolsandbox_policy::convert_currency::misleading_observation / direct

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: convert_currency
- Success@1 sequence: convert_currency
- Pass^k sequence: convert_currency

### toolsandbox_policy::convert_currency::misleading_observation / cot

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: convert_currency
- Success@1 sequence: convert_currency
- Pass^k sequence: convert_currency

### toolsandbox_policy::convert_currency::misleading_observation / react

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 1
- State corrupted: False
- Clean sequence: convert_currency
- Success@1 sequence: convert_currency
- Pass^k sequence: convert_currency -> convert_currency

### toolsandbox_policy::convert_currency::misleading_observation / self_refine

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: convert_currency
- Success@1 sequence: convert_currency
- Pass^k sequence: convert_currency

### toolsandbox_policy::find_days_till_holiday_alt::stale_state / direct

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Success@1 sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Pass^k sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation

### toolsandbox_policy::find_days_till_holiday_alt::stale_state / cot

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Success@1 sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Pass^k sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation

### toolsandbox_policy::find_days_till_holiday_alt::stale_state / react

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Success@1 sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Pass^k sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation

### toolsandbox_policy::find_days_till_holiday_alt::stale_state / self_refine

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Success@1 sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation
- Pass^k sequence: get_current_timestamp -> search_holiday -> search_holiday -> timestamp_diff -> end_conversation -> end_conversation

### toolsandbox_policy::find_address_with_lat_lon::timeout / direct

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_lat_lon -> end_conversation
- Success@1 sequence: search_lat_lon
- Pass^k sequence: search_lat_lon

### toolsandbox_policy::find_address_with_lat_lon::timeout / cot

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_lat_lon -> end_conversation
- Success@1 sequence: search_lat_lon
- Pass^k sequence: search_lat_lon -> search_lat_lon

### toolsandbox_policy::find_address_with_lat_lon::timeout / react

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_lat_lon -> end_conversation
- Success@1 sequence: search_lat_lon
- Pass^k sequence: search_lat_lon -> search_lat_lon

### toolsandbox_policy::find_address_with_lat_lon::timeout / self_refine

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_lat_lon -> end_conversation
- Success@1 sequence: search_lat_lon
- Pass^k sequence: search_lat_lon -> search_lat_lon

### toolsandbox_policy::find_thanksgiving_timestamp::schema_drift / direct

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_holiday
- Success@1 sequence: search_holiday
- Pass^k sequence: search_holiday

### toolsandbox_policy::find_thanksgiving_timestamp::schema_drift / cot

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_holiday
- Success@1 sequence: search_holiday
- Pass^k sequence: search_holiday -> search_holiday

### toolsandbox_policy::find_thanksgiving_timestamp::schema_drift / react

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_holiday
- Success@1 sequence: search_holiday
- Pass^k sequence: search_holiday -> search_holiday

### toolsandbox_policy::find_thanksgiving_timestamp::schema_drift / self_refine

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 1
- State corrupted: False
- Clean sequence: search_holiday
- Success@1 sequence: search_holiday
- Pass^k sequence: search_holiday -> search_holiday

### toolsandbox_policy::find_stock_symbol_with_company_name::vague_observation / direct

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_stock -> end_conversation
- Success@1 sequence: search_stock
- Pass^k sequence: search_stock

### toolsandbox_policy::find_stock_symbol_with_company_name::vague_observation / cot

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_stock -> end_conversation
- Success@1 sequence: search_stock
- Pass^k sequence: search_stock -> end_conversation

### toolsandbox_policy::find_stock_symbol_with_company_name::vague_observation / react

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_stock -> end_conversation
- Success@1 sequence: search_stock
- Pass^k sequence: search_stock -> search_stock

### toolsandbox_policy::find_stock_symbol_with_company_name::vague_observation / self_refine

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_stock -> end_conversation
- Success@1 sequence: search_stock
- Pass^k sequence: search_stock -> end_conversation

### toolsandbox_policy::find_temperature::misleading_observation / direct

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_weather_around_lat_lon -> end_conversation
- Success@1 sequence: search_weather_around_lat_lon
- Pass^k sequence: search_weather_around_lat_lon

### toolsandbox_policy::find_temperature::misleading_observation / cot

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_weather_around_lat_lon -> end_conversation
- Success@1 sequence: search_weather_around_lat_lon
- Pass^k sequence: search_weather_around_lat_lon -> end_conversation

### toolsandbox_policy::find_temperature::misleading_observation / react

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_weather_around_lat_lon -> end_conversation
- Success@1 sequence: search_weather_around_lat_lon
- Pass^k sequence: search_weather_around_lat_lon -> search_weather_around_lat_lon

### toolsandbox_policy::find_temperature::misleading_observation / self_refine

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_weather_around_lat_lon -> end_conversation
- Success@1 sequence: search_weather_around_lat_lon
- Pass^k sequence: search_weather_around_lat_lon -> end_conversation

### toolsandbox_policy::search_message_with_recency_latest_multiple_user_turn::stale_state / direct

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages -> end_conversation -> end_conversation
- Pass^k sequence: search_messages -> end_conversation -> end_conversation

### toolsandbox_policy::search_message_with_recency_latest_multiple_user_turn::stale_state / cot

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages -> end_conversation -> end_conversation
- Pass^k sequence: search_messages -> end_conversation -> end_conversation

### toolsandbox_policy::search_message_with_recency_latest_multiple_user_turn::stale_state / react

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages -> end_conversation -> end_conversation
- Pass^k sequence: search_messages -> end_conversation -> end_conversation

### toolsandbox_policy::search_message_with_recency_latest_multiple_user_turn::stale_state / self_refine

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages -> end_conversation -> end_conversation
- Pass^k sequence: search_messages -> end_conversation -> end_conversation

### toolsandbox_policy::search_message_with_recency_latest_multiple_user_turn_alt::timeout / direct

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages

### toolsandbox_policy::search_message_with_recency_latest_multiple_user_turn_alt::timeout / cot

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages -> end_conversation

### toolsandbox_policy::search_message_with_recency_latest_multiple_user_turn_alt::timeout / react

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages -> end_conversation

### toolsandbox_policy::search_message_with_recency_latest_multiple_user_turn_alt::timeout / self_refine

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages -> end_conversation

### toolsandbox_policy::search_message_with_recency_latest_alt::schema_drift / direct

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages

### toolsandbox_policy::search_message_with_recency_latest_alt::schema_drift / cot

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages -> end_conversation

### toolsandbox_policy::search_message_with_recency_latest_alt::schema_drift / react

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages -> end_conversation

### toolsandbox_policy::search_message_with_recency_latest_alt::schema_drift / self_refine

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages -> end_conversation

### toolsandbox_policy::search_message_with_recency_latest::vague_observation / direct

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages

### toolsandbox_policy::search_message_with_recency_latest::vague_observation / cot

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> end_conversation -> end_conversation

### toolsandbox_policy::search_message_with_recency_latest::vague_observation / react

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages -> end_conversation

### toolsandbox_policy::search_message_with_recency_latest::vague_observation / self_refine

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> end_conversation -> end_conversation

### toolsandbox_policy::search_message_with_recency_oldest::misleading_observation / direct

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp

### toolsandbox_policy::search_message_with_recency_oldest::misleading_observation / cot

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation

### toolsandbox_policy::search_message_with_recency_oldest::misleading_observation / react

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp -> end_conversation -> end_conversation

### toolsandbox_policy::search_message_with_recency_oldest::misleading_observation / self_refine

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation

### toolsandbox_policy::search_message_with_recency_oldest_alt::stale_state / direct

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation
- Success@1 sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation
- Pass^k sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation

### toolsandbox_policy::search_message_with_recency_oldest_alt::stale_state / cot

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation
- Success@1 sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation
- Pass^k sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation

### toolsandbox_policy::search_message_with_recency_oldest_alt::stale_state / react

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation
- Success@1 sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation
- Pass^k sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation

### toolsandbox_policy::search_message_with_recency_oldest_alt::stale_state / self_refine

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation
- Success@1 sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation
- Pass^k sequence: get_current_timestamp -> search_messages -> end_conversation -> end_conversation

### toolsandbox_policy::search_sender_phone_number_with_content::timeout / direct

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages

### toolsandbox_policy::search_sender_phone_number_with_content::timeout / cot

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages

### toolsandbox_policy::search_sender_phone_number_with_content::timeout / react

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages

### toolsandbox_policy::search_sender_phone_number_with_content::timeout / self_refine

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages

### toolsandbox_policy::search_message_with_recency_latest_multiple_user_turn_3_distraction_tools::schema_drift / direct

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages

### toolsandbox_policy::search_message_with_recency_latest_multiple_user_turn_3_distraction_tools::schema_drift / cot

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages -> end_conversation

### toolsandbox_policy::search_message_with_recency_latest_multiple_user_turn_3_distraction_tools::schema_drift / react

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages -> end_conversation

### toolsandbox_policy::search_message_with_recency_latest_multiple_user_turn_3_distraction_tools::schema_drift / self_refine

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_messages -> end_conversation -> end_conversation
- Success@1 sequence: search_messages
- Pass^k sequence: search_messages -> search_messages -> end_conversation

### toolsandbox_policy::add_reminder_content_and_date_and_time_multiple_user_turn_alt::vague_observation / direct

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Success@1 sequence: datetime_info_to_timestamp
- Pass^k sequence: datetime_info_to_timestamp

### toolsandbox_policy::add_reminder_content_and_date_and_time_multiple_user_turn_alt::vague_observation / cot

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Success@1 sequence: datetime_info_to_timestamp
- Pass^k sequence: datetime_info_to_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_date_and_time_multiple_user_turn_alt::vague_observation / react

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Success@1 sequence: datetime_info_to_timestamp
- Pass^k sequence: datetime_info_to_timestamp -> datetime_info_to_timestamp

### toolsandbox_policy::add_reminder_content_and_date_and_time_multiple_user_turn_alt::vague_observation / self_refine

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Success@1 sequence: datetime_info_to_timestamp
- Pass^k sequence: datetime_info_to_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_multiple_user_turn_alt::misleading_observation / direct

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_multiple_user_turn_alt::misleading_observation / cot

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_multiple_user_turn_alt::misleading_observation / react

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_multiple_user_turn_alt::misleading_observation / self_refine

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_weekday_delta_and_time_multiple_user_turn_alt::stale_state / direct

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp -> add_reminder
- Pass^k sequence: get_current_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_weekday_delta_and_time_multiple_user_turn_alt::stale_state / cot

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp -> add_reminder
- Pass^k sequence: get_current_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_weekday_delta_and_time_multiple_user_turn_alt::stale_state / react

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp -> add_reminder
- Pass^k sequence: get_current_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_weekday_delta_and_time_multiple_user_turn_alt::stale_state / self_refine

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp -> add_reminder
- Pass^k sequence: get_current_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_date_and_time_alt::timeout / direct

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Success@1 sequence: datetime_info_to_timestamp
- Pass^k sequence: datetime_info_to_timestamp

### toolsandbox_policy::add_reminder_content_and_date_and_time_alt::timeout / cot

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Success@1 sequence: datetime_info_to_timestamp
- Pass^k sequence: datetime_info_to_timestamp -> datetime_info_to_timestamp

### toolsandbox_policy::add_reminder_content_and_date_and_time_alt::timeout / react

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Success@1 sequence: datetime_info_to_timestamp
- Pass^k sequence: datetime_info_to_timestamp -> datetime_info_to_timestamp

### toolsandbox_policy::add_reminder_content_and_date_and_time_alt::timeout / self_refine

- Noise type: timeout
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: datetime_info_to_timestamp -> add_reminder
- Success@1 sequence: datetime_info_to_timestamp
- Pass^k sequence: datetime_info_to_timestamp -> datetime_info_to_timestamp

### toolsandbox_policy::add_reminder_content_and_weekday_delta_and_time_alt::schema_drift / direct

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_weekday_delta_and_time_alt::schema_drift / cot

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_weekday_delta_and_time_alt::schema_drift / react

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_weekday_delta_and_time_alt::schema_drift / self_refine

- Noise type: schema_drift
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_alt::vague_observation / direct

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_alt::vague_observation / cot

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> add_reminder

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_alt::vague_observation / react

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> get_current_timestamp

### toolsandbox_policy::add_reminder_content_and_week_delta_and_time_alt::vague_observation / self_refine

- Noise type: vague_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: get_current_timestamp -> add_reminder
- Success@1 sequence: get_current_timestamp
- Pass^k sequence: get_current_timestamp -> add_reminder

### toolsandbox_policy::remove_reminder_with_recency_latest_alt::misleading_observation / direct

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_reminder -> get_current_timestamp -> remove_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder

### toolsandbox_policy::remove_reminder_with_recency_latest_alt::misleading_observation / cot

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_reminder -> get_current_timestamp -> remove_reminder -> remove_reminder -> remove_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> get_current_timestamp -> remove_reminder -> remove_reminder -> remove_reminder

### toolsandbox_policy::remove_reminder_with_recency_latest_alt::misleading_observation / react

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: False
- Recovery detected: False
- Cost increase: 0
- State corrupted: True
- Clean sequence: search_reminder -> get_current_timestamp -> remove_reminder -> remove_reminder -> remove_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> search_reminder -> remove_reminder -> remove_reminder -> remove_reminder

### toolsandbox_policy::remove_reminder_with_recency_latest_alt::misleading_observation / self_refine

- Noise type: misleading_observation
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: False
- Pass^k: True
- Recovery detected: True
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_reminder -> get_current_timestamp -> remove_reminder -> remove_reminder -> remove_reminder
- Success@1 sequence: search_reminder
- Pass^k sequence: search_reminder -> get_current_timestamp -> remove_reminder -> remove_reminder -> remove_reminder

### toolsandbox_policy::modify_reminder_with_recency_latest::stale_state / direct

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_reminder -> get_current_timestamp -> modify_reminder
- Success@1 sequence: search_reminder -> get_current_timestamp -> modify_reminder
- Pass^k sequence: search_reminder -> get_current_timestamp -> modify_reminder

### toolsandbox_policy::modify_reminder_with_recency_latest::stale_state / cot

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_reminder -> get_current_timestamp -> modify_reminder
- Success@1 sequence: search_reminder -> get_current_timestamp -> modify_reminder
- Pass^k sequence: search_reminder -> get_current_timestamp -> modify_reminder

### toolsandbox_policy::modify_reminder_with_recency_latest::stale_state / react

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_reminder -> get_current_timestamp -> modify_reminder
- Success@1 sequence: search_reminder -> get_current_timestamp -> modify_reminder
- Pass^k sequence: search_reminder -> get_current_timestamp -> modify_reminder

### toolsandbox_policy::modify_reminder_with_recency_latest::stale_state / self_refine

- Noise type: stale_state
- Source: toolsandbox_policy_subset
- Intensity: level_1
- Clean success: True
- Success@1: True
- Pass^k: True
- Recovery detected: False
- Cost increase: 0
- State corrupted: False
- Clean sequence: search_reminder -> get_current_timestamp -> modify_reminder
- Success@1 sequence: search_reminder -> get_current_timestamp -> modify_reminder
- Pass^k sequence: search_reminder -> get_current_timestamp -> modify_reminder
