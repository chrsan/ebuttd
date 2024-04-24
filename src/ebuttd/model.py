import math

from dataclasses import dataclass, field
from enum import Enum
from typing import NamedTuple, TypedDict


def split_value(value: str) -> list[str]:
    return [v for v in value.strip().split(" ") if v]


class Unit(Enum):
    CELL = "c"
    PERCENT = "%"

    def parse(self, value: str, /, max_value: float | None = None) -> float:
        v = value.strip()
        suffix = "c" if self == Unit.CELL else "%"
        if not v or v[-1] != suffix:
            raise ValueError(value)
        n = float(v[:-1])
        if not math.isfinite(n) or n < 0.0:
            raise ValueError(value)
        if max_value is not None and n > max_value:
            raise ValueError(value)
        if self == Unit.CELL:
            return n
        return n / 100.0


class ActiveArea(NamedTuple):
    left: float = 0.0
    top: float = 0.0
    width: float = 1.0
    height: float = 1.0

    @staticmethod
    def parse(value: str) -> "ActiveArea":
        values = split_value(value)
        if len(values) != 4:
            raise ValueError(value)
        return ActiveArea(
            left=Unit.PERCENT.parse(values[0], max_value=100.0),
            top=Unit.PERCENT.parse(values[1], max_value=100.0),
            width=Unit.PERCENT.parse(values[2], max_value=100.0),
            height=Unit.PERCENT.parse(values[3], max_value=100.0),
        )


class CellResolution(NamedTuple):
    columns: int = 32
    rows: int = 15

    def is_valid(self) -> bool:
        return self.columns > 0 and self.rows > 0

    @staticmethod
    def parse(value: str) -> "CellResolution":
        values = split_value(value)
        if len(values) != 2:
            raise ValueError(value)
        cell_resolution = CellResolution(columns=int(values[0]), rows=int(values[1]))
        if cell_resolution.is_valid():
            return cell_resolution
        raise ValueError(value)


class Color(NamedTuple):
    red: int
    green: int
    blue: int
    alpha: int

    def is_valid(self) -> bool:
        return (
            self.red >= 0
            and self.red <= 255
            and self.green >= 0
            and self.green <= 255
            and self.blue >= 0
            and self.blue <= 255
            and self.alpha >= 0
            and self.alpha <= 255
        )

    @staticmethod
    def black() -> "Color":
        return Color(red=0, green=0, blue=0, alpha=255)

    @staticmethod
    def white() -> "Color":
        return Color(red=255, green=255, blue=255, alpha=255)

    @staticmethod
    def transparent() -> "Color":
        return Color(red=0, green=0, blue=0, alpha=0)

    @staticmethod
    def parse(value: str) -> "Color":
        v = value.strip()
        if not v or v[0] != "#":
            raise ValueError(value)
        v = v[1:]
        if len(v) != 6 and len(v) != 8:
            raise ValueError(value)
        color = Color(
            red=int(v[0:2], base=16),
            green=int(v[2:4], base=16),
            blue=int(v[4:6], base=16),
            alpha=int(v[6:8], base=16) if len(v) == 8 else 0,
        )
        if color.is_valid():
            return color
        raise ValueError(value)


class Direction(Enum):
    LTR = "ltr"
    RTL = "rtl"

    @staticmethod
    def parse(value: str) -> "Direction":
        match value.strip():
            case "ltr":
                return Direction.LTR
            case "rtl":
                return Direction.RTL
            case _:
                raise ValueError(value)


class DisplayAlign(Enum):
    BEFORE = "before"
    CENTER = "center"
    AFTER = "after"

    @staticmethod
    def parse(value: str) -> "DisplayAlign":
        match value.strip():
            case "before":
                return DisplayAlign.BEFORE
            case "center":
                return DisplayAlign.CENTER
            case "after":
                return DisplayAlign.AFTER
            case _:
                raise ValueError(value)


class Extent(NamedTuple):
    width: float = 0.0
    height: float = 0.0

    @staticmethod
    def parse(value: str) -> "Extent":
        values = split_value(value)
        if not values or len(values) != 2:
            raise ValueError(value)
        width = Unit.PERCENT.parse(values[0], max_value=100.0)
        height = Unit.PERCENT.parse(values[1], max_value=100.0)
        return Extent(width=width, height=height)


class FontSize(float):
    def __new__(cls, value: float) -> "FontSize":
        return super().__new__(cls, value)

    @staticmethod
    def parse(value: str) -> "FontSize":
        return FontSize(Unit.PERCENT.parse(value))


