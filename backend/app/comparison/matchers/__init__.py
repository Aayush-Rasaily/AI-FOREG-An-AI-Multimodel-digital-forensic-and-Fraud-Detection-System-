"""Comparison matcher plugins."""

from backend.app.comparison.matchers.image_matcher import ImageMatcher
from backend.app.comparison.matchers.layout_matcher import LayoutMatcher
from backend.app.comparison.matchers.metadata_matcher import MetadataMatcher
from backend.app.comparison.matchers.pdf_matcher import PdfMatcher
from backend.app.comparison.matchers.signature_stub import SignatureMatcher
from backend.app.comparison.matchers.text_matcher import TextMatcher

__all__ = [
    "ImageMatcher",
    "LayoutMatcher",
    "MetadataMatcher",
    "PdfMatcher",
    "SignatureMatcher",
    "TextMatcher",
]
