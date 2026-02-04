"""
Main entry point - Admin check and application initialization
"""
import sys
import ctypes
import os
import win32event
import win32api
import winerror
from logger import get_logger

logger = get_logger()

# Global mutex for single instance
MUTEX_NAME = "Global\\FirewallManagerSingleInstance"
mutex = None

def is_admin():
    """Check if running with administrator privileges."""
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except:
        return False

def run_as_admin():
    """Restart the application with admin privileges."""
    try:
        if sys.platform == 'win32':
            ctypes.windll.shell32.ShellExecuteW(
                None,
                "runas",
                sys.executable,
                " ".join(sys.argv),
                None,
                1
            )
    except Exception as e:
        logger.error(f"Failed to elevate privileges: {e}")
        sys.exit(1)

def check_single_instance():
    """Check if another instance is already running."""
    global mutex
    try:
        mutex = win32event.CreateMutex(None, False, MUTEX_NAME)
        last_error = win32api.GetLastError()
        
        if last_error == winerror.ERROR_ALREADY_EXISTS:
            logger.warning("Another instance is already running")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Failed to check single instance: {e}")
        return True  # Allow to run if check fails

def main():
    """Main entry point."""
    global mutex
    
    # Check for --minimized flag
    start_minimized = "--minimized" in sys.argv
    
    logger.info("=" * 60)
    logger.info("Firewall Manager Starting")
    logger.info("=" * 60)
    if start_minimized:
        logger.info("Starting minimized to tray")
    
    # Check for single instance
    if not check_single_instance():
        logger.info("Exiting - another instance is already running")
        # Release mutex before showing dialog
        if mutex:
            win32api.CloseHandle(mutex)
            mutex = None
        
        import tkinter.messagebox as messagebox
        messagebox.showinfo(
            "Already Running",
            "Firewall Manager is already running.\n\n"
            "Check the system tray or taskbar."
        )
        sys.exit(0)
    
    # Check for admin privileges
    if not is_admin():
        logger.warning("Administrator privileges required. Requesting elevation...")
        # Release mutex before elevation
        if mutex:
            win32api.CloseHandle(mutex)
            mutex = None
        run_as_admin()
        sys.exit(0)
    
    logger.info("Running with administrator privileges")
    
    # Import GUI only after admin check
    try:
        from gui import FirewallGUI
        logger.info("GUI module loaded")
    except Exception as e:
        logger.error(f"Failed to load GUI module: {e}")
        import traceback
        logger.error(traceback.format_exc())
        if mutex:
            win32api.CloseHandle(mutex)
        sys.exit(1)
    
    try:
        logger.info("Initializing application...")
        app = FirewallGUI(start_minimized=start_minimized)
        logger.info("Application initialized successfully")
        app.run()
        logger.info("Application closed normally")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        # Release mutex on exit
        if mutex:
            win32api.CloseHandle(mutex)
            logger.info("Mutex released")

if __name__ == "__main__":
    main()
