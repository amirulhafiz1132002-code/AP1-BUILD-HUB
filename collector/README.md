# Public GitHub Metadata Collector

`github_metadata.py` is a read-only Python standard-library collector for public GitHub repository metadata.

## Scope

- Uses unauthenticated HTTPS `GET` requests to the GitHub REST API.
- Supports one-repository lookup and bounded public-repository listing for a user or organization.
- Normalizes a small allowlist of public metadata into candidate records.
- Labels candidates `AUTOMATED_DISCOVERY` / `DISCOVERED` for human review.

## Usage

Run from the repository root:

```bash
python collector/github_metadata.py repo OWNER REPOSITORY
python collector/github_metadata.py list OWNER --owner-type user --max-pages 2
python collector/github_metadata.py list ORGANIZATION --owner-type org --max-pages 2
```

Output is JSON on standard output. Errors are written to standard error and return exit code `2`.

## Safety boundary

- No token, credential, or authenticated session is accepted or required.
- Requests use `GET` only; the collector contains no GitHub write operation.
- Private repositories are rejected or excluded; output fields are explicitly allowlisted.
- Pagination is bounded (`max_pages` 1–100; 100 repositories per page).
- No registry file is read or written. Candidate output is not a registry registration or human approval.
- No workflow, webhook, scheduler, service, or external integration is configured.

GitHub's unauthenticated API rate limits apply. A rate-limit or network error is reported as a failure; it is not silently retried or labeled successful.

## Tests

```bash
python -m unittest discover -s tests -v
```

Tests use mocked HTTP responses and do not call GitHub.