class FontStyle(Enum):
    NORMAL = "normal"
    ITALIC = "italic"

    @staticmethod
    def parse(value: str) -> "FontStyle":
        match value.strip():
            case "normal":
                return FontStyle.NORMAL
            case "italic":
                return FontStyle.ITALIC
            case _:
                raise ValueError(value)


class FontWeight(Enum):
    NORMAL = "normal"
    BOLD = "bold"

    @staticmethod
    def parse(value: str) -> "FontWeight":
        match value.strip():
            case "normal":
                return FontWeight.NORMAL
            case "bold":
                return FontWeight.BOLD
            case _:
                raise ValueError(value)


class LineHeight(float):
    def __new__(cls, value: float) -> "LineHeight":
        return super().__new__(cls, value)

    @staticmethod
    def parse(value: str) -> "LineHeight | None":
        value = value.strip()
        if value == "normal":
            return None
        return LineHeight(Unit.PERCENT.parse(value))


class LinePadding(float):
    def __new__(cls, value: float) -> "LinePadding":
        return super().__new__(cls, value)

    @staticmethod
    def parse(value: str) -> "LinePadding":
        return LinePadding(Unit.CELL.parse(value))


class MultiRowAlign(Enum):
    AUTO = "auto"
    START = "start"
    CENTER = "center"
    END = "end"

    @staticmethod
    def parse(value: str) -> "MultiRowAlign":
        match value.strip():
            case "auto":
                return MultiRowAlign.AUTO
            case "start":
                return MultiRowAlign.START
            case "center":
                return MultiRowAlign.CENTER
            case "end":
                return MultiRowAlign.END
            case _:
                raise ValueError(value)


class Origin(NamedTuple):
    x: float = 0.0
    y: float = 0.0

    @staticmethod
    def parse(value: str) -> "Origin":
        values = split_value(value)
        if len(values) != 2:
            raise ValueError(value)
        x = Unit.PERCENT.parse(values[0], max_value=100.0)
        y = Unit.PERCENT.parse(values[1], max_value=100.0)
        return Origin(x=x, y=y)


class Overflow(Enum):
    HIDDEN = "hidden"
    VISIBLE = "visible"

    @staticmethod
    def parse(value: str) -> "Overflow":
        match value.strip():
            case "hidden":
                return Overflow.HIDDEN
            case "visible":
                return Overflow.VISIBLE
            case _:
                raise ValueError(value)


class Padding(NamedTuple):
    before: float = 0.0
    end: float = 0.0
    after: float = 0.0
    start: float = 0.0

    @staticmethod
    def parse(value: str) -> "Padding":
        values = split_value(value)
        if not values or len(values) > 3:
            raise ValueError(value)
        before = 0.0
        end = 0.0
        after = 0.0
        start = 0.0
        for i, v in enumerate(values):
            length = Unit.PERCENT.parse(v)
            match i:
                case 0:
                    before = length
                    end = length
                    after = length
                    start = length
                case 1:
                    end = length
                    start = length
                case 2:
                    after = length
                case _:
                    start = length
        return Padding(before=before, end=end, after=after, start=start)


class ShowBackground(Enum):
    ALWAYS = "always"
    WHEN_ACTIVE = "whenActive"

    @staticmethod
    def parse(value: str) -> "ShowBackground":
        match value.strip():
            case "always":
                return ShowBackground.ALWAYS
            case "whenActive":
                return ShowBackground.WHEN_ACTIVE
            case _:
                raise ValueError(value)


class TextAlign(Enum):
    LEFT = "left"
    CENTER = "center"
    RIGHT = "right"
    START = "start"
    END = "end"

    @staticmethod
    def parse(value: str) -> "TextAlign":
        match value.strip():
            case "left":
                return TextAlign.LEFT
            case "center":
                return TextAlign.CENTER
            case "right":
                return TextAlign.RIGHT
            case "start":
                return TextAlign.START
            case "end":
                return TextAlign.END
            case _:
                raise ValueError(value)


class TextDecoration(Enum):
    NONE = "none"
    UNDERLINE = "underline"

    @staticmethod
    def parse(value: str) -> "TextDecoration":
        match value.strip():
            case "none":
                return TextDecoration.NONE
            case "underline":
                return TextDecoration.UNDERLINE
            case _:
                raise ValueError(value)


class TextOutline(NamedTuple):
    color: Color | None = None
    thickness: float = 0.0
    blur_radius: float | None = None

    @staticmethod
    def parse(value: str) -> "TextOutline | None":
        values = split_value(value)
        if not values:
            raise ValueError(value)
        if len(values) == 1 and values[0] == "none":
            return None
        if len(values) > 3:
            raise ValueError(value)
        color = None
        if values[0].startswith("#"):
            if len(values) == 1:
                raise ValueError(value)
            color = Color.parse(values[0])
            values = values[1:]
        thickness = Unit.PERCENT.parse(values[0])
        blur_radius = None
        if len(values) > 1:
            blur_radius = Unit.PERCENT.parse(values[1])
        return TextOutline(color=color, thickness=thickness, blur_radius=blur_radius)


