
import unittest
import os
from unittest.mock import patch, MagicMock, call
from pathlib import Path

# Import the module to test
from wa_crypt_tools.commands import decrypt

class TestCmdDecrypt(unittest.TestCase):
    
    def setUp(self):
        self.mock_config = {}
        self.cwd = os.getcwd()
        self.output_dir = os.path.join(self.cwd, "output")

    @patch('wa_crypt_tools.commands.decrypt.ensure_venv')
    @patch('wa_crypt_tools.commands.decrypt.get_venv_path')
    @patch('subprocess.check_call')
    @patch('os.path.exists')
    def test_decrypt_database_full_flow(self, mock_exists, mock_subprocess, mock_get_venv_path, mock_ensure_venv):
        # Setup mocks
        mock_get_venv_path.return_value = "/mock/venv"
        
        # Path existence map
        def exists_side_effect(path):
            path = str(path)
            if "msgstore.db.crypt15" in path:
                return True
            if "wa.db.crypt15" in path:
                # We want it to be found in Databases or Backups
                # Let's say it's in Databases
                return True
            if "wadecrypt" in path:
                return True # assume binary exists
            return False
            
        mock_exists.side_effect = exists_side_effect

        # Call the function
        key = "a"*64
        result = decrypt.decrypt_database(self.mock_config, input_dir=self.output_dir, key=key)
        
        # Assertions
        self.assertEqual(result, 0)
        mock_ensure_venv.assert_called_once()
        
        wadecrypt_bin = os.path.join("/mock/venv", "bin", "wadecrypt")
        
        # Expected subprocess calls
        # 1. msgstore
        # 2. wa.db
        
        # We need to construct the full paths that the code would assume
        db_folder = os.path.join(self.output_dir, "WhatsApp", "Databases")
        
        # Note: Paths might be absolute in the implementation code
        # The test output_dir is absolute via os.getcwd()
        
        expected_calls = [
            call([wadecrypt_bin, key, os.path.join(db_folder, "msgstore.db.crypt15"), os.path.join(self.output_dir, "msgstore.db")]),
            call([wadecrypt_bin, key, os.path.join(db_folder, "wa.db.crypt15"), os.path.join(self.output_dir, "wa.db")])
        ]
        
        mock_subprocess.assert_has_calls(expected_calls, any_order=True)

    def test_decrypt_missing_key(self):
        # Should return 1 if key is missing
        result = decrypt.decrypt_database(self.mock_config, input_dir="/tmp", key=None)
        self.assertEqual(result, 1)

    @patch('wa_crypt_tools.commands.decrypt.ensure_venv')
    @patch('wa_crypt_tools.commands.decrypt.get_venv_path')
    @patch('subprocess.check_call')
    @patch('os.path.exists')
    def test_decrypt_missing_files(self, mock_exists, mock_subprocess, mock_get_venv_path, mock_ensure_venv):
         mock_get_venv_path.return_value = "/mock/venv"
         # Nothing exists
         mock_exists.return_value = False
         
         key = "a"*64
         result = decrypt.decrypt_database(self.mock_config, input_dir=self.output_dir, key=key)
         
         self.assertEqual(result, 0) # Still success even if files not found, just warnings printed
         
         mock_subprocess.assert_not_called()

if __name__ == '__main__':
    unittest.main()
