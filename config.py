# Configuration and constants

# Application metadata
APP_NAME = "WinNetGuard"
APP_VERSION = "1.0.0"
RULE_PREFIX = "[WinNetGuard]"

# UI Colors (Windows 11 Dark Theme)
COLORS = {
    'bg_dark': '#1e1e1e',
    'bg_medium': '#2d2d2d',
    'bg_light': '#3d3d3d',
    'accent_blue': '#0078d4',
    'text_primary': '#ffffff',
    'text_secondary': '#a0a0a0',
    'success': '#107c10',
    'danger': '#d13438',
    'warning': '#ff8c00'
}

# UI Settings
WINDOW_MIN_WIDTH = 800
WINDOW_MIN_HEIGHT = 600
WINDOW_DEFAULT_WIDTH = 1000
WINDOW_DEFAULT_HEIGHT = 700

# Default settings (can be overridden by user)
DEFAULT_SETTINGS = {
    'ui_font_size': 12,  # Base font size for UI elements
    'process_font_size': 12,  # Font size for process names in connections
    'connection_update_interval': 2.0,  # seconds
    'max_connections_display': 30,  # Max connections to show
    'enable_notifications': True,  # Show new app notifications
}

# Monitoring settings
CONNECTION_UPDATE_INTERVAL = 2000  # ms (increased to reduce flickering)
SEARCH_DEBOUNCE_DELAY = 300  # ms

# Notification settings
ENABLE_CONNECTION_NOTIFICATIONS = True
NOTIFICATION_SOUND = False

# Persistence
SETTINGS_FILE = "firewall_settings.json"

# Animation timings
FADE_IN_DURATION = 200  # ms
SLIDE_OUT_DURATION = 150  # ms
CROSSFADE_DURATION = 250  # ms
