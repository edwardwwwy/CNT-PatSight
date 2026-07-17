from __future__ import annotations

import hashlib
import re
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from .models import CandidateSpan, ExtractionOutput, PageText, TextSection


PARSER_VERSION = "cnt_section_rules_v7"
SPACE_RE = re.compile(r"[ \t]+")
MEASUREMENT_RE = re.compile(
    r"\b\d+(?:\.\d+)?\s*(?:°\s*C|K|sccm|slm|mL(?:\s*min[-−]?1)?|L(?:\s*min[-−]?1)?|min|h|s|wt\.?\s*%|%|g|mg|bar|kPa|MPa|atm|nm|[µu]m|cm[-−]?1|m2\s*g[-−]?1)\b",
    flags=re.I,
)


SECTION_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("abstract", re.compile(r"^abstract\b", re.I)),
    ("introduction", re.compile(r"^(?:introduction|background)\b", re.I)),
    ("catalyst_preparation", re.compile(r"^(?:catalyst|support)\s+(?:preparation|synthesis)|^preparation(?:\s+and\s+characteri[sz]ation)?\s+of\s+.+?catalysts?\b", re.I)),
    ("cvd_growth", re.compile(r"^(?:cnt|carbon\s+nanotube|nanotube)\s+(?:growth|synthesis)|^synthesis(?:\s+and\s+characteri[sz]ation)?\s+of\s+(?:cnts?|carbon\s+nanotubes?)\b|^(?:cvd|ccvd)\s+(?:growth|synthesis)|^growth\s+(?:procedure|experiment)", re.I)),
    ("characterization", re.compile(r"^(?:characteri[sz]ation|analytical\s+methods?|materials?\s+characteri[sz]ation)\b", re.I)),
    ("methods", re.compile(r"^(?:materials?\s+and\s+methods?|methods?|methodology)\b", re.I)),
    ("experimental", re.compile(r"^experimental(?:\s+(?:section|procedure|setup|method))?\b", re.I)),
    ("results", re.compile(r"^results?(?:\s+and\s+discussion)?\b", re.I)),
    ("discussion", re.compile(r"^discussion\b", re.I)),
    ("conclusion", re.compile(r"^(?:conclusions?|summary)\b", re.I)),
    ("references", re.compile(r"^(?:references|bibliography)\b", re.I)),
    ("supplementary_hints", re.compile(r"^(?:supplementary|supporting)\s+(?:information|data|material)\b", re.I)),
]


