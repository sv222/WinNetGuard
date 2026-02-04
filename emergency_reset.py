"""
Emergency Reset Script - Remove all firewall rules created by SimpleWall Alternative
Run this script if the main application has issues or you need to quickly reset all rules.

Usage:
    python emergency_reset.py
    
Requires administrator privileges.
"""
import sys
import win32com.client

RULE_PREFIX = "[SimpleWallAlternative]"
STRICT_MODE_RULE = "[SimpleWallAlternative] STRICT MODE - Block All Outbound"

def is_admin():
    """Check if running with administrator privileges."""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def remove_all_rules():
    """Remove all firewall rules created by this application."""
    if not is_admin():
        print("ERROR: This script requires administrator privileges!")
        print("Please run as administrator.")
        input("\nPress Enter to exit...")
        sys.exit(1)
    
    print("=" * 60)
    print("SimpleWall Alternative - Emergency Reset")
    print("=" * 60)
    print()
    print("This will remove ALL firewall rules created by the application,")
    print("including STRICT MODE if enabled.")
    print(f"Looking for rules with prefix: {RULE_PREFIX}")
    print()
    
    response = input("Continue? (yes/no): ").strip().lower()
    if response != "yes":
        print("Cancelled.")
        input("\nPress Enter to exit...")
        sys.exit(0)
    
    print("\nConnecting to Windows Firewall...")
    
    try:
        # Connect to Windows Firewall
        fw_policy = win32com.client.Dispatch("HNetCfg.FwPolicy2")
        rules = fw_policy.Rules
        
        # Find all rules with our prefix
        rules_to_remove = []
        strict_mode_found = False
        
        for rule in rules:
            if rule.Name.startswith(RULE_PREFIX):
                rules_to_remove.append(rule.Name)
                if rule.Name == STRICT_MODE_RULE:
                    strict_mode_found = True
        
        if not rules_to_remove:
            print("\n✅ No rules found. Nothing to remove.")
            input("\nPress Enter to exit...")
            sys.exit(0)
        
        print(f"\nFound {len(rules_to_remove)} rules to remove:")
        for rule_name in rules_to_remove:
            if rule_name == STRICT_MODE_RULE:
                print(f"  - {rule_name} ⚠ STRICT MODE")
            else:
                print(f"  - {rule_name}")
        
        if strict_mode_found:
            print("\n⚠ WARNING: Strict mode will be DISABLED!")
            print("   All applications will be able to connect freely after reset.")
        
        print("\nRemoving rules...")
        removed_count = 0
        errors = []
        
        for rule_name in rules_to_remove:
            try:
                rules.Remove(rule_name)
                removed_count += 1
                if rule_name == STRICT_MODE_RULE:
                    print(f"  ✅ Removed: {rule_name} (STRICT MODE DISABLED)")
                else:
                    print(f"  ✅ Removed: {rule_name}")
            except Exception as e:
                error_msg = f"Failed to remove {rule_name}: {str(e)}"
                errors.append(error_msg)
                print(f"  ❌ {error_msg}")
        
        print("\n" + "=" * 60)
        print(f"✅ Successfully removed {removed_count} rules")
        
        if strict_mode_found:
            print("\n⚠ Strict mode has been DISABLED")
            print("   All applications can now connect to the network.")
        
        if errors:
            print(f"\n❌ Failed to remove {len(errors)} rules")
            print("\nErrors:")
            for error in errors:
                print(f"  - {error}")
        
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        print("\nMake sure:")
        print("  1. You are running as administrator")
        print("  2. Windows Firewall service is running")
        print("  3. pywin32 is installed (pip install pywin32)")
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    remove_all_rules()
