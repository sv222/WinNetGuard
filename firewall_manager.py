"""
Firewall Manager - Core logic for managing Windows Firewall rules via COM API
"""
import os
import win32com.client
import pythoncom
from typing import List, Dict, Optional
from config import RULE_PREFIX
from safety import is_safe_to_block

class FirewallRule:
    """Represents a firewall rule."""
    def __init__(self, name: str, app_path: str, enabled: bool, direction: str):
        self.name = name
        self.app_path = app_path
        self.enabled = enabled
        self.direction = direction

class FirewallManager:
    """Manages Windows Firewall rules using COM API."""
    
    def __init__(self):
        self.fw_policy = None
        self._initialize()
    
    def _initialize(self):
        """Initialize COM connection to Windows Firewall."""
        try:
            # Initialize COM for this thread
            pythoncom.CoInitialize()
            self.fw_policy = win32com.client.Dispatch("HNetCfg.FwPolicy2")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize firewall manager: {e}")
    
    def add_allow_rule(self, app_path: str) -> tuple[bool, str]:
        """
        Add a rule to explicitly allow an application.
        Note: This is deprecated - allow rules are no longer used.
        Kept for backward compatibility.
        
        Args:
            app_path: Full path to the executable
            
        Returns:
            (success, message)
        """
        return True, "Allow rules are no longer used - remove block rule instead"
    
    def remove_allow_rule(self, app_path: str) -> tuple[bool, str]:
        """
        Remove allow rule for an application.
        Note: This is deprecated - allow rules are no longer used.
        Kept for backward compatibility.
        
        Args:
            app_path: Full path to the executable
            
        Returns:
            (success, message)
        """
        return True, "Allow rules are no longer used"
    
    def is_strict_mode_enabled(self) -> bool:
        """
        Check if strict mode is enabled.
        Note: Strict mode has been removed - always returns False.
        Kept for backward compatibility.
        """
        return False
    
    def add_block_rule(self, app_path: str) -> tuple[bool, str]:
        """
        Add a rule to block an application.
        
        Args:
            app_path: Full path to the executable
            
        Returns:
            (success, message)
        """
        # Ensure COM is initialized for this thread
        try:
            pythoncom.CoInitialize()
        except:
            pass
        
        # Validate path
        if not os.path.exists(app_path):
            return False, f"Application not found: {app_path}"
        
        if not app_path.lower().endswith('.exe'):
            return False, "Only .exe files can be blocked"
        
        # Safety check
        is_safe, reason = is_safe_to_block(app_path=app_path)
        if not is_safe:
            return False, reason
        
        app_name = os.path.basename(app_path)
        rule_name = f"{RULE_PREFIX} {app_name}"
        
        try:
            # Check if rule already exists
            existing_rule = self._find_rule(rule_name)
            if existing_rule:
                return False, f"Rule already exists for {app_name}"
            
            # Create outbound block rule
            rule = win32com.client.Dispatch("HNetCfg.FwRule")
            rule.Name = rule_name
            rule.Description = f"Block {app_name} - Created by {RULE_PREFIX}"
            rule.ApplicationName = app_path
            rule.Action = 0  # NET_FW_ACTION_BLOCK
            rule.Direction = 2  # NET_FW_RULE_DIR_OUT (outbound)
            rule.Enabled = True
            
            self.fw_policy.Rules.Add(rule)
            
            return True, f"Successfully blocked {app_name}"
        
        except Exception as e:
            return False, f"Failed to create rule: {str(e)}"
    
    def remove_rule(self, app_path: str) -> tuple[bool, str]:
        """
        Remove blocking rule for an application.
        
        Args:
            app_path: Full path to the executable
            
        Returns:
            (success, message)
        """
        # Ensure COM is initialized for this thread
        try:
            pythoncom.CoInitialize()
        except:
            pass
        
        app_name = os.path.basename(app_path)
        rule_name = f"{RULE_PREFIX} {app_name}"
        
        try:
            existing_rule = self._find_rule(rule_name)
            if not existing_rule:
                return False, f"No rule found for {app_name}"
            
            self.fw_policy.Rules.Remove(rule_name)
            return True, f"Successfully unblocked {app_name}"
        
        except Exception as e:
            return False, f"Failed to remove rule: {str(e)}"
    
    def get_active_rules(self) -> List[FirewallRule]:
        """
        Get all rules created by this application.
        
        Returns:
            List of FirewallRule objects
        """
        rules = []
        try:
            for rule in self.fw_policy.Rules:
                if rule.Name.startswith(RULE_PREFIX):
                    rules.append(FirewallRule(
                        name=rule.Name,
                        app_path=rule.ApplicationName or "",
                        enabled=rule.Enabled,
                        direction="OUT" if rule.Direction == 2 else "IN"
                    ))
        except Exception as e:
            print(f"Error retrieving rules: {e}")
        
        return rules
    
    def is_blocked(self, app_path: str) -> bool:
        """Check if an application is currently blocked."""
        app_name = os.path.basename(app_path)
        rule_name = f"{RULE_PREFIX} {app_name}"
        return self._find_rule(rule_name) is not None
    
    def _find_rule(self, rule_name: str):
        """Find a rule by name."""
        try:
            for rule in self.fw_policy.Rules:
                if rule.Name == rule_name:
                    return rule
        except:
            pass
        return None