SPAN_KEYWORDS: dict[str, dict[str, str]] = {
    "catalyst": {
        "catalyst": r"\bcatal(?:yst|ysts|ytic)\b",
        "precursor": r"\bprecursor\b",
        "support": r"\b(?:support|supported|mgo|al2o3|sio2|zeolite)\b",
        "impregnation": r"\bimpregnat(?:ed|ion)\b",
        "sol_gel": r"\bsol[- ]?gel\b",
        "calcination": r"\bcalcina(?:tion|ted|te)\b",
        "reduction": r"\breduc(?:tion|ed|ing)\b",
        "active_metal": r"\b(?:fe|co|ni|mo|iron|cobalt|nickel|molybdenum)\b",
    },
    "process": {
        "cvd": r"\b(?:cvd|ccvd|chemical\s+vapou?r\s+deposition)\b",
        "reactor": r"\b(?:reactor|quartz\s+tube|fluidi[sz]ed\s+bed|fixed\s+bed|furnace)\b",
        "temperature": r"\btemperature\b|°\s*C",
        "pressure": r"\bpressure\b|\b(?:kpa|mpa|bar|atm)\b",
        "time": r"\b(?:reaction|growth|holding|residence)\s+time\b|\b\d+(?:\.\d+)?\s*(?:min|h|s)\b",
        "heating_cooling": r"\b(?:heat(?:ed|ing)|cool(?:ed|ing)|ramp(?:ed|ing))\b",
        "growth": r"\b(?:growth|synthesis|deposition|pyrolysis|decomposition)\b",
    },
    "gas": {
        "methane": r"\b(?:methane|ch4)\b",
        "hydrogen": r"\b(?:hydrogen|h2)\b",
        "inert_gas": r"\b(?:argon|ar|nitrogen|n2|helium|he)\b",
        "reactive_gas": r"\b(?:co2|carbon\s+dioxide|oxygen|o2|steam|nh3|ammonia)\b",
        "flow": r"\b(?:flow|flowrate|flow\s+rate|sccm|slm|ml\s*min)\b",
        "gas_program": r"\b(?:gas\s+mixture|feed\s+gas|carrier\s+gas|atmosphere)\b",
    },
    "yield": {
        "yield": r"\byield\b",
        "conversion": r"\bconversion\b",
        "weight_gain": r"\b(?:weight|mass)\s+gain\b",
        "productivity": r"\bproductivity\b",
        "growth_rate": r"\bgrowth\s+rate\b",
        "carbon_efficiency": r"\bcarbon\s+(?:efficiency|balance|conversion)\b",
        "throughput": r"\b(?:throughput|production\s+rate|capacity)\b",
    },
    "characterization": {
        "microscopy": r"\b(?:tem|hrtem|sem|fe[- ]?sem|afm)\b",
        "raman": r"\braman\b|\b(?:id/ig|ig/id|d[- ]band|g[- ]band|rbm)\b",
        "tga": r"\b(?:tga|thermogravimetric)\b",
        "xrd": r"\b(?:xrd|x[- ]ray\s+diffraction)\b",
        "surface_area": r"\b(?:bet|surface\s+area|pore\s+(?:size|volume))\b",
        "dimensions": r"\b(?:diameter|length|wall\s+number|multi[- ]?walled|single[- ]?walled)\b",
        "purity": r"\b(?:purity|amorphous\s+carbon|residue|ash)\b",
    },
    "purification": {
        "purification": r"\bpurif(?:y|ied|ication)\b",
        "acid_treatment": r"\b(?:acid\s+wash|acid\s+treatment|hcl|hno3|sulfuric\s+acid|nitric\s+acid)\b",
        "oxidation": r"\b(?:oxidation|oxidized|air\s+treatment)\b",
        "filtration": r"\b(?:filter|filtration|centrifugation)\b",
    },
    "scale_safety": {
        "scale": r"\b(?:scale[- ]?up|large[- ]scale|pilot|industrial|continuous\s+operation|batch)\b",
        "equipment": r"\b(?:equipment|apparatus|system\s+diagram|process\s+flow)\b",
        "safety": r"\b(?:safety|hazard|explosion|flammable|toxic|risk)\b",
        "emission_waste": r"\b(?:emission|waste|effluent|environmental)\b",
    },
}


def stable_id(prefix: str, *parts: Any) -> str:
    digest = hashlib.sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:20].upper()
    return f"{prefix}_{digest}"


def clean_heading(value: str) -> str:
    heading = SPACE_RE.sub(" ", value.strip())
    heading = re.sub(r"^\s*(?:section\s+)?(?:\d+(?:\.\d+)*|[IVXLC]+)[.)]?\s+", "", heading, flags=re.I)
    return heading.strip(" :.-")


def normalize_section_name(value: str) -> str:
    heading = clean_heading(value)
    for normalized, pattern in SECTION_PATTERNS:
        if pattern.search(heading):
            return normalized
    return "other"


def detect_heading(line: str) -> tuple[str, str, str] | None:
    raw = SPACE_RE.sub(" ", line.strip())
    if not raw or len(raw) > 120:
        return None
    # Some two-column first pages merge a short left-column label with the
    # right-column Abstract heading (for example, "Article Info Abstract").
    # Treat the trailing label as the heading and keep subsequent text in the
    # reviewable abstract section.
    if len(raw) <= 50 and re.search(r"\babstract\s*$", raw, flags=re.I):
        return "Abstract", "abstract", ""
    number_match = re.match(r"^\s*((?:\d+(?:\.\d+)*|[IVXLC]+)[.)]?)\s+", raw, flags=re.I)
    numbered = bool(number_match)
    cleaned = clean_heading(raw)
    normalized = normalize_section_name(cleaned)
    if normalized == "other":
        return None
    pattern = next(pattern for name, pattern in SECTION_PATTERNS if name == normalized)
    match = pattern.match(cleaned)
    if not match:
        return None
    heading_text = cleaned[: match.end()].strip(" :.-")
    remainder = cleaned[match.end():].strip(" :.-")
    heading_words = heading_text.split()
    # Reject lowercase prose fragments such as "results" or "experimental"
    # that happen to start a wrapped line. Real unnumbered headings in the
    # supported corpus are capitalized/title case or all caps.
    capitalized = bool(cleaned and cleaned[0].isupper())
    looks_heading = numbered or raw.isupper() or raw.istitle() or (capitalized and len(heading_words) <= 8)
    if not looks_heading:
        return None
    raw_heading = f"{number_match.group(1)} {heading_text}" if number_match else heading_text
    return raw_heading, normalized, remainder


