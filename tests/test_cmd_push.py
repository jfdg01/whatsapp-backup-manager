
import unittest
from unittest.mock import patch
from pathlib import Path
import subprocess

from wa_crypt_tools.commands.push import push_whatsapp


class TestCmdPush(unittest.TestCase):
    def setUp(self):
        self.mock_input = Path("/tmp/mock_input")
        self.mock_wa = self.mock_input / "WhatsApp"

    @patch('wa_crypt_tools.commands.push.os.path.exists')
    def test_push_input_not_found(self, mock_exists):
        # Setup: os.path.exists returns False
        mock_exists.return_value = False

        result = push_whatsapp(self.mock_input)

        self.assertFalse(result)
        mock_exists.assert_called_with(str(self.mock_wa))

    @patch('wa_crypt_tools.commands.push.os.path.exists')
    @patch('wa_crypt_tools.commands.push.subprocess.check_call')
    def test_push_adb_check_fails(self, mock_check_call, mock_exists):
        # Setup: exists=True, but ADB check fails
        mock_exists.return_value = True
        mock_check_call.side_effect = [
            subprocess.CalledProcessError(1, 'adb')
        ]

        result = push_whatsapp(self.mock_input)

        self.assertFalse(result)

    @patch('wa_crypt_tools.commands.push.os.path.exists')
    @patch('wa_crypt_tools.commands.push.subprocess.check_call')
    def test_push_success(self, mock_check_call, mock_exists):
        # Setup: everything works
        mock_exists.return_value = True
        mock_check_call.return_value = 0

        result = push_whatsapp(self.mock_input, device_id="device123")

        self.assertTrue(result)

        expected_adb_base = ['adb', '-s', 'device123']
        target_base = "/sdcard/Android/media/com.whatsapp"

        # Calls expected:
        # 1. get-state
        # 2. mkdir -p target
        # 3. push source target

        # Verify push call specifically
        mock_check_call.assert_any_call(
            expected_adb_base + ["push", str(self.mock_wa), target_base]
        )

    @patch('wa_crypt_tools.commands.push.os.path.exists')
    @patch('wa_crypt_tools.commands.push.subprocess.check_call')
    def test_push_mkdir_fails(self, mock_check_call, mock_exists):
        # Setup: exists=True, ADB check ok, but mkdir fails
        mock_exists.return_value = True

        # list of side effects: success (get-state), error (mkdir)
        mock_check_call.side_effect = [
            0,
            subprocess.CalledProcessError(1, 'mkdir')
        ]

        result = push_whatsapp(self.mock_input)

        self.assertFalse(result)
