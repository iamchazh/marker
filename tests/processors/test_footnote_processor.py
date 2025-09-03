import pytest

from marker.processors.footnote import FootnoteProcessor
from marker.schema import BlockTypes


@pytest.mark.filename("population_stats.pdf")
@pytest.mark.config({"page_range": [4]})
def test_footnote_processor(pdf_document):
    processor = FootnoteProcessor()
    processor(pdf_document)

    page0_footnotes = pdf_document.pages[0].contained_blocks(pdf_document, [BlockTypes.Footnote])
    assert len(page0_footnotes) >= 2

    assert page0_footnotes[-1].raw_text(pdf_document).strip().startswith("5")


@pytest.mark.filename("population_stats.pdf")
@pytest.mark.config({"page_range": [4, 5]})
def test_footnote_processor_endnotes(pdf_document):
    processor = FootnoteProcessor({"push_to_end": True})
    processor(pdf_document)

    first_page = pdf_document.pages[0]
    last_page = pdf_document.pages[-1]

    assert (
        len(first_page.contained_blocks(pdf_document, [BlockTypes.Footnote])) == 0
    )
    assert len(last_page.contained_blocks(pdf_document, [BlockTypes.Footnote])) >= 2
