"""Tests for firewall manager module (requires admin)"""
import unittest
import ctypes
import os
from firewall_manager import FirewallManager, FirewallRule


def is_admin():
    """Check if running as admin."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


@unittest.skipUnless(is_admin(), "Requires administrator privileges")
class TestFirewallManager(unittest.TestCase):
    """Test firewall manager functionality."""
    
    def setUp(self):
        """Initialize firewall manager."""
        self.fw = FirewallManager()
        self.test_app = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'test_app.exe')
    
    def test_initialization(self):
        """Test firewall manager initializes."""
        self.assertIsNotNone(self.fw.fw_policy)
    
    def test_get_active_rules(self):
        """Test getting active rules."""
        rules = self.fw.get_active_rules()
        self.assertIsInstance(rules, list)
        for rule in rules:
            self.assertIsInstance(rule, FirewallRule)
    
    def test_is_strict_mode_enabled(self):
        """Test checking strict mode status (always False now)."""
        is_strict = self.fw.is_strict_mode_enabled()
        self.assertFalse(is_strict)
    
    def test_add_remove_block_rule(self):
        """Test adding and removing block rule."""
        # Create dummy file
        with open(self.test_app, 'w') as f:
            f.write('')
        
        try:
            # Add block rule
            success, msg = self.fw.add_block_rule(self.test_app)
            if not success and "critical" in msg.lower():
                self.skipTest("Test app path is protected")
            self.assertTrue(success, msg)
            
            # Check if blocked
            self.assertTrue(self.fw.is_blocked(self.test_app))
            
            # Remove rule
            success, msg = self.fw.remove_rule(self.test_app)
            self.assertTrue(success, msg)
            
            # Check if unblocked
            self.assertFalse(self.fw.is_blocked(self.test_app))
        finally:
            # Cleanup
            if os.path.exists(self.test_app):
                os.unlink(self.test_app)
            # Ensure rule is removed
            self.fw.remove_rule(self.test_app)
    
    def test_add_remove_allow_rule(self):
        """Test adding and removing allow rule (deprecated)."""
        # Create dummy file
        with open(self.test_app, 'w') as f:
            f.write('')
        
        try:
            # Add allow rule (should succeed but do nothing)
            success, msg = self.fw.add_allow_rule(self.test_app)
            self.assertTrue(success)
            
            # Remove allow rule (should succeed but do nothing)
            success, msg = self.fw.remove_allow_rule(self.test_app)
            self.assertTrue(success)
        finally:
            # Cleanup
            if os.path.exists(self.test_app):
                os.unlink(self.test_app)
    
    def test_block_nonexistent_file(self):
        """Test blocking non-existent file fails."""
        success, msg = self.fw.add_block_rule("C:\\NonExistent\\app.exe")
        self.assertFalse(success)
        self.assertIn("not found", msg.lower())
    
    def test_block_non_exe_file(self):
        """Test blocking non-exe file fails."""
        test_file = os.path.join(os.environ.get('TEMP', 'C:\\Temp'), 'test.txt')
        with open(test_file, 'w') as f:
            f.write('test')
        
        try:
            success, msg = self.fw.add_block_rule(test_file)
            self.assertFalse(success)
            self.assertIn("exe", msg.lower())
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)
    
    def test_duplicate_block_rule(self):
        """Test adding duplicate block rule fails."""
        with open(self.test_app, 'w') as f:
            f.write('')
        
        try:
            success, msg = self.fw.add_block_rule(self.test_app)
            if not success and "critical" in msg.lower():
                self.skipTest("Test app path is protected")
            self.assertTrue(success)
            
            # Try to add again
            success, msg = self.fw.add_block_rule(self.test_app)
            self.assertFalse(success)
            self.assertIn("already exists", msg.lower())
        finally:
            if os.path.exists(self.test_app):
                os.unlink(self.test_app)
            self.fw.remove_rule(self.test_app)


if __name__ == '__main__':
    unittest.main()
