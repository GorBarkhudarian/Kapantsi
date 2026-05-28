"""
Management command: verify_blockchain

Verifies the integrity of the blockchain vote log chain.
Checks that each block's hash links correctly to the previous one
and that no entries have been tampered with.

Usage:
    python manage.py verify_blockchain
    python manage.py verify_blockchain --verbose
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Verify the integrity of the blockchain vote log.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Print each block entry during verification.',
        )

    def handle(self, *args, **options):
        from voting.models import BlockchainVoteLog

        entries = list(BlockchainVoteLog.objects.order_by('timestamp'))
        total = len(entries)

        self.stdout.write(f'\nVerifying {total} blockchain block(s)...\n')

        if total == 0:
            self.stdout.write(self.style.WARNING('No blockchain entries found.'))
            return

        is_valid = True
        prev_hash = '0' * 64

        for idx, entry in enumerate(entries, start=1):
            import hashlib, json

            if options['verbose']:
                self.stdout.write(
                    f'  Block {idx:>4}: {entry.vote_hash[:16]}...  '
                    f'prev: {entry.previous_hash[:16]}...'
                )

            # Check previous hash linkage
            if entry.previous_hash != prev_hash:
                self.stdout.write(
                    self.style.ERROR(
                        f'  Block {idx}: Previous hash mismatch! '
                        f'Expected {prev_hash[:16]}... '
                        f'Got {entry.previous_hash[:16]}...'
                    )
                )
                is_valid = False

            # Recompute hash and verify
            data = entry.block_data.copy()
            data['previous_hash'] = entry.previous_hash
            block_str = json.dumps(data, sort_keys=True)
            computed = hashlib.sha256(block_str.encode()).hexdigest()

            if computed != entry.vote_hash:
                self.stdout.write(
                    self.style.ERROR(
                        f'  Block {idx}: Hash mismatch — data has been tampered!'
                    )
                )
                is_valid = False

            prev_hash = entry.vote_hash

        self.stdout.write('')
        if is_valid:
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ Chain is VALID. All {total} block(s) verified successfully.'
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    '✗ Chain integrity FAILED. One or more blocks are invalid.'
                )
            )
        self.stdout.write('')