class Space(Enum):
    DEFAULT = "default"
    PRESERVE = "preserve"

    @staticmethod
    def parse(value: str) -> "Space":
        match value.strip():
            case "default":
                return Space.DEFAULT
            case "preserve":
                return Space.PRESERVE
            case _:
                raise ValueError(value)


class UnicodeBidi(Enum):
    NORMAL = "normal"
    EMBED = "embed"
    BIDI_OVERRIDE = "bidiOverride"

    @staticmethod
    def parse(value: str) -> "UnicodeBidi":
        match value.strip():
            case "normal":
                return UnicodeBidi.NORMAL
            case "embed":
                return UnicodeBidi.EMBED
            case "bidiOverride":
                return UnicodeBidi.BIDI_OVERRIDE
            case _:
                raise ValueError(value)


class WrapOption(Enum):
    WRAP = "wrap"
    NO_WRAP = "noWrap"

    @staticmethod
    def parse(value: str) -> "WrapOption":
        match value.strip():
            case "wrap":
                return WrapOption.WRAP
            case "noWrap":
                return WrapOption.NO_WRAP
            case _:
                raise ValueError(value)


class WritingMode(Enum):
    LRTB = "lrtb"
    RLTB = "rltb"
    TBRL = "tbrl"
    TBLR = "tblr"

    @staticmethod
    def parse(value: str) -> "WritingMode":
        match value.strip():
            case "lrtb" | "lr":
                return WritingMode.LRTB
            case "rltb" | "rl":
                return WritingMode.RLTB
            case "tbrl" | "tb":
                return WritingMode.TBRL
            case "tblr":
                return WritingMode.TBLR
            case _:
                raise ValueError(value)


class Br:
    pass


def default_font_family() -> list[str]:
    return ["default"]


@dataclass
class Span:
    id: str = ""
    language: str = ""
    space: Space = Space.DEFAULT
    background_color: Color = Color.transparent()
    color: Color = Color.white()
    direction: Direction = Direction.LTR
    font_family: list[str] = field(default_factory=default_font_family)
    font_size: FontSize = FontSize(1.0)
    font_style: FontStyle = FontStyle.NORMAL
    font_weight: FontWeight = FontWeight.NORMAL
    text_decoration: TextDecoration = TextDecoration.NONE
    text_outline: TextOutline | None = None
    unicode_bidi: UnicodeBidi = UnicodeBidi.NORMAL
    wrap_option: WrapOption = WrapOption.WRAP
    text: str = ""


@dataclass
class Paragraph:
    id: str = ""
    begin_secs: float = 0.0
    end_secs: float = 0.0
    region_index: int = 0
    language: str = ""
    space: Space = Space.DEFAULT
    background_color: Color = Color.transparent()
    direction: Direction = Direction.LTR
    fill_line_gap: bool = False
    line_height: LineHeight | None = None
    line_padding: LinePadding = LinePadding(0.0)
    multi_row_align: MultiRowAlign = MultiRowAlign.AUTO
    text_align: TextAlign = TextAlign.START
    unicode_bidi: UnicodeBidi = UnicodeBidi.NORMAL
    contents: list[Br | Span] = field(default_factory=list)


@dataclass
class Div:
    id: str = ""
    language: str = ""
    background_color: Color = Color.transparent()
    paragraphs: list[Paragraph] = field(default_factory=list)


@dataclass
class Body:
    background_color: Color = Color.transparent()
    divs: list[Div] = field(default_factory=list)


@dataclass
class Region:
    origin: Origin = Origin()
    extent: Extent = Extent()
    display_align: DisplayAlign = DisplayAlign.BEFORE
    overflow: Overflow = Overflow.HIDDEN
    padding: Padding = Padding()
    show_background: ShowBackground = ShowBackground.ALWAYS
    writing_mode: WritingMode = WritingMode.LRTB


@dataclass
class Document:
    active_area: ActiveArea = ActiveArea()
    cell_resolution: CellResolution = CellResolution()
    language: str = ""
    space: Space = Space.DEFAULT
    regions: list[Region] = field(default_factory=list)
    body: Body = field(default_factory=Body)


