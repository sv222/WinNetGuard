"""
Application Registry - Track allowed/blocked/unknown applications
"""
import json
import os
from typing import Set, Dict
from config import SETTINGS_FILE, DEFAULT_SETTINGS

class AppRegistry:
    """Manages whitelist, blacklist, and tracks known applications."""
    
    def __init__(self, settings_file: str = None):
        self.settings_file = settings_file or SETTINGS_FILE
        self.whitelist: Set[str] = set()  # Allowed apps (paths)
        self.blacklist: Set[str] = set()  # Blocked apps (paths)
        self.pending_decisions: Set[str] = set()  # Apps waiting for user decision
        self.settings: Dict = DEFAULT_SETTINGS.copy()  # User settings
        self._load_settings()
    
    def _load_settings(self):
        """Load whitelist/blacklist/settings from file."""
        if os.path.exists(self.settings_file):
            try:
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.whitelist = set(data.get('whitelist', []))
                    self.blacklist = set(data.get('blacklist', []))
                    # Load user settings, merge with defaults
                    saved_settings = data.get('settings', {})
                    self.settings.update(saved_settings)
            except Exception as e:
                print(f"Error loading settings: {e}")
    
    def _save_settings(self):
        """Save whitelist/blacklist/settings to file."""
        try:
            data = {
                'whitelist': list(self.whitelist),
                'blacklist': list(self.blacklist),
                'settings': self.settings
            }
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def get_setting(self, key: str):
        """Get a setting value."""
        return self.settings.get(key, DEFAULT_SETTINGS.get(key))
    
    def update_setting(self, key: str, value):
        """Update a setting value."""
        self.settings[key] = value
        self._save_settings()
    
    def is_whitelisted(self, app_path: str) -> bool:
        """Check if app is in whitelist."""
        return app_path.lower() in {p.lower() for p in self.whitelist}
    
    def is_blacklisted(self, app_path: str) -> bool:
        """Check if app is in blacklist."""
        return app_path.lower() in {p.lower() for p in self.blacklist}
    
    def is_known(self, app_path: str) -> bool:
        """Check if app decision was made (in whitelist or blacklist)."""
        path_lower = app_path.lower()
        return path_lower in {p.lower() for p in self.whitelist} or \
               path_lower in {p.lower() for p in self.blacklist}
    
    def add_to_whitelist(self, app_path: str):
        """Add app to whitelist."""
        self.whitelist.add(app_path)
        # Remove from blacklist if present
        self.blacklist.discard(app_path)
        self.pending_decisions.discard(app_path)
        self._save_settings()
    
    def add_to_blacklist(self, app_path: str):
        """Add app to blacklist."""
        self.blacklist.add(app_path)
        # Remove from whitelist if present
        self.whitelist.discard(app_path)
        self.pending_decisions.discard(app_path)
        self._save_settings()
    
    def remove_from_whitelist(self, app_path: str):
        """Remove app from whitelist."""
        self.whitelist.discard(app_path)
        self._save_settings()
    
    def remove_from_blacklist(self, app_path: str):
        """Remove app from blacklist."""
        self.blacklist.discard(app_path)
        self._save_settings()
    
    def forget_app(self, app_path: str):
        """Remove app from both lists (will ask again on next connection)."""
        self.whitelist.discard(app_path)
        self.blacklist.discard(app_path)
        self.pending_decisions.discard(app_path)
        self._save_settings()
    
    def get_whitelist(self) -> list:
        """Get list of whitelisted apps."""
        return sorted(list(self.whitelist))
    
    def get_blacklist(self) -> list:
        """Get list of blacklisted apps."""
        return sorted(list(self.blacklist))
