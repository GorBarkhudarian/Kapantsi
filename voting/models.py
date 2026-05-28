import hashlib
import json
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Vote(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='votes'
    )
    issue = models.ForeignKey(
        'issues.Issue',
        on_delete=models.CASCADE,
        related_name='votes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'issue')]
        verbose_name = _('Vote')
        verbose_name_plural = _('Votes')

    def __str__(self):
        return f'{self.user} voted on #{self.issue_id}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.issue.refresh_vote_count()
        BlockchainVoteLog.create_entry(self)

    def delete(self, *args, **kwargs):
        issue = self.issue
        super().delete(*args, **kwargs)
        issue.refresh_vote_count()


class BlockchainVoteLog(models.Model):
    vote = models.OneToOneField(Vote, on_delete=models.SET_NULL, null=True, related_name='blockchain_log')
    vote_hash = models.CharField(max_length=64, unique=True)
    previous_hash = models.CharField(max_length=64)
    block_data = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']
        verbose_name = _('Blockchain Vote Log')
        verbose_name_plural = _('Blockchain Vote Logs')

    def __str__(self):
        return f'Block {self.id}: {self.vote_hash[:16]}...'

    @classmethod
    def get_last_hash(cls):
        last = cls.objects.order_by('-timestamp').first()
        if last:
            return last.vote_hash
        return '0' * 64

    @classmethod
    def create_entry(cls, vote):
        previous_hash = cls.get_last_hash()
        data = {
            'vote_id': vote.id,
            'user_id': vote.user_id,
            'issue_id': vote.issue_id,
            'timestamp': vote.created_at.isoformat() if vote.created_at else '',
            'previous_hash': previous_hash,
        }
        block_str = json.dumps(data, sort_keys=True)
        vote_hash = hashlib.sha256(block_str.encode()).hexdigest()
        return cls.objects.create(
            vote=vote,
            vote_hash=vote_hash,
            previous_hash=previous_hash,
            block_data=data,
        )

    @classmethod
    def verify_chain(cls):
        entries = list(cls.objects.order_by('timestamp'))
        if not entries:
            return True
        prev = '0' * 64
        for entry in entries:
            if entry.previous_hash != prev:
                return False
            data = entry.block_data.copy()
            data['previous_hash'] = entry.previous_hash
            block_str = json.dumps(data, sort_keys=True)
            computed = hashlib.sha256(block_str.encode()).hexdigest()
            if computed != entry.vote_hash:
                return False
            prev = entry.vote_hash
        return True
