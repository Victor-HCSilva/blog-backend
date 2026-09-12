from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from auth.routes import get_current_user
from core.database import get_db
from publication import schemas
from publication.service import (
    create_publication_service,
    get_owned_publication_by_slug_service,
    get_publication_by_slug_service,
    list_owned_publications_service,
    list_publications_service,
    publish_publication_service,
    update_publication_service,
)
from users.models import User

router = APIRouter(prefix="/publications", tags=["Publications"])


@router.post(
    "", response_model=schemas.PublicationResponse, status_code=status.HTTP_201_CREATED
)
async def create_publication(
    pub: schemas.PublicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_pub = await create_publication_service(
        db=db,
        slug=pub.slug,
        title=pub.title,
        document=pub.document.model_dump(mode="json"),
        presentation=pub.presentation.model_dump(mode="json"),
        user_id=current_user.id,
        thumbnail_url=pub.thumbnail_url,
    )
    return db_pub


@router.get("", response_model=list[schemas.PublicationResponse])
async def list_publications(db: AsyncSession = Depends(get_db)):
    return await list_publications_service(db=db)


@router.get("/mine", response_model=list[schemas.PublicationResponse])
async def list_my_publications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await list_owned_publications_service(db=db, user_id=current_user.id)


@router.get("/{slug}", response_model=schemas.PublicationResponse)
async def get_publication(slug: str, db: AsyncSession = Depends(get_db)):
    db_pub = await get_publication_by_slug_service(db=db, slug=slug)
    if not db_pub:
        raise HTTPException(status_code=404, detail="Publicação não encontrada")
    return db_pub


@router.post("/{slug}/publish", response_model=schemas.PublicationResponse)
async def publish_publication(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_pub = await get_owned_publication_by_slug_service(
        db=db, slug=slug, user_id=current_user.id
    )
    if not db_pub:
        raise HTTPException(status_code=404, detail="Publicação não encontrada")
    return await publish_publication_service(db=db, db_pub=db_pub)


@router.put("/{slug}", response_model=schemas.PublicationResponse)
async def update_publication(
    slug: str,
    pub: schemas.PublicationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_pub = await get_owned_publication_by_slug_service(
        db=db, slug=slug, user_id=current_user.id
    )
    if not db_pub:
        raise HTTPException(status_code=404, detail="Publicação não encontrada")
    if db_pub.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Você não pode editar esta publicação.",
        )

    return await update_publication_service(
        db=db,
        db_pub=db_pub,
        title=pub.title,
        document=pub.document.model_dump(mode="json"),
        presentation=pub.presentation.model_dump(mode="json"),
        thumbnail_url=pub.thumbnail_url,
    )
