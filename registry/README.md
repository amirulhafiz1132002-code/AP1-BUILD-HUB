# AP1 Repository Registry

The registry is the controlled inventory of GitHub repositories associated with the AP1 ecosystem.

## Purpose

- Keep repository identity and ownership references in one documented place.
- Distinguish a discovered repository from an approved AP1 project.
- Preserve a reviewable record of registration source and verification state.
- Provide a stable input contract for future read-only telemetry collectors.

## Files

- `projects.json` — registry data document; starts empty.
- `../schemas/project-registry.schema.json` — validation schema.
- `../docs/REGISTRY-MODEL.md` — lifecycle, review rules, and data boundaries.

## Registration sources

- `MANUAL` — entered by an authorized human.
- `AUTOMATED_DISCOVERY` — observed by a future read-only discovery process.

The source describes how a candidate entered the registry. It does not grant approval.

## Lifecycle

`DISCOVERED` → `PENDING_REVIEW` → `APPROVED` or `REJECTED`

An approved project may later become `ARCHIVED`. A discovered or manually submitted repository must not be treated as an official AP1 project until a human review is recorded.

## Data rules

- Use the GitHub repository ID as the stable identity when available.
- Keep the canonical `owner/name` and repository URL for navigation.
- Record timestamps as ISO 8601 date-time values with timezone information.
- Do not store credentials, tokens, private keys, session cookies, personal contact details, or private user data.
- Do not copy source code or project secrets into this registry.
- Keep repository-specific source-of-truth data in its owning repository.

## Current implementation state

The registry data file is intentionally empty. This phase defines the data contract and review process only. No repository discovery job, GitHub API collector, webhook, scheduled task, or automatic approval is active.
