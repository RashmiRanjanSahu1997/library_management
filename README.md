# Library Management System (LMS) — Django REST API

This README explains how to set up, run and test the Library Management System API built with Django + Django REST Framework + Simple JWT. It includes optional instructions for MySQL, email, Swagger docs and Celery for async email processing.

---

## Features

* JWT authentication (djangorestframework-simplejwt)
* Roles: `STUDENT`, `LIBRARIAN` (custom `User` model with email as login)
* CRUD for Authors, Genres, Books
* Borrow request flow (request → approve/reject → return)
* Book reviews
* Email notifications on approve/reject (sync by default, optional Celery async)
* Per-user rate-limiting on borrow requests
* Swagger UI (drf-yasg)

---

## Prerequisites

* Python 3.10+ recommended
* pip
* Virtualenv (recommended)
* MySQL (optional) or use default SQLite
* (Optional) Redis & Celery for async tasks

---

## Quick start (development)

1. Clone repository / copy project files

```bash
git clone <repo-url> library_management
cd library_management
```

2. Create & activate virtual environment

```bash
python -m venv .venv
# mac/linux
source .venv/bin/activate
# windows
.venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

> Example `requirements.txt` should include:
>
> ```text
> Django>=4.2
> djangorestframework
> djangorestframework-simplejwt
> django-filter
> drf-yasg
> mysqlclient  # optional if using MySQL
> celery redis  # optional for async tasks
> ```

4. Environment variables

Create a `.env` file (or export environment variables) in project root. Example `.env`:

```env
DJANGO_SECRET_KEY=replace-me
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=mysql://root:password@127.0.0.1:3306/lms_db  # optional, used if you configure dj-database-url
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=you@gmail.com
EMAIL_HOST_PASSWORD=app-password
DEFAULT_FROM_EMAIL='Library <no-reply@example.com>'
```

> Alternatively for simple local development, skip MySQL and use SQLite (DEFAULT). You can still set email backend to console to see emails in terminal.

5. Configure `settings.py`

* Set `AUTH_USER_MODEL = 'library.User'`
* Database: either the supplied MySQL config or default SQLite.
* Add JWT & REST_FRAMEWORK settings (see `settings.py` snippets in project files).
* Add `SWAGGER_SETTINGS` to expose `Bearer` auth to the Swagger UI (see canvas file).

6. Create database (MySQL)

```sql
CREATE DATABASE lms_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

7. Apply migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

8. Create superuser (optional)

```bash
python manage.py createsuperuser
```

9. Run development server

```bash
python manage.py runserver
```

Open: `http://127.0.0.1:8000/swagger/` for API docs or `http://127.0.0.1:8000/api/` to test endpoints.

---

## Authentication (JWT)

* Obtain token:

```
POST /api/token/
{ "email": "user@example.com", "password": "pass" }
```

* Refresh token:

```
POST /api/token/refresh/
{ "refresh": "<refresh_token>" }
```

Include header in requests:

```
Authorization: Bearer <access_token>
```

To enable Bearer auth in Swagger, ensure `SWAGGER_SETTINGS` in `settings.py` includes the `'Bearer'` apiKey definition.

---

## Email configuration

For development you can use console backend (shows mails in terminal):

```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

For real SMTP (Gmail example):

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', 'no-reply@example.com')
```

> For Gmail use an app password or allow less secure apps (not recommended). For production, use transactional email provider (SendGrid, Mailgun, SES).

### Async email (Celery)

If you expect high volume, run email sending asynchronously with Celery + Redis.

* Example tasks file (e.g., `library/tasks.py`):

```python
from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_notification_email(subject, message, recipient_list):
    send_mail(subject, message, 'no-reply@example.com', recipient_list)
```

* Call `send_notification_email.delay(subject, message, [email])` from views instead of blocking `send_mail`.

---

## Rate-limiting / Throttling

* Borrow endpoint throttle uses DRF throttle classes. Example in `settings.py`:

```python
REST_FRAMEWORK = {
    ...
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '1000/day',
        'anon': '10/day',
        'borrow': '5/day',
    }
}
```

The custom `BorrowRequestRateThrottle` in `BorrowRequestViewSet` uses the `borrow` scope by default.

---

## Swagger / API docs

* Swagger is available if `drf_yasg` is installed and included in `INSTALLED_APPS`.
* Visit `/swagger/` to view and `Authorize` using `Bearer <token>` once `SWAGGER_SETTINGS` includes the Bearer definition.

