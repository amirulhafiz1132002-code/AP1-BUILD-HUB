# AP1 Repository Registry Model

## 1. Objective

Define a hybrid, review-controlled inventory for GitHub repositories associated with the AP1 ecosystem. The registry is an index and governance record; it does not replace the source repository or grant access to it.

## 2. Hybrid intake

### Manual registration

An authorized human may submit a repository candidate. The entry must include its canonical GitHub identity and the available metadata. A manual submission is not automatically approved.

### Automated discovery

A future discovery component may enumerate repositories visible to its explicitly authorized GitHub identity and submit candidates for review. Discovery must be read-only.

Discovery must not:
- create, edit, archive, transfer, or delete repositories;
- change branches, settings, permissions, issues, or workflows;
- create commits, pull requests, releases, or deployments;
- infer that a repository is an official AP1 project from its name alone;
- approve or reject candidates.

Automated discovery is not enabled by this document.

## 3. Identity and deduplication

- Use the immutable GitHub repository ID as the primary external identity.
- Keep `owner/name` as the human-readable locator; it can change after a rename or transfer.
- Use `project_id` in the form `github:owner/name` as the registry-facing identifier.
- Before adding a candidate, compare repository ID and normalized full name against existing entries.
- If identifiers conflict or ownership is unclear, mark the candidate for human review; do not silently merge records.

## 4. Lifecycle

| Status | Meaning |
|---|---|
| `DISCOVERED` | Observed as a candidate; not yet reviewed |
| `PENDING_REVIEW` | Submitted for human decision |
| `APPROVED` | Explicit human approval is recorded |
| `REJECTED` | Human review declined the candidate |
| `ARCHIVED` | Retained for history but no longer active in the registry |

Only `APPROVED` entries may be presented as approved AP1 projects. A status change to `APPROVED` or `REJECTED` requires an approval record containing the decision, reviewer identifier, and timestamp.

## 5. Minimum metadata

Each project record contains:
- registry project identifier;
- GitHub repository ID, full name, and URL;
- registration source;
- lifecycle status;
- registration timestamp.

Default branch, visibility, archive state, discovery timestamp, last verification timestamp, and evidence references may be recorded when available. Unknown values must be omitted or explicitly represented as unknown where the schema permits; never guess them.

## 6. Evidence and freshness

- Prefer direct GitHub repository metadata and canonical browser URLs.
- Record the time a metadata snapshot was observed.
- A previously verified value is not proof that the value remains current.
- Preserve evidence references for consequential review decisions.
- If GitHub cannot be reached or a field cannot be confirmed, report the relevant state as unknown or pending rather than successful.

## 7. Security and privacy

- Use least-privilege GitHub access for any future discovery integration.
- Keep tokens and credentials in platform-managed secret storage, never in registry files.
- Do not collect personal contact details, private user data, or unrelated repository content.
- Private repository metadata must only be accessed where the connected identity is authorized and the collection purpose is documented.
- Do not expose private repository names or metadata in public outputs.

## 8. Change control

Registry writes require an authorized action. Automated discovery may propose candidates, but human approval remains the authority for official project membership. Changes to repository settings or source code are outside this registry's authority and require separate approval.

## 9. Implementation boundary

BUILD 02.1 establishes the file structure, schema, and governance model only. It does not implement a collector, API client, scheduler, webhook, dashboard, CI workflow, or synchronization process. Those components require separate design, permission review, implementation, and verification.
