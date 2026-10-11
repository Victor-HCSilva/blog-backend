from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from auth.routes import get_current_user
from core.database import get_db
from publication import schemas
from publication.service import (
    create_publication_service,
    get_owned_publication_by_slug_service,
    get_publication_by_slug_service,
    get_user_reactions_service,
    get_user_recommendations_service,
    list_owned_publications_service,
    list_publications_service,
    publish_publication_service,
    record_publication_view_service,
    set_publication_reaction_service,
    update_publication_service,
)
from users.service import get_user_by_publication, get_user_preferences_service
from text_to_audio.dto import PublicationDTO
from text_to_audio.engine import TextToAudio
from users.models import User

router = APIRouter(prefix="/publications", tags=["Publications"])


@router.get(
    "/recommendations/me",
    response_model=list[schemas.PersonalizedPublicationResponse],
)
async def get_my_recommendations(
    top_n: int = Query(default=12, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    preferences = await get_user_preferences_service(
        db=db, user_id=current_user.id
    )
    recommendations = await get_user_recommendations_service(
        db=db,
        user_id=current_user.id,
        preferences=preferences,
        top_n=top_n,
    )
    return [
        {
            **schemas.PublicationResponse.model_validate(publication).model_dump(),
            "relevance_score": score,
        }
        for publication, score in recommendations
    ]


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


@router.get("/reactions/me", response_model=schemas.UserReactionsResponse)
async def get_my_publication_reactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reactions = await get_user_reactions_service(db=db, user_id=current_user.id)
    return {"reactions": reactions}


@router.post("/{slug}/views", status_code=status.HTTP_204_NO_CONTENT)
async def record_publication_view(
    slug: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    publication = await get_publication_by_slug_service(db=db, slug=slug)
    if publication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicação não encontrada.",
        )

    await record_publication_view_service(
        db=db, publication=publication, user_id=current_user.id
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{slug}/reaction", response_model=schemas.ReactionResponse)
async def update_publication_reaction(
    slug: str,
    payload: schemas.ReactionUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    publication = await get_publication_by_slug_service(db=db, slug=slug)
    if publication is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Publicação não encontrada.",
        )

    return await set_publication_reaction_service(
        db=db,
        publication_id=publication.id,
        user_id=current_user.id,
        reaction=payload.reaction,
    )


@router.get("/{slug}", response_model=schemas.PublicationResponse)
async def get_publication(slug: str, db: AsyncSession = Depends(get_db)):
    db_pub = await get_publication_by_slug_service(db=db, slug=slug)
    if not db_pub:
        raise HTTPException(status_code=404, detail="Publicação não encontrada")
    return db_pub


@router.post("/{slug}/audio", response_class=Response)
async def generate_publication_audio(slug: str, db: AsyncSession = Depends(get_db)):
    db_pub = await get_publication_by_slug_service(db=db, slug=slug)
    author = await get_user_by_publication(
        db=db,
        publication_id=db_pub.id
    )

    if not db_pub:
        raise HTTPException(status_code=404, detail="Publicação não encontrada")

    blocks = db_pub.document.get("blocks", [])
    text_parts = [db_pub.title]
    for block in blocks:
        if block.get("type") == "list":
            content_groups = block.get("items", [])
        else:
            content_groups = [block.get("content", [])]
        text_parts.extend(
            item.get("text", "") for content in content_groups for item in content
        )

    text = "\n".join(part.strip() for part in text_parts if part.strip())
    if not text:
        raise HTTPException(status_code=400, detail="A publicação não possui texto")

    audio = await run_in_threadpool(
        TextToAudio(
            PublicationDTO(
                author_name= author.username or "autor da publicação",
                date=db_pub.created_at.date() or None,
                content=text,
            )
        ).convert
    )
    return Response(
        content=audio,
        media_type="audio/mpeg",
        headers={"Content-Disposition": f'inline; filename="{db_pub.slug}.mp3"'},
    )


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
