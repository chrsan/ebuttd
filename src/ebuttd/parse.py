import functools
import xml.etree.ElementTree as ET

from collections import deque

from . import model

XML_NS = "http://www.w3.org/XML/1998/namespace"

TT_NS = "http://www.w3.org/ns/ttml"
TTP_NS = "http://www.w3.org/ns/ttml#parameter"
TTS_NS = "http://www.w3.org/ns/ttml#styling"
TTM_NS = "http://www.w3.org/ns/ttml#metadata"

EBUTTM_NS = "urn:ebu:tt:metadata"
EBUTTS_NS = "urn:ebu:tt:style"
EBUTTDT_NS = "urn:ebu:tt:datatypes"

ITTP_NS = "http://www.w3.org/ns/ttml/profile/imsc1#parameter"
ITTS_NS = "http://www.w3.org/ns/ttml/profile/imsc1#styling"

ID_ATTR = f"{{{XML_NS}}}id"
LANG_ATTR = f"{{{XML_NS}}}lang"
SPACE_ATTR = f"{{{XML_NS}}}space"

TT_ELEM = f"{{{TT_NS}}}tt"
TIME_BASE_ATTR = f"{{{TTP_NS}}}timeBase"
ACTIVE_AREA_ATTR = f"{{{ITTP_NS}}}activeArea"
CELL_RESOLUTION_ATTR = f"{{{TTP_NS}}}cellResolution"

HEAD_ELEM = f"{{{TT_NS}}}head"
STYLING_ELEM = f"{{{TT_NS}}}styling"
LAYOUT_ELEM = f"{{{TT_NS}}}layout"

STYLE_ELEM = f"{{{TT_NS}}}style"
BACKGROUND_COLOR_ATTR = f"{{{TTS_NS}}}backgroundColor"
COLOR_ATTR = f"{{{TTS_NS}}}color"
DIRECTION_ATTR = f"{{{TTS_NS}}}direction"
FILL_LINE_GAP_ATTR = f"{{{ITTS_NS}}}fillLineGap"
FONT_FAMILY_ATTR = f"{{{TTS_NS}}}fontFamily"
FONT_SIZE_ATTR = f"{{{TTS_NS}}}fontSize"
FONT_STYLE_ATTR = f"{{{TTS_NS}}}fontStyle"
FONT_WEIGHT_ATTR = f"{{{TTS_NS}}}fontWeight"
LINE_HEIGHT_ATTR = f"{{{TTS_NS}}}lineHeight"
LINE_PADDING_ATTR = f"{{{EBUTTS_NS}}}linePadding"
MULTI_ROW_ALIGN_ATTR = f"{{{EBUTTS_NS}}}multiRowAlign"
TEXT_ALIGN_ATTR = f"{{{TTS_NS}}}textAlign"
TEXT_DECORATION_ATTR = f"{{{TTS_NS}}}textDecoration"
TEXT_OUTLINE_ATTR = f"{{{TTS_NS}}}textOutline"
UNICODE_BIDI_ATTR = f"{{{TTS_NS}}}unicodeBidi"
WRAP_OPTION_ATTR = f"{{{TTS_NS}}}wrapOption"

REGION_ELEM = f"{{{TT_NS}}}region"
ORIGIN_ATTR = f"{{{TTS_NS}}}origin"
EXTENT_ATTR = f"{{{TTS_NS}}}extent"
DISPLAY_ALIGN_ATTR = f"{{{TTS_NS}}}displayAlign"
OVERFLOW_ATTR = f"{{{TTS_NS}}}overflow"
PADDING_ATTR = f"{{{TTS_NS}}}padding"
SHOW_BACKGROUND_ATTR = f"{{{TTS_NS}}}showBackground"
WRITING_MODE_ATTR = f"{{{TTS_NS}}}writingMode"

BODY_ELEM = f"{{{TT_NS}}}body"
DIV_ELEM = f"{{{TT_NS}}}div"
P_ELEM = f"{{{TT_NS}}}p"
BR_ELEM = f"{{{TT_NS}}}br"
SPAN_ELEM = f"{{{TT_NS}}}span"


class Context:
    document: model.Document
    ids: set[str]
    styles: dict[str, model.StyleProperties]
    regions: dict[str, tuple[int, str]]

    def __init__(self, document: model.Document) -> None:
        self.document = document
        self.ids = set()
        self.styles = dict()
        self.regions = dict()

    def add_id(self, id: str) -> None:
        if id in self.ids:
            raise ParseError(f"Non unique identifier: {id}")
        self.ids.add(id)


class ParseError(Exception):
    pass


