from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.routes import get_current_user
from core.database import get_db
from users.models import User
from users.schemas import (
    UserCreate,
    UserPreferencesResponse,
    UserPreferencesUpdate,
    UserResponse,
    UserUpdate,
)
from users.service import (
    create_user_service,
    delete_user_service,
    get_user_service,
    get_user_preferences_service,
    list_users_service,
    set_user_preferences_service,
    update_user_service,
)

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me/preferences", response_model=UserPreferencesResponse)
async def get_my_preferences(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    preferences = await get_user_preferences_service(db=db, user_id=current_user.id)
    return {"preferences": preferences}


@router.put("/me/preferences", response_model=UserPreferencesResponse)
async def update_my_preferences(
    preferences: UserPreferencesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    saved_preferences = await set_user_preferences_service(
        db=db, user_id=current_user.id, preferences=preferences.preferences
    )
    return {"preferences": saved_preferences}


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    return await create_user_service(
        db=db,
        username=user_in.username,
        password=user_in.password,
    )


@router.get("", response_model=list[UserResponse])
async def list_users(
    skip: int = 0, limit: int = 10, db: AsyncSession = Depends(get_db)
):
    return await list_users_service(db=db, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await get_user_service(db=db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado."
        )
    return user


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, user_in: UserUpdate, db: AsyncSession = Depends(get_db)
):
    user = await get_user_service(db=db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado."
        )

    return await update_user_service(
        db=db,
        user=user,
        username=user_in.username,
        password=user_in.password,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    user = await get_user_service(db=db, user_id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado."
        )

    await delete_user_service(db=db, user=user)
