from datetime import date

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import models


User = get_user_model()


def user_has_relations(user):
    for field in user._meta.get_fields():
        if not isinstance(field, (models.OneToOneRel, models.ManyToOneRel, models.ManyToManyRel)):
            continue

        accessor = field.get_accessor_name()

        if accessor in ('usermeta', 'target', 'sender', 'social_auth'):
            continue

        if isinstance(field, models.OneToOneRel):
            try:
                getattr(user, accessor)
                return True, accessor
            except field.related_model.DoesNotExist:
                pass
        elif isinstance(field, models.ManyToManyRel):
            manager = getattr(user, accessor)
            if manager.exists():
                return True, accessor
        elif isinstance(field, models.ManyToOneRel):
            manager = getattr(user, accessor)
            if manager.exists():
                return True, accessor

    return False, None


class Command(BaseCommand):
    help = 'Delete users with empty email, no relations, registered before 2025-07-01'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cutoff',
            type=lambda s: date.fromisoformat(s),
            default=date(2025, 7, 1),
            help='Delete users registered before this date (ISO format, default: 2025-07-01)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        cutoff = options['cutoff']
        candidates = User.objects.filter(
            date_joined__lt=cutoff,
        ).filter(
            models.Q(email='') | models.Q(email__isnull=True),
        )

        self.stdout.write(f'Candidates with empty email and date_joined < {cutoff}: {candidates.count()}')

        to_delete = []
        skipped = []

        for user in candidates.iterator():
            has_rel, rel_name = user_has_relations(user)
            if has_rel:
                skipped.append((user, rel_name))
            else:
                to_delete.append(user)

        self.stdout.write(f'Users with relations (skipped): {len(skipped)}')
        for user, rel_name in skipped:
            self.stdout.write(f'  pk={user.pk} username={user.username!r} has {rel_name}')

        self.stdout.write(f'Users with no relations (to delete): {len(to_delete)}')
        for user in to_delete:
            self.stdout.write(f'  pk={user.pk} username={user.username!r} joined={user.date_joined}')

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN — no users were deleted'))
            return

        count = 0
        for user in to_delete:
            user.delete()
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Deleted {count} user(s)'))
