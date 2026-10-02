"""Exemplo de uso e utilitários para PresentationSchema no ciclo de vida de publicações."""

from presentation.schemas import LayoutConfig, PresentationSchema
from publication.models import Publication


def create_default_presentation() -> PresentationSchema:
    """Retorna uma configuração padrão pronta para uso."""
    return PresentationSchema()


def validate_presentation_payload(raw_data: dict) -> PresentationSchema:
    """Valida um payload bruto recebido da API ou lido do banco."""
    return PresentationSchema.model_validate(raw_data)


# Exemplo conceitual:
# 1. Ao salvar no banco:
# pydantic_presentation = PresentationSchema(
#     layout=LayoutConfig(
#         width="wide",
#         show_table_of_contents=True,
#         header_style="cover_overlay",
#     )
# )
# nova_publicacao = Publication(
#     slug="minha-publicacao",
#     title="Exemplo",
#     document={"blocks": []},
#     presentation=pydantic_presentation.model_dump(mode="json"),
#     user_id=1,
# )
#
# 2. Ao ler do banco:
# estilo = validate_presentation_payload(pub.presentation)
# print(estilo.layout.show_table_of_contents)