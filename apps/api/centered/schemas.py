from typing import Literal
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CheckIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    timezone: str = "UTC"
    available_minutes: int = Field(ge=1, le=120)
    energy: int | None = Field(default=None, ge=1, le=5)
    stress: int | None = Field(default=None, ge=1, le=5)
    sleep_hours: float | None = Field(default=None, ge=0, le=24, allow_inf_nan=False)
    allow_movement: bool = True

    @field_validator("timezone")
    @classmethod
    def valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError):
            raise ValueError("Use an IANA timezone such as America/Chicago") from None
        return value


class Feedback(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["completed", "skipped"]
    helpful: bool | None = None
    effort: int | None = Field(default=None, ge=1, le=5)
    reason: Literal["no_time", "unsuitable", "not_interested", "other"] | None = None
