"""Tests for config module"""
import unittest
from config import (
    APP_NAME, APP_VERSION, RULE_PREFIX,
    COLORS, DEFAULT_SETTINGS,
    WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT
)


class TestConfig(unittest.TestCase):
    """Test configuration constants."""
    
    def test_app_metadata(self):
        """Test app metadata is defined."""
        self.assertIsInstance(APP_NAME, str)
        self.assertIsInstance(APP_VERSION, str)
        self.assertIsInstance(RULE_PREFIX, str)
        self.assertTrue(len(APP_NAME) > 0)
        self.assertTrue(len(APP_VERSION) > 0)
        self.assertTrue(len(RULE_PREFIX) > 0)
    
    def test_rule_prefix_format(self):
        """Test rule prefix has correct format."""
        self.assertTrue(RULE_PREFIX.startswith('['))
        self.assertTrue(RULE_PREFIX.endswith(']'))
    
    def test_colors_defined(self):
        """Test all required colors are defined."""
        required_colors = [
            'bg_dark', 'bg_medium', 'bg_light',
            'text_primary', 'text_secondary',
            'accent_blue', 'success', 'danger', 'warning'
        ]
        for color in required_colors:
            self.assertIn(color, COLORS)
            self.assertIsInstance(COLORS[color], str)
            self.assertTrue(COLORS[color].startswith('#'))
    
    def test_default_settings_structure(self):
        """Test default settings have required keys."""
        required_keys = [
            'ui_font_size', 'process_font_size',
            'connection_update_interval', 'max_connections_display',
            'enable_notifications'
        ]
        for key in required_keys:
            self.assertIn(key, DEFAULT_SETTINGS)
    
    def test_default_settings_types(self):
        """Test default settings have correct types."""
        self.assertIsInstance(DEFAULT_SETTINGS['ui_font_size'], int)
        self.assertIsInstance(DEFAULT_SETTINGS['process_font_size'], int)
        self.assertIsInstance(DEFAULT_SETTINGS['connection_update_interval'], (int, float))
        self.assertIsInstance(DEFAULT_SETTINGS['max_connections_display'], int)
        self.assertIsInstance(DEFAULT_SETTINGS['enable_notifications'], bool)
    
    def test_default_settings_ranges(self):
        """Test default settings are within valid ranges."""
        self.assertGreaterEqual(DEFAULT_SETTINGS['ui_font_size'], 8)
        self.assertLessEqual(DEFAULT_SETTINGS['ui_font_size'], 20)
        self.assertGreaterEqual(DEFAULT_SETTINGS['process_font_size'], 8)
        self.assertLessEqual(DEFAULT_SETTINGS['process_font_size'], 20)
        self.assertGreaterEqual(DEFAULT_SETTINGS['connection_update_interval'], 1.0)
        self.assertLessEqual(DEFAULT_SETTINGS['connection_update_interval'], 10.0)
        self.assertGreaterEqual(DEFAULT_SETTINGS['max_connections_display'], 10)
        self.assertLessEqual(DEFAULT_SETTINGS['max_connections_display'], 100)
    
    def test_window_dimensions(self):
        """Test window dimensions are valid."""
        self.assertIsInstance(WINDOW_MIN_WIDTH, int)
        self.assertIsInstance(WINDOW_MIN_HEIGHT, int)
        self.assertIsInstance(WINDOW_DEFAULT_WIDTH, int)
        self.assertIsInstance(WINDOW_DEFAULT_HEIGHT, int)
        self.assertGreater(WINDOW_MIN_WIDTH, 0)
        self.assertGreater(WINDOW_MIN_HEIGHT, 0)
        self.assertGreaterEqual(WINDOW_DEFAULT_WIDTH, WINDOW_MIN_WIDTH)
        self.assertGreaterEqual(WINDOW_DEFAULT_HEIGHT, WINDOW_MIN_HEIGHT)


if __name__ == '__main__':
    unittest.main()
