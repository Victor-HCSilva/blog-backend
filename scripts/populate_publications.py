import argparse
import asyncio
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from data import novos_posts
from core.database import AsyncSessionLocal, engine
from presentation.schemas import (
    BackgroundConfig,
    ColorPalette,
    ComponentStyleConfig,
    LayoutConfig,
    PresentationSchema,
    TemplatePreset,
    TypographyConfig,
)
from publication.models import Publication, PublicationTag
from sqlalchemy import select
from users.models import User

STYLE_OPTIONS = [
    {
        "template": TemplatePreset.CLEAN,
        "background": "#F8FAFC",
        "surface": "#FFFFFF",
        "foreground": "#172033",
        "muted": "#64748B",
        "accent": "#2563EB",
        "accent_secondary": "#38BDF8",
        "font": "sans",
        "width": "standard",
        "header": "classic",
    },
    {
        "template": TemplatePreset.ACADEMIC,
        "background": "#F8F5EC",
        "surface": "#FFFEFA",
        "foreground": "#292524",
        "muted": "#78716C",
        "accent": "#7C3E18",
        "accent_secondary": "#B7791F",
        "font": "serif",
        "width": "narrow",
        "header": "centered",
    },
    {
        "template": TemplatePreset.IMMERSIVE,
        "background": "#111827",
        "surface": "#1F2937",
        "foreground": "#F9FAFB",
        "muted": "#9CA3AF",
        "accent": "#A78BFA",
        "accent_secondary": "#22D3EE",
        "font": "sans",
        "width": "narrow",
        "header": "cover_overlay",
    },
    {
        "template": TemplatePreset.EDITORIAL,
        "background": "#F6F1EA",
        "surface": "#FFFDF9",
        "foreground": "#292524",
        "muted": "#78716C",
        "accent": "#BE4B32",
        "accent_secondary": "#D6A84F",
        "font": "serif",
        "width": "wide",
        "header": "split",
    },
    {
        "template": TemplatePreset.MINIMALIST,
        "background": "#FFFFFF",
        "surface": "#F8FAFC",
        "foreground": "#111827",
        "muted": "#6B7280",
        "accent": "#0F766E",
        "accent_secondary": "#14B8A6",
        "font": "sans",
        "width": "standard",
        "header": "minimal",
    },
    {
        "template": TemplatePreset.CYBER_DARK,
        "background": "#080D1B",
        "surface": "#111827",
        "foreground": "#E0F2FE",
        "muted": "#94A3B8",
        "accent": "#22D3EE",
        "accent_secondary": "#A3E635",
        "font": "mono",
        "width": "wide",
        "header": "cover_overlay",
    },
    {
        "template": TemplatePreset.WARM_BRUTALIST,
        "background": "#FFF1D6",
        "surface": "#FFF9ED",
        "foreground": "#271B12",
        "muted": "#725A43",
        "accent": "#C2410C",
        "accent_secondary": "#1D4ED8",
        "font": "display",
        "width": "wide",
        "header": "centered",
    },
]


def build_presentation(index: int) -> dict:
    option = STYLE_OPTIONS[index % len(STYLE_OPTIONS)]
    presentation = PresentationSchema(
        template=option["template"],
        colors=ColorPalette(
            background=option["background"],
            surface=option["surface"],
            foreground=option["foreground"],
            muted=option["muted"],
            accent=option["accent"],
            accent_secondary=option["accent_secondary"],
        ),
        background=BackgroundConfig(
            mode="solid",
            color=option["background"],
            accent_color=option["accent"],
        ),
        typography=TypographyConfig(
            family=option["font"],
            family_headings=option["font"],
            family_body=option["font"],
            size="medium",
            line_height="relaxed",
        ),
        layout=LayoutConfig(
            width=option["width"],
            header_style=option["header"],
            show_table_of_contents=index % 3 == 1,
            show_reading_progress=True,
            show_estimated_reading_time=True,
        ),
        components=ComponentStyleConfig(
            radius="md" if index % 2 == 0 else "sm",
            shadow="subtle" if index % 2 == 0 else "medium",
            border_width="thin",
        ),
    )
    return presentation.model_dump(mode="json")


def build_document(raw_text: str) -> dict:
    return {
        "blocks": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": raw_text,
                        "styles": {"bold": False, "italic": False, "code": False},
                    }
                ],
            }
        ]
    }


async def populate(user_id: int) -> None:
    async with AsyncSessionLocal() as db:
        user = await db.get(User, user_id)
        if user is None:
            raise ValueError(f"Não existe usuário com id={user_id}.")

        created = 0
        skipped = 0
        for index, item in enumerate(novos_posts):
            existing = await db.scalar(
                select(Publication).where(Publication.slug == item["slug"])
            )
            if existing is not None:
                skipped += 1
                print(f"Ignorada (slug já existe): {item['slug']}")
                continue

            publication = Publication(
                slug=item["slug"],
                title=item["title"],
                user_id=user_id,
                document=build_document(item["raw_text"]),
                presentation=build_presentation(index),
                is_published=True,
                like=0,
                dislike=0,
            )
            db.add(publication)
            await db.flush()
            db.add_all(
                PublicationTag(publication_id=publication.id, tag=tag)
                for tag in item["tags"]
            )
            created += 1

        await db.commit()
        print(f"Publicações criadas: {created}; ignoradas: {skipped}.")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Popula o catálogo com os artigos de data.py."
    )
    parser.add_argument(
        "--user-id",
        required=True,
        type=int,
        help="ID do usuário que será autor das publicações de exemplo.",
    )
    args = parser.parse_args()
    try:
        await populate(args.user_id)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