def extract_pdfplumber_page(page: Any) -> tuple[str, bool]:
    """Extract one page in reading order, splitting a detected two-column body."""

    try:
        words = page.extract_words() or []
    except Exception:
        words = []
    width = float(page.width)
    height = float(page.height)
    body_words = [
        word for word in words
        if float(word.get("top", 0)) >= height * 0.08 and float(word.get("bottom", height)) <= height * 0.94
    ]
    if len(body_words) >= 80:
        centers = [((float(word["x0"]) + float(word["x1"])) / 2) / width for word in body_words]
        left_ratio = sum(center < 0.46 for center in centers) / len(centers)
        right_ratio = sum(center > 0.54 for center in centers) / len(centers)
        gutter_ratio = sum(0.47 <= center <= 0.53 for center in centers) / len(centers)
        two_column = left_ratio >= 0.35 and right_ratio >= 0.35 and gutter_ratio <= 0.035
    else:
        two_column = False
    if not two_column:
        return page.extract_text(x_tolerance=2, y_tolerance=3) or "", False
    left = page.crop((0, 0, width * 0.495, height)).extract_text(x_tolerance=2, y_tolerance=3) or ""
    right = page.crop((width * 0.505, 0, width, height)).extract_text(x_tolerance=2, y_tolerance=3) or ""
    return f"{left.strip()}\n{right.strip()}".strip(), True


def label_scientific_reports_frontmatter(page: Any, text: str) -> tuple[str, bool]:
    """Add reviewable section labels omitted by the Scientific Reports layout.

    Scientific Reports places an unlabelled abstract directly after the author
    block and starts the introduction after a visible vertical gap (or after a
    Keywords line). This uses layout coordinates only for that publisher marker
    and deliberately reports the inference as a parser warning.
    """

    if "www.nature.com/scientificreports" not in text.lower():
        return text, False
    try:
        rows = page.extract_text_lines(return_chars=False) or []
    except Exception:
        return text, False
    if len(rows) < 12:
        return text, False
    author_index = next(
        (
            index
            for index, row in enumerate(rows[:20])
            if "*" in str(row.get("text", "")) and 220 <= float(row.get("top", 0)) <= 340
        ),
        None,
    )
    if author_index is None or author_index + 5 >= len(rows):
        return text, False
    abstract_start = author_index + 1
    body_start: int | None
    keywords_index = next(
        (
            index
            for index in range(abstract_start + 3, min(len(rows), 45))
            if str(rows[index].get("text", "")).strip().lower().startswith("keywords")
        ),
        None,
    )
    if keywords_index is not None and keywords_index + 1 < len(rows):
        body_start = keywords_index + 1
    else:
        body_start = next(
            (
                index
                for index in range(abstract_start + 5, min(len(rows), 55))
                if float(rows[index].get("top", 0)) - float(rows[index - 1].get("bottom", 0)) >= 18
            ),
            None,
        )
    if body_start is None or body_start <= abstract_start:
        return text, False
    output: list[str] = []
    for index, row in enumerate(rows):
        if index == abstract_start:
            output.append("Abstract")
        if index == body_start:
            output.append("Introduction")
        row_text = str(row.get("text", "")).strip()
        if row_text:
            output.append(row_text)
    return "\n".join(output), True


def remove_repeated_headers_footers(pages: list[PageText]) -> list[PageText]:
    if len(pages) < 3:
        return pages
    candidates: list[list[str]] = []
    counter: Counter[str] = Counter()
    for page in pages:
        lines = [SPACE_RE.sub(" ", line.strip()) for line in page.text.splitlines() if line.strip()]
        selected = lines[:2] + lines[-2:]
        candidates.append(selected)
        counter.update(set(selected))
    threshold = max(3, int(len(pages) * 0.6))
    repeated = {line for line, count in counter.items() if count >= threshold and len(line) < 160}
    output: list[PageText] = []
    for page in pages:
        lines = [line for line in page.text.splitlines() if SPACE_RE.sub(" ", line.strip()) not in repeated]
        output.append(PageText(page.page_number, "\n".join(lines).strip()))
    return output


