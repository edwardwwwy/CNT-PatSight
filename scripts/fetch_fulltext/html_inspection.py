from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin

from .models import HtmlInspection


SPACE_RE = re.compile(r"\s+")


class ScholarlyHtmlParser(HTMLParser):
    SKIP_TAGS = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form"}
    BLOCK_TAGS = {
        "p", "div", "section", "article", "li", "h1", "h2", "h3", "h4", "h5", "h6",
        "figcaption", "caption", "tr", "br",
    }

    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=True)
        self.base_url = base_url
        self.skip_depth = 0
        self.tag_stack: list[str] = []
        self.current_heading = ""
        self.heading_level = 0
        self.heading_parts: list[str] = []
        self.headings: list[str] = []
        self.text_parts: list[str] = []
        self.title = ""
        self.in_title = False
        self.title_parts: list[str] = []
        self.pdf_links: list[str] = []
        self.anchor_href = ""
        self.anchor_parts: list[str] = []
        self.article_seen = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        attributes = {key.lower(): value or "" for key, value in attrs}
        self.tag_stack.append(tag)
        if tag in self.SKIP_TAGS:
            self.skip_depth += 1
        if self.skip_depth:
            return
        if tag == "article":
            self.article_seen = True
        if tag == "title":
            self.in_title = True
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6"}:
            self.current_heading = tag
            self.heading_level = int(tag[1])
            self.heading_parts = []
            self.text_parts.append("\n")
        if tag in self.BLOCK_TAGS:
            self.text_parts.append("\n")
        if tag == "meta":
            name = (attributes.get("name") or attributes.get("property") or "").lower()
            content = attributes.get("content", "").strip()
            if name in {"citation_pdf_url", "dc.identifier.pdf", "eprints.document_url"} and content:
                self._add_pdf_link(content)
            if name in {"citation_title", "dc.title", "og:title"} and content and not self.title:
                self.title = SPACE_RE.sub(" ", content).strip()
        if tag == "link":
            href = attributes.get("href", "")
            media_type = attributes.get("type", "").lower()
            rel = attributes.get("rel", "").lower()
            if href and ("pdf" in media_type or "alternate" in rel and href.lower().endswith(".pdf")):
                self._add_pdf_link(href)
        if tag == "a":
            self.anchor_href = attributes.get("href", "")
            self.anchor_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP_TAGS and self.skip_depth:
            self.skip_depth -= 1
        if not self.skip_depth:
            if tag == "title":
                self.in_title = False
                if not self.title:
                    self.title = SPACE_RE.sub(" ", " ".join(self.title_parts)).strip()
            if tag in {"h1", "h2", "h3", "h4", "h5", "h6"} and self.current_heading:
                heading = SPACE_RE.sub(" ", " ".join(self.heading_parts)).strip()
                if heading:
                    self.headings.append(heading)
                self.current_heading = ""
                self.heading_parts = []
                self.text_parts.append("\n")
            if tag == "a" and self.anchor_href:
                label = SPACE_RE.sub(" ", " ".join(self.anchor_parts)).strip().lower()
                href = self.anchor_href
                if href and ("pdf" in label or re.search(r"\.pdf(?:$|[?#])", href, flags=re.I)):
                    self._add_pdf_link(href)
                self.anchor_href = ""
                self.anchor_parts = []
            if tag in self.BLOCK_TAGS:
                self.text_parts.append("\n")
        if self.tag_stack:
            self.tag_stack.pop()

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        text = SPACE_RE.sub(" ", data).strip()
        if not text:
            return
        if self.in_title:
            self.title_parts.append(text)
        if self.anchor_href:
            self.anchor_parts.append(text)
        if self.current_heading:
            self.heading_parts.append(text)
        self.text_parts.append(text)

    def _add_pdf_link(self, href: str) -> None:
        url = urljoin(self.base_url, href.strip())
        if url.startswith(("http://", "https://")) and url not in self.pdf_links:
            self.pdf_links.append(url)


def inspect_html(content: bytes, base_url: str, content_type: str = "") -> HtmlInspection:
    charset = "utf-8"
    match = re.search(r"charset=([\w.-]+)", content_type, flags=re.I)
    if match:
        charset = match.group(1)
    try:
        decoded = content.decode(charset, errors="replace")
    except LookupError:
        decoded = content.decode("utf-8", errors="replace")
    parser = ScholarlyHtmlParser(base_url)
    try:
        parser.feed(decoded)
    except Exception:
        pass
    raw_text = " ".join(parser.text_parts)
    text = re.sub(r"\n\s*\n+", "\n\n", re.sub(r"[ \t]+", " ", raw_text)).strip()
    lower = text.lower()
    markers = {
        "abstract": bool(re.search(r"\babstract\b", lower)),
        "introduction": bool(re.search(r"\bintroduction\b", lower)),
        "methods": bool(re.search(r"\b(?:methods?|experimental|materials and methods)\b", lower)),
        "results": bool(re.search(r"\bresults?(?: and discussion)?\b", lower)),
        "conclusion": bool(re.search(r"\bconclusions?\b", lower)),
        "references": bool(re.search(r"\breferences\b", lower)),
    }
    marker_count = sum(markers.values())
    length = len(text)
    likely = (length >= 5000 and marker_count >= 4) or (parser.article_seen and length >= 8000 and marker_count >= 3)
    note = f"visible_chars={length}; scholarly_markers={marker_count}; article_tag={parser.article_seen}"
    return HtmlInspection(
        title=parser.title,
        text=text,
        headings=list(dict.fromkeys(parser.headings)),
        pdf_links=parser.pdf_links[:20],
        is_likely_fulltext=likely,
        validation_note=note,
    )
