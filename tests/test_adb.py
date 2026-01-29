import unittest
from unittest.mock import patch, MagicMock
from wa_crypt_tools.adb import get_adb_base, list_devices, get_product_model, check_connection, AdbError

class TestAdb(unittest.TestCase):
    
    def test_get_adb_base(self):
        self.assertEqual(get_adb_base(), ["adb"])
        self.assertEqual(get_adb_base("123"), ["adb", "-s", "123"])

    @patch("wa_crypt_tools.adb.run_adb_command")
    def test_check_connection_success(self, mock_run):
        mock_run.return_value = "device"
        self.assertTrue(check_connection("123"))
        mock_run.assert_called_with(["adb", "-s", "123", "get-state"])

    @patch("wa_crypt_tools.adb.run_adb_command")
    def test_check_connection_fail(self, mock_run):
        mock_run.side_effect = AdbError("Fail")
        self.assertFalse(check_connection("123"))

    @patch("wa_crypt_tools.adb.run_adb_command")
    def test_get_product_model(self, mock_run):
        mock_run.return_value = "Pixel 6"
        self.assertEqual(get_product_model("123"), "Pixel 6")
        
    @patch("wa_crypt_tools.adb.run_adb_command")
    def test_get_product_model_fail(self, mock_run):
        mock_run.side_effect = AdbError("Fail")
        self.assertEqual(get_product_model("123"), "Unknown Model")

    @patch("wa_crypt_tools.adb.run_adb_command")
    def test_list_devices(self, mock_run):
        mock_output = """List of devices attached
device1\tdevice model:Pixel_6 product:oriole
device2\tunauthorized
"""
        mock_run.return_value = mock_output
        devices = list_devices()
        self.assertEqual(len(devices), 2)
        self.assertEqual(devices[0]['id'], "device1")
        self.assertEqual(devices[0]['model'], "Pixel 6")
        self.assertEqual(devices[0]['state'], "device") # Wait, my parser logic might be off on 'device' keyword?
        
        # Let's double check the parser implementation.
        # Line: "device1\tdevice model:Pixel_6 ..." -> split() -> ["device1", "device", "model:Pixel_6", ...]
        # parts[1] is state.
        
        self.assertEqual(devices[1]['id'], "device2")
        self.assertEqual(devices[1]['state'], "unauthorized")

    @patch("wa_crypt_tools.adb.run_adb_command")
    def test_list_devices_empty(self, mock_run):
        mock_run.return_value = "List of devices attached\n"
        devices = list_devices()
        self.assertEqual(len(devices), 0)

if __name__ == '__main__':
    unittest.main()