def extract_pdf_pages(path: Path) -> tuple[list[PageText], list[tuple[int, str]], str, list[str]]:
    warnings: list[str] = []
    tables: list[tuple[int, str]] = []
    try:
        import pdfplumber  # type: ignore

        pages: list[PageText] = []
        with pdfplumber.open(path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                try:
                    text, two_column = extract_pdfplumber_page(page)
                    if two_column:
                        warnings.append(f"page_{page_number}_two_column_reading_order")
                    if page_number == 1 and not two_column:
                        text, frontmatter_labeled = label_scientific_reports_frontmatter(page, text)
                        if frontmatter_labeled:
                            warnings.append("page_1_scientific_reports_abstract_and_introduction_inferred")
                except Exception as exc:
                    text = ""
                    warnings.append(f"page_{page_number}_text_error:{type(exc).__name__}")
                pages.append(PageText(page_number, text))
                if len(tables) < 30:
                    try:
                        extracted = page.extract_tables() or []
                    except Exception as exc:
                        extracted = []
                        warnings.append(f"page_{page_number}_table_error:{type(exc).__name__}")
                    for table in extracted[:5]:
                        rendered_rows = []
                        for row in (table or [])[:100]:
                            rendered_rows.append("\t".join(SPACE_RE.sub(" ", str(cell or "")).strip() for cell in row))
                        rendered = "\n".join(row for row in rendered_rows if row.strip())
                        if rendered:
                            tables.append((page_number, rendered[:20000]))
        return remove_repeated_headers_footers(pages), tables, f"pdfplumber_{pdfplumber.__version__}+{PARSER_VERSION}", warnings
    except ModuleNotFoundError:
        try:
            import pypdf  # type: ignore
        except ModuleNotFoundError as exc:
            raise RuntimeError("PDF parsing requires pdfplumber or pypdf; use the bundled workspace Python runtime") from exc
        reader = pypdf.PdfReader(str(path))
        pages = []
        for page_number, pdf_page in enumerate(reader.pages, start=1):
            try:
                text = pdf_page.extract_text() or ""
            except Exception as exc:
                text = ""
                warnings.append(f"page_{page_number}_text_error:{type(exc).__name__}")
            pages.append(PageText(page_number, text))
        warnings.append("tables_not_extracted:pypdf_fallback")
        return remove_repeated_headers_footers(pages), [], f"pypdf_{pypdf.__version__}+{PARSER_VERSION}", warnings


def segment_pages(
    source_id: str,
    fulltext_id: str,
    content_hash: str,
    title: str,
    abstract_fallback: str,
    pages: list[PageText],
    tables: list[tuple[int, str]],
    extractor: str,
) -> list[TextSection]:
    sections: list[TextSection] = []
    order = 1

    def add(raw: str, normalized: str, text: str, start: int | None, end: int | None, extractor_name: str = extractor) -> None:
        nonlocal order
        cleaned_text = re.sub(r"\n{3,}", "\n\n", text).strip()
        if not cleaned_text:
            return
        section_id = stable_id("SEC", source_id, content_hash, order, raw, cleaned_text[:200])
        sections.append(
            TextSection(
                section_id, source_id, fulltext_id, content_hash, raw, normalized,
                order, cleaned_text, start, end, extractor_name, 1,
            )
        )
        order += 1

    add("Title (metadata)", "title", title, 1 if pages else None, 1 if pages else None, "metadata_registry")
    current_raw = "Front matter"
    current_normalized = "other"
    buffer: list[str] = []
    page_start: int | None = pages[0].page_number if pages else None
    page_end: int | None = page_start

    def flush() -> None:
        nonlocal buffer
        add(current_raw, current_normalized, "\n".join(buffer), page_start, page_end)
        buffer = []

    for page in pages:
        lines = page.text.splitlines()
        line_index = 0
        while line_index < len(lines):
            stripped = lines[line_index].strip()
            line_index += 1
            if not stripped:
                if buffer and buffer[-1] != "":
                    buffer.append("")
                continue
            heading = detect_heading(stripped)
            # PDF line wrapping frequently splits long numbered subsection
            # headings after a formula or slash. Join only a short numbered
            # line with its immediate successor, and only when the combined
            # text is recognized as a supported section heading.
            if (
                heading is None
                and line_index < len(lines)
                and len(stripped) <= 100
                and re.match(r"^\s*(?:\d+(?:\.\d+)*|[IVXLC]+)[.)]?\s+", stripped, flags=re.I)
            ):
                continuation = lines[line_index].strip()
                combined = f"{stripped} {continuation}".strip()
                combined_heading = detect_heading(combined) if continuation and len(combined) <= 120 else None
                if combined_heading:
                    heading = combined_heading
                    line_index += 1
            if heading:
                flush()
                current_raw, current_normalized, remainder = heading
                page_start = page.page_number
                page_end = page.page_number
                if remainder:
                    buffer.append(remainder)
            else:
                if not buffer:
                    page_start = page.page_number
                page_end = page.page_number
                buffer.append(stripped)
    flush()

    if abstract_fallback and not any(section.section_name_normalized == "abstract" for section in sections):
        add("Abstract (metadata fallback)", "abstract", abstract_fallback, None, None, "metadata_registry")

    for page in pages:
        lines = [line.strip() for line in page.text.splitlines() if line.strip()]
        for line in lines:
            if re.match(r"^(?:fig(?:ure)?\.?\s*\d+|table\s+\d+)\b", line, flags=re.I):
                normalized = "figure_captions" if line.lower().startswith(("fig", "figure")) else "tables"
                add(line.split(".", 1)[0], normalized, line, page.page_number, page.page_number)
            elif re.search(r"\b(?:supplementary|supporting)\s+(?:information|figure|table|data|material)\b", line, flags=re.I):
                add("Supplementary hint", "supplementary_hints", line, page.page_number, page.page_number)
    for index, (page_number, table_text) in enumerate(tables, start=1):
        add(f"Extracted table p{page_number}.{index}", "tables", table_text, page_number, page_number)
    return sections


class StructuredHtmlParser(HTMLParser):
    SKIP = {"script", "style", "noscript", "svg", "nav", "footer", "header", "form"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.skip_depth = 0
        self.capture_tag = ""
        self.capture_parts: list[str] = []
        self.blocks: list[tuple[str, str]] = []
        self.row: list[str] = []
        self.cell_parts: list[str] = []
        self.in_cell = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if tag in self.SKIP:
            self.skip_depth += 1
        if self.skip_depth:
            return
        if tag in {"h1", "h2", "h3", "h4", "h5", "h6", "p", "figcaption", "caption"} and not self.capture_tag:
            self.capture_tag = tag
            self.capture_parts = []
        if tag == "tr":
            self.row = []
        if tag in {"td", "th"}:
            self.in_cell = True
            self.cell_parts = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag in self.SKIP and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag in {"td", "th"} and self.in_cell:
            self.row.append(SPACE_RE.sub(" ", " ".join(self.cell_parts)).strip())
            self.in_cell = False
        if tag == "tr" and self.row:
            self.blocks.append(("table_row", "\t".join(self.row)))
            self.row = []
        if tag == self.capture_tag:
            text = SPACE_RE.sub(" ", " ".join(self.capture_parts)).strip()
            if text:
                kind = "heading" if tag.startswith("h") else ("figure_caption" if tag == "figcaption" else ("table_caption" if tag == "caption" else "paragraph"))
                self.blocks.append((kind, text))
            self.capture_tag = ""
            self.capture_parts = []

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        text = SPACE_RE.sub(" ", data).strip()
        if not text:
            return
        if self.capture_tag:
            self.capture_parts.append(text)
        if self.in_cell:
            self.cell_parts.append(text)


def extract_html_sections(
    path: Path,
    source_id: str,
    fulltext_id: str,
    content_hash: str,
    title: str,
    abstract_fallback: str,
) -> tuple[list[TextSection], str, str, list[str]]:
    content = path.read_bytes()
    decoded = content.decode("utf-8", errors="replace")
    parser = StructuredHtmlParser()
    parser.feed(decoded)
    extractor = f"stdlib_html_parser+{PARSER_VERSION}"
    sections: list[TextSection] = []
    order = 1

    def add(raw: str, normalized: str, text: str) -> None:
        nonlocal order
        if not text.strip():
            return
        section_id = stable_id("SEC", source_id, content_hash, order, raw, text[:200])
        sections.append(TextSection(section_id, source_id, fulltext_id, content_hash, raw, normalized, order, text.strip(), None, None, extractor, 1))
        order += 1

    add("Title (metadata)", "title", title)
    current_raw = "HTML front matter"
    current_normalized = "other"
    buffer: list[str] = []
    table_rows: list[str] = []

    def flush() -> None:
        nonlocal buffer
        if buffer:
            add(current_raw, current_normalized, "\n\n".join(buffer))
            buffer = []

    def flush_table() -> None:
        nonlocal table_rows
        if table_rows:
            add("HTML table", "tables", "\n".join(table_rows))
            table_rows = []

    for kind, text in parser.blocks:
        if kind == "heading":
            flush()
            flush_table()
            current_raw = text
            current_normalized = normalize_section_name(text)
        elif kind == "figure_caption":
            flush()
            add("HTML figure caption", "figure_captions", text)
        elif kind == "table_caption":
            flush_table()
            add(text, "tables", text)
        elif kind == "table_row":
            table_rows.append(text)
        else:
            flush_table()
            buffer.append(text)
    flush()
    flush_table()
    if abstract_fallback and not any(section.section_name_normalized == "abstract" for section in sections):
        add("Abstract (metadata fallback)", "abstract", abstract_fallback)
    raw_text = "\n\n".join(text for kind, text in parser.blocks if kind != "table_row")
    return sections, raw_text, extractor, []


def chunk_text(text: str, max_chars: int = 1200) -> list[str]:
    normalized = SPACE_RE.sub(" ", text.replace("\n", " ")).strip()
    if not normalized:
        return []
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(])", normalized)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if current and len(current) + 1 + len(sentence) > max_chars:
            chunks.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        chunks.append(current)
    return chunks


def build_candidate_spans(sections: list[TextSection]) -> list[CandidateSpan]:
    spans: list[CandidateSpan] = []
    experimental_sections = {"methods", "experimental", "catalyst_preparation", "cvd_growth", "characterization", "tables"}
    for section in sections:
        if section.section_name_normalized in {"title", "references"}:
            continue
        for chunk in chunk_text(section.text):
            if len(chunk) < 40:
                continue
            for span_type, keyword_patterns in SPAN_KEYWORDS.items():
                matched = [name for name, pattern in keyword_patterns.items() if re.search(pattern, chunk, flags=re.I)]
                if not matched:
                    continue
                context = section.section_name_normalized in experimental_sections
                measurement = bool(MEASUREMENT_RE.search(chunk))
                if len(matched) >= 2 and (context or measurement):
                    confidence = 0.9
                    rule = "high:multiple_keywords+experimental_context_or_measurement"
                elif len(matched) >= 2 or context and measurement:
                    confidence = 0.75
                    rule = "medium:multiple_keywords_or_context_plus_measurement"
                elif context:
                    confidence = 0.6
                    rule = "medium:single_keyword_in_experimental_section"
                elif measurement:
                    confidence = 0.55
                    rule = "low:single_keyword_with_measurement"
                elif span_type in {"yield", "purification", "scale_safety"}:
                    confidence = 0.45
                    rule = "low:single_high_value_keyword_outside_experimental_section"
                else:
                    continue
                page_range = ""
                if section.page_start is not None:
                    page_range = f"p{section.page_start}" if section.page_end in {None, section.page_start} else f"p{section.page_start}-p{section.page_end}"
                # The same sentence can legitimately occur in a table,
                # caption, and narrative section. Include section identity so
                # those traceable occurrences do not collide in SQLite.
                span_id = stable_id(
                    "SPAN", section.source_id, section.input_content_hash,
                    section.section_id, span_type, chunk,
                )
                spans.append(
                    CandidateSpan(
                        section.source_id,
                        span_id,
                        section.input_fulltext_id,
                        section.section_id,
                        span_type,
                        chunk,
                        rule,
                        confidence,
                        "; ".join(matched),
                        page_range,
                        1,
                    )
                )
    return spans


def extract_document(
    path: Path,
    fulltext_type: str,
    source_id: str,
    fulltext_id: str,
    content_hash: str,
    title: str,
    abstract_fallback: str,
) -> ExtractionOutput:
    page_count = 0
    table_count = 0
    if fulltext_type in {"pdf", "local_pdf"}:
        pages, tables, extractor, warnings = extract_pdf_pages(path)
        page_count = len(pages)
        table_count = len(tables)
        sections = segment_pages(source_id, fulltext_id, content_hash, title, abstract_fallback, pages, tables, extractor)
        raw_text = "\n\n".join(f"===== PAGE {page.page_number} =====\n{page.text}" for page in pages)
    elif fulltext_type == "html":
        sections, raw_text, extractor, warnings = extract_html_sections(path, source_id, fulltext_id, content_hash, title, abstract_fallback)
        table_count = sum(section.section_name_normalized == "tables" for section in sections)
    else:
        raise ValueError(f"Unsupported fulltext_type: {fulltext_type}")
    spans = build_candidate_spans(sections)
    extracted_char_count = len(re.sub(r"\s+", "", raw_text))
    section_types = {section.section_name_normalized for section in sections}
    reference_detected = int("references" in section_types)
    experimental_types = {"methods", "experimental", "catalyst_preparation", "cvd_growth"}
    experimental_detected = int(bool(section_types & experimental_types))
    text_error_count = sum("_text_error:" in warning for warning in warnings)
    parse_quality, ocr_required = assess_parse_quality(
        fulltext_type,
        page_count,
        extracted_char_count,
        text_error_count,
        bool(reference_detected),
    )

    span_types = {span.span_type for span in spans if span.confidence_score >= 0.6}
    evidence_types = span_types & {"catalyst", "process", "gas", "yield", "characterization"}
    synthesis_core = span_types & {"catalyst", "process", "gas"}
    corpus_text = " ".join(section.text for section in sections)
    cnt_identity = bool(re.search(r"\b(?:CNTs?|MWCNTs?|SWCNTs?|VACNTs?|MWNTs?|SWNTs?)\b|carbon\s+nanotubes?|tubular\s+carbon", corpus_text, flags=re.I))
    eligible = int(
        parse_quality in {"good", "partial"}
        and bool(experimental_detected)
        and cnt_identity
        and len(evidence_types) >= 2
        and bool(synthesis_core)
    )
    if eligible:
        relevance_status = "candidate_extract"
        promotion_reason = "fulltext_cnt_identity+experimental_section+multi_type_experimental_evidence"
    elif parse_quality in {"scanned", "broken_layout", "unreadable", "metadata_only"}:
        relevance_status = "needs_fulltext_review"
        promotion_reason = f"parse_quality_{parse_quality}_blocks_automatic_candidate"
    else:
        relevance_status = "insufficient_experimental_evidence"
        promotion_reason = "requires_cnt_identity_experimental_section_and_at_least_two_evidence_types"
    return ExtractionOutput(
        sections=sections,
        spans=spans,
        raw_text=raw_text,
        extractor=extractor,
        warnings=warnings,
        parse_quality=parse_quality,
        page_count=page_count,
        extracted_char_count=extracted_char_count,
        table_count=table_count,
        reference_section_detected=reference_detected,
        experimental_section_detected=experimental_detected,
        ocr_required=ocr_required,
        fulltext_relevance_status=relevance_status,
        candidate_extract_eligible=eligible,
        promotion_reason=promotion_reason,
    )


def assess_parse_quality(
    fulltext_type: str,
    page_count: int,
    extracted_char_count: int,
    text_error_count: int,
    reference_detected: bool,
) -> tuple[str, int]:
    """Classify extraction quality without invoking OCR or changing source status."""

    if fulltext_type in {"pdf", "local_pdf"} and page_count and extracted_char_count < max(200, page_count * 60):
        return "scanned", 1
    if extracted_char_count < 30:
        return "unreadable", 0
    if extracted_char_count < 500:
        return "metadata_only", 0
    if page_count and text_error_count >= max(2, page_count // 3):
        return "broken_layout", 0
    if extracted_char_count < 2000 or not reference_detected:
        return "partial", 0
    return "good", 0
