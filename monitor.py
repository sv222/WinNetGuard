"""
Network Monitor - Track active connections and map to processes
"""
import psutil
import threading
import time
from typing import List, Dict, Callable
from dataclasses import dataclass

@dataclass
class Connection:
    """Represents an active network connection."""
    process_name: str
    process_path: str
    pid: int
    local_addr: str
    local_port: int
    remote_addr: str
    remote_port: int
    status: str
    protocol: str

class NetworkMonitor:
    """Monitor network connections in background thread."""
    
    def __init__(self, update_callback: Callable[[List[Connection]], None] = None, 
                 new_app_callback: Callable[[str], None] = None,
                 update_interval: float = 2.0):
        self.update_callback = update_callback
        self.new_app_callback = new_app_callback
        self.running = False
        self.thread = None
        self.connections = []
        self.update_interval = update_interval  # seconds
        self.seen_apps: set = set()  # Track apps we've seen
    
    def start(self):
        """Start monitoring in background thread."""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """Stop monitoring."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
    
    def get_connections(self) -> List[Connection]:
        """Get current list of connections."""
        return self.connections.copy()
    
    def get_current_connections(self) -> List[Connection]:
        """Fetch current connections immediately (not from cache)."""
        return self._fetch_connections()
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.running:
            try:
                self.connections = self._fetch_connections()
                
                if self.update_callback:
                    self.update_callback(self.connections)
                
            except Exception as e:
                print(f"Monitor error: {e}")
            
            time.sleep(self.update_interval)
    
    def _fetch_connections(self) -> List[Connection]:
        """Fetch current network connections."""
        connections = []
        new_apps = set()
        
        try:
            # Get all network connections
            net_connections = psutil.net_connections(kind='inet')
            
            # Map PIDs to process info
            process_cache = {}
            
            for conn in net_connections:
                if conn.status == 'NONE' or not conn.raddr:
                    continue
                
                pid = conn.pid
                if not pid:
                    continue
                
                # Get process info (cached)
                if pid not in process_cache:
                    try:
                        proc = psutil.Process(pid)
                        process_cache[pid] = {
                            'name': proc.name(),
                            'path': proc.exe()
                        }
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        process_cache[pid] = {
                            'name': 'Unknown',
                            'path': ''
                        }
                
                proc_info = process_cache[pid]
                
                # Track new apps
                if proc_info['path'] and proc_info['path'] not in self.seen_apps:
                    new_apps.add(proc_info['path'])
                    self.seen_apps.add(proc_info['path'])
                
                connections.append(Connection(
                    process_name=proc_info['name'],
                    process_path=proc_info['path'],
                    pid=pid,
                    local_addr=conn.laddr.ip if conn.laddr else '',
                    local_port=conn.laddr.port if conn.laddr else 0,
                    remote_addr=conn.raddr.ip if conn.raddr else '',
                    remote_port=conn.raddr.port if conn.raddr else 0,
                    status=conn.status,
                    protocol='TCP' if conn.type == 1 else 'UDP'
                ))
            
            # Notify about new apps
            if self.new_app_callback and new_apps:
                for app_path in new_apps:
                    self.new_app_callback(app_path)
        
        except Exception as e:
            print(f"Error fetching connections: {e}")
        
        return connections
