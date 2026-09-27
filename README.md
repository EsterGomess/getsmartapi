
# Ideiateca API

This is the backend API for the Ideiateca application — an MVP project developed
for a graduate program at PUC-Rio.

The application organizes and retains knowledge using the **Zettelkasten** method
created by Niklas Luhmann. The API provides authentication, note management, and
link (graph) operations.

---

## Table of Contents

- [Overview and Structure](#overview-and-structure)
- [Prerequisites](#prerequisites)
- [Environment Variables](#environment-variables)
- [Running Locally](#running-locally)
- [Database Migrations](#database-migrations)
- [Running Tests](#running-tests)
- [Seeding the Database](#seeding-the-database)
- [Running with Docker](#running-with-docker)
  - [Production Mode](#production-mode)
  - [Development Mode](#development-mode)
  - [Useful Docker Commands](#useful-docker-commands)
- [Deploying to Vercel](#deploying-to-vercel)
- [API Documentation](#api-documentation)
- [Authentication](#authentication)

---

## Overview and Structure

```text
Ideiateca/                                ← backend root
├── app/                               ← FastAPI source code
│   ├── api/routers/v1/                ← HTTP routes
│   ├── core/                          ← security, config
│   ├── crud/                          ← database access
│   ├── models/                        ← SQLAlchemy models
│   ├── schemas/                       ← Pydantic schemas
│   ├── services/                      ← business logic
│   └── main.py                        ← app entrypoint
├── alembic/                           ← database migrations
│   ├── versions/                      ← migration files
│   └── env.py
├── scripts/                           ← seed and utility scripts
│   ├── create_api_client.py           ← creates the default APIClient
├── tests/                             ← test suite
├── Dockerfile                         ← multi-stage (builder + runtime)
├── docker-compose.yml                 ← base (production)
├── docker-compose.override.yml        ← development (volumes, reload)
├── docker-compose.prod.yml            ← production overrides
├── alembic.ini
├── pyproject.toml                      ← Vercel FastAPI entrypoint
├── requirements.txt
└── .env                               ← NOT copied into the container
```

---

## Prerequisites

- [Python](https://www.python.org/) (version 3.12+ recommended)
- [pip](https://pip.pypa.io/) or an equivalent package manager
- [PostgreSQL](https://www.postgresql.org/) (version 16+ recommended)
- [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/) (if running via containers)

---

## Environment Variables

Create a `.env.developement` file at the project root based on `.env.example`:

```bash
cp .env.developement.example .env.developement
```

Available settings:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | Async PostgreSQL connection string; accepts provider URLs and selects `asyncpg` | - |
| `DATABASE_URL_SYNC` | Sync PostgreSQL connection string for Alembic; selects `psycopg2` | Derived from `DATABASE_URL` if omitted |
| `POSTGRES_USER` | PostgreSQL username when not using `DATABASE_URL` | Required with `POSTGRES_PASSWORD` and `POSTGRES_DB` |
| `POSTGRES_PASSWORD` | PostgreSQL password when not using `DATABASE_URL` | Required with `POSTGRES_USER` and `POSTGRES_DB` |
| `POSTGRES_DB` | PostgreSQL database name when not using `DATABASE_URL` | Required with `POSTGRES_USER` and `POSTGRES_PASSWORD` |
| `CORS_ALLOWED_ORIGINS` | Comma-separated browser origins allowed by CORS | `http://localhost:3000` |
| `DB_POOL_SIZE` | SQLAlchemy connections kept per instance | `1` |
| `DB_MAX_OVERFLOW` | Extra SQLAlchemy connections per instance | `0` |
| `SECRET_KEY` | JWT signing key (min 32 bytes) | - |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | User JWT lifetime in minutes | `43200` (30 days) |
| `API_CLIENT_ACCESS_TOKEN_EXPIRE_MINUTES` | APIClient JWT lifetime in minutes | `43200` (30 days) |
| `GEMINI_API_KEY` | Google Gemini API key (used by the AI suggestion feature) | - |
| `ENV` | Environment name (`development` / `production`) | `development` |

> ⚠️ **Note:** The `.env.developement` file is not copied into the Docker image for security reasons
> (listed in `.dockerignore`). In production/Docker, pass the variables through
> `docker-compose` or the command line.

---

## Running Locally

### 1. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/macOS
# or
.venv\Scripts\activate         # Windows PowerShell
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start the development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at [http://localhost:8000](http://localhost:8000).

### 4. Production-style run

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Database Migrations

Migrations are managed by Alembic. All commands must run **inside the container** or
with the virtual environment active.

### Apply pending migrations

```bash
alembic upgrade head
```

### Create a new migration

```bash
alembic revision --autogenerate -m "describe your change"
```

> ⚠️ Always review the generated file in `alembic/versions/` before applying.
> Autogenerate doesn't detect every change (e.g., enum modifications, column renames).

### Roll back one migration

```bash
alembic downgrade -1
```

### See the current revision

```bash
alembic current
```

---

## Running Tests

The test suite uses the PostgreSQL database configured for the project. Start the
database, apply migrations, then run pytest inside the application container:

```bash
docker compose build app
docker compose run --rm app alembic upgrade head
docker compose run --rm app python -m pytest
```

To run one test module:

```bash
docker compose run --rm app python -m pytest tests/services/test_auth.py
docker compose run --rm app python -m pytest tests/services/test_notes_ai.py
```

The database fixture rolls back test changes at the end of each test. The
`notes_ai` tests mock the Gemini client and do not call the external API.

---

## Seeding the Database

The API requires an **APIClient** to authenticate callers. Create a client with
the interactive prompt; the password is hidden while you type and must have at
least 16 characters:

```bash
docker compose exec -it app python -m scripts.create_api_client
```

The script can also read `API_CLIENT_USERNAME` and `API_CLIENT_PASSWORD` from its
environment for automated one-time setup. Do not commit these values or leave
them in a public client bundle. The script stores only a password hash and refuses
to replace a client with the same username.

For a frontend deployed on Vercel, store the client credentials as server-side
environment variables and have server-side functions call this API. Do not use
the `NEXT_PUBLIC_` prefix or send the shared client password or APIClient token
to browser code. The Vercel server-side layer must keep the APIClient token private
and forward authenticated requests to the FastAPI service.

> ⚠️ This repository contains the FastAPI backend, not the Vercel frontend proxy.
> The APIClient has access to the protected API routes, so use a dedicated strong
> credential for each deployed client and rotate it if it is exposed.

To create a human **User** account, use the `/api/v1/customers/register` endpoint
(requires APIClient authentication first).

---

## Running with Docker

### Production Mode

The project uses a multi-stage image (`builder` ➔ `runtime`) to keep the final
image light. In production, Compose starts the `migration` service after the
database healthcheck passes. The application starts after that service finishes
successfully.

To bring the stack up in production:

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

The API will be available at [http://localhost:8000](http://localhost:8000).

To run the API directly via the Docker CLI:

```bash
# Build the image
docker build -t ideiateca-api .

# Run the container (requires an external Postgres)
docker run -p 8000:8000 --env-file .env.developement ideiateca-api
```

---

### Development Mode

For development with source volume sync, hot reload, and migrations on startup:

```bash
# Docker Compose automatically merges docker-compose.override.yml
docker compose up --build
```

The base Compose file waits for the PostgreSQL healthcheck before starting the
application. The development override runs `alembic upgrade head`, then starts
Uvicorn with `--reload`. These commands are configured directly in
`docker-compose.override.yml`; the project does not use an `entrypoint.sh`.

---

### Useful Docker Commands

| Action | Command |
| :--- | :--- |
| **Start services in the background** | `docker compose up -d` |
| **Rebuild and start images** | `docker compose up --build` |
| **Stop the containers** | `docker compose down` |
| **Stop and remove volumes** | `docker compose down -v` |
| **View logs in real time** | `docker compose logs -f app` |
| **Access the container shell** | `docker compose exec app bash` |
| **Check container status** | `docker compose ps` |
| **Connect to the database** | `docker compose exec db psql -U postgres -d gieokgonggan` |
| **Run a migration** | `docker compose exec app alembic upgrade head` |
| **Run all tests** | `docker compose run --rm app python -m pytest` |
| **Run authentication tests** | `docker compose run --rm app python -m pytest tests/services/test_auth.py` |
| **Run notes AI tests** | `docker compose run --rm app python -m pytest tests/services/test_notes_ai.py` |
| **Seed the APIClient** | `docker compose exec app python -m scripts.create_api_client` |

---

## Deploying to Vercel

The FastAPI application is exported from `app.main:app`; `pyproject.toml` tells
Vercel to use that entrypoint. Vercel runs it as a Python Function, so the Docker
Compose services and startup commands are not used for this deployment.

1. Import this repository into Vercel using the repository root as the project
   root.
2. Add a PostgreSQL provider from the Vercel Marketplace, such as Neon. Set
   `DATABASE_URL` to its pooled connection URL and `DATABASE_URL_SYNC` to its
   direct/unpooled URL for Alembic. Both URLs can use standard `postgresql://`
   provider formats; the application selects the required SQLAlchemy drivers.
3. Configure Production environment variables in Vercel: `ENV=production`, a
   strong `SECRET_KEY`, both database URLs, and `GEMINI_API_KEY` if AI suggestions
   are enabled. Set `CORS_ALLOWED_ORIGINS` to the exact frontend origin(s),
   separated by commas, only if the browser calls this API directly.
4. Link the project locally with the Vercel CLI, install the Python dependencies,
   then apply the production database migrations before deploying:

   ```bash
   vercel link
   pip install -r requirements.txt
   vercel env run -e production -- alembic upgrade head
   ```

5. Deploy with `vercel --prod` or push to the connected production branch.

Keep APIClient credentials and tokens in server-side code. The browser must not
receive the shared APIClient password or bearer token. This repository contains
the API, so a frontend that needs the APIClient token should proxy its API calls
through server-side functions. The Python runtime on Vercel is currently in beta;
review its function and Hobby plan limits before relying on it for important data.

---

## API Documentation

Once running, the API exposes interactive documentation:

| Interface | URL |
| :--- | :--- |
| **Swagger UI** | [http://localhost:8000/docs](http://localhost:8000/docs) |
| **ReDoc** | [http://localhost:8000/redoc](http://localhost:8000/redoc) |
| **OpenAPI JSON** | [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json) |

### Main endpoints

| Method | Path | Description |
| :--- | :--- | :--- |
| `POST` | `/api/v1/auth/token` | Authenticate an APIClient and receive a JWT |
| `POST` | `/api/v1/customers/register` | Register a new human User (requires APIClient) |
| `POST` | `/api/v1/customers/login` | Log a User in and receive a JWT |
| `GET` | `/api/v1/notes/list` | List notes with pagination |
| `GET` | `/api/v1/notes/note/{id}` | Get a single note with its links |
| `POST` | `/api/v1/notes/create` | Create a note |
| `PATCH` | `/api/v1/notes/note/{id}` | Update a note |
| `DELETE` | `/api/v1/notes/note/{id}` | Delete a note |
| `GET` | `/api/v1/notes/graph` | Get the full note graph (nodes + edges) |
| `GET` | `/health` | Health check |

---

## Authentication

The API uses **two independent JWT layers**:

| Layer | Purpose | Header | Endpoint |
| :--- | :--- | :--- | :--- |
| **APIClient** | Identifies the application (e.g., the frontend) | `Authorization: Bearer <token>` | `POST /api/v1/auth/token` |
| **User** | Identifies the human behind the request | `X-User-Token: <jwt>` | `POST /api/v1/customers/login` |

### Flow

```text
1. Frontend → POST /api/v1/auth/token (APIClient credentials)
             ← { access_token }

2. Frontend → POST /api/v1/customers/login (User credentials + APIClient token)
             ← { access_token }

3. Frontend → GET /api/v1/notes/list
             Headers:
               Authorization: Bearer <api_client_token>
               X-User-Token:  <user_token>
             ← { items, total, page, ... }
