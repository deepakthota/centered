# Implementation status

## Delivered in the first increment

- Empty-repository setup with independent API/mobile dependencies and lockfiles.
- Persistent manual check-in and versioned deterministic development decision.
- One active record per user/local date enforced by a database constraint.
- Daily retry handling, completed/skipped feedback, and owned history.
- SQLite for low-friction local work; PostgreSQL configuration and Alembic migration.
- React Native screen for local API connection, check-in, action, feedback and history.
- Development-token authentication, fail-closed production mode, no health-data request logging.
- Regression tests for validation, missing vs zero inputs, ownership, retries, feedback, local date and startup gates.

## Deliberately incomplete

This is a development vertical slice, not a production MVP. The sample action catalog is unreviewed; policy scores are not calibrated clinical benefit estimates. No evidence or confidence claims should be made. There is one local test identity per API instance, not multi-user sign-in.

Pending: OIDC, profiles/consent, reviewed evidence, action replacement/input correction, baseline/weekly outcomes, health connections, durable sync jobs, export/delete, support audit tooling, retention enforcement, provider approvals, native builds and deployment. No real user-health-data pilot until those gates are met.

## Testing boundaries

Backend tests exercise persistence in a fresh database and the PostgreSQL CI job uses the same contracts. Mobile lint/type checking and bundle export verify code integration, not visual layout or real-device behavior. Docker and native execution require their respective runtimes. Check the PR's CI result for hosted validation; do not infer a CI pass from the presence of a workflow.

## Source references

Implementation references consulted:
- FastAPI relational database/session guidance: https://fastapi.tiangolo.com/tutorial/sql-databases/
- Expo SDK 58: https://docs.expo.dev/versions/v58.0.0/
- Expo Router installation: https://docs.expo.dev/router/installation/

The product is based on the supplied Centered Vision v3.0 and persona workbook, plus clarified inclusion of non-wearable users and actual wellbeing as the mission outcome. Their original files remain separate; the repository contains the technical implementation plan.
