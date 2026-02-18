import json
import tempfile
import unittest
from pathlib import Path

from scripts import validate_target_integration_matrix as v


class TargetMatrixValidationTests(unittest.TestCase):
    def test_current_matrix_is_schema_valid(self) -> None:
        self.assertEqual(v.main(), 0)

    def test_invalid_matrix_fails(self) -> None:
        original = v.MATRIX_PATH.read_text()
        try:
            bad = json.loads(original)
            del bad["sources"]["kantian_ivi"]["repository_url"]
            v.MATRIX_PATH.write_text(json.dumps(bad))
            self.assertEqual(v.main(), 1)
        finally:
            v.MATRIX_PATH.write_text(original)


if __name__ == "__main__":
    unittest.main()
