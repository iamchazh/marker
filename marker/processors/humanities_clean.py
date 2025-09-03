import re
import re
from pydantic import BaseModel

from marker.processors import BaseProcessor
from marker.processors.ignoretext import IgnoreTextProcessor
from marker.schema import BlockTypes
from marker.schema.document import Document


class HumanitiesCleanConfig(BaseModel):
    normalize_quotes: bool = True
    collapse_whitespace: bool = True
    run_ignore_processor: bool = True
    ignore_patterns: list[str] = [
        r"^copyright",
        r"all rights reserved",
        r"publisher",
        r"series information",
        r"^index$",
        r"works cited",
        r"bibliography",
    ]


class HumanitiesCleanProcessor(BaseProcessor):
    """Clean and normalize text for humanities and scholarly documents."""

    block_types = (BlockTypes.Span,)
    normalize_quotes: bool = True
    collapse_whitespace: bool = True
    run_ignore_processor: bool = True
    ignore_patterns: list[str] = []

    def __init__(self, config: HumanitiesCleanConfig | None = None):
        super().__init__(config or HumanitiesCleanConfig())

    def __call__(self, document: Document):
        if self.run_ignore_processor:
            IgnoreTextProcessor()(document)

        if self.ignore_patterns:
            compiled = [re.compile(p, re.I) for p in self.ignore_patterns]
            for block in document.contained_blocks(
                (BlockTypes.Text, BlockTypes.SectionHeader)
            ):
                text = block.raw_text(document)
                if any(p.search(text) for p in compiled):
                    block.ignore_for_output = True

        for span in document.contained_blocks(self.block_types):
            text = span.text
            if self.normalize_quotes:
                text = (
                    text.replace("“", '"')
                    .replace("”", '"')
                    .replace("‘", "'")
                    .replace("’", "'")
                )
            if self.collapse_whitespace:
                text = re.sub(r"\s+", " ", text)
            span.text = text
