from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.collect_metadata.clients import (
    RawArchive,
    normalize_crossref,
    normalize_openalex,
    normalize_semantic_scholar,
    normalize_unpaywall,
)
from scripts.collect_metadata.models import NormalizedWork
from scripts.collect_metadata.scoring import RelevanceScorer
from scripts.collect_metadata.storage import MetadataStore
from scripts.collect_metadata.utils import normalize_doi, normalize_title


class NormalizationTests(unittest.TestCase):
    def test_identifier_normalization(self) -> None:
        self.assertEqual(normalize_doi("https://doi.org/10.1000/ABC."), "10.1000/abc")
        self.assertEqual(normalize_title("Multi-walled CNTs: growth"), "multi walled cnts growth")

    def test_openalex_adapter_reconstructs_abstract(self) -> None:
        work = normalize_openalex(
            {
                "id": "https://openalex.org/W123",
                "doi": "https://doi.org/10.1000/CNT",
                "display_name": "Methane CVD carbon nanotubes",
                "publication_year": 2024,
                "abstract_inverted_index": {"Methane": [0], "growth": [2], "CNT": [1]},
                "authorships": [{"author": {"display_name": "A. Author"}}],
                "primary_location": {
                    "source": {"display_name": "Carbon Journal", "host_organization_name": "Publisher"},
                    "landing_page_url": "https://example.test/article",
                },
                "best_oa_location": {"pdf_url": "https://example.test/paper.pdf"},
                "open_access": {"oa_status": "gold", "is_oa": True},
            },
            "2026-01-01T00:00:00Z",
        )
        self.assertEqual(work.external_id, "W123")
        self.assertEqual(work.abstract, "Methane CNT growth")
        self.assertEqual(work.pdf_url, "https://example.test/paper.pdf")

    def test_other_adapters_supply_requested_fields(self) -> None:
        s2 = normalize_semantic_scholar(
            {
                "paperId": "S2",
                "externalIds": {"DOI": "10.1000/CNT"},
                "title": "CNT synthesis",
                "abstract": "Abstract",
                "authors": [{"name": "A. Author"}],
                "year": 2024,
                "citationCount": 12,
                "isOpenAccess": True,
                "openAccessPdf": {"url": "https://example.test/s2.pdf"},
            },
            "2026-01-01T00:00:00Z",
        )
        crossref = normalize_crossref(
            {
                "DOI": "10.1000/CNT",
                "title": ["CNT synthesis"],
                "container-title": ["Journal"],
                "publisher": "Publisher",
                "published-print": {"date-parts": [[2024, 3, 2]]},
                "author": [{"given": "A.", "family": "Author"}],
            },
            "2026-01-01T00:00:00Z",
        )
        unpaywall = normalize_unpaywall(
            {
                "doi": "10.1000/CNT",
                "title": "CNT synthesis",
                "is_oa": True,
                "oa_status": "green",
                "best_oa_location": {
                    "url_for_pdf": "https://example.test/upw.pdf",
                    "url_for_landing_page": "https://example.test/upw",
                },
            },
            "2026-01-01T00:00:00Z",
        )
        self.assertEqual(s2.citation_count, 12)
        self.assertEqual(crossref.publisher, "Publisher")
        self.assertEqual(crossref.publication_date, "2024-03-02")
        self.assertEqual(unpaywall.open_access_status, "green")


