import re
from typing import Dict, Optional

from marker.processors import BaseProcessor
from marker.schema import BlockTypes
from marker.schema.blocks import Reference
from marker.schema.document import Document
from marker.schema.groups import PageGroup
from marker.schema.registry import get_block_class


class FootnoteLinkProcessor(BaseProcessor):
    """
    Link in-body footnote markers to footnote anchors on the same page.
    """

    marker_pattern = re.compile(r"^\s*(\d+)(?:[\]\).,:\s]*)$")

    def __call__(self, document: Document):
        reference_cls: type[Reference] = get_block_class(BlockTypes.Reference)
        for page in document.pages:
            marker_to_anchor = self.build_footnote_map(page, document, reference_cls)
            if not marker_to_anchor:
                continue
            self.link_body_markers(page, document, marker_to_anchor)

    def build_footnote_map(
        self,
        page: PageGroup,
        document: Document,
        reference_cls: type[Reference],
    ) -> Dict[str, str]:
        marker_to_anchor: Dict[str, str] = {}
        footnotes = page.contained_blocks(document, (BlockTypes.Footnote,))
        for footnote in footnotes:
            anchor = self.ensure_footnote_anchor(
                page, document, footnote, reference_cls
            )
            marker = self.extract_numeric_marker(footnote, document)
            if marker and marker not in marker_to_anchor:
                marker_to_anchor[marker] = anchor
        return marker_to_anchor

    def ensure_footnote_anchor(
        self,
        page: PageGroup,
        document: Document,
        footnote,
        reference_cls: type[Reference],
    ) -> str:
        existing_refs = footnote.contained_blocks(document, (BlockTypes.Reference,))
        if existing_refs:
            return existing_refs[0].ref

        anchor = f"page-{page.page_id}-footnote-{footnote.block_id}"
        ref_block = page.add_full_block(
            reference_cls(ref=anchor, polygon=footnote.polygon, page_id=page.page_id)
        )
        if footnote.structure is None:
            footnote.structure = []
        footnote.structure.insert(0, ref_block.id)
        return anchor

    def extract_numeric_marker(self, footnote, document: Document) -> Optional[str]:
        footnote_spans = footnote.contained_blocks(document, (BlockTypes.Span,))
        if not footnote_spans:
            return None
        return self.normalize_marker(footnote_spans[0].text)

    def normalize_marker(self, text: str) -> Optional[str]:
        marker_match = self.marker_pattern.match(text or "")
        if marker_match:
            return marker_match.group(1)
        return None

    def link_body_markers(
        self, page: PageGroup, document: Document, marker_to_anchor: Dict[str, str]
    ):
        footnotes = page.contained_blocks(document, (BlockTypes.Footnote,))
        footnote_span_ids = {
            span.id for footnote in footnotes for span in footnote.contained_blocks(document, (BlockTypes.Span,))
        }

        spans = page.contained_blocks(document, (BlockTypes.Span,))
        for span in spans:
            if span.id in footnote_span_ids:
                continue
            if not (span.has_superscript or span.superscript):
                continue
            marker = self.normalize_marker(span.text)
            if marker is None:
                continue
            if marker not in marker_to_anchor:
                continue

            span.url = f"#{marker_to_anchor[marker]}"
            span.text = marker
            span.has_superscript = False
            span.formats = [fmt for fmt in span.formats if fmt != "superscript"]
