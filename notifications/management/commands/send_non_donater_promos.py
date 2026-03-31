from django.core.management.base import BaseCommand
from django.utils import timezone

from notifications.services import (
    get_non_donater_promo_candidates,
    send_non_donater_promo,
)


class Command(BaseCommand):
    help = "Non-donater userlar uchun random promo xabar yuboradi (haftasiga max 3)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=200)

    def handle(self, *args, **options):
        limit = max(1, options["limit"])
        now = timezone.now()
        sent = 0
        skipped = 0
        failed = 0
        for user in get_non_donater_promo_candidates(limit=limit):
            ok, reason = send_non_donater_promo(user, now=now)
            if ok:
                sent += 1
            elif reason == "failed":
                failed += 1
            else:
                skipped += 1
        self.stdout.write(
            self.style.SUCCESS(
                f"Promo dispatch tugadi. sent={sent}, skipped={skipped}, failed={failed}, limit={limit}"
            )
        )
