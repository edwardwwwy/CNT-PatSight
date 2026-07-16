from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from .utils import utc_now


SCREENING_RULE_VERSION = "v1.2"
DEDUP_RULE_VERSION = "v1.0"


@dataclass(frozen=True, slots=True)
class ScreeningRules:
    screening_rule_version: str = SCREENING_RULE_VERSION
    dedup_rule_version: str = DEDUP_RULE_VERSION
    tier_a_topic_min: float = 7.0
    tier_a_evidence_min: float = 3.0
    tier_b_topic_min: float = 6.0
    direct_synthesis_bonus: float = 1.0
    strong_title_missing_abstract_tier: str = "B"
    require_strong_cnt_identity_for_candidate: bool = True
    non_cnt_title_guard: bool = True
    review_abstract_guard: bool = True
    theory_without_experiment_guard: bool = True
    preexisting_cnt_guard: bool = True
    dedup_auto_merge_threshold: float = 0.97
    dedup_review_threshold: float = 0.92
    title_min_length: int = 30

    @classmethod
    def from_file(cls, path: Path) -> "ScreeningRules":
        if not path.exists():
            return cls()
        payload = json.loads(path.read_text(encoding="utf-8"))
        screening = payload.get("screening", {})
        dedup = payload.get("dedup", {})
        return cls(
            screening_rule_version=str(payload.get("screening_rule_version", SCREENING_RULE_VERSION)),
            dedup_rule_version=str(payload.get("dedup_rule_version", DEDUP_RULE_VERSION)),
            tier_a_topic_min=float(screening.get("tier_a_topic_min", 7.0)),
            tier_a_evidence_min=float(screening.get("tier_a_evidence_min", 3.0)),
            tier_b_topic_min=float(screening.get("tier_b_topic_min", 6.0)),
            direct_synthesis_bonus=float(screening.get("direct_synthesis_bonus", 1.0)),
            strong_title_missing_abstract_tier=str(
                screening.get("strong_title_missing_abstract_tier", "B")
            ),
            require_strong_cnt_identity_for_candidate=bool(
                screening.get("require_strong_cnt_identity_for_candidate", True)
            ),
            non_cnt_title_guard=bool(screening.get("non_cnt_title_guard", True)),
            review_abstract_guard=bool(screening.get("review_abstract_guard", True)),
            theory_without_experiment_guard=bool(
                screening.get("theory_without_experiment_guard", True)
            ),
            preexisting_cnt_guard=bool(screening.get("preexisting_cnt_guard", True)),
            dedup_auto_merge_threshold=float(dedup.get("auto_merge_threshold", 0.97)),
            dedup_review_threshold=float(dedup.get("review_threshold", 0.92)),
            title_min_length=int(dedup.get("title_min_length", 30)),
        )


@dataclass(frozen=True, slots=True)
class ScoreResult:
    # Backward-compatible aliases used by reports and older callers.
    score: float
    band: str
    screening_class: str
    reasons: list[str]
    document_type: str
    topic_relevance_score: float
    metadata_evidence_likelihood_score: float
    access_score: float
    priority_tier: str
    needs_fulltext_check: bool
    pipeline_status: str
    topic_positive_reasons: list[str]
    topic_negative_reasons: list[str]
    evidence_reasons: list[str]
    priority_tier_reason: str
    screening_rule_version: str
    scored_at: str


DOCUMENT_TYPE_MAP = {
    "article": "research_article",
    "journal-article": "research_article",
    "journalarticle": "research_article",
    "study": "research_article",
    "review": "review",
    "meta-analysis": "review",
    "metaanalysis": "review",
    "posted-content": "preprint",
    "preprint": "preprint",
    "proceedings-article": "conference",
    "conference": "conference",
    "conference-paper": "conference",
    "book-chapter": "book_chapter",
    "booksection": "book_chapter",
    "book-section": "book_chapter",
    "correction": "correction",
    "erratum": "erratum",
    "retraction": "retraction",
    "patent": "patent",
}


