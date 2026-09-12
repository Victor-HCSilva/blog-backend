from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from publication.models import Publication


async def create_publication_service(
    *,
    db: AsyncSession,
    slug: str,
    title: str,
    document: dict,
    presentation: dict,
    user_id: int,
    thumbnail_url: str | None = None,
) -> Publication:
    existing_publication = await db.execute(
        select(Publication).where(Publication.slug == slug)
    )
    if existing_publication.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Slug já está em uso.",
        )

    new_publication = Publication(
        slug=slug,
        title=title,
        document=document,
        presentation=presentation,
        user_id=user_id,
        thumbnail_url=thumbnail_url,
        is_published=False,
    )
    db.add(new_publication)
    await db.commit()
    await db.refresh(new_publication)
    return new_publication


async def list_publications_service(*, db: AsyncSession):
    query = select(Publication).where(
        Publication.is_active.is_(True), Publication.is_published.is_(True)
    )
    result = await db.execute(query)
    return result.scalars().all()


async def list_owned_publications_service(
    *, db: AsyncSession, user_id: int
) -> list[Publication]:
    query = select(Publication).where(
        Publication.user_id == user_id, Publication.is_active.is_(True)
    )
    result = await db.execute(query)
    return result.scalars().all()


async def get_publication_by_slug_service(
    *, db: AsyncSession, slug: str
) -> Publication | None:
    query = select(Publication).where(
        Publication.slug == slug,
        Publication.is_active.is_(True),
        Publication.is_published.is_(True),
    )
    result = await db.execute(query)
    return result.scalars().first()


async def get_owned_publication_by_slug_service(
    *, db: AsyncSession, slug: str, user_id: int
) -> Publication | None:
    query = select(Publication).where(
        Publication.slug == slug,
        Publication.user_id == user_id,
        Publication.is_active.is_(True),
    )
    result = await db.execute(query)
    return result.scalars().first()


async def update_publication_service(
    *,
    db: AsyncSession,
    db_pub: Publication,
    title: str,
    document: dict,
    presentation: dict,
    thumbnail_url: str | None = None,
) -> Publication:
    db_pub.title = title
    db_pub.document = document
    db_pub.presentation = presentation
    db_pub.thumbnail_url = thumbnail_url

    await db.commit()
    await db.refresh(db_pub)
    return db_pub


async def publish_publication_service(
    *, db: AsyncSession, db_pub: Publication
) -> Publication:
    db_pub.is_published = True
    await db.commit()
    await db.refresh(db_pub)
    return db_pub
