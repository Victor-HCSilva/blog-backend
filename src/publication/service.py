import time
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from engine_recommendation import TFIDFRecommender, UserRepr
from engine_recommendation.recommendation import build_publication_repr
from publication.models import (
    Publication,
    PublicationReaction,
    PublicationReadHistory,
    PublicationTag,
)


# ---------------------------------------------------------------------------
# Cache simples em memória para o TF-IDF (evita reconstruir a cada request)
# ---------------------------------------------------------------------------

_recommender_cache: TFIDFRecommender | None = None
_cache_built_at: float = 0.0
_cache_fingerprint: tuple[object, ...] = ()
_CACHE_TTL_SECONDS: float = 300.0  # 5 minutos


async def _get_recommender(
    db: AsyncSession, publications: list[Publication]
) -> TFIDFRecommender:
    global _recommender_cache, _cache_built_at, _cache_fingerprint

    tags_result = await db.execute(
        select(PublicationTag.publication_id, PublicationTag.tag).where(
            PublicationTag.publication_id.in_(
                [publication.id for publication in publications]
            )
        )
    )
    tags_by_publication: dict[int, list[str]] = {}
    for publication_id, tag in tags_result:
        tags_by_publication.setdefault(publication_id, []).append(tag)

    publication_fingerprint = tuple(
        (publication.id, publication.updated_at) for publication in publications
    )
    tags_fingerprint = tuple(
        sorted(
            (publication_id, tag)
            for publication_id, tags in tags_by_publication.items()
            for tag in tags
        )
    )
    fingerprint = (publication_fingerprint, tags_fingerprint)
    now = time.monotonic()
    if (
        _recommender_cache is None
        or fingerprint != _cache_fingerprint
        or (now - _cache_built_at) > _CACHE_TTL_SECONDS
    ):
        _recommender_cache = TFIDFRecommender(tag_boost=0.25).fit([
            build_publication_repr(
                publication, tags=tags_by_publication.get(publication.id, [])
            )
            for publication in publications
        ])
        _cache_built_at = now
        _cache_fingerprint = fingerprint

    return _recommender_cache


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
    result = await db.execute(query.order_by(Publication.created_at.desc()))
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


async def get_related_publications_service(
    *,
    db: AsyncSession,
    slug: str,
    top_n: int = 5,
) -> list[tuple[Publication, float]]:
    """
    Retorna as publicações mais relacionadas a um determinado slug,
    usando TF-IDF + Jaccard de tags.

    O modelo é reconstruído apenas quando o cache expira (TTL de 5 min),
    evitando o custo de ajuste a cada requisição.
    """
    # Busca todas as publicações publicadas e ativas
    all_pubs = await list_publications_service(db=db)

    if len(all_pubs) < 2:
        return []

    # Verifica se o slug existe no corpus antes de prosseguir
    slugs_in_corpus = {p.slug for p in all_pubs}
    if slug not in slugs_in_corpus:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicação não encontrada.",
        )

    recommender = await _get_recommender(db, all_pubs)

    recommendations = recommender.recommend(slug=slug, top_n=top_n)

    slug_to_pub = {p.slug: p for p in all_pubs}
    return [
        (slug_to_pub[rec_slug], score)
        for rec_slug, score in recommendations
        if rec_slug in slug_to_pub
    ]


async def get_user_recommendations_service(
    *,
    db: AsyncSession,
    user_id: int,
    preferences: list[str],
    top_n: int,
) -> list[tuple[Publication, float]]:
    publications = await list_publications_service(db=db)
    if len(publications) < 2:
        return []

    history_query = (
        select(Publication.slug)
        .join(
            PublicationReadHistory,
            PublicationReadHistory.publication_id == Publication.id,
        )
        .where(
            PublicationReadHistory.user_id == user_id,
            Publication.is_active.is_(True),
            Publication.is_published.is_(True),
        )
        .order_by(PublicationReadHistory.last_viewed_at.desc())
        .limit(50)
    )
    read_slugs = (await db.execute(history_query)).scalars().all()
    if not preferences and not read_slugs:
        return []

    recommender = await _get_recommender(db, publications)
    recommendations = recommender.recommend_for_profile(
        UserRepr(id=user_id, preferences=preferences),
        read_slugs=list(read_slugs),
        top_n=top_n,
    )
    publications_by_slug = {publication.slug: publication for publication in publications}
    return [
        (publications_by_slug[slug], score)
        for slug, score in recommendations
        if slug in publications_by_slug
    ]


async def record_publication_view_service(
    *, db: AsyncSession, publication: Publication, user_id: int
) -> None:
    history = await db.get(
        PublicationReadHistory, (user_id, publication.id)
    )
    if history is None:
        db.add(
            PublicationReadHistory(
                user_id=user_id,
                publication_id=publication.id,
                read_count=1,
            )
        )
    else:
        history.last_viewed_at = datetime.now(timezone.utc)
        history.read_count += 1

    await db.commit()


async def set_publication_reaction_service(
    *,
    db: AsyncSession,
    publication_id: int,
    user_id: int,
    reaction: str | None,
) -> dict[str, int | str | None]:
    publication = await db.scalar(
        select(Publication)
        .where(Publication.id == publication_id)
        .with_for_update()
    )
    if publication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicação não encontrada.",
        )

    current = await db.get(PublicationReaction, (user_id, publication_id))
    previous_reaction = current.reaction if current else None
    if previous_reaction != reaction:
        if previous_reaction == "like":
            publication.like = max(0, (publication.like or 0) - 1)
        elif previous_reaction == "dislike":
            publication.dislike = max(0, (publication.dislike or 0) - 1)

        if reaction == "like":
            publication.like = (publication.like or 0) + 1
        elif reaction == "dislike":
            publication.dislike = (publication.dislike or 0) + 1

        if current is not None and reaction is None:
            await db.delete(current)
        elif current is None and reaction is not None:
            db.add(
                PublicationReaction(
                    user_id=user_id,
                    publication_id=publication_id,
                    reaction=reaction,
                )
            )
        elif current is not None:
            current.reaction = reaction

        await db.commit()
        await db.refresh(publication)

    return {
        "like": publication.like or 0,
        "dislike": publication.dislike or 0,
        "reaction": reaction,
    }


async def get_user_reactions_service(
    *, db: AsyncSession, user_id: int
) -> dict[str, str]:
    result = await db.execute(
        select(Publication.slug, PublicationReaction.reaction)
        .join(
            PublicationReaction,
            PublicationReaction.publication_id == Publication.id,
        )
        .where(
            PublicationReaction.user_id == user_id,
            Publication.is_active.is_(True),
            Publication.is_published.is_(True),
        )
    )
    return {slug: reaction for slug, reaction in result}
