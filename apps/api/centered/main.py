import os
import secrets
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated
from uuid import uuid4
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import Recommendation, get_session
from .decision import choose_action
from .schemas import CheckIn, Feedback

bearer = HTTPBearer(auto_error=False)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Deliberately fail closed until production OIDC and evidence review exist.
    if os.getenv("CENTERED_ENV", "development") not in {"development", "test"}:
        raise RuntimeError("Production mode is unavailable in this development slice")
    if len(os.getenv("CENTERED_DEV_TOKEN", "")) < 24:
        raise RuntimeError("Set CENTERED_DEV_TOKEN to a random value of at least 24 characters")
    yield


app = FastAPI(title="Centered development API", version="0.1.0", lifespan=lifespan)


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> str:
    expected = os.getenv("CENTERED_DEV_TOKEN", "")
    if (
        len(expected) < 24
        or credentials is None
        or not secrets.compare_digest(credentials.credentials.encode(), expected.encode())
    ):
        raise HTTPException(401, "Authentication required", headers={"WWW-Authenticate": "Bearer"})
    return "local-developer"


User = Annotated[str, Depends(current_user)]
DB = Annotated[Session, Depends(get_session)]


def now() -> datetime:
    return datetime.now(UTC)


def serialize(row: Recommendation) -> dict:
    return {
        "id": row.id,
        "local_date": row.local_date.isoformat(),
        "context": row.context,
        "decision": row.decision,
        "feedback": row.feedback,
    }


@app.get("/health")
def health():
    return {"status": "ok", "stage": "development"}


@app.post("/v1/check-ins")
def check_in(context: CheckIn, user: User, db: DB):
    today = now().astimezone(ZoneInfo(context.timezone)).date()
    existing = db.scalar(
        select(Recommendation).where(
            Recommendation.user_id == user, Recommendation.local_date == today
        )
    )
    payload = context.model_dump()
    if existing:
        if existing.context != payload:
            raise HTTPException(
                409, "Today's action already exists; context changes are not supported yet"
            )
        return serialize(existing)
    row = Recommendation(
        id=str(uuid4()),
        user_id=user,
        local_date=today,
        context=payload,
        decision=choose_action(context),
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(Recommendation).where(
                Recommendation.user_id == user, Recommendation.local_date == today
            )
        )
        if existing and existing.context == payload:
            return serialize(existing)
        raise HTTPException(
            409, "A daily action was created concurrently; refresh history"
        ) from None
    return serialize(row)


@app.get("/v1/history")
def history(user: User, db: DB):
    rows = db.scalars(
        select(Recommendation)
        .where(Recommendation.user_id == user)
        .order_by(Recommendation.local_date.desc())
        .limit(90)
    )
    return [serialize(row) for row in rows]


@app.put("/v1/recommendations/{recommendation_id}/feedback")
def feedback(recommendation_id: str, body: Feedback, user: User, db: DB):
    row = db.scalar(
        select(Recommendation).where(
            Recommendation.id == recommendation_id, Recommendation.user_id == user
        )
    )
    if row is None:
        raise HTTPException(404, "Recommendation not found")
    if row.decision["action"] is None:
        raise HTTPException(409, "There is no action to complete or skip")
    payload = body.model_dump()
    # Conditional write prevents simultaneous, conflicting feedback overwrites on both databases.
    db.execute(
        update(Recommendation)
        .where(
            Recommendation.id == recommendation_id,
            Recommendation.user_id == user,
            Recommendation.feedback.is_(None),
        )
        .values(feedback=payload)
        .execution_options(synchronize_session=False)
    )
    db.commit()
    db.refresh(row)
    if row.feedback != payload:
        raise HTTPException(409, "Feedback is already recorded")
    return serialize(row)
