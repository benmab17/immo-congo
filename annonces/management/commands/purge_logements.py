from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import transaction


class Command(BaseCommand):
    help = "Supprime toutes les annonces, leurs photos et les donnees dependantes."

    @transaction.atomic
    def handle(self, *args, **options):
        table_models = [
            ("annonces", "ContactUnlock"),
            ("annonces", "CommentaireAdmin"),
            ("annonces", "Notification"),
            ("annonces", "Signalement"),
            ("annonces", "Favori"),
            ("annonces", "MessageVisiteur"),
            ("annonces", "Photo"),
            ("annonces", "Logement"),
        ]
        deleted_counts = {}

        for app_label, model_name in table_models:
            model = apps.get_model(app_label, model_name)
            deleted_counts[model_name] = model.objects.count()
            model.objects.all().delete()

        self.stdout.write(
            self.style.SUCCESS(
                "Purge terminee: "
                + ", ".join(f"{name}={count}" for name, count in deleted_counts.items())
            )
        )
