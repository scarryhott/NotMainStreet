import unittest

from not_mainstreet import What, When, Where, Who, Why, build_edge_proposal


class EdgeProposalTests(unittest.TestCase):
    def test_build_edge_proposal_success(self) -> None:
        proposal, evaln = build_edge_proposal(
            proposal_id="p-1",
            tenant_id="tenant-a",
            community_id="c-1",
            session_id="sess-1",
            who=Who(user_id="u-1", roles=["member"], reputation_ref="rep:1"),
            why=Why(goal="help neighbors", constraints=[], values=["care"], urgency="normal"),
            what=What(category="service", description="deliver food", budget=10, requirements=[]),
            where=Where(scope_level="block", geo="x", service_area="y", constraints=[]),
            when=When(window="this-week", trigger_conditions=[], deadline="2026-03-01"),
            thread_ref="thread-1",
        )
        self.assertTrue(evaln.gate_results.noumenal)
        self.assertTrue(evaln.gate_results.phenomenal)
        self.assertEqual(proposal.routing_class, "service_request")
        self.assertEqual(evaln.gate_results.gate_outcome, "pass")
        self.assertFalse(evaln.needs_disambiguation)

    def test_missing_w_fails_gate(self) -> None:
        proposal, evaln = build_edge_proposal(
            proposal_id="p-2",
            tenant_id="tenant-a",
            community_id="c-1",
            session_id="sess-2",
            who=Who(user_id="", roles=["member"], reputation_ref="rep:1"),
            why=Why(goal="", constraints=[], values=[], urgency="normal"),
            what=What(category="service", description="", budget=10, requirements=[]),
            where=Where(scope_level="invalid", geo="x", service_area="y", constraints=[]),
            when=When(window="", trigger_conditions=[], deadline="2026-03-01"),
            thread_ref="thread-1",
        )
        self.assertFalse(evaln.gate_results.noumenal)
        self.assertFalse(evaln.gate_results.phenomenal)
        self.assertGreaterEqual(len(evaln.gate_results.missing_fields), 1)
        self.assertEqual(evaln.gate_results.gate_outcome, "fail")
        self.assertEqual(proposal.status, "submitted")


if __name__ == "__main__":
    unittest.main()
