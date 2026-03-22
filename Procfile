web: python manage.py migrate --noinput && python manage.py loaddata annonces_fixes.json && python manage.py collectstatic --noinput && gunicorn immo_congo.wsgi
