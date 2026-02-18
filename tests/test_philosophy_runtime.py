import unittest
from io import BytesIO
from zipfile import ZipFile

from not_mainstreet import (
    ContinuityConstraint,
    EventSpine,
    NodeState,
    Proposal,
    extract_docx_text,
    l_diag,
    run_cycle,
)
from not_mainstreet.governance import SovereigntyContext, sovereignty_weight


def _make_minimal_docx(text: str) -> bytes:
    body = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:body><w:p><w:r><w:t>{text}</w:t></w:r></w:p></w:body>
</w:document>'''
    buf = BytesIO()
    with ZipFile(buf, "w") as zf:
        zf.writestr("word/document.xml", body)
    return buf.getvalue()


class PhilosophyRuntimeTests(unittest.TestCase):
    def test_rejects_when_not_anchored(self) -> None:
        spine = EventSpine()
        spine.append("NodeRegistered", {"node_id": "n1"})

        out = run_cycle(
            spine,
            Proposal("p1", "n1", dx=0.1, dy=0.1, noumenal_valid=True, phenomenal_valid=True),
            ContinuityConstraint(0.3, 0.3),
            l_diag(0.2, 0.3),
            trust_score=0.4,
            tenure_score=0.2,
        )
        self.assertFalse(out.committed)
        self.assertEqual(out.reason, "verification_floor")

    def test_commits_and_generates_relational_artifact(self) -> None:
        spine = EventSpine()
        spine.append("NodeRegistered", {"node_id": "n1"})
        spine.append("NodeTransitioned", {"node_id": "n1", "next_state": "anchored"})

        out = run_cycle(
            spine,
            Proposal("p2", "n1", dx=0.1, dy=0.1, noumenal_valid=True, phenomenal_valid=True),
            ContinuityConstraint(0.3, 0.3),
            l_diag(0.2, 0.3),
            trust_score=0.4,
            tenure_score=0.2,
        )
        self.assertTrue(out.committed)
        artifacts = spine.for_type("RelationalArtifactCreated")
        self.assertEqual(len(artifacts), 1)

    def test_laplacian_is_diagnostic_not_constraint(self) -> None:
        spine = EventSpine()
        spine.append("NodeRegistered", {"node_id": "n1"})
        spine.append("NodeTransitioned", {"node_id": "n1", "next_state": "anchored"})

        out = run_cycle(
            spine,
            Proposal("p3", "n1", dx=0.5, dy=0.1, noumenal_valid=True, phenomenal_valid=True),
            ContinuityConstraint(0.3, 0.3),
            l_diag(999.0, 999.0),
            trust_score=0.4,
            tenure_score=0.2,
        )
        self.assertFalse(out.committed)
        self.assertEqual(out.reason, "continuity_violation")

    def test_docx_text_extraction(self) -> None:
        blob = _make_minimal_docx("hello philosophy")
        text = extract_docx_text(blob)
        self.assertIn("hello philosophy", text)

    def test_sovereignty_weight_bounds(self) -> None:
        value = sovereignty_weight(NodeState.TRUSTED, SovereigntyContext(trust_score=1.0, tenure_score=1.0))
        self.assertGreaterEqual(value, 0.0)
        self.assertLessEqual(value, 1.0)


if __name__ == "__main__":
    unittest.main()
