import unittest

from not_mainstreet import empathy_reflection


class EmpathyEngineTests(unittest.TestCase):
    def test_empathy_reflection_defaults(self) -> None:
        payload = empathy_reflection("help community gardens")
        self.assertEqual(payload.mode, "complexify")
        self.assertIn("advisory", payload.amplification_notice)
        self.assertGreaterEqual(len(payload.guardrails), 3)

    def test_invalid_mode_falls_back(self) -> None:
        payload = empathy_reflection("anything", mode="unknown")
        self.assertEqual(payload.mode, "complexify")


if __name__ == "__main__":
    unittest.main()
