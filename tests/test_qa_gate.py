import unittest
from control.qa_gate import QAGate

class TestQAGate(unittest.TestCase):
    def setUp(self):
        self.qa = QAGate()

    def test_valid_script(self):
        script = {
            "title": "Clean Architecture in Python",
            "original_value": "Comprehensive benchmarks against micro-frameworks",
            "claims": [
                {"claim": "c1", "source": "https://python.org"},
                {"claim": "c2", "source": "https://github.com"},
                {"claim": "c3", "source": "https://arxiv.org"}
            ]
        }
        rules = {"require_original_value": True, "min_sourced_claims": 3, "banned_topics": ["medical", "finance"]}
        passed, errors = self.qa.validate_script(script, rules)
        self.assertTrue(passed)
        self.assertEqual(errors, [])

    def test_banned_topic_rejected(self):
        script = {
            "title": "Best Medical Treatments for Coding Burnout",
            "original_value": "Doctors advice",
            "claims": [{"claim": "c1"}, {"claim": "c2"}, {"claim": "c3"}]
        }
        rules = {"require_original_value": True, "min_sourced_claims": 3, "banned_topics": ["medical"]}
        passed, errors = self.qa.validate_script(script, rules)
        self.assertFalse(passed)
        self.assertIn("Title contains banned topic keyword: medical", errors[0])
