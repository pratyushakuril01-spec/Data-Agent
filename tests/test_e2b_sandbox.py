"""
tests/test_e2b_sandbox.py
Unit tests for the E2B Sandbox Manager in fallback and cloud execution scenarios.
"""

import unittest
from core.e2b_sandbox import E2BSandboxManager


class TestE2BSandboxManager(unittest.TestCase):

    def setUp(self):
        # Default test without cloud key to test safe local execution
        self.mgr = E2BSandboxManager(api_key=None)

    def test_run_basic_python(self):
        code = "print('Hello from Sandbox!')\nx = 10 * 5\nprint(f'Result={x}')"
        result = self.mgr.run_code(code)

        self.assertFalse(result.is_cloud_sandbox)
        self.assertIn("Hello from Sandbox!", result.stdout)
        self.assertIn("Result=50", result.stdout)
        self.assertIsNone(result.error)

    def test_run_pandas_in_sandbox(self):
        code = """
import pandas as pd
data = {'merchant': ['Netflix', 'Spotify'], 'amount': [15.49, 10.99]}
df = pd.DataFrame(data)
print(f"Total: {df['amount'].sum()}")
"""
        result = self.mgr.run_code(code)
        self.assertIn("Total: 26.48", result.stdout)
        self.assertIsNone(result.error)

    def test_syntax_error_handling(self):
        code = "def bad_syntax(:\n    pass"
        result = self.mgr.run_code(code)
        self.assertIsNotNone(result.error)
        self.assertIn("SyntaxError", result.error)


if __name__ == '__main__':
    unittest.main()
