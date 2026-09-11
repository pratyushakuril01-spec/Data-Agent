"""
tests/test_langgraph_agent.py
Unit tests for the LangGraph Audit Agent and tool bindings.
"""

import unittest
import os
from core.langgraph_agent import LangGraphAuditAgent, build_audit_tools
from core.e2b_sandbox import E2BSandboxManager
from core.normalizer import MerchantNormalizer
from core.detector import SubscriptionDetector


class TestLangGraphAgent(unittest.TestCase):

    def setUp(self):
        self.agent = LangGraphAuditAgent()

    def test_tools_factory(self):
        sandbox_mgr = E2BSandboxManager()
        norm = MerchantNormalizer()
        det = SubscriptionDetector(norm)
        tools = build_audit_tools(sandbox_mgr, norm, det)

        self.assertEqual(len(tools), 4)
        tool_names = [t.name for t in tools]
        self.assertIn("execute_python_in_e2b_sandbox", tool_names)
        self.assertIn("normalize_merchant", tool_names)
        self.assertIn("audit_statement_data", tool_names)
        self.assertIn("draft_cancellation_email", tool_names)

    def test_run_audit_end_to_end(self):
        sample_path = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'personal_chase_sample.csv')
        report = self.agent.run_audit(sample_path)

        self.assertGreater(report.total_transactions, 0)
        self.assertGreater(len(report.detected_subscriptions), 0)
        self.assertTrue(any(s.merchant == "Netflix" for s in report.detected_subscriptions))
        self.assertTrue(report.price_hikes_count > 0)


if __name__ == '__main__':
    unittest.main()
