
import unittest
import os
import argparse
from unittest.mock import patch, MagicMock, call
from wa_crypt_tools.commands import pull
from wa_crypt_tools.adb import AdbError

class TestCmdPull(unittest.TestCase):

    def setUp(self):
        self.args = argparse.Namespace(
            output="/tmp/output",
            device="device123",
            pull_device=None
        )
        self.config = {
            "output": "/tmp/output",
            "device": "device123"
        }

    @patch("wa_crypt_tools.commands.pull.check_connection")
    @patch("wa_crypt_tools.commands.pull.os.makedirs")
    @patch("wa_crypt_tools.commands.pull.os.path.isdir")
    @patch("wa_crypt_tools.commands.pull.os.listdir")
    def test_pull_no_device(self, mock_listdir, mock_isdir, mock_makedirs, mock_check):
        mock_check.return_value = False
        
        ret = pull.pull_data(self.config, "device123")
        self.assertEqual(ret, 1)

    @patch("wa_crypt_tools.commands.pull.check_connection")
    @patch("wa_crypt_tools.commands.pull.os.makedirs")
    @patch("wa_crypt_tools.commands.pull.os.path.isdir")
    @patch("wa_crypt_tools.commands.pull.os.listdir")
    @patch("wa_crypt_tools.commands.pull.run_adb_command")
    @patch("wa_crypt_tools.commands.pull.subprocess.check_call")
    def test_pull_success(self, mock_subprocess, mock_adb_run, mock_listdir, mock_isdir, mock_makedirs, mock_check):
        mock_check.return_value = True
        # Destination is empty or not existing
        mock_isdir.return_value = True
        mock_listdir.return_value = [] # Empty

        # Mock ADB shell checks for presence
        # 1. Contacts presence check (success)
        # 2. WhatsApp dir presence check (success)
        mock_adb_run.side_effect = [
            None, # contact check success
            None  # wa folder check success
        ]

        ret = pull.pull_data(self.config, "device123")
        
        self.assertEqual(ret, 0)
        
        # Verify subprocess calls for pulling
        # 1. Contacts
        # 2. msgstore
        # 3. wa.db
        # 4. Backups
        # 5. Media
        # Exact calls might change, but we expect at least 5 calls
        self.assertTrue(mock_subprocess.call_count >= 5)
        
    @patch("wa_crypt_tools.commands.pull.check_connection")
    @patch("wa_crypt_tools.commands.pull.os.listdir")
    @patch("wa_crypt_tools.commands.pull.os.path.isdir")
    def test_pull_dir_not_empty(self, mock_isdir, mock_listdir, mock_check):
        mock_check.return_value = True
        mock_isdir.side_effect = lambda p: p.endswith("WhatsApp")
        mock_listdir.return_value = ["some_file"]
        
        ret = pull.pull_data(self.config, "device123")
        self.assertEqual(ret, 1)

if __name__ == '__main__':
    unittest.main()
