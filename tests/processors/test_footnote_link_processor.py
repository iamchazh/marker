from marker.processors.footnote_link import FootnoteLinkProcessor
from marker.schema import BlockTypes
from marker.schema.blocks import Footnote, Line, Reference, Span, Text
from marker.schema.document import Document
from marker.schema.groups.page import PageGroup
from marker.schema.polygon import PolygonBox


def make_polygon():
    return PolygonBox.from_bbox([0, 0, 10, 10], ensure_nonzero_area=True)


def add_line_with_span(
    page: PageGroup,
    parent_block,
    text: str,
    *,
    superscript: bool = False,
    has_superscript: bool = False,
) -> Span:
    line = page.add_full_block(Line(polygon=make_polygon(), page_id=page.page_id))
    parent_block.add_structure(line)

    formats = ["superscript"] if superscript else ["plain"]
    span = page.add_full_block(
        Span(
            polygon=make_polygon(),
            page_id=page.page_id,
            text=text,
            font="Times",
            font_weight=400,
            font_size=10,
            minimum_position=0,
            maximum_position=max(0, len(text) - 1),
            formats=formats,
            has_superscript=has_superscript,
        )
    )
    line.add_structure(span)
    return span


def build_page_with_text_and_footnote(footnote_text: str):
    page = PageGroup(
        polygon=make_polygon(),
        page_id=0,
        block_description="Page",
        structure=[],
        children=[],
    )

    body = page.add_block(Text, make_polygon())
    page.add_structure(body)

    footnote = page.add_block(Footnote, make_polygon())
    page.add_structure(footnote)

    add_line_with_span(page, footnote, footnote_text)
    return page, body, footnote


def test_footnote_link_processor_links_numeric_superscripts():
    page, body, footnote = build_page_with_text_and_footnote("1. Footnote body.")
    body_span = add_line_with_span(page, body, "1", superscript=True)
    document = Document(filepath="test.pdf", pages=[page])

    FootnoteLinkProcessor()(document)

    assert body_span.url == "#page-0-footnote-1"
    assert body_span.text == "1"
    assert body_span.has_superscript is False
    assert "superscript" not in body_span.formats

    refs = footnote.contained_blocks(document, (BlockTypes.Reference,))
    assert len(refs) == 1
    assert refs[0].ref == "page-0-footnote-1"


def test_footnote_link_processor_reuses_existing_anchor():
    page, body, footnote = build_page_with_text_and_footnote("1. Footnote body.")
    body_span = add_line_with_span(page, body, "1", has_superscript=True)

    existing_ref = page.add_full_block(
        Reference(ref="page-0-custom", polygon=make_polygon(), page_id=page.page_id)
    )
    footnote.structure.insert(0, existing_ref.id)

    document = Document(filepath="test.pdf", pages=[page])
    FootnoteLinkProcessor()(document)

    assert body_span.url == "#page-0-custom"
    refs = footnote.contained_blocks(document, (BlockTypes.Reference,))
    assert len(refs) == 1


def test_footnote_link_processor_ignores_non_numeric_markers():
    page, body, _ = build_page_with_text_and_footnote("* Equal contribution.")
    body_span = add_line_with_span(page, body, "*", superscript=True)
    document = Document(filepath="test.pdf", pages=[page])

    FootnoteLinkProcessor()(document)

    assert body_span.url is None
    assert body_span.text == "*"
    assert "superscript" in body_span.formats
