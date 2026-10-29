import os
from datetime import date

from sqlalchemy import JSON, Date, String, UniqueConstraint, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Recommendation(Base):
    __tablename__ = "recommendations"
    __table_args__ = (UniqueConstraint("user_id", "local_date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True)
    local_date: Mapped[date] = mapped_column(Date)
    context: Mapped[dict] = mapped_column(JSON)
    decision: Mapped[dict] = mapped_column(JSON)
    feedback: Mapped[dict | None] = mapped_column(JSON, nullable=True)


def make_engine(url: str):
    options = {"check_same_thread": False} if url.startswith("sqlite") else {}
    return create_engine(url, connect_args=options, pool_pre_ping=True)


engine = make_engine(os.getenv("DATABASE_URL", "sqlite:///./centered.db"))
SessionFactory = sessionmaker(engine, expire_on_commit=False)


def get_session():
    with SessionFactory() as session:
        yield session
