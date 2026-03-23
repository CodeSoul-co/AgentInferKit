# Stateful Tool Environment Change Summary

## Background

This document summarizes the architectural changes made to AgentInferKit while extending the original stateless mock tool layer into a stateful, reproducible tool environment.

The goal of this round of work was not to add more standalone tools, but to upgrade the tool execution substrate so that the project can support:

- shared world state
- explicit state transitions
- delayed side effects
- environment-aware execution
- domain-level evaluation
- backend abstraction for future migration

---

## Scope of Work

The changes completed so far cover four major areas:

1. Phase 1: stateful core abstraction
2. Phase 1 second pass: coverage and evaluator integration
3. Phase 2: environment layer and side-effect scheduling
4. Phase 2.5: calendar domain
5. Phase 3: backend abstraction and runner integration

---

## 1. Stateful Core Abstraction

The original minimal stateful prototype in `src/toolsim/` was upgraded into a more formal execution core.

### Main changes

#### `src/toolsim/tool_spec.py`

Added richer tool abstraction primitives:

- `ToolMetadata`
- `PreconditionSpec`
- `PostconditionSpec`
- `ConditionCheckResult`
- `ExecutionContext`
- richer `ToolExecutionResult`

This allows tools to declare:

- version and domain metadata
- required permissions
- idempotency semantics
- preconditions and postconditions
- partial/pending execution states

The implementation remains backward compatible with older tools that still use the simpler `execute(state, args)` pattern.

#### `src/toolsim/world_state.py`

Expanded `WorldState` into a stronger execution substrate.

Added support for:

- named snapshots
- rollback
- explicit clock helpers
- pending effects
- basic policy checks
- effect lifecycle fields (`status`, retry info, source tool)

This preserves the existing in-memory state model while making it suitable for more realistic environment behavior.

#### `src/toolsim/stateful_executor.py`

Upgraded the executor from simple tool dispatch into a structured execution controller.

Added support for:

- permission checks
- declarative precondition/postcondition checks
- structured `ExecutionRecord`
- duration and timeout metadata
- pending/partial status propagation
- scheduled/applied effect tracking
- backend identity in execution records

#### `src/toolsim/stateful_tracer.py`

Improved tracer support with:

- filtering by tool and status
- summary statistics
- export of richer execution records

---

## 2. Coverage and Evaluator Integration

After the first abstraction pass, focused tests and evaluator support were added so that the new stateful-core fields are not just stored, but also verified and consumed.

### Main changes

#### Expanded tests

Added or updated focused coverage for:

- permission failures
- precondition failures
- named snapshots and rollback
- pending effects
- partial/pending execution records
- tracer summaries and filters

Relevant test files include:

- `tests/test_stateful_executor.py`
- `tests/test_stateful_tracer.py`
- `tests/test_world_state.py`
- `tests/test_evaluator.py`

#### `src/toolsim/evaluator.py`

Extended call-level evaluation to surface new execution signals:

- `partial_calls`
- `pending_calls`
- `invalid_calls`

This keeps the evaluator aligned with the richer Phase 1 execution record format.

---

## 3. Environment Layer and Side-Effect Scheduling

A dedicated environment layer was added so that tool execution can happen inside a scheduler-aware runtime instead of directly operating on state alone.

### Main changes

#### `src/toolsim/side_effects.py`

Added:

- `EffectApplicationResult`
- `SideEffectScheduler`
- default handler registration

The first built-in delayed side effect is:

- `search.reindex_file_snapshot`

#### `src/toolsim/environment.py`

Added `ToolEnvironment`, which now manages:

- world state
- backend
- side-effect scheduler
- automatic time advancement
- ready-effect application
- snapshot/rollback delegation through backend

This environment is now the standard container for executing stateful tools.

#### `src/toolsim/file_tools.py`

`file.write` was extended with an opt-in delayed side effect path:

- `schedule_search_reindex=True`
- `reindex_delay=<float>`

This preserves the old demo behavior by default, but enables delayed indexing experiments when needed.

#### `src/toolsim/search_tools.py`

Search tools were updated to align with delayed reindex semantics while keeping explicit indexing behavior intact.

#### `src/toolsim/experiment_runner.py`

The experiment runner now supports:

- explicit `ToolEnvironment`
- time advancement inside `tool_calls`
- reuse of a single environment over a whole run

This means delayed effects can now be tested through the experiment entry point, not just by directly calling the executor.

---

## 4. Calendar Domain

