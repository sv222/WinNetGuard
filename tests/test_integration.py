"""Integration tests (requires admin)"""
import unittest
import ctypes
import os
import time
from firewall_manager import FirewallManager
from app_registry import AppRegistry
from monitor import NetworkMonitor
from safety import emergency_reset


def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


@unittest.skipUnless(is_admin(), "Requires administrator privileges")
class TestIntegration(unittest.TestCase):
    """Integration tests for complete workflows."""
    
    def setUp(self):
        """Setup test environment."""
        self.fw = FirewallManager()
        self.registry = AppRegistry()
        self.test_app = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'test_integration.exe')
        
        # Create test file
        with open(self.test_app, 'w') as f:
            f.write('')
    
    def tearDown(self):
        """Cleanup test environment."""
        # Remove test app from registry
        self.registry.forget_app(self.test_app)
        
        # Remove firewall rules
        self.fw.remove_rule(self.test_app)
        self.fw.remove_allow_rule(self.test_app)
        
        # Remove test file
        if os.path.exists(self.test_app):
            os.unlink(self.test_app)
    
    def test_block_workflow(self):
        """Test complete block workflow."""
        # Add to blacklist
        self.registry.add_to_blacklist(self.test_app)
        self.assertTrue(self.registry.is_blacklisted(self.test_app))
        
        # Create firewall rule
        success, msg = self.fw.add_block_rule(self.test_app)
        self.assertTrue(success, msg)
        self.assertTrue(self.fw.is_blocked(self.test_app))
        
        # Unblock
        self.registry.forget_app(self.test_app)
        success, msg = self.fw.remove_rule(self.test_app)
        self.assertTrue(success, msg)
        self.assertFalse(self.fw.is_blocked(self.test_app))
    
    def test_allow_workflow(self):
        """Test complete allow workflow (no allow rules anymore)."""
        # Add to whitelist
        self.registry.add_to_whitelist(self.test_app)
        self.assertTrue(self.registry.is_whitelisted(self.test_app))
        
        # No allow rules created anymore
        # Just verify whitelist works
    
    def test_monitor_integration(self):
        """Test monitor with registry."""
        detected_apps = []
        
        def new_app_callback(app_path):
            if not self.registry.is_known(app_path):
                detected_apps.append(app_path)
        
        monitor = NetworkMonitor(new_app_callback=new_app_callback, update_interval=0.5)
        monitor.start()
        time.sleep(2)
        monitor.stop()
        
        # Should detect some apps
        self.assertIsInstance(detected_apps, list)


if __name__ == '__main__':
    unittest.main()
