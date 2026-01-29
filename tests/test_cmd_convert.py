import unittest
from unittest.mock import patch, MagicMock
from wa_crypt_tools.commands.convert import convert_vcf

class TestCmdConvert(unittest.TestCase):
    @patch('wa_crypt_tools.commands.convert.ensure_venv')
    @patch('wa_crypt_tools.commands.convert.get_venv_python_path')
    @patch('subprocess.check_call')
    @patch('os.path.exists')
    def test_convert_vcf_success(self, mock_exists, mock_check_call, mock_get_py, mock_ensure_venv):
        # Setup
        mock_exists.return_value = True
        mock_get_py.return_value = '/path/to/venv/python'
        
        # Action
        ret = convert_vcf('input.vcf', 'output.json')
        
        # Verify
        self.assertEqual(ret, 0)
        mock_ensure_venv.assert_called_once()
        mock_check_call.assert_called_once()
        
        # Check command args (flexible check)
        cmd = mock_check_call.call_args[0][0]
        self.assertEqual(cmd[0], '/path/to/venv/python')
        self.assertIn('wa_crypt_tools.commands.convert', cmd)
        self.assertIn('--internal', cmd)

    @patch('os.path.exists')
    def test_convert_vcf_file_not_found(self, mock_exists):
        mock_exists.return_value = False
        ret = convert_vcf('missing.vcf', 'output.json')
        self.assertEqual(ret, 1)

if __name__ == '__main__':
    unittest.main()
