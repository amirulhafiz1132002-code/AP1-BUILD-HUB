"""Offline tests for the public GitHub metadata collector."""
import json
import unittest
from urllib.parse import urlparse, parse_qs

from collector.github_metadata import GitHubAPIError, GitHubPublicMetadataCollector


def repository_payload(**overrides):
    payload = {
        "id": 12345,
        "name": "demo",
        "full_name": "sample-owner/demo",
        "html_url": "https://github.com/sample-owner/demo",
        "default_branch": "main",
        "visibility": "public",
        "private": False,
        "archived": False,
        "description": "Public demo repository",
        "created_at": "2025-01-01T00:00:00Z",
        "updated_at": "2025-02-01T00:00:00Z",
        "pushed_at": "2025-02-02T00:00:00Z",
        "language": "Python",
        "stargazers_count": 4,
        "forks_count": 2,
        "open_issues_count": 1,
        "permissions": {"admin": True},
        "owner": {"email": "must-not-leak@example.invalid"},
    }
    payload.update(overrides)
    return payload


class FakeResponse:
    status = 200

    def __init__(self, payload):
        self.body = json.dumps(payload).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self):
        return self.body


class FakeOpener:
    def __init__(self, payloads):
        self.payloads = list(payloads)
        self.requests = []

    def __call__(self, request, timeout):
        self.requests.append((request, timeout))
        if not self.payloads:
            raise AssertionError("Unexpected extra HTTP request")
        return FakeResponse(self.payloads.pop(0))


class CollectorTests(unittest.TestCase):
    def test_single_repository_normalizes_public_allowlist(self):
        opener = FakeOpener([repository_payload()])
        collector = GitHubPublicMetadataCollector(opener=opener)
        result = collector.get_public_repository("sample-owner", "demo")

        self.assertEqual(result["project_id"], "github:sample-owner/demo")
        self.assertEqual(result["registration_source"], "AUTOMATED_DISCOVERY")
        self.assertEqual(result["status"], "DISCOVERED")
        self.assertEqual(result["github"]["visibility"], "public")
        self.assertEqual(result["github"]["repository_id"], "12345")
        self.assertNotIn("permissions", result["github"])
        self.assertNotIn("owner", result["github"])
        request, timeout = opener.requests[0]
        self.assertEqual(request.get_method(), "GET")
        self.assertNotIn("Authorization", request.headers)
        self.assertEqual(timeout, 10.0)

    def test_private_repository_is_rejected(self):
        collector = GitHubPublicMetadataCollector(opener=FakeOpener([repository_payload(private=True)]))
        with self.assertRaises(GitHubAPIError):
            collector.get_public_repository("sample-owner", "demo")

    def test_internal_repository_is_rejected(self):
        payload = repository_payload(visibility="internal", private=False)
        collector = GitHubPublicMetadataCollector(opener=FakeOpener([payload]))
        with self.assertRaises(GitHubAPIError):
            collector.get_public_repository("sample-owner", "demo")

    def test_missing_required_metadata_is_rejected(self):
        payload = repository_payload()
        del payload["id"]
        collector = GitHubPublicMetadataCollector(opener=FakeOpener([payload]))
        with self.assertRaises(GitHubAPIError):
            collector.get_public_repository("sample-owner", "demo")

    def test_owner_and_repository_inputs_are_validated_before_network(self):
        opener = FakeOpener([])
        collector = GitHubPublicMetadataCollector(opener=opener)
        with self.assertRaises(ValueError):
            collector.get_public_repository("owner/name", "demo")
        with self.assertRaises(ValueError):
            collector.get_public_repository("owner", "../private")
        self.assertEqual(opener.requests, [])

    def test_user_listing_paginates_and_marks_candidates(self):
        page_one = [repository_payload(id=i, full_name=f"sample-owner/repo-{i}") for i in range(100)]
        page_two = [repository_payload(id=101, full_name="sample-owner/repo-100")]
        opener = FakeOpener([page_one, page_two])
        collector = GitHubPublicMetadataCollector(opener=opener)
        results = collector.list_public_repositories("sample-owner", max_pages=3)

        self.assertEqual(len(results), 101)
        self.assertTrue(all(item["status"] == "DISCOVERED" for item in results))
        self.assertEqual(parse_qs(urlparse(opener.requests[0][0].full_url).query)["page"], ["1"])
        self.assertEqual(parse_qs(urlparse(opener.requests[1][0].full_url).query)["page"], ["2"])
        self.assertEqual(parse_qs(urlparse(opener.requests[0][0].full_url).query)["type"], ["public"])

    def test_private_items_in_listing_are_excluded(self):
        opener = FakeOpener([[repository_payload(), repository_payload(id=2, private=True)]])
        results = GitHubPublicMetadataCollector(opener=opener).list_public_repositories("sample-owner")
        self.assertEqual(len(results), 1)

    def test_organization_endpoint_is_selected(self):
        opener = FakeOpener([[repository_payload()]])
        GitHubPublicMetadataCollector(opener=opener).list_public_repositories("sample-org", owner_type="org")
        self.assertIn("/orgs/sample-org/repos?", opener.requests[0][0].full_url)

    def test_page_limit_is_bounded(self):
        collector = GitHubPublicMetadataCollector(opener=FakeOpener([]))
        with self.assertRaises(ValueError):
            collector.list_public_repositories("sample-owner", max_pages=101)


if __name__ == "__main__":
    unittest.main()
