import os
import sys
import unittest
import json
import argparse
from unittest.mock import patch, MagicMock

# Add project root to sys.path
sys.path.insert(0, os.getcwd())

from wa_crypt_tools.config import load_config, merge_args_with_config
from wa_crypt_tools.env_utils import get_venv_path, ensure_venv

class TestConfigEnv(unittest.TestCase):
    def setUp(self):
        self.test_config = "test_config.json"
        with open(self.test_config, 'w') as f:
            json.dump({"output": "test_output", "key": "1234"}, f)
            
    def tearDown(self):
        if os.path.exists(self.test_config):
            os.remove(self.test_config)
            
    def test_load_config(self):
        cfg = load_config(self.test_config)
        self.assertEqual(cfg['output'], "test_output")
        self.assertEqual(cfg['key'], "1234")
        
    def test_merge_args(self):
        cfg = load_config(self.test_config)
        args = argparse.Namespace(
            output=None,
            key=None,
            input=None,
            device=None,
            pull_device=None,
            push_device=None
        )
        
        # Test merging
        merge_args_with_config(args, cfg)
        self.assertTrue(args.output.endswith("test_output")) # Should be absolute
        self.assertEqual(args.key, "1234")
        
    def test_env_path(self):
        path = get_venv_path("/tmp")
        self.assertEqual(path, "/tmp/wa-crypt-tools")

if __name__ == '__main__':
    unittest.main()