def parse(input: str) -> model.Document:
    root = ET.fromstring(input)
    if root.tag != TT_ELEM:
        raise ParseError(f"Invalid root element: {root.tag}")
    match root.get(TIME_BASE_ATTR):
        case None:
            raise ParseError("Missing `timeBase` attribute")
        case v if v != "media":
            raise ParseError(f"Invalid `timeBase` attribute: {v}")
    document = model.Document()
    if v := root.get(ACTIVE_AREA_ATTR):
        document.active_area = model.ActiveArea.parse(v)
    if v := root.get(CELL_RESOLUTION_ATTR):
        document.cell_resolution = model.CellResolution.parse(v)
    if (v := root.get(LANG_ATTR)) is not None:
        document.language = v.strip()
    else:
        raise ParseError("Missing attribute `lang`")
    if v := root.get(SPACE_ATTR):
        document.space = model.Space.parse(v)
    ctx = Context(document)
    _parse_head(root, ctx)
    _parse_body(root, ctx)
    return document


def _parse_id(elem: ET.Element, required: bool = False) -> str:
    if v := elem.get(ID_ATTR):
        if s := v.strip():
            return s
        raise ParseError(f"Empty `id` attribute on {elem.tag}")
    if required:
        raise ParseError(f"Missing `id` attribute on {elem.tag}")
    return ""


def _parse_head(root: ET.Element, ctx: Context) -> None:
    head, count = functools.reduce(
        lambda acc, elem: (elem, acc[1] + 1), root.iterfind(HEAD_ELEM), (None, 0)
    )
    if head is None:
        raise ParseError("Missing element `head`")
    if count > 1:
        raise ParseError("Multiple `head` elements")
    styling_count = 0
    layout_count = 0
    for elem in head:
        if elem.tag == STYLING_ELEM:
            if styling_count != 0:
                raise ParseError("Multiple `styling` elements")
            styling_count += 1
            _parse_styles(elem, ctx)
            if not ctx.styles:
                raise ParseError("Missing element `style`")
        elif elem.tag == LAYOUT_ELEM:
            if layout_count != 0:
                raise ParseError("Multiple `layout` elements")
            layout_count += 1
            _parse_regions(elem, ctx)
            if not ctx.document.regions:
                raise ParseError("Missing element `region`")
    if styling_count == 0:
        raise ParseError("Missing element `styling`")
    if layout_count == 0:
        raise ParseError("Missing element `layout`")


def _parse_styles(styling: ET.Element, ctx: Context) -> None:
    for elem in styling:
        if elem.tag != STYLE_ELEM:
            continue
        id = _parse_id(elem, required=True)
        ctx.add_id(id)
        properties = model.StyleProperties()
        for name, value in elem.items():
            if name == BACKGROUND_COLOR_ATTR:
                properties["background_color"] = model.Color.parse(value)
            elif name == COLOR_ATTR:
                properties["color"] = model.Color.parse(value)
            elif name == DIRECTION_ATTR:
                properties["direction"] = model.Direction.parse(value)
            elif name == FILL_LINE_GAP_ATTR:
                match value.strip():
                    case "true":
                        properties["fill_line_gap"] = True
                    case "false":
                        properties["fill_line_gap"] = False
                    case _:
                        raise ParseError(f"Invaid `fillLineGap` attribute: {value}")
            elif name == FONT_FAMILY_ATTR:
                properties["font_family"] = [v for v in value.strip().split(",") if v]
            elif name == FONT_SIZE_ATTR:
                properties["font_size"] = model.FontSize.parse(value)
            elif name == FONT_STYLE_ATTR:
                properties["font_style"] = model.FontStyle.parse(value)
            elif name == FONT_WEIGHT_ATTR:
                properties["font_weight"] = model.FontWeight.parse(value)
            elif name == LINE_HEIGHT_ATTR:
                properties["line_height"] = model.LineHeight.parse(value)
            elif name == LINE_PADDING_ATTR:
                properties["line_padding"] = model.LinePadding.parse(value)
            elif name == MULTI_ROW_ALIGN_ATTR:
                properties["multi_row_align"] = model.MultiRowAlign.parse(value)
            elif name == TEXT_ALIGN_ATTR:
                properties["text_align"] = model.TextAlign.parse(value)
            elif name == TEXT_DECORATION_ATTR:
                properties["text_decoration"] = model.TextDecoration.parse(value)
            elif name == TEXT_OUTLINE_ATTR:
                properties["text_outline"] = model.TextOutline.parse(value)
            elif name == UNICODE_BIDI_ATTR:
                properties["unicode_bidi"] = model.UnicodeBidi.parse(value)
            elif name == WRAP_OPTION_ATTR:
                properties["wrap_option"] = model.WrapOption.parse(value)
        ctx.styles[id] = properties


