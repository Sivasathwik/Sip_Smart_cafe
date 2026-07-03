# Sip Smart Cafe Deployment

## Local setup

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py runserver
```

## Production environment variables

Set these on Vercel:

```text
DJANGO_SECRET_KEY=replace-with-a-long-random-secret
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=.vercel.app,your-domain.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://*.vercel.app,https://your-domain.com
DATABASE_URL=your-postgres-database-url
DJANGO_SECURE_SSL_REDIRECT=False
DJANGO_SESSION_COOKIE_SECURE=True
DJANGO_CSRF_COOKIE_SECURE=True
DJANGO_SECURE_HSTS_SECONDS=31536000
```

Use a Postgres database for deployment, such as Vercel Postgres, Neon, or Supabase. SQLite is fine locally but is not persistent on Vercel.

## Start command

```text
gunicorn coffeshop.wsgi:application
```
