# Centered

One achievable wellbeing action for today, with transparent reasoning and optional wearable context.

**Status: first development slice.** The manual check-in → daily action → feedback → history flow is implemented. Sample actions are **not evidence-reviewed**. Use synthetic inputs only. This is not a launched wellness product.

## Repository

```
apps/api/       FastAPI, SQLAlchemy, Alembic, pytest
apps/mobile/    React Native, Expo Router, TypeScript
docs/          Product decisions, architecture and implementation status
compose.yaml   Local PostgreSQL and API
```

## Run the API

Requires Python 3.12+ and [uv](https://docs.astral.sh/uv/). From `apps/api`:

```bash
uv sync --frozen
export CENTERED_DEV_TOKEN="$(python -c 'import secrets; print(secrets.token_hex(32))')"
uv run alembic upgrade head
uv run uvicorn centered.main:app --host 127.0.0.1 --port 8000 --no-access-log
```

The default database is local SQLite. Swagger UI: http://127.0.0.1:8000/docs. Use the generated development token with the **Authorize** button. Do not commit it. All authenticated development requests belong to one local test identity. Production mode deliberately refuses to start until real authentication and evidence gates are implemented.

### PostgreSQL with Docker

From the repository root, copy `.env.example` to `.env` and fill both values with independent random hex strings of at least 32 characters. Then:

```bash
docker compose up --build
```

The migration service applies Alembic migrations before the API starts. PostgreSQL is private to the Compose network; the API binds to host loopback. Data survives container restarts in the named volume. `docker compose down` preserves it.

## Run the mobile client

Use the Node version recorded in `apps/mobile/.nvmrc`. From `apps/mobile`:

```bash
npm ci
npm start
```

Open in a compatible Expo Go app/simulator. Enter the API address and the development token generated above. The token is held only in application memory and cleared when disconnected; it is not embedded in the mobile bundle.

- iOS simulator on the API's Mac host: `http://127.0.0.1:8000`.
- Android emulator on the API host: `http://10.0.2.2:8000`.
- Physical devices need a reachable development endpoint; phone loopback refers to the phone itself. The default loopback binding is intentionally not reachable from a phone. Use a trusted HTTPS development tunnel if testing there.

Manual input and history are functional. HealthKit/Health Connect are **not connected**. Native health integrations will require development builds rather than Expo Go. Web is not a supported client in this increment. Mobile execution still needs simulator/device validation; a TypeScript check alone is not device testing.

## API contracts

All `/v1` endpoints require `Authorization: Bearer <development-token>`.

| Method | Endpoint | Behavior |
|---|---|---|
| GET | `/health` | Process liveness; no health data |
| POST | `/v1/check-ins` | Validate context and persist one action for the user's local date |
| GET | `/v1/history` | Most recent 90 days for authenticated identity |
| PUT | `/v1/recommendations/{id}/feedback` | Record completed/skipped and optional helpfulness/effort |

Check-in example:

```json
{
  "timezone": "America/Chicago",
  "available_minutes": 10,
  "energy": 2,
  "stress": null,
  "sleep_hours": null,
  "allow_movement": false
}
```

Energy/stress accept 1–5 or null; unknown sleep is null, not zero. Identical daily retries return the existing record. Changing an already-created day's inputs returns 409 rather than silently replacing it. Identical feedback retries are safe; conflicting feedback returns 409. Explicit replacement/correction remains a later milestone. With one available minute, the demo catalog returns no suitable action and does not permit completion feedback.

## Verification

From `apps/api`:

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run alembic upgrade head
uv run alembic check
```

From `apps/mobile`:

```bash
npm run typecheck
npm run lint
```

CI additionally runs API tests against an isolated PostgreSQL service. `TEST_DATABASE_URL` is for a **disposable test database only**: the fixture drops/recreates test tables. Never point it at any valuable data.

## Next milestones

1. Managed OIDC sign-in, user profile/consent and reviewed action/evidence catalog.
2. Explicit correction/replacement, wellbeing baseline/weekly feedback, export and deletion.
3. HealthKit/Health Connect permission and sync spikes, normalization, provenance and deduplication.
4. Real-device validation and invitation pilot after release gates pass.

See [implementation status](docs/implementation-status.md) and [MVP plan](docs/mvp-and-technical-plan.md). No hosting, paid resources or public application deployment is configured.
