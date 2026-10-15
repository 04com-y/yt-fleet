import unittest
import os
import shutil
import tempfile
from control.ledger import TopicLedger

class TestTopicLedger(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.ledger_file = os.path.join(self.test_dir, "topics.jsonl")
        self.ledger = TopicLedger(self.ledger_file)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_duplicate_topic_prevention(self):
        topic = "Top 10 Open Source AI Models"
        self.assertTrue(self.ledger.is_topic_allowed(topic))
        self.ledger.record_topic("ai-tools-en", topic, "Video Title")
        self.assertFalse(self.ledger.is_topic_allowed(topic), "Topic should be blocked within 14 days")
        self.assertTrue(self.ledger.is_topic_allowed("Completely Different Topic"))
