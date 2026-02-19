import shutil
import unittest
from pathlib import Path

from not_mainstreet import (
    ContinuityConstraint,
    EventSpine,
    cdm_hash,
    validate_continuity,
)
from not_mainstreet.database import EngineDatabases, initialize_databases, run_query


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



    def test_anchor_event_transitions_registered_node(self) -> None:
        spine = EventSpine()
        spine.append("NodeRegistered", {"node_id": "n1"})
        spine.append(
            "AnchorEvent",
            {
                "event_type": "AnchorEvent",
                "node_id": "n1",
                "verification_class": "signed_witness",
                "evidence_pointer": "evidence://anchor-1",
                "witnesses": ["w1", "w2"],
                "signer": "sig:abc",
                "occurred_at": "2026-01-01T00:00:00Z",
                "policy_version": "policy/v1",
            },
        )

        node = spine.nodes["n1"]
        self.assertEqual(node.state.value, "anchored")
        self.assertEqual(len(spine.for_type("NodeTransitioned")), 1)

    def test_anchor_event_rejects_invalid_payload(self) -> None:
        spine = EventSpine()
        spine.append("NodeRegistered", {"node_id": "n1"})

        with self.assertRaises(ValueError):
            spine.append(
                "AnchorEvent",
                {
                    "event_type": "AnchorEvent",
                    "node_id": "n1",
                    "verification_class": "not-valid",
                    "evidence_pointer": "evidence://anchor-2",
                    "witnesses": ["w1"],
                    "signer": "sig:def",
                    "occurred_at": "2026-01-01T00:00:00Z",
                    "policy_version": "policy/v1",
                },
            )



    def test_spine_persists_events_when_inside_db_configured(self) -> None:
        data_root = Path("data")
        if data_root.exists():
            shutil.rmtree(data_root)
        cfg = EngineDatabases(inside_path="data/test_spine_inside.db", outside_path="data/test_spine_outside.db")
        initialize_databases(cfg)

        spine = EventSpine(inside_db_path=cfg.inside_path)
        spine.append("NodeRegistered", {"node_id": "n1"})
        rows = run_query(cfg.inside_path, "SELECT event_type, payload_json FROM engine_events ORDER BY id ASC")
        self.assertEqual(rows[0]["event_type"], "NodeRegistered")

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
