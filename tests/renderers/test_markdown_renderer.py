import pytest

from marker.processors.footnote_link import FootnoteLinkProcessor
from marker.renderers.markdown import MarkdownRenderer
from marker.schema import BlockTypes
from marker.schema.blocks import Footnote, Line, Span, TableCell, Text
from marker.schema.document import Document
from marker.schema.groups.page import PageGroup
from marker.schema.polygon import PolygonBox


@pytest.mark.config({"page_range": [0], "disable_ocr": True})
def test_markdown_renderer(pdf_document):
    renderer = MarkdownRenderer()
    md = renderer(pdf_document).markdown

    # Verify markdown
    assert "# Subspace Adversarial Training" in md


@pytest.mark.config({"page_range": [0]})
def test_markdown_renderer_auto_ocr(pdf_document):
    renderer = MarkdownRenderer()
    md = renderer(pdf_document).markdown

    # Verify markdown
    assert "Subspace Adversarial Training" in md


@pytest.mark.config({"page_range": [0, 1], "paginate_output": True})
def test_markdown_renderer_pagination(pdf_document):
    renderer = MarkdownRenderer({"paginate_output": True})
    md = renderer(pdf_document).markdown

    assert "\n\n{0}-" in md
    assert "\n\n{1}-" in md


@pytest.mark.config({"page_range": [0, 1], "paginate_output": True})
def test_markdown_renderer_pagination_blank_last_page(pdf_document):
    # Clear all children and structure from the last page to simulate a blank page
    last_page = pdf_document.pages[-1]
    last_page.children = []
    last_page.structure = []

    renderer = MarkdownRenderer({"paginate_output": True})
    md = renderer(pdf_document).markdown

    # Should end with pagination marker and preserve trailing newlines
    assert md.endswith("}\n\n") or md.endswith(
        "}------------------------------------------------\n\n"
    )


@pytest.mark.config({"page_range": [0, 1]})
def test_markdown_renderer_metadata(pdf_document):
    renderer = MarkdownRenderer({"paginate_output": True})
    metadata = renderer(pdf_document).metadata
    assert "table_of_contents" in metadata


@pytest.mark.config({"page_range": [0, 1]})
def test_markdown_renderer_images(pdf_document):
    renderer = MarkdownRenderer({"extract_images": False})
    markdown_output = renderer(pdf_document)

    assert len(markdown_output.images) == 0
    assert "![](" not in markdown_output.markdown


@pytest.mark.config({"page_range": [5]})
def test_markdown_renderer_tables(pdf_document):
    table = pdf_document.contained_blocks((BlockTypes.Table,))[0]
    page = pdf_document.pages[0]

    cell = TableCell(
        polygon=table.polygon,
        text_lines=["54<i>.45</i>67<br>89<math>x</math>"],
        rowspan=1,
        colspan=1,
        row_id=0,
        col_id=0,
        is_header=False,
        page_id=page.page_id,
    )
    page.add_full_block(cell)
    table.structure = []
    table.add_structure(cell)

    renderer = MarkdownRenderer()
    md = renderer(pdf_document).markdown
    assert "54 <i>.45</i> 67<br>89 $x$" in md


def make_polygon():
    return PolygonBox.from_bbox([0, 0, 10, 10], ensure_nonzero_area=True)


def add_span(page: PageGroup, parent_block, text: str, superscript: bool = False) -> Span:
    line = page.add_full_block(Line(polygon=make_polygon(), page_id=page.page_id))
    parent_block.add_structure(line)
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
            formats=["superscript"] if superscript else ["plain"],
            has_superscript=superscript,
        )
    )
    line.add_structure(span)
    return span


def test_markdown_renderer_default_pagination_and_footnote_section():
    page = PageGroup(
        polygon=make_polygon(),
        page_id=0,
        block_description="Page",
        structure=[],
        children=[],
    )

    body = page.add_block(Text, make_polygon())
    page.add_structure(body)
    add_span(page, body, "Body text ")
    add_span(page, body, "1", superscript=True)

    footnote = page.add_block(Footnote, make_polygon())
    page.add_structure(footnote)
    add_span(page, footnote, "1. Footnote content.")

    document = Document(filepath="test.pdf", pages=[page])
    FootnoteLinkProcessor()(document)

    md = MarkdownRenderer({"extract_images": False})(document).markdown
    assert "\n\n{0}-" in md
    assert "[1](#page-0-footnote-1)" in md
    assert "**Footnotes**" in md
    assert "<span id=\"page-0-footnote-1\"></span>" in md
