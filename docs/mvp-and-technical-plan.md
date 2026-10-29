# Centered — MVP and Technical Plan v1

Date: October 29, 2026
Status: Implementation baseline under delegated product/technical ownership. Provider approvals, evidence review and pilot results remain release gates, not completed work.

## 1. Product commitment

Help adults choose one achievable, evidence-backed wellbeing action today. Support working professionals with and without wearables at launch. Manual context is a first-class source. Actual wellbeing improvement is the mission outcome; completion, usefulness and retention are supporting signals.

The owner has delegated product and technical planning. Learning exercises are outside this implementation plan. The supplied Vision v3.0 and five-persona workbook remain source documents; this plan records clarified decisions without overwriting them. Existing implementation references are unverified until the repository is inspected.

## 2. MVP scope

Launch as an invitation-only adult wellness pilot, with iOS and Android clients and one shared backend. Web marketing and account support can follow; a browser-only app cannot deliver the intended on-device health integrations.

Included:
- Account creation, consent, timezone, preferences, accessibility needs, available time, and user-declared activity limitations.
- Manual daily context: perceived sleep quality/duration, energy, mood, stress, available time, and optional recent activity. Answering a brief check-in must be enough to receive guidance without connecting anything.
- Optional read-only Apple HealthKit and Android Health Connect integrations, initially for steps, sleep sessions and exercise sessions. No promise that every vendor exports every metric.
- One daily recommendation with duration, manageable alternative, personal rationale, evidence link/tier, and a clear description of missing or stale context.
- Complete, skip, replace, and report-unsuitable actions. Replacements remain explicit and versioned; no silent changes to today's action.
- A short usefulness/effort response and periodic wellbeing feedback, plus history.
- Connection status, last sync, per-source permissions, disconnect, data export and account deletion.
- Private internal evidence/action review and support operations, audited and access-controlled.

Deferred: direct integrations with every wearable vendor, automatic calendar and weather connections, nutrition plans, GPS routes, physiological readiness scores, clinical data, diagnosis/treatment, social features, streaks, open-ended AI chat, autonomous coaching agents, continuously changing recommendations, model training and payments.

Calendar constraints are captured as user-entered availability at first. Recommendations must not claim to know calendar events or local weather before those integrations exist.

## 3. First user journey

1. Explain the one-action promise and optional data connections.
2. Create account, collect minimal preferences and limitations, record baseline wellbeing.
3. Offer a health connection or continue without one. Do not block on permissions.
4. Collect today's brief context, allowing unknown answers.
5. Select one eligible action and explain which inputs influenced it.
6. User accepts, replaces or skips; collect an optional reason.
7. Record completion and perceived usefulness/effort without guilt or streak pressure.
8. Ask for a weekly wellbeing check-in and show descriptive trends without asserting causation.

Initial action families: gentle movement, brief restorative breaks, sleep-support routines, and low-effort relaxation. Each concrete action requires reviewed evidence, population applicability, limitations and exclusion rules before activation. No generated evidence citations or assumed individual benefit claims.

## 4. Integration strategy and verified constraints

| Source | Decision | Release condition |
|---|---|---|
| Manual check-ins | Required in first vertical slice and launch | Standalone experience works with no wearable |
| Apple HealthKit | Primary iOS connection | Device validation, permissions, sync and store readiness |
| Android Health Connect | Primary Android connection | Device availability handling, permissions, sync and store readiness |
| Google Fit APIs | Do not start a new dependency | Official Android page says support ends at end of 2026; use recommended migration direction |
| Strava | Planned direct adapter, not a dependency for initial pilot | Review current agreement, app access/capacity and permitted recommendation use; no model training or LLM processing without an established permitted basis |
| Other vendors | Reach through platform stores where they export data; direct adapters later | Verify each advertised device/data-type combination; never market universal coverage |

HealthKit requires an entitled Apple-platform app and user authorization. Health Connect is an Android integration, not a generic server-side OAuth health feed. A phone client reads authorized data and submits minimal normalized records to Centered. Background execution is OS-controlled; stale data must remain visible and manual input must remain available.

Strava's official API update distinguishes coaching use cases from restrictions around AI/model training; the wording does not establish permission for our eventual processing design. Its full current agreement and app-specific approvals must be checked before implementation. Do not route restricted source data through another provider to evade restrictions.

## 5. Architecture decisions

