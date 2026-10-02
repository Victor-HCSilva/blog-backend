import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from presentation.schemas import (
    AuthorCardPosition,
    BackgroundConfig,
    ContainerPadding,
    ContentAlignment,
    CoverLayout,
    HeaderStyle,
    LayoutConfig,
    LayoutWidth,
    ParagraphSpacing,
    PresentationSchema,
    SidebarPosition,
    SpacingScale,
    TemplatePreset,
    TocPosition,
    TypographyConfig,
    TypographyFamily,
    TypographySize,
)
from publication.schemas import (
    DocumentSchema,
    PublicationCreate,
    PublicationPresentation,
)


class PresentationLayoutConfigTest(unittest.TestCase):
    def test_default_layout_config(self):
        layout = LayoutConfig()
        self.assertEqual(layout.width, LayoutWidth.STANDARD)
        self.assertEqual(layout.content_alignment, ContentAlignment.LEFT)
        self.assertEqual(layout.spacing, SpacingScale.COMFORTABLE)
        self.assertEqual(layout.container_padding, ContainerPadding.NORMAL)
        self.assertEqual(layout.paragraph_spacing, ParagraphSpacing.NORMAL)
        self.assertEqual(layout.header_style, HeaderStyle.CLASSIC)
        self.assertEqual(layout.cover_layout, CoverLayout.CONTAINED)
        self.assertFalse(layout.show_table_of_contents)
        self.assertEqual(layout.toc_position, TocPosition.SIDEBAR_LEFT)
        self.assertTrue(layout.show_reading_progress)
        self.assertTrue(layout.show_estimated_reading_time)
        self.assertEqual(layout.sidebar, SidebarPosition.NONE)
        self.assertEqual(layout.author_card_position, AuthorCardPosition.BOTTOM)

    def test_custom_layout_options(self):
        custom_layout = LayoutConfig(
            width=LayoutWidth.WIDE,
            content_alignment=ContentAlignment.CENTER,
            spacing=SpacingScale.LOOSE,
            container_padding=ContainerPadding.RELAXED,
            paragraph_spacing=ParagraphSpacing.LOOSE,
            header_style=HeaderStyle.COVER_OVERLAY,
            cover_layout=CoverLayout.FULL_BLEED,
            show_table_of_contents=True,
            toc_position=TocPosition.SIDEBAR_RIGHT,
            show_reading_progress=False,
            show_estimated_reading_time=False,
            sidebar=SidebarPosition.LEFT,
            author_card_position=AuthorCardPosition.BOTH,
        )
        self.assertEqual(custom_layout.width, "wide")
        self.assertEqual(custom_layout.header_style, "cover_overlay")
        self.assertEqual(custom_layout.cover_layout, "full_bleed")
        self.assertTrue(custom_layout.show_table_of_contents)
        self.assertEqual(custom_layout.toc_position, "sidebar_right")
        self.assertEqual(custom_layout.sidebar, "left")
        self.assertEqual(custom_layout.author_card_position, "both")

    def test_frontend_blog_interface_payload_compatibility(self):
        """Garante que o payload gerado atualmente pelo frontend blog-interface é 100% válido."""
        frontend_payload = {
            "template": "clean",
            "background": {
                "mode": "solid",
                "color": "#F5F7FA",
                "secondary_color": None,
                "accent_color": "#7C3AED",
            },
            "typography": {
                "family": "sans",
                "size": "medium",
            },
            "layout": {
                "width": "standard",
                "spacing": "comfortable",
            },
        }

        presentation = PresentationSchema.model_validate(frontend_payload)
        self.assertEqual(presentation.template, TemplatePreset.CLEAN)
        self.assertEqual(presentation.background.color, "#F5F7FA")
        self.assertEqual(presentation.typography.family, TypographyFamily.SANS)
        self.assertEqual(presentation.layout.width, LayoutWidth.STANDARD)
        self.assertEqual(presentation.layout.spacing, SpacingScale.COMFORTABLE)
        # Valores padrão das novas opções devem ser aplicados automaticamente
        self.assertEqual(presentation.layout.header_style, HeaderStyle.CLASSIC)
        self.assertEqual(presentation.layout.cover_layout, CoverLayout.CONTAINED)
        self.assertFalse(presentation.layout.show_table_of_contents)
        self.assertTrue(presentation.layout.show_reading_progress)

    def test_publication_create_with_new_layout_config(self):
        payload = {
            "title": "Post com Layout Avançado",
            "slug": "post-layout-avancado",
            "document": {"blocks": []},
            "presentation": {
                "template": "editorial",
                "background": {
                    "mode": "gradient",
                    "color": "#FFFFFF",
                    "secondary_color": "#F8FAFC",
                    "accent_color": "#2563EB",
                },
                "typography": {
                    "family": "serif",
                    "size": "expanded",
                },
                "layout": {
                    "width": "wide",
                    "header_style": "centered",
                    "cover_layout": "wide",
                    "show_table_of_contents": True,
                    "toc_position": "sidebar_right",
                    "sidebar": "right",
                    "author_card_position": "top",
                },
            },
        }

        create_dto = PublicationCreate.model_validate(payload)
        self.assertEqual(create_dto.title, "Post com Layout Avançado")
        self.assertEqual(create_dto.presentation.layout.header_style, HeaderStyle.CENTERED)
        self.assertEqual(create_dto.presentation.layout.cover_layout, CoverLayout.WIDE)
        self.assertTrue(create_dto.presentation.layout.show_table_of_contents)
        self.assertEqual(create_dto.presentation.layout.sidebar, SidebarPosition.RIGHT)

    def test_extra_forbidden_fields(self):
        """Valores arbitrários de CSS continuam proibidos por design."""
        with self.assertRaises(Exception):
            LayoutConfig(width="wide", arbitrary_css="display: flex;")


if __name__ == "__main__":
    unittest.main()
