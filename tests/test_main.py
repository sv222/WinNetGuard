"""Tests for main module"""
import unittest
import ctypes
from unittest.mock import patch, MagicMock
import main


class TestMain(unittest.TestCase):
    """Test main module functions."""
    
    def test_is_admin(self):
        """Test admin check function."""
        result = main.is_admin()
        self.assertIsInstance(result, bool)
    
    @patch('main.win32event.CreateMutex')
    @patch('main.win32api.GetLastError')
    def test_check_single_instance_first(self, mock_get_error, mock_create_mutex):
        """Test single instance check when first instance."""
        mock_create_mutex.return_value = 123
        mock_get_error.return_value = 0
        
        result = main.check_single_instance()
        self.assertTrue(result)
    
    @patch('main.win32event.CreateMutex')
    @patch('main.win32api.GetLastError')
    @patch('main.winerror.ERROR_ALREADY_EXISTS', 183)
    def test_check_single_instance_duplicate(self, mock_get_error, mock_create_mutex):
        """Test single instance check when already running."""
        mock_create_mutex.return_value = 123
        mock_get_error.return_value = 183
        
        result = main.check_single_instance()
        self.assertFalse(result)
    
    @patch('main.check_single_instance')
    @patch('main.is_admin')
    @patch('main.logger')
    def test_main_duplicate_instance(self, mock_logger, mock_is_admin, mock_check_single):
        """Test main exits when duplicate instance detected."""
        mock_check_single.return_value = False
        mock_is_admin.return_value = True
        
        with patch('tkinter.messagebox.showinfo'):
            with self.assertRaises(SystemExit) as cm:
                main.main()
            self.assertEqual(cm.exception.code, 0)


if __name__ == '__main__':
    unittest.main()