Use a modular monolith: one FastAPI codebase, one PostgreSQL database, and a worker process from the same codebase. Modules: identity/consent, ingestion, context, action/evidence catalog, recommendation, feedback/outcomes and account lifecycle.

Mobile: React Native with TypeScript and native Swift/Kotlin bridges for health access. Reuse shared application screens; validate health-library maintenance and OS compatibility in the integration spike before selecting a wrapper. No need to build two independent UI codebases. Framework/package versions are pinned during scaffolding after a compatibility check.

Backend: Python 3.12 baseline, FastAPI, typed request/response models, SQLAlchemy and Alembic. No existing code exists; create a fresh SQLAlchemy schema and migrations. REST with versioned endpoints and generated OpenAPI contracts.

Persistence and jobs: PostgreSQL owns transactional data and a durable jobs table. Worker claims jobs with locking, retries with backoff, records failures and supports idempotency. No Redis, broker, vector database, Kubernetes or microservices initially. Add infrastructure only for measured needs.

Authentication: standards-based managed OIDC identity, authorization-code flow with PKCE on mobile, backend token verification and strict user ownership checks. Exact vendor and hosting account selection occur before provisioning; no invented account availability or zero-cost assumption.

Deployment topology: containerized API and worker, managed PostgreSQL, managed secrets, TLS and a single US region for the initial US pilot. Separate staging and production; automated migration and rollback procedure. Hosting vendor/cost commitment remains pending an account and budget check. Native distribution uses pilot testing channels before public stores.

## 6. Data model and contracts

| Entity | Essential contents |
|---|---|
| User/Profile | Auth subject, timezone, preferences, availability, declared limitations |
| Consent | Source, data types/purpose, policy version, grant/revocation timestamps |
| Connection | Platform/provider, state, sync cursor, last successful sync, permitted uses |
| Observation | User, metric/type, value/unit, interval, source record ID, origin device/app, received time, source revision/deletion |
| DailyContext | Local date, manual answers, input freshness, versioned feature snapshot |
| Action/Evidence | Reviewed action, duration, exclusions, applicable population, source URL, evidence assessment, review/version status |
| Recommendation | Local date, selected action version, context snapshot, policy version, reasons, suitability limitations, status, replacement history |
| Feedback/Outcome | Completion/skip reason, usefulness, effort, daily feelings and periodic wellbeing response |
| Job/AuditEvent | Retry state/idempotency, consent/access/deletion events; no sensitive payloads in operational logs |

Suggested API surface: profile; consents/connections; observations batch-upsert and deletion; daily check-in; today's recommendation; recommendation feedback/replacement; wellbeing check-ins; history; export/delete account. Endpoint ownership is derived from the authenticated identity, never trusted from submitted user IDs.

Observation batches and feedback require idempotency keys. Recommendation creation has an atomic unique constraint on user/local-date/active generation, preventing duplicate recommendations from concurrent requests. Replacement is a transaction preserving history. Persist timestamps in UTC with source offsets and evaluate local days using the user's timezone, including daylight-saving transitions.

Do not sum overlapping step totals from different sources. Select a preferred origin per metric/time interval; preserve provenance and confidence in matching. Match duplicate workouts conservatively using origin identifiers and interval/type attributes. Account for provider corrections/deletions. Avoid comparing HRV or proprietary scores across devices in the MVP.

## 7. Recommendation engine

Start deterministic and testable. No LLM is required for selection or explanation.

Pipeline:
1. Validate inputs and permission for the intended use.
2. Resolve duplicates, freshness, units and missingness. Missing data is unknown, not zero.
3. Build a versioned daily context.
4. Filter reviewed actions by limitations, available time, accessibility and explicit preferences.
5. Rank eligible actions using transparent context-fit, evidence applicability, effort and recent feedback rules.
6. Select one; store considered inputs, exclusion reasons, action/evidence/policy versions and tie-breaking decision.
7. Render an explanation from reviewed templates referencing only actual available inputs.

Initial ranking is a heuristic suitability policy, not a clinically calibrated estimate of greatest wellbeing benefit. Tune after observing pilot data. Evidence quality, personal applicability and input completeness are separate concepts. Avoid confidence percentages or impact stars until validated. When no action is suitable, explain the limitation and request optional context rather than inventing a recommendation.

Users can request a lower-effort alternative or correct context. Recommendations do not change mid-day merely because a sync completes. New data can affect an explicitly requested replacement or the next day.

## 8. Outcome measurement and adaptation