A new calendar domain was implemented as the first domain that meaningfully uses:

- shared state
- clock-aware policy
- conflict detection
- stateful evaluation

### Main changes

#### `src/toolsim/calendar_tools.py`

Added four tools:

- `calendar.create_event`
- `calendar.search_events`
- `calendar.update_event`
- `calendar.delete_event`

### Calendar behavior supported

- event creation with time validation
- participant-level overlap conflict detection
- update-time conflict checks
- soft delete via `status="cancelled"`
- policy-based restriction on deleting already-started events
- use of `WorldState.clock` for time-sensitive behavior

### Registration

Calendar tools were added to the default tool registry in:

- `src/toolsim/stateful_executor.py`

### Tests

Calendar coverage was added in:

- `tests/test_calendar_tools.py`

This includes CRUD, conflict detection, and time-aware deletion policy behavior.

---

## 5. Calendar Evaluation Loop

The state-level evaluator was extended so the calendar domain can be evaluated directly.

### Added goal types in `src/toolsim/evaluator.py`

- `event_exists`
- `event_field_equals`
- `event_status_is`
- `search_hits_event`

This allows calendar tasks to be evaluated through the same evaluator layer used by the other tool domains.

---

## 6. Backend Abstraction

A new backend layer was introduced so that the tool environment is no longer tied to a single in-memory state carrier.

### New directory

- `src/toolsim/backends/`

### New files

#### `src/toolsim/backends/base.py`

Defines `BaseBackend` and the minimal backend seam for:

- state creation
- cloning
- snapshots
- rollback
- entity CRUD
- pending effect management

#### `src/toolsim/backends/mock_backend.py`

Implements the default in-memory backend.

This backend preserves current behavior and acts as the compatibility baseline.

#### `src/toolsim/backends/sandbox_backend.py`

Implements a first sandbox-oriented backend with:

- explicit session identity
- isolated state creation
- sandbox metadata in state resources/policies

This is the first step toward more realistic and isolated backend execution.

### Backend integration

The backend layer is now threaded through:

- `ToolEnvironment`
- `ExecutionContext`
- `StatefulExecutor`
- `ExperimentRunner`

`StatefulExecutor` defaults to `MockBackend`, while `ExperimentRunner` can now explicitly run with a selected backend.

Execution records also expose `backend_name` so backend-aware experiments can be traced and compared.

### Tests

Backend coverage was added in:

- `tests/test_backends.py`
- `tests/test_experiment_runner.py`

This includes:

- mock backend CRUD/snapshot compatibility
- sandbox backend session isolation
- backend-aware environment snapshot/rollback
- calendar execution through sandbox backend
- runner-level backend selection

---

## Current Result

At this point, the project supports:

- a structured stateful execution core
- environment-aware delayed side effects
- two working stateful demo domains:
  - file-search
  - calendar
- state-level evaluation for both domains
- backend abstraction with mock and sandbox implementations
- backend-aware execution through the experiment runner

---

## What Has Not Been Done Yet

The following planned items are still pending:

- `issue-tracker` domain
- `LiveBackend`
- fault injection modules
- observation shaping modules
- full backend-specific persistence layer (for example SQLite-backed sandbox storage)
- frontend/web visualization updates for the new stateful concepts
- full integration of the new stateful environment into the existing `AgentRunner` / API-calling main path

---

## Suggested Next Step

The next natural step is to implement the `issue-tracker` domain on top of the now-stable backend-aware stateful environment.

That domain is a good fit for validating:

- multi-step state transitions
- role and permission rules
- backend portability
- richer evaluator goals

---

## Reference Files

Core implementation files:

- `src/toolsim/tool_spec.py`
- `src/toolsim/world_state.py`
- `src/toolsim/stateful_executor.py`
- `src/toolsim/stateful_tracer.py`
- `src/toolsim/environment.py`
- `src/toolsim/side_effects.py`
- `src/toolsim/evaluator.py`
- `src/toolsim/experiment_runner.py`
- `src/toolsim/calendar_tools.py`
- `src/toolsim/backends/base.py`
- `src/toolsim/backends/mock_backend.py`
- `src/toolsim/backends/sandbox_backend.py`

Main test files:

- `tests/test_stateful_executor.py`
- `tests/test_stateful_tracer.py`
- `tests/test_world_state.py`
- `tests/test_environment.py`
- `tests/test_calendar_tools.py`
- `tests/test_backends.py`
- `tests/test_experiment_runner.py`
- `tests/test_evaluator.py`
