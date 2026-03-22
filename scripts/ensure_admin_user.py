import os
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "immo_congo.settings")
os.environ.setdefault("DEBUG", "True")
os.environ.setdefault("SECRET_KEY", os.getenv("SECRET_KEY", "temporary-admin-secret"))

import django

django.setup()

from django.contrib.auth import get_user_model


def main():
    username = os.getenv("DJANGO_SUPERUSER_USERNAME")
    email = os.getenv("DJANGO_SUPERUSER_EMAIL", "")
    password = os.getenv("DJANGO_SUPERUSER_PASSWORD")

    if not username or not password:
        raise SystemExit(
            "Definis DJANGO_SUPERUSER_USERNAME et DJANGO_SUPERUSER_PASSWORD avant execution."
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

    if email:
        user.email = email
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()

    print(f"Superuser {'cree' if created else 'mis a jour'}: {username}")


if __name__ == "__main__":
    main()
