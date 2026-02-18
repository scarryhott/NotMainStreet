import unittest

from not_mainstreet import (
    ContinuityConstraint,
    EventSpine,
    cdm_hash,
    validate_continuity,
)


class EventSpineTests(unittest.TestCase):
    def test_commit_blocked_for_potential_node(self) -> None:
        spine = EventSpine()
        spine.append("NodeRegistered", {"node_id": "n1"})

        with self.assertRaises(PermissionError):
            spine.append("ProposalCommitRequested", {"node_id": "n1"})

    def test_commit_allowed_after_anchor_transition(self) -> None:
        spine = EventSpine()
        spine.append("NodeRegistered", {"node_id": "n1"})
        spine.append("NodeTransitioned", {"node_id": "n1", "next_state": "anchored"})

        spine.append("ProposalCommitRequested", {"node_id": "n1"})
        self.assertEqual(len(spine.for_type("ProposalCommitRequested")), 1)


class ContinuityTests(unittest.TestCase):
    def test_continuity_constraint(self) -> None:
        c = ContinuityConstraint(epsilon_x=0.3, epsilon_y=0.2)
        self.assertTrue(validate_continuity(dx=0.2, dy=0.1, constraint=c))
        self.assertFalse(validate_continuity(dx=0.31, dy=0.1, constraint=c))


class CanonicalizationTests(unittest.TestCase):
    def test_equivalent_payloads_have_same_hash(self) -> None:
        a = {
            "title": "Cafe\u0301",
            "font_family": "Arial",
            "heading_level": "h2",
            "lines": ["  hello   world  "],
            "optional": None,
        }
        b = {
            "lines": ["hello world"],
            "heading_level": 2,
            "title": "Café",
            "font_family": "Times New Roman",
        }
        self.assertEqual(cdm_hash(a), cdm_hash(b))


if __name__ == "__main__":
    unittest.main()
