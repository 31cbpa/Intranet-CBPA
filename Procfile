release: python manage.py makemigrations --noinput && python manage.py migrate --noinput && python manage.py collectstatic --noinput
web: gunicorn proyecto_cbpa.wsgi --log-file -
