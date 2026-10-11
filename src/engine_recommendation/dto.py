from dataclasses import dataclass, field


@dataclass
class PublicationRepr:
    """Representação leve de uma publicação para o motor de recomendação."""

    id: int
    slug: str
    title: str
    raw_text: str
    tags: list[str] = field(default_factory=list)


@dataclass
class UserRepr:
    """Representação de um usuário para o motor de recomendação."""

    id: int
    preferences: list[str] = field(default_factory=list)
