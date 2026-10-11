from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, field_validator


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=12)
    password: str = Field(min_length=4, max_length=15)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=12)
    password: str | None = Field(default=None, min_length=4, max_length=15)


class UserResponse(BaseModel):
    id: int
    username: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


Preference = Annotated[str, Field(min_length=1, max_length=50)]


class UserPreferencesUpdate(BaseModel):
    preferences: list[Preference] = Field(default_factory=list, max_length=30)

    @field_validator("preferences")
    @classmethod
    def normalize_preferences(cls, preferences: list[str]) -> list[str]:
        cleaned = [preference.strip() for preference in preferences]
        if any(not preference for preference in cleaned):
            raise ValueError("As preferências não podem estar vazias.")
        return list(dict.fromkeys(cleaned))

    model_config = ConfigDict(extra="forbid")


class UserPreferencesResponse(BaseModel):
    preferences: list[str]


class UserInDB(BaseModel):
    hashed_password: str
