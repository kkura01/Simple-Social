"""Pydantic schemas for posts and fastapi-users request/response bodies."""

from pydantic import BaseModel
from fastapi_users import schemas
import uuid


class PostCreate(BaseModel):
    """Payload for creating a text-only post (unused by the current upload route)."""

    title: str
    content: str


class PostResponse(BaseModel):
    """Serialized post for API responses (unused by the current feed route)."""

    title: str
    content: str


class UserRead(schemas.BaseUser[uuid.UUID]):
    """Public user fields returned after register, verify, and /users calls."""


class UserCreate(schemas.BaseUserCreate):
    """Registration body: email, password, and optional flags."""


class UserUpdate(schemas.BaseUserUpdate):
    """Partial update body for the current user."""
