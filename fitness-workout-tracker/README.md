# Fitness Workout Tracker API

A REST API for planning workouts, scheduling them, and tracking strength progress
over time. Built with FastAPI, SQLAlchemy, and JWT authentication.

Project brief: https://roadmap.sh/projects/fitness-workout-tracker

## Features

- **JWT authentication** — sign up, log in, bcrypt-hashed passwords
- **Exercise catalogue** — 22 seeded exercises across cardio, strength, and flexibility
- **Workout management** — build workouts from multiple exercises with sets, reps, and weight
- **Scheduling** — schedule workouts for a date and time; list upcoming ones sorted by date
- **Progress reports** — training volume, per-exercise breakdowns, and progression over time
- **Strict ownership** — users can only ever access their own workouts
- **Auto-generated OpenAPI docs** at `/docs`
- **49 unit tests** covering auth, CRUD, validation, reports, and access control

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Framework | FastAPI | Auto-generates OpenAPI docs; validation built in |
| ORM | SQLAlchemy 2.x | Database-agnostic; swap SQLite for Postgres with one env var |
| Database | SQLite | Zero setup, still a real relational database |
| Auth | PyJWT + bcrypt | Stateless tokens; one-way password hashing |
| Validation | Pydantic v2 | One schema does validation, docs, and response filtering |
| Tests | pytest | Fixtures make per-test isolation cheap |

## Quick start

```bash
git clone https://github.com/lmcuong199/Backend.git
cd Backend/fitness-workout-tracker

python -m venv .venv
# Windows:
.\.venv\Scripts\Activate.ps1
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
python -c "import secrets; print(secrets.token_urlsafe(32))"   # paste as JWT_SECRET

python -m app.seed            # create tables + load the exercise catalogue
uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs**.

## Data model

```
users                exercises
  id                   id
  email (unique)       name (unique)
  hashed_password      description
  created_at           category        (cardio / strength / flexibility)
                       muscle_group    (chest / back / legs / ...)
     |                     |
     | owns                | referenced by
     v                     v
workouts  ---------->  workout_exercises
  id                     id
  user_id (FK)           workout_id  (FK)
  name                   exercise_id (FK)
  scheduled_at           sets
  status                 reps
  comment                weight
  created_at             position
```

A workout and an exercise are many-to-many, but the pairing carries its own data
(*3 sets x 8 reps at 60 kg*), so `workout_exercises` is a table with columns rather
than a plain join table.

## API reference

All timestamps are UTC. Any offset you send is converted (`18:00+07:00` is stored as `11:00Z`).

### Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/auth/signup` | - | Create an account. `409` if the email exists |
| POST | `/auth/login` | - | Exchange credentials for a JWT (valid 60 min) |
| GET | `/auth/me` | Bearer | The current user |
| POST | `/auth/logout` | Bearer | Client-side logout; discard the token |

### Exercises (public)

| Method | Path | Description |
|---|---|---|
| GET | `/exercises` | List the catalogue. `?category=`, `?muscle_group=`, `?search=` |
| GET | `/exercises/{id}` | One exercise |

### Workouts (authenticated)

| Method | Path | Description |
|---|---|---|
| POST | `/workouts` | Create a workout with its exercises |
| GET | `/workouts` | Your workouts, by date, unscheduled last. `?status=`, `?upcoming=true` |
| GET | `/workouts/{id}` | One workout |
| PATCH | `/workouts/{id}` | Update any subset of fields |
| DELETE | `/workouts/{id}` | Delete it and its entries |

### Reports (authenticated)

| Method | Path | Description |
|---|---|---|
| GET | `/reports/summary` | Totals and status breakdown. `?date_from=`, `?date_to=` |
| GET | `/reports/exercises` | Per-exercise stats, highest volume first |
| GET | `/reports/progress/{exercise_id}` | Chronological history for one exercise |

## Example walkthrough

