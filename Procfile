web: python scripts/ensure_schema.py && python manage.py migrate --noinput && gunicorn foodwaste.wsgi:application --bind 0.0.0.0:8000
