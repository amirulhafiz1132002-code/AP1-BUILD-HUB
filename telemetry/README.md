# AP1 Telemetry

This directory documents the telemetry contract and evidence rules. It does not yet contain a live collector or automated event pipeline.

## Event format

Use the JSON Schema at `schemas/build-event.schema.json` for each build, test, audit, integration, deployment, synchronization, or release event.

## Evidence rules

- Prefer immutable references such as commit SHAs and workflow-run URLs.
- Record timestamps in ISO 8601 format with an explicit timezone.
- Report the actual outcome; do not infer success from a started process.
- Use `UNKNOWN` when evidence is unavailable.
- Keep credentials, tokens, private logs, and unnecessary personal data out of telemetry.
- Do not store large build artifacts in this repository; link to an access-controlled artifact location when appropriate.

## Current implementation state

Foundation documentation and schema only. No telemetry ingestion endpoint, scheduler, webhook, GitHub Actions workflow, or external data synchronization is active.