Record baseline and a weekly repeat of the same brief wellbeing questions, tracking response completeness and participation time. The pilot can start with plainly labeled self-reported energy, stress and overall wellbeing questions; do not describe an unvalidated composite as a clinical instrument. Choose a validated instrument and verify usage/scoring terms before making validated-measure claims.

Mission reporting: within-person reported wellbeing change over several weeks, with sample size, missing data, uncertainty and wearable/no-wearable cohorts. Product reporting: helpfulness, feasibility, completion, replacement/skip reasons and time burden. Retention is a business signal.

Sensor changes are contextual and supporting outcomes, not proof that wellbeing improved or that Centered caused it. Distinguish association from causal effect; a future controlled evaluation is needed for causal claims. Compare cohorts descriptively and account for baseline differences rather than asserting parity from raw completion rates.

Adaptation in MVP means honoring stated preferences, recording unsuitable actions and adjusting explicit policy rules through review. No automatic population-wide learning from health data. Research/model training, if introduced later, requires separate purpose/consent and provider-policy review.

## 9. Privacy, reliability and release gates

Minimize cloud upload to approved record types and granularity. Do not upload full health-store exports, precise location or medical records. Encrypt transport/storage, isolate production access, protect secrets and tokens, and redact health data from telemetry. Verify user ownership on every read and mutation; audit privileged access.

Proposed retention defaults: transient ingestion payloads are discarded after normalization; normalized observations retained 90 days; recommendation/feedback history retained up to 12 months while active; document and test deletion and backup expiry before pilot. These are product decisions to validate against provider terms and applicable requirements, not legal conclusions. Disconnect stops future sync; deletion is a separate clearly offered control.

Release gates:
- Complete and useful manual-only journey; no fabricated source context.
- Real-device iOS/Android permission grant, partial grant, denial/revocation, stale sync, retries and duplicate ingestion validated.
- All enabled actions have evidence review and suitability/exclusion tests.
- Cross-user access tests, export/delete and restore/backup-expiry procedure validated.
- Every recommendation reproducible from its recorded versions and snapshot.
- Original five personas covered by acceptance scenarios: dense day, conflicting tracked data, no wearable, low energy/burnout, weak evidence.
- Internal pilot exposes feasibility/trust issues before wider beta. Launch does not require a claimed wellbeing effect that has not been measured.

## 10. Delivery sequence

| Milestone | Deliverable | Exit condition |
|---|---|---|
| 0. Inventory and integration spikes | Create fresh repository and baseline tests; validate HealthKit/Health Connect on devices; check provider and evidence access | Reuse decisions and permission/data availability matrix documented |
| 1. Manual vertical slice | Sign-in, check-in, reviewed catalog, one recommendation, feedback, stored history | End-to-end flow and ownership tests pass |
| 2. Health ingestion | Native bridges, consent, normalization, provenance, deduplication, sync status | Real-device and replay/correction tests pass |
| 3. Outcomes and lifecycle | Baseline/weekly feedback, export/delete, internal review and monitoring | Measurement and lifecycle gates pass |
| 4. Invitation pilot | Staging/production deployment and pilot distribution | Review trust, burden and suitability findings; fix blockers |
| 5. Broader beta | Expand evidence coverage and integrations based on observed gaps | Verified supported-source matrix and operational readiness |

No reliable calendar estimate until repository/device/account access and the health spikes establish actual scope. Provider approval and store review are external dependencies. Direct Strava/vendor connectors can proceed independently after their access and usage gates pass.

## 11. Immediate execution boundary

This document finalizes MVP behavior and the logical architecture. The project starts fresh in https://github.com/deepakthota/centered; milestone 0 no longer requires a legacy-code inventory. Source repository identity/access, developer signing accounts, authentication/hosting accounts and a spend ceiling are outstanding execution inputs, not assumed decisions. No production service or paid resource has been provisioned by creating this plan.

## 12. Research sources

Retrieved October 29, 2026; official documentation unless noted.
- Apple HealthKit: https://developer.apple.com/documentation/healthkit
- Apple authorization requirements: https://developer.apple.com/documentation/healthkit/authorizing-access-to-health-data
- Android Health Connect (includes Google Fit support through end of 2026): https://developer.android.com/health-and-fitness/health-connect
- Strava official API update and coaching/training clarification: https://press.strava.com/articles/updates-to-stravas-api-agreement

The historical Google Fit deprecation URL returned 404; the Android Health Connect page supplied the current support statement. Strava's press clarification is not a substitute for its current binding API agreement, which remains a connector release gate.
