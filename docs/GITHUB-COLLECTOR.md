# BUILD 02.2 — GitHub Public Metadata Collector

## 1. Objective

Provide a bounded, read-only mechanism to observe public GitHub repository metadata and emit candidate records for later human review. The collector is an observation tool, not an authority or registry writer.

## 2. Data flow

1. A caller supplies one repository identity or an owner (user or organization).
2. The collector issues unauthenticated GitHub REST API \`GET\` requests over HTTPS.
3. The response is checked for public visibility and required identity fields.
4. A strict field allowlist is normalized into JSON candidate output.
5. A human may inspect the output and decide separately whether to register a project.

Candidate records use \`registration_source: AUTOMATED_DISCOVERY\` and \`status: DISCOVERED\`. \`observed_at\` records when the collector saw the metadata; it is not a registry \`registered_at\` timestamp.

## 3. Public data boundary

The collector records repository identity and selected public metadata: repository ID, full name, canonical URL, default branch, public visibility, archive state, and available description/activity/language/count fields. Arbitrary API response fields, permissions, owner profile details, credentials, and private content are not copied.

The collector rejects a single-repository response marked private or internal and excludes private items from a listing. It does not request repository contents, issues, pull requests, workflow data, secrets, or user contact information.

## 4. Read-only and authorization boundary

- HTTP method: \`GET\` only.
- Authentication: none; no token parameter or credential store.
- GitHub mutations: none.
- Registry mutations: none; \`registry/projects.json\` is neither loaded nor changed.
- Approval: none; discovered candidates remain \`DISCOVERED\`.
- External automation: no workflow, webhook, scheduler, service, or deployment is installed.

Discovery is not authorization. A candidate name or owner match is not proof that a repository is an official AP1 project.

## 5. Pagination and failure behavior

Repository listings request public repositories in pages of up to 100. \`max_pages\` is bounded from 1 to 100 to prevent unbounded collection. Network, timeout, HTTP, rate-limit, malformed JSON, and incomplete identity failures are surfaced as errors. The collector does not silently retry or convert failures into successful/empty results.

The GitHub unauthenticated rate limit applies. A caller should treat rate-limit responses as \`PENDING\` or \`UNKNOWN\` operationally until a fresh read succeeds; no such status is written automatically by this code.

## 6. Verification

Offline unit tests use mocked responses and verify GET-only behavior, no authorization header, public-only filtering, field allowlisting, input validation, pagination, and user/organization endpoint selection. Tests do not call GitHub and do not validate the live GitHub service.

## 7. Explicit non-goals

No registry synchronization, project approval/rejection, source repository changes, GitHub Actions workflow, webhook, scheduled job, API credential, dashboard, or deployment is part of BUILD 02.2.
