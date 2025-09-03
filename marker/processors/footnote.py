import re

from marker.processors import BaseProcessor
from marker.schema import BlockTypes
from marker.schema.document import Document
from marker.schema.groups import PageGroup
from typing import Annotated, List


class FootnoteProcessor(BaseProcessor):
    """
    A processor for pushing footnotes to the bottom of the page or the end of the document,
    and relabeling mislabeled text blocks.
    """

    block_types = (BlockTypes.Footnote,)
    push_to_end: Annotated[
        bool,
        "Move all footnotes to the end of the document instead of the bottom of each page.",
    ] = False

    def __call__(self, document: Document):
        if self.push_to_end:
            all_footnotes: List = []
            for page in document.pages:
                footnote_blocks = page.contained_blocks(document, self.block_types)
                for block in footnote_blocks:
                    if block.id in page.structure:
                        page.structure.remove(block.id)
                        all_footnotes.append(block)
                self.assign_superscripts(page, document)

            if all_footnotes:
                last_page = document.pages[-1]
                for block in all_footnotes:
                    block.page_id = last_page.page_id
                    last_page.add_structure(block)
        else:
            for page in document.pages:
                self.push_footnotes_to_bottom(page, document)
                self.assign_superscripts(page, document)

    def push_footnotes_to_bottom(self, page: PageGroup, document: Document):
        footnote_blocks = page.contained_blocks(document, self.block_types)

        # Push footnotes to the bottom
        for block in footnote_blocks:
            # Check if it is top-level
            if block.id in page.structure:
                # Move to bottom if it is
                page.structure.remove(block.id)
                page.add_structure(block)

    def assign_superscripts(self, page: PageGroup, document: Document):
        footnote_blocks = page.contained_blocks(document, self.block_types)

        for block in footnote_blocks:
            for span in block.contained_blocks(document, (BlockTypes.Span,)):
                if re.match(r"^[0-9\W]+", span.text):
                    span.has_superscript = True
                break