class ScoringTests(unittest.TestCase):
    def test_priority_topic_scores_high(self) -> None:
        result = RelevanceScorer().score(
            "Methane CVD growth of MWCNTs over Fe catalyst",
            "Yield and growth temperature in a fluidized bed reactor.",
            doi="10.1000/cnt-priority",
        )
        self.assertEqual(result.band, "high")
        self.assertEqual(result.priority_tier, "A")
        self.assertEqual(result.pipeline_status, "screened_candidate")
        self.assertEqual(result.screening_class, "")
        self.assertGreaterEqual(result.score, 9.0)

    def test_metadata_score_never_marks_formal_extract(self) -> None:
        result = RelevanceScorer().score("Carbon nanotube chemical vapor deposition catalyst")
        self.assertNotEqual(result.screening_class, "formal_extract")

    def test_conditional_noise_and_metadata_missing_rules(self) -> None:
        scorer = RelevanceScorer()
        noise = scorer.score(
            "Methane catalytic decomposition for hydrogen production",
            "Coke formation over nickel catalysts.",
            doi="10.1000/noise",
        )
        self.assertEqual(noise.priority_tier, "R")
        self.assertNotIn("catalytic_decomposition_with_cnt_synthesis_context:+3.0", noise.reasons)
        synthesis_application = scorer.score(
            "CVD-grown VACNT arrays for sensors",
            "We synthesize carbon nanotube arrays by CVD over Fe catalyst at 750 C.",
            doi="10.1000/vacnt",
        )
        self.assertNotIn("application_only_without_synthesis:-4.0", synthesis_application.topic_negative_reasons)
        missing = scorer.score("Tubular carbon growth by chemical vapor deposition")
        self.assertEqual(missing.priority_tier, "M")
        self.assertTrue(missing.needs_fulltext_check)

    def test_document_type_is_classified_before_screening(self) -> None:
        scorer = RelevanceScorer()
        review = scorer.score(
            "A review of carbon nanotube CVD synthesis",
            "Catalysts and growth conditions are summarized.",
            raw_document_type="review",
            doi="10.1000/review",
        )
        self.assertEqual(review.document_type, "review")
        self.assertEqual(review.priority_tier, "C")

    def test_v12_promotes_strong_target_title_when_abstract_is_missing(self) -> None:
        result = RelevanceScorer().score(
            "Parametric study for carbon nanotube growth by catalytic CVD in a fluidized bed",
            "",
            doi="10.1000/title-only",
        )
        self.assertEqual(result.priority_tier, "B")
        self.assertEqual(result.priority_tier_reason, "metadata_missing_abstract_but_strong_target_title")

    def test_v12_rejects_explicit_non_cnt_material_despite_cnt_background(self) -> None:
        result = RelevanceScorer().score(
            "High-quality graphene using the Boudouard reaction",
            "The HiPco process produces single-walled carbon nanotubes by CVD. Here graphene was grown from CO.",
            doi="10.1000/graphene",
        )
        self.assertEqual(result.priority_tier, "R")
        self.assertEqual(result.priority_tier_reason, "explicit_non_cnt_material_in_title")

    def test_v12_demotes_theory_and_preexisting_cnt_without_synthesis(self) -> None:
        theory = RelevanceScorer().score(
            "The promoter role of sulfur in carbon nanotube growth",
            "We performed a density functional theory study of sulfur binding to Fe and CNT surfaces.",
            doi="10.1000/theory",
        )
        integration = RelevanceScorer().score(
            "Integration of Carbon Nanotubes in an HFCVD Diamond Synthesis Process",
            "Carbon nanotube layers were preliminarily deposited before diamond CVD and etched from the substrate.",
            doi="10.1000/integration",
        )
        self.assertEqual(theory.priority_tier, "C")
        self.assertEqual(integration.priority_tier, "C")


class StorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = MetadataStore(self.root / "metadata.sqlite3", similarity_threshold=0.90)
        self.store.start_run("RUN1", {})
        self.scorer = RelevanceScorer()

    def tearDown(self) -> None:
        self.store.close()
        self.temp.cleanup()

    def test_doi_merge_provider_priority_and_repeat_idempotence(self) -> None:
        first = NormalizedWork(
            source_api="openalex",
            external_id="W1",
            title="Methane CVD growth of carbon nanotubes",
            doi="10.1000/CNT",
            abstract="Short abstract.",
            citation_count=5,
            open_access_status="gold",
            collected_at="2026-01-01T00:00:00Z",
        )
        inserted = self.store.upsert_work(first, "RUN1", "raw/1.json", self.scorer)
        repeat = NormalizedWork(**{**first.to_dict(), "collected_at": "2026-01-02T00:00:00Z"})
        unchanged = self.store.upsert_work(repeat, "RUN1", "raw/2.json", self.scorer)
        enriched = self.store.upsert_work(
            NormalizedWork(
                source_api="semantic_scholar",
                external_id="S1",
                title=first.title,
                doi="https://doi.org/10.1000/cnt",
                abstract="A substantially longer abstract about methane CVD yield and growth temperature.",
                citation_count=12,
                open_access_status="closed",
                collected_at="2026-01-03T00:00:00Z",
            ),
            "RUN1",
            "raw/3.json",
            self.scorer,
        )
        self.assertEqual(inserted.action, "inserted")
        self.assertEqual(unchanged.action, "unchanged")
        self.assertEqual(enriched.match_type, "doi")
        self.assertEqual(self.store.count_works(), 1)
        row = self.store.connection.execute("SELECT * FROM works").fetchone()
        self.assertEqual(row["citation_count"], 12)
        self.assertEqual(row["open_access_status"], "closed")

    def test_title_similarity_merge_and_conflicting_doi_guard(self) -> None:
        left = self.store.upsert_work(
            NormalizedWork(
                source_api="openalex",
                external_id="W1",
                title="Synthesis of multi walled carbon nanotubes by chemical vapor deposition using iron catalyst",
                doi="10.1000/first",
                authors=["A. Author"],
                year=2023,
                collected_at="2026-01-01T00:00:00Z",
            ),
            "RUN1",
            "raw/1.json",
            self.scorer,
        )
        fuzzy = self.store.upsert_work(
            NormalizedWork(
                source_api="semantic_scholar",
                external_id="S1",
                title="Synthesis of multi-walled carbon nanotubes using iron catalyst by chemical vapour deposition",
                authors=["A. Author"],
                year=2023,
                collected_at="2026-01-02T00:00:00Z",
            ),
            "RUN1",
            "raw/2.json",
            self.scorer,
        )
        separate = self.store.upsert_work(
            NormalizedWork(
                source_api="crossref",
                external_id="10.1000/other",
                title="Synthesis of multi walled carbon nanotubes by chemical vapor deposition using iron catalyst",
                doi="10.1000/other",
                year=2023,
                collected_at="2026-01-03T00:00:00Z",
            ),
            "RUN1",
            "raw/3.json",
            self.scorer,
        )
        self.assertEqual(fuzzy.source_id, left.source_id)
        self.assertEqual(fuzzy.match_type, "title_fuzzy")
        self.assertNotEqual(separate.source_id, left.source_id)
        self.assertEqual(separate.match_type, "doi_conflict_review")
        self.assertEqual(separate.dedup_status, "needs_review")
        self.assertEqual(self.store.count_works(), 2)
        decisions = self.store.connection.execute("SELECT COUNT(*) FROM dedup_decision_log").fetchone()[0]
        self.assertEqual(decisions, 3)

    def test_short_exact_title_and_document_versions_are_not_auto_merged(self) -> None:
        first = self.store.upsert_work(
            NormalizedWork(
                source_api="openalex", external_id="W-short", title="Carbon nanotubes",
                authors=["A. Author"], year=2023, collected_at="2026-01-01T00:00:00Z",
            ),
            "RUN1", "raw/short-1.json", self.scorer,
        )
        second = self.store.upsert_work(
            NormalizedWork(
                source_api="semantic_scholar", external_id="S-short", title="Carbon nanotubes",
                authors=["A. Author"], year=2023, collected_at="2026-01-02T00:00:00Z",
            ),
            "RUN1", "raw/short-2.json", self.scorer,
        )
        self.assertNotEqual(first.source_id, second.source_id)
        self.assertEqual(second.match_type, "possible_duplicate")

    def test_legacy_csv_import_and_export_preserve_review_state(self) -> None:
        self.store.close()
        database = self.root / "legacy.sqlite3"
        master = self.root / "literature_master.csv"
        master.write_text(
            "source_id,source_type,title,year,doi_or_patent_no,screening_class,pdf_status,extraction_status,review_status\n"
            "P001,paper,Existing CNT paper,2020,10.1000/existing,formal_extract,downloaded,needs_review,pending_review\n",
            encoding="utf-8",
        )
        self.store = MetadataStore(database)
        self.store.start_run("RUN2", {})
        imported = self.store.import_legacy_csv(master, "RUN2", self.scorer)
        output = self.root / "export.csv"
        self.store.export_csv(output)
        row = self.store.connection.execute("SELECT * FROM works WHERE source_id='P001'").fetchone()
        self.assertEqual(imported, 1)
        self.assertEqual(row["screening_class"], "formal_extract")
        self.assertIn("abstract", output.read_text(encoding="utf-8-sig").splitlines()[0])

    def test_enrichment_doi_selection_is_resumable_by_source(self) -> None:
        work = NormalizedWork(
            source_api="openalex",
            external_id="W-enrich",
            title="Methane CVD growth of MWCNTs over Fe catalyst",
            doi="10.1000/enrich",
            abstract="Yield and growth temperature for carbon nanotube synthesis.",
            collected_at="2026-01-01T00:00:00Z",
        )
        self.store.upsert_work(work, "RUN1", "raw/openalex.json", self.scorer)
        self.assertEqual(
            self.store.list_dois_missing_source("semantic_scholar", 10),
            ["10.1000/enrich"],
        )
        self.store.upsert_work(
            NormalizedWork(
                source_api="semantic_scholar",
                external_id="S-enrich",
                title=work.title,
                doi=work.doi,
                collected_at="2026-01-02T00:00:00Z",
            ),
            "RUN1",
            "raw/s2.json",
            self.scorer,
        )
        self.assertEqual(self.store.list_dois_missing_source("semantic_scholar", 10), [])
        self.assertEqual(self.store.list_dois_missing_source("crossref", 10), ["10.1000/enrich"])


class ArchiveTests(unittest.TestCase):
    def test_request_credentials_are_redacted(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = RawArchive(root / "raw", root, "RUN1")
            relative = archive.save(
                "openalex",
                "search",
                "GET",
                "https://example.test/works?api_key=secret&mailto=person@example.com",
                {"x-api-key": "secret", "User-Agent": "tool person@example.com"},
                None,
                200,
                {},
                {"results": [], "echo": "secret person@example.com"},
                "",
                "2026-01-01T00:00:00Z",
            )
            payload = json.loads((root / relative).read_text(encoding="utf-8"))
            rendered = json.dumps(payload)
            self.assertNotIn("secret", rendered)
            self.assertNotIn("person@example.com", rendered)


if __name__ == "__main__":
    unittest.main()