def _parse_regions(layout: ET.Element, ctx: Context) -> None:
    for elem in layout:
        if elem.tag != REGION_ELEM:
            continue
        id = _parse_id(elem, required=True)
        ctx.add_id(id)
        region = model.Region()
        origin_parsed = False
        extent_parsed = False
        style = ""
        for name, value in elem.items():
            if name == ORIGIN_ATTR:
                region.origin = model.Origin.parse(value)
                origin_parsed = True
            elif name == EXTENT_ATTR:
                region.extent = model.Extent.parse(value)
                extent_parsed = True
            elif name == "style":
                style = value.strip()
            elif name == DISPLAY_ALIGN_ATTR:
                region.display_align = model.DisplayAlign.parse(value)
            elif name == OVERFLOW_ATTR:
                region.overflow = model.Overflow.parse(value)
            elif name == PADDING_ATTR:
                region.padding = model.Padding.parse(value)
            elif name == SHOW_BACKGROUND_ATTR:
                region.show_background = model.ShowBackground.parse(value)
            elif name == WRITING_MODE_ATTR:
                region.writing_mode = model.WritingMode.parse(value)
        if not origin_parsed:
            raise ParseError("Missing `origin` attribute")
        if not extent_parsed:
            raise ParseError("Missing `extent` attribute")
        ctx.regions[id] = (len(ctx.document.regions), style)
        ctx.document.regions.append(region)


def _resolve_style(style_stack: deque[str], ctx: Context) -> model.ResolvedStyle:
    resolved_style = model.ResolvedStyle()
    resolved_style.compute(
        mask=model.COMPUTE_ALL_MASK,
        parent_font_size=None,
        cell_resolution=ctx.document.cell_resolution,
    )
    parent_font_size = resolved_style.font_size
    for index, value in enumerate(style_stack):
        if index != 0:
            resolved_style.inherited()
        for id in value.split(" "):
            if not id:
                continue
            properties = ctx.styles.get(id)
            if properties is None:
                raise ParseError("Invalid style id: {id}")
            mask = resolved_style.merge_properties(properties)
            resolved_style.compute(
                mask=mask,
                parent_font_size=parent_font_size,
                cell_resolution=ctx.document.cell_resolution,
            )
            parent_font_size = resolved_style.font_size
    return resolved_style


def _parse_body(root: ET.Element, ctx: Context) -> None:
    body, count = functools.reduce(
        lambda acc, elem: (elem, acc[1] + 1), root.iterfind(BODY_ELEM), (None, 0)
    )
    if body is None:
        raise ParseError("Missing element `body`")
    if count > 1:
        raise ParseError("Multiple `body` elements")
    style_stack = deque()
    if value := body.get("style", "").strip():
        style_stack.append(value)
    resolved_style = _resolve_style(style_stack, ctx)
    ctx.document.body.background_color = resolved_style.background_color
    _parse_div(body, style_stack, ctx)


def _parse_div(body: ET.Element, style_stack: deque[str], ctx: Context) -> None:
    for elem in body:
        if elem.tag != DIV_ELEM:
            continue
        if id := _parse_id(elem, required=False):
            ctx.add_id(id)
        region_index = -1
        region_style = ""
        if region_id := elem.get("region", "").strip():
            if pair := ctx.regions.get(region_id):
                region_index = pair[0]
                region_style = pair[1]
            else:
                raise ParseError(f"Invalid region identifier: {region_id}")
        if region_style:
            style_stack.appendleft(region_style)
        style = elem.get("style", "").strip()
        if style:
            style_stack.append(style)
        background_color = _resolve_style(style_stack, ctx).background_color
        language = elem.get(LANG_ATTR, "").strip()
        div = model.Div(id=id, language=language, background_color=background_color)
        ctx.document.body.divs.append(div)
        _parse_para(elem, style_stack, region_index, ctx)
        if style:
            style_stack.pop()
        if region_style:
            style_stack.popleft()
    if not ctx.document.body.divs:
        raise ParseError("Missing element `div`")


class Scanner:
    def __init__(self, input: str) -> None:
        self.input = input

    def scan_char(self, c: str) -> None:
        if self.input and self.input[0] == c:
            self.input = self.input[1:]
        else:
            raise ValueError()

    def scan_int(self, num_digits: int = 0, limit: int = 0) -> int:
        count = 0
        for c in self.input:
            if c.isascii() and c.isdecimal():
                count += 1
            else:
                break
        if count == 0 or (num_digits > 0 and count != num_digits):
            raise ValueError()
        n = int(self.input[:count])
        if limit > 0 and n > limit:
            raise ValueError()
        self.input = self.input[count:]
        return n


