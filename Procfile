web: gunicorn config.wsgi:application
worker: celery worker --app=cappuccino2.taskapp --loglevel=info
