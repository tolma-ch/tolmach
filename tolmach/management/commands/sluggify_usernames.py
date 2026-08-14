import re

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from slugify import slugify


User = get_user_model()

USERNAME_RE = re.compile(r'^[0-9a-zA-Z._-]+$')


class Command(BaseCommand):
    help = 'Sluggify usernames that contain invalid characters'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print old -> new mappings without saving',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        candidates = [u for u in User.objects.iterator() if not USERNAME_RE.match(u.username)]

        if not candidates:
            self.stdout.write('All usernames are valid — nothing to do.')
            return

        existing = set(User.objects.values_list('username', flat=True))
        mappings = []
        for user in candidates:
            new = slugify(user.username)
            if not new:
                new = f'user-{user.pk}'
            original = new
            suffix = 1
            while new in existing:
                new = f'{original}-{suffix}'
                suffix += 1
            existing.add(new)
            mappings.append((user, new))

        self.stdout.write(f'Found {len(mappings)} username(s) to sluggify:\n')
        for user, new in mappings:
            self.stdout.write(f'  {user.username!r} -> {new!r}')

        if dry_run:
            self.stdout.write(self.style.WARNING('\nDRY RUN — no changes were saved'))
            return

        for user, new in mappings:
            user.username = new
            user.save(update_fields=['username'])

        self.stdout.write(self.style.SUCCESS(f'\nUpdated {len(mappings)} username(s)'))