```bash
# 1. Sign up
curl -X POST localhost:8000/auth/signup \
  -H "Content-Type: application/json" \
  -d '{"email":"lifter@example.com","password":"supersecret1"}'

# 2. Log in and keep the token
TOKEN=$(curl -s -X POST localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"lifter@example.com","password":"supersecret1"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 3. Find some exercises
curl "localhost:8000/exercises?category=strength"

# 4. Create a workout
curl -X POST localhost:8000/workouts \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
    "name": "Push Day",
    "scheduled_at": "2026-08-20T18:00:00+07:00",
    "comment": "Go lighter on shoulders",
    "entries": [
      {"exercise_id": 1, "sets": 4, "reps": 8, "weight": 60},
      {"exercise_id": 10, "sets": 3, "reps": 10, "weight": 30},
      {"exercise_id": 14, "sets": 3, "reps": 1, "weight": null}
    ]
  }'

# 5. Mark it done
curl -X PATCH localhost:8000/workouts/1 \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"status":"completed"}'

# 6. See your progress
curl "localhost:8000/reports/progress/1" -H "Authorization: Bearer $TOKEN"
```

Sample response from step 4:

```json
{
  "id": 1,
  "name": "Push Day",
  "scheduled_at": "2026-08-20T11:00:00Z",
  "status": "pending",
  "comment": "Go lighter on shoulders",
  "created_at": "2026-08-14T09:12:44Z",
  "entries": [
    {
      "id": 1, "exercise_id": 1, "sets": 4, "reps": 8, "weight": 60.0, "position": 0,
      "exercise": {
        "id": 1, "name": "Bench Press", "category": "strength",
        "muscle_group": "chest", "description": "Barbell press from a flat bench."
      }
    }
  ]
}
```

## Design notes

**Ownership is enforced in the SQL `WHERE` clause**, not by an `if` after loading.
There is no code path that fetches a workout without also filtering on `user_id`,
so the check cannot be forgotten.

**Other users' workouts return `404`, not `403`.** A `403` confirms the resource
exists, letting someone enumerate IDs. Login errors are identical for "wrong
password" and "unknown email" for the same reason.

**Timestamps go through a custom `UtcDateTime` column type.** SQLite silently
discards timezone offsets, so `18:00+07:00` would be stored as `18:00` and read
back as UTC — a 7-hour error. The type converts to UTC on write and re-attaches
UTC on read.

**Training volume is `sets x reps x weight`**, with `NULL` weight coalesced to `0`
so bodyweight exercises don't turn an entire `SUM` into `NULL`.

**Reports count only `completed` workouts.** A planned workout isn't progress.

**bcrypt rounds are configurable** via `BCRYPT_ROUNDS`, defaulting to a secure 12.
The test suite sets 4, which took the suite from 96s to 18s.

## Testing

```bash
pytest              # 49 tests
pytest -v           # one line per test
pytest -k ownership # only access-control tests
```

Tests run against a throwaway database in a temp directory — `conftest.py` sets
`DATABASE_URL` before the app is imported, and every test starts from a wiped,
freshly seeded schema.

## Project structure

```
fitness-workout-tracker/
  app/
    main.py         FastAPI app, OpenAPI metadata, router registration
    database.py     engine, session factory, UtcDateTime, FK pragma
    models.py       SQLAlchemy tables
    schemas.py      Pydantic request/response shapes
    security.py     bcrypt hashing, JWT create/decode
    deps.py         get_current_user - the auth gate
    seed.py         exercise catalogue seeder (idempotent)
    routers/
      auth.py       signup, login, me, logout
      exercises.py  public catalogue
      workouts.py   CRUD + ownership
      reports.py    aggregation queries
  tests/            49 pytest tests
  requirements.txt
  pytest.ini
```

## Possible improvements

- Alembic migrations instead of `create_all`
- Refresh tokens and a denylist so logout revokes server-side
- Pagination on `/workouts` and `/exercises`
- Estimated 1-rep-max in reports (Epley: `weight * (1 + reps / 30)`)
- Postgres via docker-compose (one env var change)
