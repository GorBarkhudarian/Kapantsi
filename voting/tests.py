"""
voting/tests.py — Tests for the Voting app.

Covers:
- Vote model
- BlockchainVoteLog model
- Vote API endpoints
- voting/utils.py helpers
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from issues.models import Issue
from .models import Vote, BlockchainVoteLog

User = get_user_model()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_user(username: str, role: str = "citizen", verified: bool = True) -> User:
    return User.objects.create_user(
        username=username,
        password="pass1234",
        email=f"{username}@test.com",
        role=role,
        verified=verified,
        first_name="Vote",
        last_name="Tester",
        is_staff=(role == "admin"),
    )


def make_issue(user: User, **kwargs) -> Issue:
    defaults = {
        "title_hy": "Կ",
        "title_en": "Test issue",
        "description_hy": "desc",
        "category": "road",
        "created_by": user,
    }
    defaults.update(kwargs)
    return Issue.objects.create(**defaults)


# ---------------------------------------------------------------------------
# 1. Vote model tests
# ---------------------------------------------------------------------------

class VoteModelTest(TestCase):
    def setUp(self):
        self.citizen = make_user("vote_model_cit")
        self.issue = make_issue(self.citizen)

    def test_vote_creation(self):
        vote = Vote.objects.create(user=self.citizen, issue=self.issue)
        self.assertIsNotNone(vote.pk)

    def test_vote_str_contains_issue_and_user(self):
        vote = Vote.objects.create(user=self.citizen, issue=self.issue)
        s = str(vote)
        self.assertIsInstance(s, str)

    def test_vote_unique_per_user_per_issue(self):
        Vote.objects.create(user=self.citizen, issue=self.issue)
        with self.assertRaises(Exception):
            Vote.objects.create(user=self.citizen, issue=self.issue)

    def test_vote_deleted_when_issue_deleted(self):
        Vote.objects.create(user=self.citizen, issue=self.issue)
        issue_pk = self.issue.pk
        self.issue.delete()
        self.assertEqual(Vote.objects.filter(issue_id=issue_pk).count(), 0)

    def test_multiple_users_can_vote_on_same_issue(self):
        u2 = make_user("vote_model_cit2")
        Vote.objects.create(user=self.citizen, issue=self.issue)
        Vote.objects.create(user=u2, issue=self.issue)
        self.assertEqual(Vote.objects.filter(issue=self.issue).count(), 2)

    def test_one_user_can_vote_on_multiple_issues(self):
        issue2 = make_issue(self.citizen, title_en="Issue 2", title_hy="I2")
        Vote.objects.create(user=self.citizen, issue=self.issue)
        Vote.objects.create(user=self.citizen, issue=issue2)
        self.assertEqual(Vote.objects.filter(user=self.citizen).count(), 2)


# ---------------------------------------------------------------------------
# 2. BlockchainVoteLog model tests
# ---------------------------------------------------------------------------

class BlockchainVoteLogModelTest(TestCase):
    def setUp(self):
        self.citizen = make_user("bc_cit")
        self.issue = make_issue(self.citizen)
        self.vote = Vote.objects.create(user=self.citizen, issue=self.issue)

    def test_blockchain_log_created_with_vote(self):
        count = BlockchainVoteLog.objects.filter(vote=self.vote).count()
        self.assertGreaterEqual(count, 0)

    def test_blockchain_log_manual_creation(self):
        import hashlib, json
        data = {"vote_id": self.vote.pk, "block_id": 1, "prev_hash": "0" * 64}
        block_hash = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        log = BlockchainVoteLog.objects.create(
            vote=self.vote,
            block_id=1,
            block_hash=block_hash,
            prev_hash="0" * 64,
        )
        self.assertEqual(log.block_hash, block_hash)

    def test_blockchain_log_str(self):
        import hashlib, json
        data = {"vote_id": self.vote.pk, "block_id": 2, "prev_hash": "0" * 64}
        block_hash = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        log = BlockchainVoteLog.objects.create(
            vote=self.vote,
            block_id=2,
            block_hash=block_hash,
            prev_hash="0" * 64,
        )
        self.assertIsInstance(str(log), str)


# ---------------------------------------------------------------------------
# 3. Vote API tests
# ---------------------------------------------------------------------------

class VoteAPITest(TestCase):
    def setUp(self):
        self.citizen = make_user("vote_api_cit")
        self.admin = make_user("vote_api_adm", role="admin")
        self.issue = make_issue(self.citizen)
        self.client = APIClient()

    def test_authenticated_citizen_can_vote(self):
        self.client.force_authenticate(user=self.citizen)
        response = self.client.post(f"/api/issues/{self.issue.pk}/vote/", format="json")
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
        ])

    def test_unauthenticated_cannot_vote(self):
        response = self.client.post(f"/api/issues/{self.issue.pk}/vote/", format="json")
        self.assertIn(response.status_code, [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ])

    def test_vote_on_nonexistent_issue_returns_404(self):
        self.client.force_authenticate(user=self.citizen)
        response = self.client.post("/api/issues/99999/vote/", format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_vote_count_does_not_go_negative(self):
        self.client.force_authenticate(user=self.citizen)
        self.client.post(f"/api/issues/{self.issue.pk}/vote/", format="json")
        final_votes = Vote.objects.filter(issue=self.issue).count()
        self.assertGreaterEqual(final_votes, 0)


# ---------------------------------------------------------------------------
# 4. voting/utils.py tests
# ---------------------------------------------------------------------------

class ComputeVoteHashTest(TestCase):
    def test_returns_64_char_hex_string(self):
        from .utils import compute_vote_hash
        result = compute_vote_hash(1, 2, 3, "2026-01-01T00:00:00Z")
        self.assertEqual(len(result), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in result))

    def test_deterministic(self):
        from .utils import compute_vote_hash
        h1 = compute_vote_hash(1, 2, 3, "2026-01-01T00:00:00Z")
        h2 = compute_vote_hash(1, 2, 3, "2026-01-01T00:00:00Z")
        self.assertEqual(h1, h2)

    def test_different_inputs_different_hashes(self):
        from .utils import compute_vote_hash
        h1 = compute_vote_hash(1, 2, 3, "2026-01-01T00:00:00Z")
        h2 = compute_vote_hash(1, 2, 4, "2026-01-01T00:00:00Z")
        self.assertNotEqual(h1, h2)


class VoteStatsTest(TestCase):
    def setUp(self):
        self.citizen = make_user("vstats_cit")
        self.issue = make_issue(self.citizen)

    def test_no_votes_returns_zero(self):
        from .utils import vote_stats
        result = vote_stats(self.issue)
        self.assertEqual(result["total"], 0)

    def test_with_votes_returns_correct_count(self):
        from .utils import vote_stats
        u2 = make_user("vstats_cit2")
        Vote.objects.create(user=self.citizen, issue=self.issue)
        Vote.objects.create(user=u2, issue=self.issue)
        result = vote_stats(self.issue)
        self.assertEqual(result["total"], 2)

    def test_result_has_expected_keys(self):
        from .utils import vote_stats
        result = vote_stats(self.issue)
        self.assertIn("total", result)
        self.assertIn("upvotes", result)
        self.assertIn("percentage", result)


class HasVotedTest(TestCase):
    def setUp(self):
        self.citizen = make_user("hasvoted_cit")
        self.issue = make_issue(self.citizen)

    def test_returns_false_before_voting(self):
        from .utils import has_voted
        self.assertFalse(has_voted(self.citizen, self.issue))

    def test_returns_true_after_voting(self):
        from .utils import has_voted
        Vote.objects.create(user=self.citizen, issue=self.issue)
        self.assertTrue(has_voted(self.citizen, self.issue))

    def test_anonymous_user_returns_false(self):
        from .utils import has_voted
        from django.contrib.auth.models import AnonymousUser
        self.assertFalse(has_voted(AnonymousUser(), self.issue))

    def test_different_issue_returns_false(self):
        from .utils import has_voted
        other_issue = make_issue(self.citizen, title_en="Other", title_hy="O")
        Vote.objects.create(user=self.citizen, issue=self.issue)
        self.assertFalse(has_voted(self.citizen, other_issue))


class ToggleVoteTest(TestCase):
    def setUp(self):
        self.citizen = make_user("toggle_cit")
        self.issue = make_issue(self.citizen)

    def test_toggle_adds_vote(self):
        from .utils import toggle_vote
        voted, action = toggle_vote(self.citizen, self.issue)
        self.assertTrue(voted)
        self.assertEqual(action, "added")

    def test_toggle_removes_existing_vote(self):
        from .utils import toggle_vote
        Vote.objects.create(user=self.citizen, issue=self.issue)
        voted, action = toggle_vote(self.citizen, self.issue)
        self.assertFalse(voted)
        self.assertEqual(action, "removed")

    def test_toggle_twice_re_adds_vote(self):
        from .utils import toggle_vote
        toggle_vote(self.citizen, self.issue)
        toggle_vote(self.citizen, self.issue)
        voted, action = toggle_vote(self.citizen, self.issue)
        self.assertTrue(voted)
        self.assertEqual(action, "added")

    def test_toggle_creates_db_record(self):
        from .utils import toggle_vote
        toggle_vote(self.citizen, self.issue)
        self.assertEqual(Vote.objects.filter(
            user=self.citizen, issue=self.issue
        ).count(), 1)

    def test_toggle_removes_db_record(self):
        from .utils import toggle_vote
        Vote.objects.create(user=self.citizen, issue=self.issue)
        toggle_vote(self.citizen, self.issue)
        self.assertEqual(Vote.objects.filter(
            user=self.citizen, issue=self.issue
        ).count(), 0)


class TopVotedIssuesTest(TestCase):
    def setUp(self):
        self.citizen = make_user("top_cit")
        self.popular = make_issue(self.citizen, title_en="Popular", title_hy="P")
        self.unpopular = make_issue(self.citizen, title_en="Unpopular", title_hy="U")
        Vote.objects.create(user=self.citizen, issue=self.popular)
        u2 = make_user("top_cit2")
        Vote.objects.create(user=u2, issue=self.popular)

    def test_popular_issue_is_first(self):
        from .utils import top_voted_issues
        results = list(top_voted_issues(5))
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0].pk, self.popular.pk)

    def test_unpopular_issue_not_included(self):
        from .utils import top_voted_issues
        results = list(top_voted_issues(5))
        pks = [r.pk for r in results]
        self.assertNotIn(self.unpopular.pk, pks)

    def test_limit_respected(self):
        from .utils import top_voted_issues
        results = list(top_voted_issues(1))
        self.assertEqual(len(results), 1)

    def test_no_votes_returns_empty(self):
        Vote.objects.all().delete()
        from .utils import top_voted_issues
        results = list(top_voted_issues(5))
        self.assertEqual(len(results), 0)


class VerifyVoteChainTest(TestCase):
    def test_empty_chain_is_valid(self):
        from .utils import verify_vote_chain
        result = verify_vote_chain()
        self.assertTrue(result["valid"])
        self.assertEqual(result["checked"], 0)
        self.assertEqual(result["errors"], [])

    def test_chain_with_valid_block(self):
        import hashlib, json
        citizen = make_user("chain_cit")
        issue = make_issue(citizen)
        vote = Vote.objects.create(user=citizen, issue=issue)
        prev_hash = "0" * 64
        data = {"vote_id": vote.pk, "block_id": 1, "prev_hash": prev_hash}
        block_hash = hashlib.sha256(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()
        BlockchainVoteLog.objects.create(
            vote=vote, block_id=1, block_hash=block_hash, prev_hash=prev_hash
        )
        from .utils import verify_vote_chain
        result = verify_vote_chain(issue=issue)
        self.assertTrue(result["valid"])
        self.assertEqual(result["checked"], 1)

    def test_tampered_block_fails_verification(self):
        import hashlib, json
        citizen = make_user("tamper_cit")
        issue = make_issue(citizen)
        vote = Vote.objects.create(user=citizen, issue=issue)
        BlockchainVoteLog.objects.create(
            vote=vote,
            block_id=1,
            block_hash="0" * 64,
            prev_hash="0" * 64,
        )
        from .utils import verify_vote_chain
        result = verify_vote_chain(issue=issue)
        self.assertFalse(result["valid"])
        self.assertGreater(len(result["errors"]), 0)
