import unittest
import os
import sys
from flask import Flask
from task_scheduler import TaskScheduler

class TestTaskScheduler(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.db_name = "test_petfinder.db"
        
    def test_scheduler_initialization(self):
        """Test that the TaskScheduler can be initialized without errors."""
        try:
            scheduler = TaskScheduler(self.app, self.db_name)
            self.assertIsNotNone(scheduler)
            scheduler.shutdown()
            print("TaskScheduler initialized successfully!")
        except Exception as e:
            self.fail(f"TaskScheduler initialization failed with error: {e}")
            
if __name__ == "__main__":
    unittest.main()