from marker.processors.ignoretext import IgnoreTextProcessor
from marker.schema.blocks import Line, Span, Text
from marker.schema.document import Document
from marker.schema.groups.page import PageGroup
from marker.schema.polygon import PolygonBox


def make_polygon():
    return PolygonBox.from_bbox([0, 0, 10, 10], ensure_nonzero_area=True)


def add_text_block(page: PageGroup, text_value: str) -> Text:
    text_block = page.add_block(Text, make_polygon())
    page.add_structure(text_block)

    line = page.add_full_block(Line(polygon=make_polygon(), page_id=page.page_id))
    text_block.add_structure(line)

    span = page.add_full_block(
        Span(
            polygon=make_polygon(),
            page_id=page.page_id,
            text=text_value,
            font="Times",
            font_weight=400,
            font_size=10,
            minimum_position=0,
            maximum_position=max(0, len(text_value) - 1),
            formats=["plain"],
        )
    )
    line.add_structure(span)
    return text_block


def test_ignoretext_processor_removes_explicit_footer_strings():
    page = PageGroup(
        polygon=make_polygon(),
        page_id=0,
        block_description="Page",
        structure=[],
        children=[],
    )
    footer_like = add_text_block(
        page, "Digitized   by Google  Original from UNIVERSITY OF CALIFORNIA"
    )
    normal_text = add_text_block(page, "Regular paragraph content.")
    document = Document(filepath="test.pdf", pages=[page])

    IgnoreTextProcessor()(document)

    assert footer_like.ignore_for_output is True
    assert normal_text.ignore_for_output is False
