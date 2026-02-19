import unittest

from not_mainstreet import OpenClawBridge, UserContext


class OpenClawBridgeTests(unittest.TestCase):
    def test_refinement_cycle(self) -> None:
        bridge = OpenClawBridge()
        facts, profile, proposal = bridge.run_refinement_cycle(
            UserContext(
                user_id="u-1",
                intent="improve local food routing",
                region_hint="district-9",
                density_band="moderate",
            )
        )
        self.assertGreaterEqual(len(facts), 3)
        self.assertEqual(profile["user_id"], "u-1")
        self.assertIn("openclaw refinement", proposal.title)
        self.assertGreaterEqual(len(proposal.patch_outline), 3)


if __name__ == "__main__":
    unittest.main()
