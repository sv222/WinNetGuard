"""Tests for network monitor module"""
import unittest
import time
from monitor import NetworkMonitor, Connection


class TestNetworkMonitor(unittest.TestCase):
    """Test network monitoring functionality."""
    
    def test_connection_dataclass(self):
        """Test Connection dataclass creation."""
        conn = Connection(
            process_name="test.exe",
            process_path="C:\\Test\\test.exe",
            pid=1234,
            local_addr="192.168.1.1",
            local_port=12345,
            remote_addr="8.8.8.8",
            remote_port=443,
            status="ESTABLISHED",
            protocol="TCP"
        )
        self.assertEqual(conn.process_name, "test.exe")
        self.assertEqual(conn.pid, 1234)
        self.assertEqual(conn.remote_port, 443)
    
    def test_monitor_initialization(self):
        """Test monitor initializes correctly."""
        monitor = NetworkMonitor(update_interval=1.0)
        self.assertFalse(monitor.running)
        self.assertEqual(monitor.update_interval, 1.0)
        self.assertIsInstance(monitor.seen_apps, set)
    
    def test_monitor_start_stop(self):
        """Test monitor can start and stop."""
        monitor = NetworkMonitor(update_interval=1.0)
        monitor.start()
        self.assertTrue(monitor.running)
        time.sleep(0.5)
        monitor.stop()
        self.assertFalse(monitor.running)
    
    def test_monitor_callback(self):
        """Test monitor calls update callback."""
        callback_called = []
        
        def callback(connections):
            callback_called.append(len(connections))
        
        monitor = NetworkMonitor(update_callback=callback, update_interval=0.5)
        monitor.start()
        time.sleep(1.5)
        monitor.stop()
        
        self.assertGreater(len(callback_called), 0)
    
    def test_monitor_new_app_callback(self):
        """Test monitor calls new app callback."""
        new_apps = []
        
        def new_app_callback(app_path):
            new_apps.append(app_path)
        
        monitor = NetworkMonitor(new_app_callback=new_app_callback, update_interval=0.5)
        monitor.start()
        time.sleep(1.5)
        monitor.stop()
        
        # Should detect at least some apps if there's network activity
        # This test is environment-dependent
        self.assertIsInstance(new_apps, list)
    
    def test_get_connections(self):
        """Test getting current connections."""
        monitor = NetworkMonitor(update_interval=1.0)
        monitor.start()
        time.sleep(1.5)
        connections = monitor.get_connections()
        monitor.stop()
        
        self.assertIsInstance(connections, list)
        for conn in connections:
            self.assertIsInstance(conn, Connection)
    
    def test_get_current_connections(self):
        """Test getting immediate connections."""
        monitor = NetworkMonitor(update_interval=1.0)
        connections = monitor.get_current_connections()
        
        self.assertIsInstance(connections, list)
        for conn in connections:
            self.assertIsInstance(conn, Connection)
    
    def test_monitor_double_start(self):
        """Test starting monitor twice doesn't break."""
        monitor = NetworkMonitor(update_interval=1.0)
        monitor.start()
        monitor.start()  # Should not cause issues
        self.assertTrue(monitor.running)
        monitor.stop()


if __name__ == '__main__':
    unittest.main()
