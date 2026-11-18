# AP1-BUILD-HUB Operating Model

## 1. Purpose

AP1-BUILD-HUB is the coordination and evidence-documentation layer for AP1 development activity. It is not automatically a deployment platform, credential store, or source-of-truth replacement for individual project repositories.

## 2. Governance

- Human intention and explicit authorization govern consequential changes.
- Audits are read-only unless a change is explicitly approved.
- Every status must be supported by evidence or labeled unknown.
- Project repositories retain ownership of their source code and release state.
- Contributions and external integrations remain review-first.

## 3. Workflow

1. **AUDIT** — inspect repository, branch, workflow, and project state.
2. **PRIORITIZE** — select a scoped task and define acceptance evidence.
3. **EXECUTE** — make only approved changes within the agreed boundary.
4. **VERIFY** — inspect resulting files, commits, tests, and external state.

## 4. Status vocabulary

- `VERIFIED`: directly supported by current, inspectable evidence.
- `FAILED`: a check ran and its result was unsuccessful.
- `PENDING`: work or verification has not completed.
- `UNKNOWN`: insufficient evidence is available.
- `NOT_APPLICABLE`: the check does not apply, with a recorded reason.

Do not use `VERIFIED` for an unexecuted test or an assumed integration.

## 5. Telemetry contract

Build events must follow `schemas/build-event.schema.json`. Each event should identify its project, event type, timestamp, outcome, source reference, and evidence references where available. Do not place secrets or unnecessary personal data in events.

## 6. Integration boundaries

Any future GitHub API, webhook, CI, or external service integration must document:
- required permissions and least-privilege scope;
- data collected and retention expectations;
- secret storage boundary;
- failure behavior and retry policy;
- verification method and rollback or disable procedure.

No such integration is enabled by this foundation commit.

## 7. Change control

Before modifying an existing project or connecting a service, inspect its current state, propose the exact scope and files, and obtain explicit approval. Verify the resulting state after execution.
