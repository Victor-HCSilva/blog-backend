from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from presentation.schemas import (
    BackgroundConfig,
    LayoutConfig,
    LayoutWidth,
    PresentationSchema,
    PublicationPresentation,
    TemplatePreset,
    TypographyConfig,
    TypographyFamily,
    TypographySize,
)


class InlineStyles(BaseModel):
    bold: bool = False
    italic: bool = False
    code: bool = False


class InlineContent(BaseModel):
    type: Literal["text", "link"] = "text"
    text: str = Field(min_length=1)
    href: HttpUrl | None = None
    styles: InlineStyles = Field(default_factory=InlineStyles)


class HeadingProps(BaseModel):
    level: int = Field(default=2, ge=1, le=6)


class CodeBlockProps(BaseModel):
    language: str | None = Field(default=None, min_length=1, max_length=32)


class ListProps(BaseModel):
    ordered: bool = False


class DocumentBlock(BaseModel):
    type: Literal["paragraph", "heading", "codeBlock", "quote", "list"]
    props: HeadingProps | CodeBlockProps | ListProps | None = None
    content: list[InlineContent] = Field(default_factory=list)
    items: list[list[InlineContent]] = Field(default_factory=list)


class DocumentSchema(BaseModel):
    blocks: list[DocumentBlock] = Field(default_factory=list)


class PublicationBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    slug: str = Field(
        min_length=1, max_length=255, pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    )
    document: DocumentSchema
    presentation: PublicationPresentation
    thumbnail_url: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")


class PublicationCreate(PublicationBase):
    user_id: int | None = None


class PublicationUpdate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    document: DocumentSchema
    presentation: PublicationPresentation
    thumbnail_url: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")


class PublicationResponse(PublicationBase):
    id: int
    user_id: int
    is_published: bool
    created_at: datetime
    like: int = 0
    dislike: int = 0

    model_config = ConfigDict(from_attributes=True, extra="forbid")


class RelatedPublicationResponse(BaseModel):
    """Resposta de publicações relacionadas retornadas pelo motor TF-IDF."""

    slug: str
    title: str
    thumbnail_url: str | None
    relevance_score: float = Field(
        ge=0.0, le=1.0, description="Pontuação de relevância (0–1)"
    )

    model_config = ConfigDict(from_attributes=False)


class PersonalizedPublicationResponse(PublicationResponse):
    relevance_score: float = Field(ge=0.0, le=1.0)


class ReactionUpdate(BaseModel):
    reaction: Literal["like", "dislike"] | None


class ReactionResponse(BaseModel):
    like: int
    dislike: int
    reaction: Literal["like", "dislike"] | None


class UserReactionsResponse(BaseModel):
    reactions: dict[str, Literal["like", "dislike"]]
