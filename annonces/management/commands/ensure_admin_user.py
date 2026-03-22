import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Cree ou met a jour un superuser a partir des variables d'environnement."

    def handle(self, *args, **options):
        username = os.getenv("DJANGO_SUPERUSER_USERNAME")
        email = os.getenv("DJANGO_SUPERUSER_EMAIL", "")
        password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

        if not username or not password:
            raise CommandError(
                "Definis DJANGO_SUPERUSER_USERNAME et DJANGO_SUPERUSER_PASSWORD avant d'executer cette commande."
            )

        user_model = get_user_model()
        user, created = user_model.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        updates = []
        if email and user.email != email:
            user.email = email
            updates.append("email")
        if not user.is_staff:
            user.is_staff = True
            updates.append("is_staff")
        if not user.is_superuser:
            user.is_superuser = True
            updates.append("is_superuser")

        user.set_password(password)
        updates.append("password")
        user.save(update_fields=list(dict.fromkeys(updates)))

        action = "cree" if created else "mis a jour"
        self.stdout.write(self.style.SUCCESS(f"Superuser {action}: {username}"))
