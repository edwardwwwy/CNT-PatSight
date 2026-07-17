from __future__ import annotations

import unittest
from pathlib import Path

from scripts.production.pipeline import doctor


ROOT = Path(__file__).resolve().parents[1]


class RepositoryHealthTests(unittest.TestCase):
    def test_public_assets_pass_doctor(self) -> None:
        result = doctor()
        self.assertTrue(result["valid"], result["errors"])
        self.assertEqual(result["temporary_database"], "ok")

    def test_batch_builders_depend_on_common_helpers(self) -> None:
        obsolete_import = "from scripts.extraction.build_a_class_batch import"
        for path in (ROOT / "scripts/extraction").glob("build_a_class_batch_*.py"):
            self.assertNotIn(
                obsolete_import,
                path.read_text(encoding="utf-8-sig"),
                path.name,
            )


if __name__ == "__main__":
    unittest.main()
