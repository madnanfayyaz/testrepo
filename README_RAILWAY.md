# GRC Platform (Railway-safe scaffold)

## Deploy on Railway (Docker)
1) Push this repo to GitHub
2) Railway -> New Project -> Deploy from GitHub
3) Add PostgreSQL service
4) In App service Variables set:
   - DATABASE_URL = ${{Postgres.DATABASE_URL}}
   - DJANGO_SECRET_KEY = <random>
   - DJANGO_ALLOWED_HOSTS = *
   - DJANGO_DEBUG = 0

5) Deploy

## One-time setup (Railway shell)
python manage.py migrate
python manage.py seed_initial_data --tenant-name "Client A"

Health check:
/healthz/