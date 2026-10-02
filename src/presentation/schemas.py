from enum import Enum
from typing import Literal, Optional
from pydantic import BaseModel, ConfigDict, Field

HEX_COLOR_REGEX = r"^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$"


class TemplatePreset(str, Enum):
    CLEAN = "clean"
    ACADEMIC = "academic"
    IMMERSIVE = "immersive"
    EDITORIAL = "editorial"
    MINIMALIST = "minimalist"
    CYBER_DARK = "cyber_dark"
    WARM_BRUTALIST = "warm_brutalist"


class TypographyFamily(str, Enum):
    SANS = "sans"
    SERIF = "serif"
    MONO = "mono"
    DISPLAY = "display"


class TypographySize(str, Enum):
    COMPACT = "compact"
    MEDIUM = "medium"
    EXPANDED = "expanded"


class LayoutWidth(str, Enum):
    NARROW = "narrow"      # 680px (foco extremo / leitura imersiva)
    STANDARD = "standard"  # 780px (padrão editorial)
    WIDE = "wide"          # 940px (ideal para código/tabelas)
    FULL = "full"          # 100% / largura total fluida


class SpacingScale(str, Enum):
    COMPACT = "compact"
    COMFORTABLE = "comfortable"
    TIGHT = "tight"
    LOOSE = "loose"


class ContentAlignment(str, Enum):
    LEFT = "left"
    CENTER = "center"


class ContainerPadding(str, Enum):
    COMPACT = "compact"
    NORMAL = "normal"
    RELAXED = "relaxed"


class ParagraphSpacing(str, Enum):
    COMPACT = "compact"
    NORMAL = "normal"
    LOOSE = "loose"


class HeaderStyle(str, Enum):
    MINIMAL = "minimal"
    CLASSIC = "classic"
    CENTERED = "centered"
    COVER_OVERLAY = "cover_overlay"
    SPLIT = "split"


class CoverLayout(str, Enum):
    HIDDEN = "hidden"
    CONTAINED = "contained"
    WIDE = "wide"
    FULL_BLEED = "full_bleed"


class TocPosition(str, Enum):
    SIDEBAR_LEFT = "sidebar_left"
    SIDEBAR_RIGHT = "sidebar_right"
    INLINE = "inline"


class SidebarPosition(str, Enum):
    NONE = "none"
    LEFT = "left"
    RIGHT = "right"


class AuthorCardPosition(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"
    BOTH = "both"
    HIDDEN = "hidden"


class BorderRadius(str, Enum):
    NONE = "none"
    SM = "sm"
    MD = "md"
    LG = "lg"
    FULL = "full"


class ShadowIntensity(str, Enum):
    NONE = "none"
    SUBTLE = "subtle"
    MEDIUM = "medium"
    ELEVATED = "elevated"
    HARD = "hard"


class PatternType(str, Enum):
    DOTS = "dots"
    GRID = "grid"
    NOISE = "noise"
    DIAGONAL = "diagonal"


class ColorPalette(BaseModel):
    background: str = Field(default="#FFFFFF", pattern=HEX_COLOR_REGEX)
    surface: str = Field(default="#F8FAFC", pattern=HEX_COLOR_REGEX)
    foreground: str = Field(default="#0F172A", pattern=HEX_COLOR_REGEX)
    muted: str = Field(default="#64748B", pattern=HEX_COLOR_REGEX)
    accent: str = Field(default="#7C3AED", pattern=HEX_COLOR_REGEX)
    accent_secondary: Optional[str] = Field(default=None, pattern=HEX_COLOR_REGEX)

    model_config = ConfigDict(extra="forbid")


class BackgroundConfig(BaseModel):
    mode: Literal["solid", "gradient", "pattern"] = "solid"
    color: str = Field(default="#F5F7FA", pattern=HEX_COLOR_REGEX)
    secondary_color: Optional[str] = Field(default=None, pattern=HEX_COLOR_REGEX)
    accent_color: str = Field(default="#7C3AED", pattern=HEX_COLOR_REGEX)
    gradient_direction: Literal["to_right", "to_bottom", "to_bottom_right", "radial"] = "to_bottom_right"
    pattern: Optional[PatternType] = None
    pattern_opacity: float = Field(default=0.08, ge=0.0, le=1.0)

    model_config = ConfigDict(extra="forbid")


class TypographyConfig(BaseModel):
    family: TypographyFamily = TypographyFamily.SANS
    family_headings: Optional[TypographyFamily] = None
    family_body: Optional[TypographyFamily] = None
    size: TypographySize = TypographySize.MEDIUM
    line_height: Literal["compact", "normal", "relaxed"] = "normal"

    model_config = ConfigDict(extra="forbid")


class ComponentStyleConfig(BaseModel):
    radius: BorderRadius = BorderRadius.MD
    shadow: ShadowIntensity = ShadowIntensity.SUBTLE
    border_width: Literal["none", "thin", "thick"] = "thin"
    frosted_glass: bool = False

    model_config = ConfigDict(extra="forbid")


class LayoutConfig(BaseModel):
    # 1. Dimensão e alinhamento do container principal
    width: LayoutWidth = LayoutWidth.STANDARD
    content_alignment: ContentAlignment = ContentAlignment.LEFT

    # 2. Espaçamentos e ritmo vertical
    spacing: SpacingScale = SpacingScale.COMFORTABLE
    container_padding: ContainerPadding = ContainerPadding.NORMAL
    paragraph_spacing: ParagraphSpacing = ParagraphSpacing.NORMAL

    # 3. Estilos de cabeçalho e imagem de capa
    header_style: HeaderStyle = HeaderStyle.CLASSIC
    cover_layout: CoverLayout = CoverLayout.CONTAINED

    # 4. Navegação e elementos dinâmicos de leitura
    show_table_of_contents: bool = False
    toc_position: TocPosition = TocPosition.SIDEBAR_LEFT
    show_reading_progress: bool = True
    show_estimated_reading_time: bool = True

    # 5. Barras laterais e apresentação do autor
    sidebar: SidebarPosition = SidebarPosition.NONE
    author_card_position: AuthorCardPosition = AuthorCardPosition.BOTTOM

    model_config = ConfigDict(extra="forbid")


class PresentationSchema(BaseModel):
    template: TemplatePreset = TemplatePreset.CLEAN
    colors: Optional[ColorPalette] = Field(default_factory=ColorPalette)
    background: BackgroundConfig = Field(default_factory=BackgroundConfig)
    typography: TypographyConfig = Field(default_factory=TypographyConfig)
    layout: LayoutConfig = Field(default_factory=LayoutConfig)
    components: Optional[ComponentStyleConfig] = Field(default_factory=ComponentStyleConfig)

    model_config = ConfigDict(extra="forbid")


# Alias para compatibilidade e semântica com o domínio de publicações
PublicationPresentation = PresentationSchema