def _parse_timecode(attr: str, input: str) -> float:
    scanner = Scanner(input)
    try:
        secs = scanner.scan_int() * 3600.0
        scanner.scan_char(":")
        secs += scanner.scan_int(num_digits=2, limit=59) * 60.0
        scanner.scan_char(":")
        secs += scanner.scan_int(num_digits=2, limit=59)
        scanner.scan_char(".")
        secs += scanner.scan_int(num_digits=3) * 0.001
    except ValueError:
        raise ParseError(f"Invalid `{attr}` attribute value: {input}")
    if scanner.input:
        raise ParseError(f"Invalid `{attr}` attribute value: {input}")
    return secs


def _parse_para(
    div: ET.Element, style_stack: deque[str], parent_region_index: int, ctx: Context
) -> None:
    paragraphs = ctx.document.body.divs[-1].paragraphs
    for elem in div:
        if elem.tag != P_ELEM:
            continue
        id = _parse_id(elem, required=True)
        ctx.add_id(id)
        if v := elem.get("begin"):
            begin = _parse_timecode("begin", v.strip())
        else:
            raise ParseError("Missing `begin` attribute")
        if v := elem.get("end"):
            end = _parse_timecode("end", v.strip())
        else:
            raise ParseError("Missing `end` attribute")
        region_index = -1
        region_style = ""
        if region_id := elem.get("region", "").strip():
            if pair := ctx.regions.get(region_id):
                region_index = pair[0]
                region_style = pair[1]
            else:
                raise ParseError(f"Invalid region identifier: {region_id}")
        if region_index != -1 and parent_region_index != -1:
            raise ParseError("Multiple regions")
        if region_index == -1:
            if parent_region_index == -1:
                raise ParseError("Missing `region` attribute")
            region_index = parent_region_index
        if region_style:
            style_stack.appendleft(region_style)
        style = elem.get("style", "").strip()
        if style:
            style_stack.append(style)
        resolved_style = _resolve_style(style_stack, ctx)
        language = elem.get(LANG_ATTR, "").strip()
        space = model.Space.DEFAULT
        if v := elem.get(SPACE_ATTR):
            space = model.Space.parse(v)
        para = model.Paragraph(
            id=id,
            begin_secs=begin,
            end_secs=end,
            region_index=region_index,
            language=language,
            space=space,
            background_color=resolved_style.background_color,
            direction=resolved_style.direction,
            fill_line_gap=resolved_style.fill_line_gap,
            line_height=resolved_style.line_height,
            line_padding=resolved_style.line_padding,
            multi_row_align=resolved_style.multi_row_align,
            text_align=resolved_style.text_align,
            unicode_bidi=resolved_style.unicode_bidi,
        )
        paragraphs.append(para)
        _parse_paragraph_content(elem, style_stack, ctx)
        if style:
            style_stack.pop()
        if region_style:
            style_stack.popleft()
    if not paragraphs:
        raise ParseError("Missing element `p`")


def _parse_paragraph_content(para: ET.Element, style_stack: deque[str], ctx: Context):
    contents = ctx.document.body.divs[-1].paragraphs[-1].contents
    for elem in para:
        if elem.tag == BR_ELEM:
            contents.append(model.Br())
            continue
        if elem.tag != SPAN_ELEM:
            continue
        if id := _parse_id(elem, required=False):
            ctx.add_id(id)
        style = elem.get("style", "").strip()
        if style:
            style_stack.append(style)
        resolved_style = _resolve_style(style_stack, ctx)
        language = elem.get(LANG_ATTR, "").strip()
        space = model.Space.DEFAULT
        if v := elem.get(SPACE_ATTR):
            space = model.Space.parse(v)
        span = model.Span(
            id=id,
            language=language,
            space=space,
            background_color=resolved_style.background_color,
            color=resolved_style.color,
            direction=resolved_style.direction,
            font_family=resolved_style.font_family,
            font_size=resolved_style.font_size,
            font_style=resolved_style.font_style,
            font_weight=resolved_style.font_weight,
            text_decoration=resolved_style.text_decoration,
            text_outline=resolved_style.text_outline,
            unicode_bidi=resolved_style.unicode_bidi,
            wrap_option=resolved_style.wrap_option,
            text=elem.text or "",
        )
        contents.append(span)
        if style:
            style_stack.pop()
