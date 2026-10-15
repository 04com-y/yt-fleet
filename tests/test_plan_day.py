import unittest
from control.plan_day import plan_day

class TestPlanDay(unittest.TestCase):
    def test_plan_day_output(self):
        res = plan_day(channels_dir="channels", config_dir="config")
        self.assertIn("include", res)
        self.assertIsInstance(res["include"], list)

    def test_plan_day_specific_channel(self):
        res = plan_day(channels_dir="channels", config_dir="config", only_channel="ai-tools-en")
        self.assertEqual(res["include"], [{"channel": "ai-tools-en"}])
