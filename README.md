# Project Task Manager API

Django REST Framework backend with JWT auth, role-based access control, and PostgreSQL.

## Features
- JWT Authentication (signup, login, refresh, logout)
- Custom User model (email-based login)
- Projects with Admin / Member roles (RBAC)
- Tasks with status tracking, priority, due dates, overdue detection
- Comments on tasks
- Dashboard endpoint with aggregated stats
- PostgreSQL on Railway, SQLite for local dev

---

## Tech Stack
| Layer      | Tech                          |
|-----------|-------------------------------|
| Framework  | Django 4.2 + DRF 3.14        |
| Auth       | SimpleJWT                     |
| Database   | PostgreSQL (Railway) / SQLite |
| ORM        | Django ORM                    |
| Deployment | Railway + Gunicorn            |
| Static     | WhiteNoise                    |

---

## Local Setup

```bash
# 1. Clone and enter
git clone <repo> && cd project_manager

# 2. Virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Environment variables
cp .env.example .env
# Edit .env — at minimum set SECRET_KEY

# 5. Migrate (uses SQLite locally)
python manage.py migrate

# 6. Create superuser
python manage.py createsuperuser

# 7. Run
python manage.py runserver
```

API base URL: `http://localhost:8000/api/v1/`

---

## Railway Deployment

1. Push code to GitHub
2. Create a new Railway project → **Deploy from GitHub repo**
3. Add a **PostgreSQL** plugin — `DATABASE_URL` is injected automatically
4. Set environment variables in Railway dashboard:
   ```
   SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_hex(32))">
   DEBUG=False
   ALLOWED_HOSTS=your-app.up.railway.app
   CORS_ALLOWED_ORIGINS=https://your-frontend.up.railway.app
   ```
5. Railway runs `railway.toml` start command automatically:
   `migrate → collectstatic → gunicorn`

---

## API Reference

### Auth
| Method | Endpoint                  | Auth | Description              |
|--------|---------------------------|------|--------------------------|
| POST   | /auth/register/           | ✗    | Sign up + get tokens     |
| POST   | /auth/login/              | ✗    | Login + get tokens       |
| POST   | /auth/logout/             | ✓    | Blacklist refresh token  |
| POST   | /auth/token/refresh/      | ✗    | Refresh access token     |
| GET    | /auth/me/                 | ✓    | Get current user         |
| PATCH  | /auth/me/                 | ✓    | Update profile           |
| POST   | /auth/change-password/    | ✓    | Change password          |

### Projects
| Method | Endpoint                              | Role    | Description              |
|--------|---------------------------------------|---------|--------------------------|
| GET    | /projects/                            | Member+ | List my projects         |
| POST   | /projects/                            | Any     | Create project           |
| GET    | /projects/{id}/                       | Member  | Project detail           |
| PATCH  | /projects/{id}/                       | Admin   | Update project           |
| DELETE | /projects/{id}/                       | Admin   | Delete project           |
| GET    | /projects/{id}/members/               | Member  | List members             |
| POST   | /projects/{id}/members/add/           | Admin   | Add member by email      |
| PATCH  | /projects/{id}/members/{uid}/         | Admin   | Change member role       |
| DELETE | /projects/{id}/members/{uid}/         | Admin   | Remove member            |

### Tasks
| Method | Endpoint                              | Role          | Description              |
|--------|---------------------------------------|---------------|--------------------------|
| GET    | /tasks/project/{project_pk}/          | Member        | List tasks (filterable)  |
| POST   | /tasks/project/{project_pk}/          | Member        | Create task              |
| GET    | /tasks/{id}/                          | Member        | Task detail + comments   |
| PATCH  | /tasks/{id}/                          | Admin/Assignee| Update task              |
| DELETE | /tasks/{id}/                          | Admin         | Delete task              |
| GET    | /tasks/{id}/comments/                 | Member        | List comments            |
| POST   | /tasks/{id}/comments/                 | Member        | Add comment              |
| PATCH  | /tasks/{id}/comments/{cid}/           | Author        | Edit own comment         |
| DELETE | /tasks/{id}/comments/{cid}/           | Author/Admin  | Delete comment           |

**Task filters:** `?status=todo|in_progress|in_review|done` `?priority=low|medium|high|urgent`
`?assignee=<user_id>` `?overdue=true` `?due_before=YYYY-MM-DD` `?due_after=YYYY-MM-DD`
`?search=<text>` `?ordering=due_date|-created_at`

### Dashboard
| Method | Endpoint       | Description                              |
|--------|----------------|------------------------------------------|
| GET    | /dashboard/    | Task stats, overdue, upcoming, projects  |

---

## RBAC Summary

| Action                    | Admin | Member |
|--------------------------|-------|--------|
| View project & tasks     | ✓     | ✓      |
| Create tasks             | ✓     | ✓      |
| Update any task          | ✓     | ✗      |
| Update own task status   | ✓     | ✓      |
| Delete task              | ✓     | ✗      |
| Add/remove members       | ✓     | ✗      |
| Change member roles      | ✓     | ✗      |
| Update/delete project    | ✓     | ✗      |
| Comment on tasks         | ✓     | ✓      |

---

## Project Structure
```
project_manager/
├── config/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── accounts/       # User model, auth views, JWT
│   ├── projects/       # Project & ProjectMember models, RBAC
│   ├── tasks/          # Task & Comment models, filters
│   └── dashboard/      # Aggregated stats endpoint
├── manage.py
├── requirements.txt
├── Procfile
├── railway.toml
└── .env.example
```