class StyleProperties(TypedDict, total=False):
    background_color: Color
    color: Color
    direction: Direction
    fill_line_gap: bool
    font_family: list[str]
    font_size: FontSize
    font_style: FontStyle
    font_weight: FontWeight
    line_height: LineHeight | None
    line_padding: LinePadding
    multi_row_align: MultiRowAlign
    text_align: TextAlign
    text_decoration: TextDecoration
    text_outline: TextOutline | None
    unicode_bidi: UnicodeBidi
    wrap_option: WrapOption


COMPUTE_FONT_SIZE_BIT = 1
COMPUTE_LINE_HEIGHT_BIT = 2
COMPUTE_LINE_PADDING_BIT = 4
COMPUTE_TEXT_OUTLINE_BIT = 8

COMPUTE_ALL_MASK = (
    COMPUTE_FONT_SIZE_BIT
    | COMPUTE_LINE_HEIGHT_BIT
    | COMPUTE_LINE_PADDING_BIT
    | COMPUTE_TEXT_OUTLINE_BIT
)


@dataclass
class ResolvedStyle:
    background_color: Color = Color.transparent()
    color: Color = Color.white()
    direction: Direction = Direction.LTR
    fill_line_gap: bool = False
    font_family: list[str] = field(default_factory=default_font_family)
    font_size: FontSize = FontSize(1.0)
    font_style: FontStyle = FontStyle.NORMAL
    font_weight: FontWeight = FontWeight.NORMAL
    line_height: LineHeight | None = None
    line_padding: LinePadding = LinePadding(0.0)
    multi_row_align: MultiRowAlign = MultiRowAlign.AUTO
    text_align: TextAlign = TextAlign.START
    text_decoration: TextDecoration = TextDecoration.NONE
    text_outline: TextOutline | None = None
    unicode_bidi: UnicodeBidi = UnicodeBidi.NORMAL
    wrap_option: WrapOption = WrapOption.WRAP

    def compute(
        self,
        mask: int,
        parent_font_size: FontSize | None,
        cell_resolution: CellResolution,
    ) -> None:
        compute_font_size = (mask & COMPUTE_FONT_SIZE_BIT) != 0
        if compute_font_size:
            if parent_font_size is None:
                self.font_size = FontSize(self.font_size * 1.0 / cell_resolution.rows)
            else:
                self.font_size = FontSize(self.font_size * parent_font_size)
        if compute_font_size or (mask & COMPUTE_LINE_HEIGHT_BIT) != 0:
            if self.line_height is not None:
                self.line_height = LineHeight(self.line_height * self.font_size)
        if (mask & COMPUTE_LINE_PADDING_BIT) != 0:
            self.line_padding = LinePadding(
                self.line_padding * 1.0 / cell_resolution.columns
            )
        if compute_font_size or (mask & COMPUTE_TEXT_OUTLINE_BIT) != 0:
            if self.text_outline is not None:
                outline = self.text_outline
                thickness = outline.thickness * self.font_size
                if outline.blur_radius is None:
                    blur_radius = None
                else:
                    blur_radius = outline.blur_radius * self.font_size
                self.text_outline = self.text_outline._replace(
                    thickness=thickness, blur_radius=blur_radius
                )

    def inherited(self) -> None:
        self.background_color = Color.transparent()
        self.unicode_bidi = UnicodeBidi.NORMAL

    def merge_properties(self, properties: StyleProperties) -> int:
        mask = 0
        if v := properties.get("background_color"):
            self.background_color = v
        if v := properties.get("color"):
            self.color = v
        if v := properties.get("direction"):
            self.direction = v
        if v := properties.get("fill_line_gap"):
            self.fill_line_gap = v
        if v := properties.get("font_family"):
            self.font_family = v.copy()
        if v := properties.get("font_style"):
            self.font_style = v
        if v := properties.get("font_weight"):
            self.font_weight = v
        if v := properties.get("multi_row_align"):
            self.multi_row_align = v
        if v := properties.get("text_align"):
            self.text_align = v
        if v := properties.get("text_decoration"):
            self.text_decoration = v
        if v := properties.get("unicode_bidi"):
            self.unicode_bidi = v
        if v := properties.get("wrap_option"):
            self.wrap_option = v
        if "line_height" in properties:
            self.line_height = properties["line_height"]
            mask |= COMPUTE_LINE_HEIGHT_BIT
        if "text_outline" in properties:
            self.text_outline = properties["text_outline"]
            mask |= COMPUTE_TEXT_OUTLINE_BIT
        if v := properties.get("font_size"):
            self.font_size = v
            mask |= COMPUTE_FONT_SIZE_BIT
        if v := properties.get("line_padding"):
            self.line_padding = v
            mask |= COMPUTE_LINE_PADDING_BIT
        return mask
