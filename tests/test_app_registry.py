"""Tests for app registry module"""
import unittest
import os
import json
import tempfile
from app_registry import AppRegistry


class TestAppRegistry(unittest.TestCase):
    """Test app registry functionality."""
    
    def setUp(self):
        """Create temporary settings file for testing."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        self.temp_file.close()
        self.registry = AppRegistry(settings_file=self.temp_file.name)
    
    def tearDown(self):
        """Clean up temporary file."""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_initialization(self):
        """Test registry initializes with default settings."""
        self.assertIsInstance(self.registry.whitelist, set)
        self.assertIsInstance(self.registry.blacklist, set)
        self.assertIsInstance(self.registry.settings, dict)
    
    def test_default_settings(self):
        """Test default settings are loaded."""
        self.assertEqual(self.registry.get_setting('ui_font_size'), 12)
        self.assertEqual(self.registry.get_setting('process_font_size'), 12)
        self.assertEqual(self.registry.get_setting('connection_update_interval'), 2.0)
        self.assertEqual(self.registry.get_setting('max_connections_display'), 30)
        self.assertTrue(self.registry.get_setting('enable_notifications'))
    
    def test_add_to_whitelist(self):
        """Test adding app to whitelist."""
        app_path = "C:\\Test\\app.exe"
        self.registry.add_to_whitelist(app_path)
        self.assertIn(app_path, self.registry.whitelist)
        self.assertNotIn(app_path, self.registry.blacklist)
    
    def test_add_to_blacklist(self):
        """Test adding app to blacklist."""
        app_path = "C:\\Test\\app.exe"
        self.registry.add_to_blacklist(app_path)
        self.assertIn(app_path, self.registry.blacklist)
        self.assertNotIn(app_path, self.registry.whitelist)
    
    def test_move_from_whitelist_to_blacklist(self):
        """Test moving app from whitelist to blacklist."""
        app_path = "C:\\Test\\app.exe"
        self.registry.add_to_whitelist(app_path)
        self.registry.add_to_blacklist(app_path)
        self.assertNotIn(app_path, self.registry.whitelist)
        self.assertIn(app_path, self.registry.blacklist)
    
    def test_move_from_blacklist_to_whitelist(self):
        """Test moving app from blacklist to whitelist."""
        app_path = "C:\\Test\\app.exe"
        self.registry.add_to_blacklist(app_path)
        self.registry.add_to_whitelist(app_path)
        self.assertNotIn(app_path, self.registry.blacklist)
        self.assertIn(app_path, self.registry.whitelist)
    
    def test_forget_app(self):
        """Test forgetting app removes from both lists."""
        app_path = "C:\\Test\\app.exe"
        self.registry.add_to_whitelist(app_path)
        self.registry.forget_app(app_path)
        self.assertNotIn(app_path, self.registry.whitelist)
        self.assertNotIn(app_path, self.registry.blacklist)
    
    def test_is_whitelisted(self):
        """Test checking if app is whitelisted."""
        app_path = "C:\\Test\\app.exe"
        self.assertFalse(self.registry.is_whitelisted(app_path))
        self.registry.add_to_whitelist(app_path)
        self.assertTrue(self.registry.is_whitelisted(app_path))
    
    def test_is_blacklisted(self):
        """Test checking if app is blacklisted."""
        app_path = "C:\\Test\\app.exe"
        self.assertFalse(self.registry.is_blacklisted(app_path))
        self.registry.add_to_blacklist(app_path)
        self.assertTrue(self.registry.is_blacklisted(app_path))
    
    def test_is_known(self):
        """Test checking if app is known."""
        app_path = "C:\\Test\\app.exe"
        self.assertFalse(self.registry.is_known(app_path))
        self.registry.add_to_whitelist(app_path)
        self.assertTrue(self.registry.is_known(app_path))
    
    def test_update_setting(self):
        """Test updating a setting."""
        self.registry.update_setting('ui_font_size', 14)
        self.assertEqual(self.registry.get_setting('ui_font_size'), 14)
    
    def test_persistence(self):
        """Test settings persist to file."""
        app_path = "C:\\Test\\app.exe"
        self.registry.add_to_whitelist(app_path)
        self.registry.update_setting('ui_font_size', 16)
        
        # Create new registry instance with same file
        new_registry = AppRegistry(settings_file=self.temp_file.name)
        self.assertIn(app_path, new_registry.whitelist)
        self.assertEqual(new_registry.get_setting('ui_font_size'), 16)
    
    def test_get_whitelist(self):
        """Test getting whitelist as list."""
        apps = ["C:\\Test\\app1.exe", "C:\\Test\\app2.exe"]
        for app in apps:
            self.registry.add_to_whitelist(app)
        whitelist = self.registry.get_whitelist()
        self.assertEqual(len(whitelist), 2)
        for app in apps:
            self.assertIn(app, whitelist)
    
    def test_get_blacklist(self):
        """Test getting blacklist as list."""
        apps = ["C:\\Test\\app1.exe", "C:\\Test\\app2.exe"]
        for app in apps:
            self.registry.add_to_blacklist(app)
        blacklist = self.registry.get_blacklist()
        self.assertEqual(len(blacklist), 2)
        for app in apps:
            self.assertIn(app, blacklist)


if __name__ == '__main__':
    unittest.main()
