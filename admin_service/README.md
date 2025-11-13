# Admin Service Backend (FastAPI)

This service provides administrative CRUD APIs for managing users, plans, promo codes, referrals, nodes, and subscriptions. It exposes dedicated endpoints for operational actions such as suspending or resuming subscriptions, issuing promo codes, switching subscription nodes, and banning users.

## Stack choice

The service implements the **FastAPI + React** stack option described in the requirements. The backend is implemented with FastAPI and is ready for consumption by a React frontend (not included in this repository). All endpoints are secured with JWT-based authorization and an IP allow list middleware.

## Features

- CRUD endpoints for `users`, `plans`, `promocodes`, `referrals`, `nodes`, and `subscriptions`.
- Operational actions: suspend/resume subscriptions, issue promo codes, change subscription nodes, and ban users.
- JWT authentication with bcrypt password hashing.
- Configurable IP allow list enforced via middleware.
- Structured audit log capturing all mutating operations and privileged actions.
- Automatic database migrations-on-start via SQLAlchemy (SQLite by default).
- Optional bootstrap admin user created on startup when credentials are provided via environment variables.

## Configuration

Environment variables are read via `pydantic` settings using the `ADMIN_SERVICE_` prefix. The most important settings are:

| Variable | Description |
| --- | --- |
| `ADMIN_SERVICE_SECRET_KEY` | Secret key used to sign JWT tokens (required). |
| `ADMIN_SERVICE_DATABASE_URL` | SQLAlchemy database URL (defaults to local SQLite). |
| `ADMIN_SERVICE_ALLOWED_IPS` | Comma-separated list of IP addresses allowed to access the service. |
| `ADMIN_SERVICE_ACCESS_TOKEN_EXPIRE_MINUTES` | JWT lifetime in minutes (default: 60). |
| `ADMIN_SERVICE_BOOTSTRAP_ADMIN_EMAIL` | Email used to seed an initial admin user (optional). |
| `ADMIN_SERVICE_BOOTSTRAP_ADMIN_PASSWORD` | Password for the bootstrap admin user (optional). |

> **Note:** When both bootstrap variables are provided, the service creates the admin user during startup if it does not exist.

## Running locally

1. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

2. Set the required environment variables (at minimum `ADMIN_SERVICE_SECRET_KEY`). For example:

   ```bash
   export ADMIN_SERVICE_SECRET_KEY="change-me"
   export ADMIN_SERVICE_BOOTSTRAP_ADMIN_EMAIL="admin@example.com"
   export ADMIN_SERVICE_BOOTSTRAP_ADMIN_PASSWORD="supersecret"
   export ADMIN_SERVICE_ALLOWED_IPS="127.0.0.1,::1"
   ```

3. Start the service:

   ```bash
   uvicorn admin_service.backend.app.main:app --reload
   ```

4. Interact with the API using the automatically generated OpenAPI docs at `http://127.0.0.1:8000/docs`.

## Authentication workflow

1. Log in via `POST /auth/login` using a valid email/password pair to receive a JWT token.
2. Include the token in subsequent requests: `Authorization: Bearer <token>`.
3. Requests originating from IPs outside the configured allow list are rejected with HTTP 403.

## Database schema

The database schema is defined in `admin_service/backend/app/models.py`. SQLAlchemy handles table creation on startup. SQLite is used by default, but any database supported by SQLAlchemy can be configured via `ADMIN_SERVICE_DATABASE_URL`.

## Audit logging

All mutating endpoints append entries to the `audit_logs` table. Each record includes:

- Acting user ID
- Action name
- Target entity type and ID
- Optional metadata payload
- Request IP address
- Timestamp

The log can be retrieved via `GET /audit/`.

## Testing the actions

Example requests (replace `<TOKEN>` with a valid JWT):

```bash
curl -X POST http://127.0.0.1:8000/actions/subscriptions/suspend \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"subscription_id": 1, "reason": "payment_issue"}'
```

```bash
curl -X POST http://127.0.0.1:8000/actions/promocodes/issue \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "discount_percent": 15, "valid_for_hours": 24}'
```

These requests will update the corresponding entities and create audit log entries.
