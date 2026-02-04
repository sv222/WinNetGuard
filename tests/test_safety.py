"""Tests for safety module"""
import unittest
from safety import is_safe_to_block, emergency_reset, get_app_rules_count, CORE_WHITELIST


class TestSafety(unittest.TestCase):
    """Test safety checks and emergency functions."""
    
    def test_core_whitelist_structure(self):
        """Test core whitelist has required keys."""
        self.assertIn('ports', CORE_WHITELIST)
        self.assertIn('processes', CORE_WHITELIST)
        self.assertIn('ips', CORE_WHITELIST)
        self.assertIsInstance(CORE_WHITELIST['ports'], list)
        self.assertIsInstance(CORE_WHITELIST['processes'], list)
        self.assertIsInstance(CORE_WHITELIST['ips'], list)
    
    def test_block_critical_process(self):
        """Test blocking critical system process is prevented."""
        safe, reason = is_safe_to_block(app_path="C:\\Windows\\System32\\svchost.exe")
        self.assertFalse(safe)
        self.assertIn("critical system process", reason.lower())
    
    def test_block_critical_port_dns(self):
        """Test blocking DNS port is prevented."""
        safe, reason = is_safe_to_block(port=53)
        self.assertFalse(safe)
        self.assertIn("critical port", reason.lower())
    
    def test_block_critical_port_dhcp(self):
        """Test blocking DHCP ports is prevented."""
        safe, reason = is_safe_to_block(port=67)
        self.assertFalse(safe)
        safe, reason = is_safe_to_block(port=68)
        self.assertFalse(safe)
    
    def test_block_critical_port_ntp(self):
        """Test blocking NTP port is prevented."""
        safe, reason = is_safe_to_block(port=123)
        self.assertFalse(safe)
    
    def test_block_loopback_ip(self):
        """Test blocking loopback addresses is prevented."""
        safe, reason = is_safe_to_block(ip="127.0.0.1")
        self.assertFalse(safe)
        safe, reason = is_safe_to_block(ip="::1")
        self.assertFalse(safe)
    
    def test_block_safe_application(self):
        """Test blocking non-critical application is allowed."""
        safe, reason = is_safe_to_block(app_path="C:\\Program Files\\TestApp\\test.exe")
        self.assertTrue(safe)
        self.assertEqual(reason, "")
    
    def test_block_safe_port(self):
        """Test blocking non-critical port is allowed."""
        safe, reason = is_safe_to_block(port=8080)
        self.assertTrue(safe)
    
    def test_block_safe_ip(self):
        """Test blocking non-loopback IP is allowed."""
        safe, reason = is_safe_to_block(ip="8.8.8.8")
        self.assertTrue(safe)
    
    def test_block_multiple_criteria(self):
        """Test blocking with multiple criteria."""
        # Safe app on safe port
        safe, reason = is_safe_to_block(
            app_path="C:\\Program Files\\TestApp\\test.exe",
            port=8080
        )
        self.assertTrue(safe)
        
        # Safe app on critical port
        safe, reason = is_safe_to_block(
            app_path="C:\\Program Files\\TestApp\\test.exe",
            port=53
        )
        self.assertFalse(safe)


if __name__ == '__main__':
    unittest.main()
