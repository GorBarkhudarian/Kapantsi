"""
Serializers for the Voting app.
Covers Vote and BlockchainVoteLog models with full field representation.
"""
from rest_framework import serializers
from .models import Vote, BlockchainVoteLog


class VoteSerializer(serializers.ModelSerializer):
    """
    Serializer for individual votes.
    Exposes the voter's display name and the associated issue title.
    """
    voter_username = serializers.SerializerMethodField()
    voter_full_name = serializers.SerializerMethodField()
    issue_title = serializers.SerializerMethodField()

    class Meta:
        model = Vote
        fields = [
            'id',
            'voter_username',
            'voter_full_name',
            'issue',
            'issue_title',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_voter_username(self, obj):
        if obj.user:
            return obj.user.username
        return 'anonymous'

    def get_voter_full_name(self, obj):
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return 'Unknown'

    def get_issue_title(self, obj):
        if obj.issue:
            return obj.issue.title_hy
        return ''


class BlockchainVoteLogSerializer(serializers.ModelSerializer):
    """
    Read-only serializer for blockchain vote log entries.
    Used for the transparency and audit log endpoint.
    """
    voter_username = serializers.SerializerMethodField()
    issue_id = serializers.SerializerMethodField()

    class Meta:
        model = BlockchainVoteLog
        fields = [
            'id',
            'vote',
            'voter_username',
            'issue_id',
            'vote_hash',
            'previous_hash',
            'block_data',
            'timestamp',
        ]
        read_only_fields = fields

    def get_voter_username(self, obj):
        try:
            return obj.vote.user.username if obj.vote else 'unknown'
        except Exception:
            return 'unknown'

    def get_issue_id(self, obj):
        try:
            return obj.vote.issue_id if obj.vote else None
        except Exception:
            return None


class ChainVerificationSerializer(serializers.Serializer):
    """
    Serializer for the blockchain chain integrity verification result.
    """
    is_valid = serializers.BooleanField(read_only=True)
    total_blocks = serializers.IntegerField(read_only=True)
    message = serializers.CharField(read_only=True)
    verified_at = serializers.DateTimeField(read_only=True)
