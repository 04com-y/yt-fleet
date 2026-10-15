import unittest
import yaml
import glob
import os
from control.schema import ChannelConfig, GlobalConfig, WeekTemplate

class TestSchemas(unittest.TestCase):
    def test_all_channel_configs(self):
        channel_files = glob.glob("channels/*.yml")
        self.assertGreaterEqual(len(channel_files), 15, "Should have at least 15 channel configs")
        for fpath in channel_files:
            with open(fpath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                config = ChannelConfig(**data)
                self.assertTrue(config.slug, f"Slug missing in {fpath}")
                self.assertIn(config.language, ["en", "hi", "es", "pt"], f"Invalid language in {fpath}")

    def test_global_config(self):
        with open("config/global.yml", "r") as f:
            data = yaml.safe_load(f)
            cfg = GlobalConfig(**data)
            self.assertFalse(cfg.pause)

    def test_week_template(self):
        with open("config/week_template.yml", "r") as f:
            data = yaml.safe_load(f)
            wt = WeekTemplate(**data)
            self.assertEqual(len(wt.schedule), 7, "Must have 7 days in schedule")
