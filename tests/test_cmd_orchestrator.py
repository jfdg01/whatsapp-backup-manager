import unittest
from unittest.mock import patch, MagicMock
from wa_crypt_tools.commands.orchestrator import run_orchestrator


class TestOrchestrator(unittest.TestCase):
    
    @patch('wa_crypt_tools.commands.orchestrator.pull_data')
    @patch('wa_crypt_tools.commands.orchestrator.decrypt_database')
    @patch('wa_crypt_tools.commands.orchestrator.convert_vcf')
    @patch('os.path.exists')
    def test_workflow_success(self, mock_exists, mock_convert, mock_decrypt, mock_pull):
        # Setup
        mock_pull.return_value = 0
        mock_decrypt.return_value = 0
        mock_convert.return_value = 0
        # Mock exists to return True for contacts.vcf
        mock_exists.return_value = True
        
        config = {'output': '/tmp/out', 'key': 'abc'}
        
        # Execute
        ret = run_orchestrator(config)
        
        # Verify
        self.assertEqual(ret, 0)
        mock_pull.assert_called_once_with(config)
        # decrypt called with adjusted input dir
        # decrypt input_dir should be absolute path of config output
        # checks args valid
        self.assertTrue(mock_decrypt.called) 
        _, kwargs = mock_decrypt.call_args
        self.assertIn('input_dir', kwargs)
        
        mock_convert.assert_called_once()
    
    @patch('wa_crypt_tools.commands.orchestrator.pull_data')
    def test_pull_fail(self, mock_pull):
        mock_pull.return_value = 1
        config = {}
        ret = run_orchestrator(config)
        self.assertEqual(ret, 1)

    @patch('wa_crypt_tools.commands.orchestrator.pull_data')
    @patch('wa_crypt_tools.commands.orchestrator.decrypt_database')
    @patch('wa_crypt_tools.commands.orchestrator.convert_vcf')
    def test_decrypt_skipped_if_no_key(self, mock_convert, mock_decrypt, mock_pull):
        mock_pull.return_value = 0
        config = {'output': '/tmp', 'key': None} # No key
        
        run_orchestrator(config)
        
        mock_pull.assert_called()
        mock_decrypt.assert_not_called()
        # Convert could still run if contacts exist (mock default exists behavior?)
        # os.path.exists not mocked here, so it will check real FS. 
        # /tmp/contacts.vcf probably doesn't exist.
