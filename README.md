# RAGVault

**A document vault built for retrieval.** RAGVault ingests your text files, chunks them, tracks every ingestion as an idempotent job, and streams the content back through a paged reader — all behind per-user ownership and short-lived, rotating sessions.

It is a full-stack project: an async FastAPI backend on PostgreSQL and Redis, plus a React client that talks to it.

![Python](https://img.shields.io/badge/python-3.14-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-18-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-8-DC382D?logo=redis&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=black)
![TypeScript](https://img.shields.io/badge/TypeScript-6-3178C6?logo=typescript&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-3DA639)

---

## Table of contents

- [Why RAGVault](#why-ragvault)
- [What works today](#what-works-today)
- [Architecture](#architecture)
- [Tech stack](#tech-stack)
- [Repository layout](#repository-layout)
- [Getting started](#getting-started)
  - [Option A — Docker Compose](#option-a--docker-compose-recommended)
  - [Option B — Local development](#option-b--local-development)
- [Environment variables](#environment-variables)
- [Database migrations](#database-migrations)
- [API overview](#api-overview)
- [Data model](#data-model)
- [Design notes](#design-notes)
- [Testing](#testing)
- [Roadmap](#roadmap)
- [Contributing](#contributing)
- [License](#license)

---

## Why RAGVault

Most "RAG demo" repos stop at a single script that embeds a PDF and prints an answer. RAGVault is the part that comes after the demo: the unglamorous plumbing that decides whether a retrieval system survives contact with real users.

That means a few deliberate choices:

- **Every document belongs to exactly one user.** Ownership is enforced in the query, not just the route, so one user's `document_id` is never another user's data.
- **Ingestion is idempotent.** A flaky network or a double-click cannot create duplicate documents. The client sends an `idempotency_key`; the server returns the existing job if it has seen it before.
- **Sessions rotate.** Access tokens are short-lived, refresh tokens are tracked server-side and revoked on logout, and the client silently refreshes once on a `401` before giving up.
- **Reading is paged by character, not by record.** A 500 KB document does not get loaded into memory to be displayed — the reader asks for windows of text, forwards and backwards.

The retrieval generation layer (embeddings, vector search, LLM answering) is intentionally scaffolded but not yet wired; see [Roadmap](#roadmap). The ingestion, storage, chunking, and job machinery it will sit on top of is here and tested.

---

## What works today

### Accounts & authentication
- Registration in two steps: request an OTP (`/user/request-create`), verify it and create the account (`/user/create`). OTPs are hashed with Argon2 before storage and expire on a configurable clock.
- Login with **username or email** (exactly one, enforced by validation).
- JWT access + refresh tokens. Refresh sessions are persisted with their `jti` and rotated near expiry; logout revokes the session server-side.
- Forgot-password and authenticated change-password flows, both OTP/old-password gated.
- `GET /user/me` returns the caller's own account details for the shell header.

### Documents & ingestion
- Upload `.txt`, `.csv`, and `.md` files up to 50 MB as multipart form data.
- Each upload creates an **ingestion job** (`pending` → `completed` / `failed`) with the client's idempotency key, unique per user.
- Content is split into overlapping character chunks (120-char window, 20-char overlap) and persisted in order for downstream retrieval.
- Paginated document listing that returns lightweight summaries — never the full text.
- Character-window document reading with `prev`/`next` navigation, so arbitrarily large documents stay cheap to view.
- Delete with cascade cleanup of a document's chunks and jobs.

### Platform & reliability
- Redis-backed fixed-window rate limiting for OTP requests, OTP verification attempts, and password changes.
- Celery worker with Redis as broker/backend for out-of-band email delivery (Brevo transactional API).
- A single, consistent error envelope across the API, with a mapping from database constraints to friendly, machine-readable error codes.
- Structured logging configured from a JSON `dictConfig`, with a safe fallback to `basicConfig`.

### Frontend
- Login/registration UI with OTP entry, forgot-password and change-password flows.
- Document dashboard: paginated list, drag-and-drop upload, delete with confirmation.
- A dedicated reader route with infinite scroll in **both** directions, scroll-anchored so prepending earlier text does not jump the viewport.
- Transparent token refresh: concurrent `401`s share a single in-flight refresh request instead of each rotating the token.
- Session persisted in `localStorage`; a failed background refresh automatically signs the user out.

---

## Architecture

```mermaid
flowchart TD
    SPA["React SPA<br/>(Vite · Tailwind)"]
    API["FastAPI<br/>/api/v1"]
    AUTH["User routes<br/>OTP · JWT · sessions"]
    DOCS["Document routes<br/>upload · list · read · delete"]
    PG[("PostgreSQL 18<br/>users · documents · chunks<br/>jobs · sessions · OTPs")]
    REDIS[("Redis 8<br/>rate limits · Celery")]
    CELERY["Celery worker"]
    BREVO["Brevo API<br/>transactional email"]

    SPA -->|"Bearer access token"| API
    API --> AUTH
    API --> DOCS
    AUTH --> PG
    DOCS --> PG
    AUTH --> REDIS
    AUTH --> CELERY
    DOCS --> CELERY
    CELERY --> REDIS
    CELERY -->|"send OTP email"| BREVO
```

The request path is synchronous: uploads create and complete their ingestion job inline. Celery exists for work that must not block a response — today that is OTP email delivery, which is the natural seam for moving chunking and future embedding work off the request path.

### Upload flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as API
    participant DB as PostgreSQL

    C->>API: POST /document/upload (file + idempotency_key)
    API->>DB: find job by (user_id, idempotency_key)
    alt job already exists
        DB-->>API: existing job
        API-->>C: 200 (no duplicate work)
    else new job
        API->>DB: insert job (pending)
        API->>DB: insert document + chunks
        API->>DB: mark job completed
        API-->>C: 200 (job + document_id)
    end
```

---

## Tech stack

| Layer | Choice | Notes |
| --- | --- | --- |
| Language | Python **3.14** | `requires-python = ">=3.14"` |
| API framework | FastAPI + Uvicorn | Async throughout, OpenAPI at `/docs` |
| ORM / DB | SQLAlchemy 2.0 (async) + asyncpg | Typed `Mapped[...]` models |
| Migrations | Alembic | `backend/alembic/` |
| Validation | Pydantic v2 + pydantic-settings | Request/response schemas and config |
| Auth | python-jose (JWT) + argon2-cffi | Access/refresh tokens, Argon2 password + OTP hashing |
| Cache / broker | Redis 8 | Rate limits, Celery broker/backend |
| Background work | Celery 5 | OTP email delivery |
| Email | Brevo HTTP API | `app/utils/send_email.py` |
| Frontend | React 19 + TypeScript 6 + Vite 8 | `frontend/` |
| Styling | Tailwind CSS 4 | Via `@tailwindcss/vite` |
| Client validation | Zod 4 | Mirrors backend rules |
| Testing | pytest + pytest-asyncio + httpx + Hypothesis + freezegun | Unit and integration suites |
| Lint/format | Ruff (backend), ESLint (frontend) | |

---

## Repository layout

```
RAGVault/
├── backend/
│   ├── app/
│   │   ├── api/            # routers and dependencies (token + upload validation)
│   │   ├── core/           # config, security, exceptions, logging
│   │   ├── db/             # async engine and session factory
│   │   ├── infrastructure/ # Redis client and rate limiting
│   │   ├── models/         # SQLAlchemy models
│   │   ├── repositories/   # data access, one module per aggregate
│   │   ├── schemas/        # Pydantic request/response contracts
│   │   ├── services/       # business logic (user, document, jobs, OTP, email)
│   │   ├── utils/          # chunking, email transport
│   │   ├── workers/        # Celery app
│   │   └── main.py         # app factory, CORS, exception handlers
│   ├── alembic/            # migration environment and versions
│   ├── tests/              # unit/ and integration/
│   └── alembic.ini
├── frontend/
│   └── src/
│       ├── api/            # fetch client, token store, endpoint wrappers
│       ├── components/     # forms, document list/reader, UI primitives
│       ├── context/        # AuthProvider, ToastProvider
│       ├── pages/          # LoginRegister, Dashboard, DocumentReader
│       ├── types/          # request/response contracts
│       └── utils/          # validation mirrors, formatting
├── compose.yaml            # backend, postgres, redis, celery
├── Dockerfile
├── pyproject.toml
└── package.json            # thin wrapper over the frontend scripts
```

---

## Getting started

**Prerequisites:** Docker and Docker Compose (recommended), or Python 3.14 + Node.js + a local PostgreSQL 18 and Redis 8 for the manual path.

Both paths need a `.env` at the repository root. See [Environment variables](#environment-variables); `backend/.env.example` is the starting point.

### Option A — Docker Compose (recommended)

```bash
cp backend/.env.example .env    # then fill in the secrets
docker compose up --build
```

Compose starts four services:

| Service | Image / build | Port | Role |
| --- | --- | --- | --- |
| `backend` | built from `Dockerfile` | `8000` | FastAPI app |
| `postgres` | `postgres:18` | internal | primary datastore |
| `redis` | `redis:8` | internal | rate limits + Celery |
| `celery` | same image as `backend` | — | OTP email worker |

Then run migrations inside the backend container:

```bash
docker compose exec backend alembic -c backend/alembic.ini upgrade head
```

The API is now at `http://localhost:8000`, with interactive docs at `http://localhost:8000/docs`.

Compose is set up for development: `app/` is synced into the container with a restart on change, and changes to `pyproject.toml` trigger a rebuild. Migration files are volume-mounted so editing them does not require a rebuild.

### Option B — Local development

**Backend**

```bash
python -m venv .venv
source .venv/bin/activate

pip install -e ".[dev]"          # installs the backend with dev tools

cd backend
alembic upgrade head             # apply migrations
uvicorn app.main:app --reload    # http://localhost:8000
```

**Celery worker** (separate terminal, for OTP email):

```bash
cd backend
celery -A app.workers.celery_app.celery_app worker --loglevel=info
```

**Frontend**

```bash
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

The backend already allows the Vite dev origin (`http://localhost:5173`) via CORS in `backend/app/main.py`. Point the client elsewhere with `VITE_API_BASE_URL` (see below).

---

## Environment variables

Settings are loaded by `pydantic-settings` from `.env` (override the file path with `ENV_FILE`). Compose additionally reads `POSTGRES_USER`, `POSTGRES_PASSWORD`, and `POSTGRES_DB` to configure the database container.

| Variable | Required | Description |
| --- | --- | --- |
| `POSTGRES_URL` | yes | Async SQLAlchemy DSN, e.g. `postgresql+asyncpg://user:pass@host:5432/db` |
| `JWT_SECRET_KEY` | yes | Signing key for access and refresh tokens |
| `JWT_ALGORITHM` | yes | JWT algorithm, e.g. `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | yes | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | yes | Refresh token lifetime; rotation kicks in as it approaches expiry |
| `REDIS_URL` | yes | Redis DSN used for rate limits and Celery |
| `OTP_EXPIRE_MINUTES` | yes | How long a verification code stays valid |
| `LOG_IN_ATTEMPTS` | yes | Max login / OTP-request attempts per window |
| `LOG_IN_BLOCK_WINDOW_SEC` | yes | Window length for login-related limits |
| `CREATE_ACCOUNT_ATTEMPTS` | yes | Max account-creation attempts per window |
| `CREATE_ACCOUNT_BLOCK_WINDOW_SEC` | yes | Window length for account-creation limits |
| `BREVO_API_KEY` | yes | Brevo API key for transactional email |
| `VERIFICATION_EMAIL` | yes | Sender address for OTP emails |
| `REGEX` | no | Allowed-character pattern for new passwords (has a default) |

Frontend configuration lives in `frontend/.env.local`:

| Variable | Default | Description |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `http://localhost:8000/api/v1` | Base URL of the API |

---

## Database migrations

Alembic is configured at `backend/alembic.ini` with scripts under `backend/alembic/`.

```bash
cd backend

alembic upgrade head                              # apply all migrations
alembic downgrade -1                              # roll back one revision
alembic revision --autogenerate -m "add table"    # generate from model changes
alembic current                                   # show the applied revision
```

Migrations are the source of truth for the real schema and should be applied before starting the app. Note that the Alembic connection URL is read from `backend/alembic.ini`, so keep its `sqlalchemy.url` in sync with your environment when running outside Compose.

---

## API overview

All routes are served under **`/api/v1`**. Protected routes expect `Authorization: Bearer <access_token>`.

### Users — `/api/v1/user`

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `POST` | `/request-create` | none | Send a registration OTP; returns `otp_id` and a `task_id` |
| `POST` | `/create` | none | Verify the OTP and create the account |
| `POST` | `/login` | none | Exchange username **or** email + password for tokens |
| `POST` | `/refresh-token` | refresh | Rotate/refresh; returns a new access token (and a new refresh token when rotating) |
| `POST` | `/logout` | refresh | Revoke the current session |
| `POST` | `/change-password` | access | Change password (requires the old one) |
| `POST` | `/request-forgot-password` | none | Send a reset OTP |
| `POST` | `/forgot-password` | none | Verify the OTP and set a new password |
| `GET` | `/me` | access | The caller's own account details |

### Documents — `/api/v1/document`

| Method | Path | Auth | Purpose |
| --- | --- | --- | --- |
| `POST` | `/upload` | access | Multipart upload; creates an ingestion job and the document |
| `POST` | `/get-all-documents` | access | Paginated list of the user's documents (summaries only) |
| `POST` | `/get-document` | access | Read a character window (`start`, `limit`, `prev`) |
| `POST` | `/delete?document_id=<uuid>` | access | Delete a document and its chunks |

### Examples

Log in and capture a token:

```bash
curl -s -X POST http://localhost:8000/api/v1/user/login \
  -H "Content-Type: application/json" \
  -d '{"user_name": "ada", "password": "Corr3ct@Horse"}'
```

Upload a markdown file idempotently:

```bash
curl -X POST "http://localhost:8000/api/v1/document/upload?file_name=Reading%20Notes" \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -F "text_file=@notes.md;type=text/markdown" \
  -F "idempotency_key=$(uuidgen)"
```

Read the first window, then continue forward:

```bash
curl -X POST http://localhost:8000/api/v1/document/get-document \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"id": "<document-uuid>", "start": 0, "limit": 5000, "prev": false}'
```

Errors always come back in one shape:

```json
{
  "error": {
    "code": 409,
    "error_code": "EMAIL_ALREADY_EXISTS",
    "message": "An account with this email already exists."
  }
}
```

---

## Data model

```mermaid
erDiagram
    USERS ||--o{ DOCUMENTS : owns
    USERS ||--o{ INGESTION_JOBS : runs
    USERS ||--o{ USER_SESSIONS : has
    USERS ||--o{ LLM_RUNS : triggers
    DOCUMENTS ||--o{ DOCUMENT_CHUNKS : "split into"
    DOCUMENTS ||--o{ INGESTION_JOBS : tracks
    DOCUMENTS ||--o{ LLM_RUNS : "answers about"

    USERS {
        uuid id PK
        string user_name UK
        string name
        string email UK
        text password
    }
    DOCUMENTS {
        uuid id PK
        uuid user_id FK
        string title
        text original_text
    }
    DOCUMENT_CHUNKS {
        uuid document_id PK
        int chunk_index PK
        text content
    }
    INGESTION_JOBS {
        uuid id PK
        uuid user_id FK
        uuid document_id FK
        string status
        uuid idempotency_key
    }
    USER_SESSIONS {
        uuid id PK
        uuid user_id FK
        uuid refresh_token_jti UK
        bool is_revoked
        datetime expires_at
    }
    LLM_RUNS {
        uuid id PK
        uuid user_id FK
        uuid document_id FK
        string model
        string status
    }
```

Highlights:

- **`document_chunks`** uses a composite primary key of `(document_id, chunk_index)`, so a document's chunks are inherently ordered and scoped.
- **`ingestion_jobs`** carries a unique `(user_id, idempotency_key)` constraint — the database, not the application, is the final guarantee against duplicates.
- **`user_sessions`** makes refresh tokens revocable: each row holds the refresh token's `jti`, its expiry, and a revocation flag.
- **`llm_runs`** is reserved for the retrieval/answer layer; the table exists so the model has somewhere to record prompts, responses, latency, and failures.
- Foreign keys cascade on delete and the ORM relationships mirror that, so deleting a user or document cleans up its dependents.

---

## Design notes

A few conventions worth knowing before you extend the codebase.

**Layered flow.** Routers stay thin and delegate to services; services contain the business rules; repositories own the SQL. Exception translation lives in the service layer so HTTP concerns never leak into the data layer.

**One error envelope.** `AppError` subclasses carry a public message, an internal message, a status code, and a machine-readable `error_code`. Registered handlers turn them — plus validation errors, HTTP exceptions, and unexpected failures — into the same JSON shape. Database integrity errors are mapped to friendly codes (for example a unique-constraint violation becomes `EMAIL_ALREADY_EXISTS` or `USERNAME_ALREADY_EXISTS`) by inspecting the constraint name.

**Idempotent ingestion.** The upload route requires an `idempotency_key`. The first request creates the job; retries find it by `(user_id, idempotency_key)` and return it untouched.

**Character-window reading.** Documents are read with SQL `substring` over the stored text rather than by fetching the column. The response reports `text_length`, `next_start`, and directional `has_next`/`has_prev` flags so the client can page in either direction without knowing the document's size up front.

**Chunking.** `app/utils/chunk_data.py` performs a fixed-stride overlapping split (120 characters with 20 characters of overlap). It is deterministic and dependency-free, which keeps ingestion fast and testable; swapping in token-aware chunking is a localized change.

**Transactions.** Services commit explicitly and roll back on `SQLAlchemyError`, translating the failure before re-raising. The request-scoped session dependency also rolls back on any unhandled exception and always closes the session.

**Client token handling.** The fetch client attaches the appropriate bearer token per request, and on a `401` for an access-token request it performs exactly one shared refresh-and-retry. Refresh is deduplicated through a single in-flight promise so a burst of concurrent failures does not rotate the token multiple times.

---

## Testing

Tests live in `backend/tests/`, split into `unit/` (schemas, security, utilities, handlers) and `integration/` (routes, services, ingestion lifecycle against a live database).

```bash
cd backend
pytest                       # run everything
pytest tests/unit            # fast, no external services
pytest tests/integration     # requires PostgreSQL + Redis
```

Integration tests reflect the schema directly from the SQLAlchemy metadata (they `create_all` a scratch database) and exercise the API through an in-process ASGI client, so they need a reachable PostgreSQL and Redis. The suite uses `Hypothesis` for property-based tests and `freezegun` for time-dependent paths.

Backend lint and format:

```bash
ruff check backend
ruff format backend
```

Frontend type-check, build, and lint:

```bash
npm run build    # tsc -b && vite build
npm run lint
```

---

## Roadmap

RAGVault's storage and ingestion spine is in place; the retrieval layer is the next chapter.

- [ ] **Embeddings** — generate vectors for each persisted chunk and store them for similarity search.
- [ ] **Vector retrieval** — semantic search over a user's chunks, scoped to the owning user.
- [ ] **Answer generation** — wire `llm_runs` to a model provider, recording prompt, response, latency, and failures.
- [ ] **Async ingestion** — move chunking and embedding into Celery so uploads return immediately and process in the background.
- [ ] **Streaming responses** — stream generated answers to the client as they are produced.
- [ ] **Richer formats** — PDF and DOCX ingestion behind the existing file-validation seam.
- [ ] **Sharper tests** — add end-to-end coverage against a live stack and expand the property-based suite.

---

## Contributing

Issues and pull requests are welcome. A good change here is small, layered, and tested:

1. Keep routers thin and put logic in services.
2. Raise `AppError` subclasses (or translate a database error) rather than returning ad-hoc errors.
3. Add a Pydantic schema for any new request/response shape.
4. If models change, generate an Alembic revision and include it.
5. Run `ruff` and `pytest` before opening the PR.

---

## License

Released under the [MIT License](LICENSE). © 2026 Lucky Dubey.
