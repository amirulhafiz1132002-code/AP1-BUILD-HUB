"""Read-only collector for public GitHub repository metadata.

This module never authenticates, writes to GitHub, or changes the AP1 registry.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

DEFAULT_API_BASE = "https://api.github.com"
USER_AGENT = "AP1-BUILD-HUB-public-metadata-collector/0.1"
OWNER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")


class GitHubAPIError(RuntimeError):
    """Safe, concise error for failed GitHub API requests."""

    def __init__(self, message: str, status: int | None = None) -> None:
        super().__init__(message)
        self.status = status


class GitHubPublicMetadataCollector:
    """Fetch and normalize public repository metadata using unauthenticated GETs."""

    def __init__(
        self,
        api_base: str = DEFAULT_API_BASE,
        timeout: float = 10.0,
        opener: Callable[..., Any] | None = None,
    ) -> None:
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout
        self._opener = opener or urlopen

    def _get_json(self, path: str) -> Any:
        request = Request(
            f"{self.api_base}{path}",
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": USER_AGENT,
                "X-GitHub-Api-Version": "2022-11-28",
            },
            method="GET",
        )
        try:
            with self._opener(request, timeout=self.timeout) as response:
                status = getattr(response, "status", 200)
                if status < 200 or status >= 300:
                    raise GitHubAPIError(f"GitHub API returned HTTP {status}", status)
                raw = response.read()
        except HTTPError as exc:
            raise GitHubAPIError(f"GitHub API returned HTTP {exc.code}", exc.code) from None
        except URLError as exc:
            raise GitHubAPIError(f"GitHub API network error: {exc.reason}") from None
        except TimeoutError:
            raise GitHubAPIError("GitHub API request timed out") from None

        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise GitHubAPIError("GitHub API returned invalid JSON") from None

    @staticmethod
    def _validate_owner(owner: str) -> str:
        if not isinstance(owner, str) or not OWNER_RE.fullmatch(owner):
            raise ValueError("owner must be a valid GitHub account or organization name")
        return owner

    @staticmethod
    def _validate_repo(repo: str) -> str:
        if not isinstance(repo, str) or not REPO_RE.fullmatch(repo) or repo in {".", ".."}:
            raise ValueError("repo must be a valid GitHub repository name")
        return repo

    @staticmethod
    def _normalize_repository(payload: dict[str, Any], observed_at: str) -> dict[str, Any]:
        if payload.get("private") is True:
            raise GitHubAPIError("Refusing to collect a private repository", 403)

        required = ("id", "full_name", "html_url", "default_branch")
        if any(payload.get(key) in (None, "") for key in required):
            raise GitHubAPIError("GitHub response is missing required public repository metadata")

        full_name = payload["full_name"]
        if not isinstance(full_name, str) or full_name.count("/") != 1:
            raise GitHubAPIError("GitHub response contains an invalid repository identity")

        visibility = payload.get("visibility")
        if visibility not in {"public", None}:
            raise GitHubAPIError("Refusing to collect a repository that is not public")
        if visibility is None and payload.get("private") is not False:
            raise GitHubAPIError("Repository visibility could not be confirmed as public")

        # Deliberate allowlist: never copy arbitrary API fields into collector output.
        metadata: dict[str, Any] = {
            "repository_id": str(payload["id"]),
            "full_name": full_name,
            "url": payload["html_url"],
            "default_branch": payload["default_branch"],
            "visibility": "public",
            "archived": bool(payload.get("archived", False)),
        }
        for source, target in (
            ("description", "description"),
            ("created_at", "created_at"),
            ("updated_at", "updated_at"),
            ("pushed_at", "pushed_at"),
            ("language", "primary_language"),
            ("stargazers_count", "stars"),
            ("forks_count", "forks"),
            ("open_issues_count", "open_issues"),
        ):
            value = payload.get(source)
            if value is not None:
                metadata[target] = value

        return {
            "project_id": f"github:{full_name}",
            "registration_source": "AUTOMATED_DISCOVERY",
            "status": "DISCOVERED",
            "observed_at": observed_at,
            "github": metadata,
        }

    def get_public_repository(self, owner: str, repo: str) -> dict[str, Any]:
        """Fetch one repository; only explicitly public metadata is returned."""
        owner = self._validate_owner(owner)
        repo = self._validate_repo(repo)
        payload = self._get_json(f"/repos/{quote(owner, safe='')}/{quote(repo, safe='')}")
        if not isinstance(payload, dict):
            raise GitHubAPIError("GitHub API returned an unexpected repository payload")
        observed_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        return self._normalize_repository(payload, observed_at)

    def list_public_repositories(
        self, owner: str, owner_type: str = "user", max_pages: int = 10
    ) -> list[dict[str, Any]]:
        """List public repositories for a user or organization, with bounded pagination."""
        owner = self._validate_owner(owner)
        if owner_type not in {"user", "org"}:
            raise ValueError("owner_type must be 'user' or 'org'")
        if not isinstance(max_pages, int) or isinstance(max_pages, bool) or not 1 <= max_pages <= 100:
            raise ValueError("max_pages must be an integer from 1 to 100")

        endpoint = "users" if owner_type == "user" else "orgs"
        results: list[dict[str, Any]] = []
        observed_at = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        for page in range(1, max_pages + 1):
            query = urlencode({"type": "public", "sort": "updated", "per_page": 100, "page": page})
            payload = self._get_json(f"/{endpoint}/{quote(owner, safe='')}/repos?{query}")
            if not isinstance(payload, list):
                raise GitHubAPIError("GitHub API returned an unexpected repository-list payload")
            for item in payload:
                if not isinstance(item, dict):
                    raise GitHubAPIError("GitHub API returned an invalid repository item")
                if item.get("private") is True:
                    continue
                results.append(self._normalize_repository(item, observed_at))
            if len(payload) < 100:
                break
        return results


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Read-only public GitHub repository metadata collector")
    subparsers = parser.add_subparsers(dest="command", required=True)
    one = subparsers.add_parser("repo", help="collect one public repository")
    one.add_argument("owner")
    one.add_argument("repo")
    listing = subparsers.add_parser("list", help="list public repositories for an owner")
    listing.add_argument("owner")
    listing.add_argument("--owner-type", choices=("user", "org"), default="user")
    listing.add_argument("--max-pages", type=int, default=10)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    collector = GitHubPublicMetadataCollector()
    try:
        if args.command == "repo":
            result: Any = collector.get_public_repository(args.owner, args.repo)
        else:
            result = {
                "owner": args.owner,
                "owner_type": args.owner_type,
                "registration_source": "AUTOMATED_DISCOVERY",
                "status": "DISCOVERED",
                "repositories": collector.list_public_repositories(
                    args.owner, args.owner_type, args.max_pages
                ),
            }
        json.dump(result, sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    except (GitHubAPIError, ValueError) as exc:
        print(f"collector error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
