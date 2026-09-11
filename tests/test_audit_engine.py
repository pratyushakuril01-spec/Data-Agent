"""
tests/test_audit_engine.py
Comprehensive unit tests for parser, normalizer, detector, email generator, and ReAct agent.
"""

import unittest
import os
import pandas as pd

from core.parser import StatementParser
from core.normalizer import MerchantNormalizer
from core.detector import SubscriptionDetector, RecurringItem
from core.email_generator import CancellationEmailGenerator
from core.agent import GhostAuditReActAgent


class TestStatementParser(unittest.TestCase):

    def test_parse_chase_sample(self):
        sample_path = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'personal_chase_sample.csv')
        df = StatementParser.parse(sample_path)
        self.assertFalse(df.empty)
        self.assertIn('date', df.columns)
        self.assertIn('raw_description', df.columns)
        self.assertIn('amount', df.columns)
        self.assertTrue((df['amount'] > 0).any())

    def test_parse_amex_sample(self):
        sample_path = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'small_business_amex_sample.csv')
        df = StatementParser.parse(sample_path)
        self.assertFalse(df.empty)
        self.assertGreater(len(df), 10)


class TestMerchantNormalizer(unittest.TestCase):

    def setUp(self):
        self.normalizer = MerchantNormalizer()

    def test_known_merchants(self):
        cases = [
            ("AMZN DIG*2948 866-216-1072 WA", "Amazon Prime"),
            ("NETFLIX.COM 866-579-7172 CA", "Netflix"),
            ("SPOTIFY USA 129384 NY", "Spotify"),
            ("OPENAI *CHATGPT SUBSCRIPTION", "OpenAI / ChatGPT"),
            ("PLANET FIT CLUB #104 SEATTLE WA", "Planet Fitness"),
            ("ADOBE *CREATIVE CLOUD 800-833-6687 CA", "Adobe Creative Cloud"),
            ("GITHUB, INC. 877-448-4820 CA", "GitHub"),
            ("DROPBOX*39824 SAN FRANCISCO CA", "Dropbox"),
        ]
        for raw, expected in cases:
            norm_name, category, is_sub, hint = self.normalizer.normalize(raw)
            self.assertEqual(norm_name, expected, f"Failed on: {raw}")
            self.assertTrue(is_sub)

    def test_noise_cleaning(self):
        raw = "POS DEBIT PURCHASE 12345 ACME SERVERS 800-555-0199 CA"
        cleaned = self.normalizer.clean_raw_descriptor(raw)
        self.assertNotIn("Pos Debit", cleaned)
        self.assertNotIn("800-555-0199", cleaned)


class TestSubscriptionDetector(unittest.TestCase):

    def setUp(self):
        self.detector = SubscriptionDetector()

    def test_personal_chase_audit(self):
        sample_path = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'personal_chase_sample.csv')
        df = StatementParser.parse(sample_path)
        items = self.detector.analyze(df)

        self.assertGreater(len(items), 0)
        merchants = [i.merchant for i in items]
        self.assertIn("Netflix", merchants)
        self.assertIn("Amazon Prime", merchants)
        self.assertIn("Spotify", merchants)
        self.assertIn("Adobe Creative Cloud", merchants)

        # Check Netflix price hike detection
        netflix_item = next(i for i in items if i.merchant == "Netflix")
        self.assertTrue(netflix_item.has_price_hike)
        self.assertAlmostEqual(netflix_item.initial_amount, 15.49, places=2)
        self.assertAlmostEqual(netflix_item.current_amount, 22.99, places=2)
        self.assertAlmostEqual(netflix_item.price_hike_amount, 7.50, places=2)
        self.assertEqual(netflix_item.cadence, "Monthly")

        # Check trial rollover detection
        trial_item = next((i for i in items if i.is_trial_rollover), None)
        self.assertIsNotNone(trial_item)
        self.assertIn("Meditation App Pro Trial", trial_item.merchant)

    def test_business_amex_audit(self):
        sample_path = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'small_business_amex_sample.csv')
        df = StatementParser.parse(sample_path)
        items = self.detector.analyze(df)

        merchants = [i.merchant for i in items]
        self.assertIn("Slack", merchants)
        self.assertIn("GitHub", merchants)
        self.assertIn("OpenAI / ChatGPT", merchants)
        self.assertIn("Dropbox", merchants)

        dropbox_item = next(i for i in items if i.merchant == "Dropbox")
        self.assertTrue(dropbox_item.has_price_hike)
        self.assertAlmostEqual(dropbox_item.price_hike_amount, 3.00, places=2)


class TestEmailGenerator(unittest.TestCase):

    def test_price_hike_email(self):
        item = RecurringItem(
            merchant="Netflix",
            category="Streaming & Media",
            cadence="Monthly",
            current_amount=22.99,
            initial_amount=15.49,
            min_amount=15.49,
            max_amount=22.99,
            transaction_count=5,
            first_date="2024-01-15",
            last_date="2024-05-15",
            days_between_avg=30.2,
            has_price_hike=True,
            price_hike_amount=7.50,
            price_hike_pct=48.4,
            hike_detected_date="2024-04-15",
            raw_descriptors=["NETFLIX.COM 866-579-7172 CA"]
        )

        email = CancellationEmailGenerator.generate(
            item=item,
            user_name="Jane Doe",
            user_email="jane@example.com",
            account_last4="4321"
        )
        self.assertIn("Netflix", email['subject'])
        self.assertIn("Jane Doe", email['body'])
        self.assertIn("22.99", email['body'])
        self.assertIn("15.49", email['body'])
        self.assertIn("FTC", email['body'])
        self.assertIn("mailto:", email['mailto_link'])


class TestReActAgent(unittest.TestCase):

    def test_full_agent_run(self):
        agent = GhostAuditReActAgent()
        sample_path = os.path.join(os.path.dirname(__file__), '..', 'sample_data', 'personal_chase_sample.csv')
        report = agent.run_audit(sample_path)

        self.assertGreater(report.total_transactions, 0)
        self.assertGreater(report.recurring_monthly_burn, 0)
        self.assertGreater(report.price_hikes_count, 0)
        self.assertGreater(len(report.react_trace), 3)

        # Verify trace contains Thought -> Action -> Observation
        first_step = report.react_trace[0]
        self.assertTrue(len(first_step.thought) > 0)
        self.assertEqual(first_step.action, "parse_statement")
        self.assertTrue(len(first_step.observation) > 0)


if __name__ == '__main__':
    unittest.main()