class RelevanceScorer:
    """Transparent metadata-only screening; never grants ``formal_extract``."""

    CNT_STRONG = re.compile(
        r"\bcarbon\s+nano\s*tubes?\b|\bcarbon\s+nanotubes?\b|"
        r"\b(?:cnts?|mwcnts?|swcnts?|dwcnts?|mwnts?|swnts?|vacnts?)\b|"
        r"\b(?:multi|single|double)[-\s]?walled\s+(?:carbon\s+)?nanotubes?\b|"
        r"碳纳米管|纳米碳管|碳纳米管阵列",
        re.I,
    )
    CNT_WEAK = re.compile(
        r"\btubular\s+carbon\b|\bcarbon\s+filaments?\b|\bcarbon\s+nanostructures?\b|"
        r"管状碳材料|碳纳米材料",
        re.I,
    )
    ROUTE_STRONG = re.compile(
        r"\b(?:cvd|ccvd|pecvd|fccvd|fc[-\s]?cvd)\b|"
        r"chemical\s+vapou?r\s+deposition|floating\s+catalyst\s+(?:chemical\s+)?vapou?r\s+deposition",
        re.I,
    )
    CATALYTIC_DECOMPOSITION = re.compile(
        r"catalytic\s+(?:methane|hydrocarbon|co)?\s*(?:decomposition|pyrolysis)", re.I
    )
    SYNTHESIS_EVIDENCE = re.compile(
        r"\b(?:synthesi[sz](?:e|ed|ing|ation)?|growth|grown|prepar(?:e|ed|ation)|"
        r"produc(?:e|ed|tion)|fabricat(?:e|ed|ion)|catalysts?|temperature|yield|deposition)\b",
        re.I,
    )
    APPLICATION = re.compile(
        r"\b(?:sensors?|composites?|electrodes?|adsorption|drug\s+delivery|supercapacitors?|"
        r"batter(?:y|ies)|photocatalysis|biosensors?|field\s+emission)\b",
        re.I,
    )
    THEORY_ONLY = re.compile(r"\b(?:simulation|theoretical|density\s+functional|molecular\s+dynamics)\b", re.I)
    EXPERIMENTAL_SYNTHESIS = re.compile(
        r"\b(?:we\s+(?:synthesi[sz]ed|grew|grow|fabricated|produced)|"
        r"(?:cnts?|carbon\s+nanotubes?|mwcnts?|swcnts?|vacnts?)\s+(?:were|was)\s+"
        r"(?:synthesi[sz]ed|grown|fabricated|produced)|experimental(?:ly)?\s+(?:growth|synthesis))\b",
        re.I,
    )
    REVIEW_LIKE = re.compile(
        r"\b(?:this|the|our)\s+(?:review|perspective)\b|\bwe\s+review\b|"
        r"\brecent\s+advances\b.*\breviewed\b",
        re.I | re.S,
    )
    NON_CNT_TITLE = re.compile(
        r"\b(?:graphene|boron\s+nitride\s+nanotubes?|(?:ws2|mos2|tmdc)\s+nanotubes?|"
        r"carbon\s+quantum\s+dots?|carbon\s+nanofibers?)\b",
        re.I,
    )
    PREEXISTING_CNT = re.compile(
        r"\b(?:pre[-\s]?(?:deposited|existing)|preliminarily\s+deposited|"
        r"integration\s+of\s+carbon\s+nanotubes?|transferring\s+.*carbon\s+nanotubes?|"
        r"photonic\s+sorting|functionaliz(?:e|ed|ation)\s+of\s+carbon\s+nanotubes?|"
        r"(?:fe|co|ni)@cnt|cnt[-\s]?based\s+(?:catalyst|electrode)|"
        r"carbon\s+nanotubes?\s+as\s+(?:a\s+)?(?:support|electrode|adsorbent))\b",
        re.I,
    )
    DIRECT_SYNTHESIS = re.compile(
        r"(?:\b(?:synthesi[sz](?:e|ed|ing|ation)?|growth|grown|produc(?:e|ed|tion)|"
        r"fabricat(?:e|ed|ion))\b.{0,100}\b(?:carbon\s+nanotubes?|cnts?|mwcnts?|swcnts?|vacnts?)\b)|"
        r"(?:\b(?:carbon\s+nanotubes?|cnts?|mwcnts?|swcnts?|vacnts?)\b.{0,100}"
        r"\b(?:synthesi[sz](?:e|ed|ing|ation)?|growth|grown|produc(?:e|ed|tion)|"
        r"fabricat(?:e|ed|ion))\b)",
        re.I | re.S,
    )
    TITLE_DIRECT_SYNTHESIS = re.compile(
        r"\b(?:synthesi[sz](?:e|ed|ing|ation)?|growth|grown|produc(?:e|ed|tion)|"
        r"fabricat(?:e|ed|ion))\b.{0,40}\b(?:carbon\s+nanotubes?|cnts?|mwcnts?|swcnts?|vacnts?)\b|"
        r"\b(?:carbon\s+nanotubes?|cnts?|mwcnts?|swcnts?|vacnts?)\b.{0,12}"
        r"\b(?:synthesis|growth|production)\b",
        re.I,
    )

    def __init__(self, rules: ScreeningRules | None = None):
        self.rules = rules or ScreeningRules()

    @classmethod
    def from_file(cls, path: Path) -> "RelevanceScorer":
        return cls(ScreeningRules.from_file(path))

    def classify_document_type(
        self,
        title: str,
        source_type: str = "paper",
        raw_document_type: str = "",
    ) -> str:
        text = title.strip().lower()
        if source_type.lower() == "patent":
            return "patent"
        if re.search(r"\bretraction\b|retracted\s+article", text):
            return "retraction"
        if re.search(r"\berratum\b", text):
            return "erratum"
        if re.search(r"\bcorrection\b|corrigendum", text):
            return "correction"
        raw = raw_document_type.strip().lower().replace("_", "-")
        if raw in DOCUMENT_TYPE_MAP:
            return DOCUMENT_TYPE_MAP[raw]
        if re.search(r"\b(?:a|systematic|critical|comprehensive)\s+review\b|\breview\s+article\b", text):
            return "review"
        if source_type.lower() in {"paper", "article"}:
            return "research_article"
        return "unknown"

    def score(
        self,
        title: str,
        abstract: str = "",
        *,
        source_type: str = "paper",
        raw_document_type: str = "",
        doi: str = "",
        pdf_url: str = "",
        html_url: str = "",
        pdf_path: str = "",
    ) -> ScoreResult:
        title_text = title.lower()
        text = f"{title}\n{abstract}".lower()
        positive: list[str] = []
        negative: list[str] = []
        evidence: list[str] = []
        topic = 0.0

        title_strong_identity = bool(self.CNT_STRONG.search(title_text))
        strong_identity = bool(self.CNT_STRONG.search(text))
        weak_identity = bool(self.CNT_WEAK.search(text))
        has_identity = strong_identity or weak_identity
        if strong_identity:
            topic += 3.0
            positive.append("cnt_identity_strong:+3.0")
        elif weak_identity:
            topic += 1.5
            positive.append("cnt_identity_weak:+1.5")

        synthesis_evidence = bool(self.SYNTHESIS_EVIDENCE.search(text))
        strong_route = bool(self.ROUTE_STRONG.search(text))
        title_strong_route = bool(self.ROUTE_STRONG.search(title_text))
        conditional_decomposition = bool(self.CATALYTIC_DECOMPOSITION.search(text))
        title_conditional_decomposition = bool(self.CATALYTIC_DECOMPOSITION.search(title_text))
        direct_synthesis = bool(self.DIRECT_SYNTHESIS.search(text))
        title_direct_synthesis = bool(self.TITLE_DIRECT_SYNTHESIS.search(title_text))
        title_target_strong = title_strong_identity and (
            title_strong_route or title_conditional_decomposition or title_direct_synthesis
        )
        if strong_route:
            topic += 3.0
            positive.append("cvd_route_strong:+3.0")
        elif conditional_decomposition and has_identity and synthesis_evidence:
            topic += 3.0
            positive.append("catalytic_decomposition_with_cnt_synthesis_context:+3.0")
        elif conditional_decomposition:
            negative.append("catalytic_decomposition_without_cnt_synthesis_context:+0.0")

        if direct_synthesis and strong_identity:
            topic += self.rules.direct_synthesis_bonus
            positive.append(f"direct_cnt_synthesis_context:+{self.rules.direct_synthesis_bonus:.1f}")

        catalyst = self._match(text, r"\bcatal(?:yst|ysts|ytic|ysis)\b|\b(?:fe|co|ni|mo)\b")
        if catalyst:
            topic += 1.0
            positive.append("catalyst_context:+1.0")
        carbon_source = self._match(
            text,
            r"\bmethane\b|\bch4\b|\bbiogas\b|\bnatural\s+gas\b|\bhydrocarbons?\b|\bcarbon\s+monoxide\b|\bco\b",
        )
        if carbon_source:
            topic += 1.0
            positive.append("carbon_source:+1.0")
        process_result = self._match(
            text,
            r"\byield\b|productivity|conversion|growth\s+(?:rate|temperature)|synthesis\s+temperature|"
            r"\btemperature\b|\bflow\s+rate\b|\bpressure\b",
        )
        if process_result:
            topic += 1.0
            positive.append("process_or_result_context:+1.0")
        reactor = self._match(text, r"fluidi[sz]ed\s+bed|floating\s+catalyst|fixed\s+bed|aerosol")
        if reactor:
            topic += 0.5
            positive.append("priority_reactor:+0.5")
        characterization = self._match(text, r"\b(?:tem|hrtem|sem|raman|tga|xrd)\b")
        if characterization:
            topic += 0.5
            positive.append("characterization_context:+0.5")

        preexisting_cnt = bool(self.PREEXISTING_CNT.search(text)) and not title_target_strong
        application_only = (
            (bool(self.APPLICATION.search(text)) and not direct_synthesis and not title_target_strong)
            or (self.rules.preexisting_cnt_guard and preexisting_cnt)
        )
        if application_only:
            topic -= 4.0
            negative.append("application_only_without_synthesis:-4.0")
        elif self.APPLICATION.search(text):
            positive.append("application_terms_with_synthesis_context:no_penalty")
        theory_only = (
            self.rules.theory_without_experiment_guard
            and bool(self.THEORY_ONLY.search(text))
            and not bool(self.EXPERIMENTAL_SYNTHESIS.search(text))
        )
        if theory_only:
            topic -= 3.0
            negative.append("theory_only_without_experiment:-3.0")

        evidence_groups = (
            ("catalyst_or_preparation", r"\bcatalysts?\b|\b(?:fe|co|ni|mo)\b|impregnation|sol[-\s]?gel|calcination"),
            ("reaction_conditions", r"\b\d+(?:\.\d+)?\s*(?:°\s*c|℃|k|sccm|ml\s*/\s*min|min|hours?|h)\b|temperature|pressure"),
            ("gas_or_reactor", r"\b(?:ch4|methane|h2|hydrogen|ar|argon|n2|nitrogen|co2)\b|flow\s+rate|reactor|fluidi[sz]ed\s+bed"),
            ("yield_or_conversion", r"\byield\b|productivity|conversion|growth\s+rate|g\s*/\s*g"),
            ("characterization", r"\b(?:tem|hrtem|sem|raman|tga|xrd)\b"),
        )
        for code, pattern in evidence_groups:
            if self._match(text, pattern):
                evidence.append(code)
        metadata_evidence = float(len(evidence))

        access = 3.0 if pdf_path else (2.0 if pdf_url else (1.0 if html_url else 0.0))
        document_type = self.classify_document_type(title, source_type, raw_document_type)
        topic = round(max(0.0, min(10.0, topic)), 2)
        band = "high" if topic >= 7.0 else ("medium" if topic >= 4.0 else "low")

        non_cnt_title = (
            self.rules.non_cnt_title_guard
            and not title_strong_identity
            and bool(self.NON_CNT_TITLE.search(title_text))
        )
        review_like = (
            document_type == "review"
            or (self.rules.review_abstract_guard and bool(self.REVIEW_LIKE.search(text)))
        )

        if non_cnt_title:
            tier = "R"
            tier_reason = "explicit_non_cnt_material_in_title"
        elif not has_identity:
            tier = "R"
            tier_reason = "no_cnt_identity_term"
        elif document_type in {"correction", "erratum", "retraction"}:
            tier = "C"
            tier_reason = f"document_type_{document_type}"
        elif review_like or application_only or theory_only:
            tier = "C"
            tier_reason = "related_non_primary_experimental_target"
        elif not abstract.strip():
            if title_target_strong:
                tier = self.rules.strong_title_missing_abstract_tier
                tier_reason = "metadata_missing_abstract_but_strong_target_title"
            else:
                tier = "M"
                tier_reason = "metadata_missing:abstract"
        elif self.rules.require_strong_cnt_identity_for_candidate and not strong_identity:
            tier = "C"
            tier_reason = "generic_or_weak_nanocarbon_identity"
        elif topic >= self.rules.tier_a_topic_min and metadata_evidence >= self.rules.tier_a_evidence_min:
            tier = "A"
            tier_reason = "high_topic_and_metadata_evidence"
        elif topic >= self.rules.tier_b_topic_min:
            tier = "B"
            tier_reason = "relevant_needs_fulltext_confirmation"
        else:
            tier = "C"
            tier_reason = "related_but_below_experimental_priority"

        if tier == "R":
            screening_class = "reject"
            pipeline_status = "reject"
        elif tier == "C":
            screening_class = "source_observation_only" if document_type == "review" and topic >= 6 else "background_reference"
            pipeline_status = screening_class
        else:
            # Metadata alone cannot grant candidate_extract. A/B/M remain in
            # the screened-candidate queue until full text is checked.
            screening_class = ""
            pipeline_status = "screened_candidate"
        needs_fulltext = tier in {"A", "B", "M"}
        reasons = [*positive, *negative, *[f"metadata_evidence:{item}" for item in evidence]]
        return ScoreResult(
            score=topic,
            band=band,
            screening_class=screening_class,
            reasons=reasons,
            document_type=document_type,
            topic_relevance_score=topic,
            metadata_evidence_likelihood_score=metadata_evidence,
            access_score=access,
            priority_tier=tier,
            needs_fulltext_check=needs_fulltext,
            pipeline_status=pipeline_status,
            topic_positive_reasons=positive,
            topic_negative_reasons=negative,
            evidence_reasons=evidence,
            priority_tier_reason=tier_reason,
            screening_rule_version=self.rules.screening_rule_version,
            scored_at=utc_now(),
        )

    @staticmethod
    def _match(text: str, pattern: str) -> bool:
        return re.search(pattern, text, flags=re.I) is not None
