"""
Safety module - Critical system protections and emergency reset functionality
"""
import win32com.client
from config import RULE_PREFIX

# Critical services that should NEVER be blocked
CORE_WHITELIST = {
    'ports': [
        53,    # DNS
        67,    # DHCP Client
        68,    # DHCP Server
        123,   # NTP
    ],
    'processes': [
        'svchost.exe',
        'lsass.exe',
        'services.exe',
        'csrss.exe',
        'winlogon.exe',
        'dwm.exe',
    ],
    'ips': [
        '127.0.0.1',
        '::1',
    ]
}

def is_safe_to_block(app_path: str = None, port: int = None, ip: str = None) -> tuple[bool, str]:
    """
    Check if it's safe to block the given target.
    
    Returns:
        (is_safe, reason) - True if safe to block, False with reason if not
    """
    if app_path:
        app_name = app_path.lower().split('\\')[-1]
        if app_name in CORE_WHITELIST['processes']:
            return False, f"Cannot block critical system process: {app_name}"
    
    if port and port in CORE_WHITELIST['ports']:
        return False, f"Cannot block critical port: {port} (required for system stability)"
    
    if ip and ip in CORE_WHITELIST['ips']:
        return False, f"Cannot block loopback address: {ip}"
    
    return True, ""

def emergency_reset() -> tuple[int, list[str]]:
    """
    Remove ALL rules created by this application.
    
    Returns:
        (count, errors) - Number of rules removed and list of any errors
    """
    try:
        fw_policy = win32com.client.Dispatch("HNetCfg.FwPolicy2")
        rules = fw_policy.Rules
        
        removed_count = 0
        errors = []
        
        # Collect rules to remove (can't modify collection while iterating)
        rules_to_remove = []
        for rule in rules:
            if rule.Name.startswith(RULE_PREFIX):
                rules_to_remove.append(rule.Name)
        
        # Remove collected rules
        for rule_name in rules_to_remove:
            try:
                rules.Remove(rule_name)
                removed_count += 1
            except Exception as e:
                errors.append(f"Failed to remove {rule_name}: {str(e)}")
        
        return removed_count, errors
    
    except Exception as e:
        return 0, [f"Emergency reset failed: {str(e)}"]

def get_app_rules_count() -> int:
    """Get count of rules created by this app."""
    try:
        fw_policy = win32com.client.Dispatch("HNetCfg.FwPolicy2")
        count = 0
        for rule in fw_policy.Rules:
            if rule.Name.startswith(RULE_PREFIX):
                count += 1
        return count
    except:
        return 0
