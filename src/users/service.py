from fastapi import HTTPException, status
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from users.models import User, UserPreference
from publication.models import Publication
password_hash = PasswordHash.recommended()


async def create_user_service(
    *, db: AsyncSession, username: str, password: str
) -> User:
    result = await db.execute(select(User).where(User.username == username))
    if result.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username já está em uso."
        )

    new_user = User(username=username, password=password_hash.hash(password))
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def list_users_service(*, db: AsyncSession, skip: int = 0, limit: int = 10):
    result = await db.execute(select(User).offset(skip).limit(limit))
    return result.scalars().all()


async def get_user_service(*, db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalars().first()


async def update_user_service(
    *, db: AsyncSession, user: User, username: str | None, password: str | None
) -> User:
    if username is not None:
        user.username = username
    if password is not None:
        user.password = password_hash.hash(password)

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user_service(*, db: AsyncSession, user: User) -> None:
    user.is_active = False
    await db.commit()

async def get_user_by_publication(
    *, 
    db: AsyncSession, 
    publication_id: int
) -> Optional[User]:
    # Faz o JOIN no banco e retorna direto o autor da publicação
    stmt = (
        select(User)
        .join(Publication, Publication.user_id == User.id)
        .where(Publication.id == publication_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_user_preferences_service(
    *, db: AsyncSession, user_id: int
) -> list[str]:
    preferences = await db.get(UserPreference, user_id)
    return list(preferences.preferences) if preferences else []


async def set_user_preferences_service(
    *, db: AsyncSession, user_id: int, preferences: list[str]
) -> list[str]:
    stored_preferences = await db.get(UserPreference, user_id)
    if stored_preferences is None:
        stored_preferences = UserPreference(
            user_id=user_id, preferences=preferences
        )
        db.add(stored_preferences)
    else:
        stored_preferences.preferences = preferences

    await db.commit()
    return list(stored_preferences.preferences)