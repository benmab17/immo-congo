import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "immo_congo.settings")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "temporary-reset-secret"))

import django

django.setup()

from django.apps import apps
from django.db import transaction


@transaction.atomic
def main():
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

    print(
        "Purge terminee: "
        + ", ".join(f"{name}={count}" for name, count in deleted_counts.items())
    )


if __name__ == "__main__":
    main()
