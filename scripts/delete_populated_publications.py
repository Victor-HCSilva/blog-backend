import argparse
import asyncio
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))
sys.path.insert(0, str(REPOSITORY_ROOT / "src"))

from data import novos_posts
from core.database import AsyncSessionLocal, engine
from publication.models import Publication
from sqlalchemy import delete, select
from users.models import User


async def delete_populated(user_id: int) -> None:
    slugs = [item["slug"] for item in novos_posts]
    async with AsyncSessionLocal() as db:
        publications = (
            await db.execute(
                select(Publication).where(
                    Publication.user_id == user_id,
                    Publication.slug.in_(slugs),
                )
            )
        ).scalars().all()

        if not publications:
            print("Nenhuma publicação de exemplo deste usuário foi encontrada.")
            return

        publication_ids = [publication.id for publication in publications]
        await db.execute(
            delete(Publication).where(Publication.id.in_(publication_ids))
        )
        await db.commit()
        print(f"Publicações de exemplo removidas: {len(publication_ids)}.")


async def main() -> None:
    parser = argparse.ArgumentParser(
        description="Remove do catálogo os artigos de data.py do usuário informado."
    )
    parser.add_argument(
        "--user-id",
        required=True,
        type=int,
        help="Remove somente publicações de exemplo pertencentes a este usuário.",
    )
    args = parser.parse_args()
    try:
        await delete_populated(args.user_id)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
