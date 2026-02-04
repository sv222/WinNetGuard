"""
GUI - Main interface using CustomTkinter with notifications and whitelist/blacklist
"""
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox, Toplevel
import os
from typing import List
from config import COLORS, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT, WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT, ENABLE_CONNECTION_NOTIFICATIONS
from firewall_manager import FirewallManager
from monitor import NetworkMonitor, Connection
from safety import emergency_reset, get_app_rules_count, is_safe_to_block
from app_registry import AppRegistry
import pystray
from PIL import Image, ImageDraw
import threading

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class PendingAppRow(ctk.CTkFrame):
    """Single row for pending app decision."""
    
    def __init__(self, parent, app_path: str, on_allow, on_block, on_copy, ui_font_size: int = 12):
        super().__init__(parent, fg_color=COLORS['bg_medium'], corner_radius=6)
        
        self.app_path = app_path
        self.app_name = os.path.basename(app_path)
        self.on_allow = on_allow
        self.on_block = on_block
        self.on_copy = on_copy
        self.ui_font_size = ui_font_size
        
        self._create_widgets()
    
    def _create_widgets(self):
        # App icon and name
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=10, pady=8)
        
        ctk.CTkLabel(
            info_frame,
            text=f"🌐 {self.app_name}",
            font=("Segoe UI", self.ui_font_size, "bold"),
            text_color=COLORS['text_primary'],
            anchor="w"
        ).pack(fill="x")
        
        ctk.CTkLabel(
            info_frame,
            text=self.app_path,
            font=("Segoe UI", 9),
            text_color=COLORS['text_secondary'],
            anchor="w"
        ).pack(fill="x")
        
        # Buttons
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="right", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="📋",
            width=30,
            height=30,
            fg_color=COLORS['bg_light'],
            hover_color=COLORS['accent_blue'],
            font=("Segoe UI", 12),
            command=lambda: self.on_copy(self.app_name, self.app_path)
        ).pack(side="left", padx=3)
        
        ctk.CTkButton(
            btn_frame,
            text="✅ Allow",
            width=80,
            height=30,
            fg_color=COLORS['success'],
            hover_color="#0d6b0d",
            font=("Segoe UI", 10, "bold"),
            command=lambda: self.on_allow(self.app_path)
        ).pack(side="left", padx=3)
        
        ctk.CTkButton(
            btn_frame,
            text="🚫 Block",
            width=80,
            height=30,
            fg_color=COLORS['danger'],
            hover_color="#a82a2d",
            font=("Segoe UI", 10, "bold"),
            command=lambda: self.on_block(self.app_path)
        ).pack(side="left", padx=3)


class NewAppsDialog(Toplevel):
    """Dialog showing queue of new applications requiring decisions."""
    
    def __init__(self, parent, on_allow, on_block, on_copy, on_hidden, ui_font_size: int = 12):
        super().__init__(parent)
        
        self.on_allow = on_allow
        self.on_block = on_block
        self.on_copy = on_copy
        self.on_hidden = on_hidden  # Callback when dialog is hidden
        self.ui_font_size = ui_font_size
        self.pending_apps = []
        self.app_rows = {}
        self.is_hidden = False  # Track if dialog is hidden
        self.was_minimized = False  # Track if dialog was intentionally minimized
        
        self.title("New Connections Detected")
        self.geometry("700x500")
        self.minsize(600, 400)
        self.configure(bg=COLORS['bg_dark'])
        
        # Make transient but NOT modal (no grab_set)
        self.transient(parent)
        
        self._create_widgets()
        
        # Center on parent
        self.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() // 2) - (self.winfo_width() // 2)
        y = parent.winfo_y() + (parent.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")
        
        # Hide dialog on close (don't block apps)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_widgets(self):
        main_frame = ctk.CTkFrame(self, fg_color=COLORS['bg_dark'])
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Header
        header = ctk.CTkFrame(main_frame, fg_color=COLORS['bg_medium'], corner_radius=8)
        header.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(
            header,
            text="⚠️ New Applications Requesting Network Access",
            font=("Segoe UI", 16, "bold"),
            text_color=COLORS['text_primary']
        ).pack(pady=15)
        
        ctk.CTkLabel(
            header,
            text="Choose to allow or block each application. Closing this window will block all remaining apps.",
            font=("Segoe UI", 10),
            text_color=COLORS['text_secondary']
        ).pack(pady=(0, 10))
        
        # Scrollable list
        self.apps_container = ctk.CTkScrollableFrame(
            main_frame,
            fg_color=COLORS['bg_light'],
            corner_radius=8
        )
        self.apps_container.pack(fill="both", expand=True, pady=(0, 10))
        
        # Footer with bulk actions
        footer = ctk.CTkFrame(main_frame, fg_color="transparent")
        footer.pack(fill="x")
        
        ctk.CTkButton(
            footer,
            text="✅ Allow All",
            width=120,
            fg_color=COLORS['success'],
            hover_color="#0d6b0d",
            command=self._allow_all
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            footer,
            text="⏸️ Postpone",
            width=120,
            fg_color=COLORS['warning'],
            hover_color="#cc7000",
            command=self._postpone
        ).pack(side="left", padx=5)
        
        ctk.CTkButton(
            footer,
            text="🚫 Block All",
            width=120,
            fg_color=COLORS['danger'],
            hover_color="#a82a2d",
            command=self._block_all
        ).pack(side="left", padx=5)
        
        self.count_label = ctk.CTkLabel(
            footer,
            text="Pending: 0",
            font=("Segoe UI", 11),
            text_color=COLORS['text_secondary']
        )
        self.count_label.pack(side="right", padx=10)
    
    def add_app(self, app_path: str):
        """Add app to pending list."""
        if app_path not in self.app_rows:
            self.pending_apps.append(app_path)
            
            row = PendingAppRow(
                self.apps_container,
                app_path,
                self._handle_allow,
                self._handle_block,
                self.on_copy,
                self.ui_font_size
            )
            row.pack(fill="x", pady=3, padx=5)
            self.app_rows[app_path] = row
            
            self._update_count()
    
    def _handle_allow(self, app_path: str):
        """Handle allow for single app."""
        self.on_allow(app_path)
        self._remove_app(app_path)
    
    def _handle_block(self, app_path: str):
        """Handle block for single app."""
        self.on_block(app_path)
        self._remove_app(app_path)
    
    def _remove_app(self, app_path: str):
        """Remove app from pending list."""
        if app_path in self.app_rows:
            self.app_rows[app_path].destroy()
            del self.app_rows[app_path]
            self.pending_apps.remove(app_path)
            self._update_count()
            
            # Close dialog if no more apps
            if not self.pending_apps:
                self.is_hidden = True
                if self.on_hidden:
                    self.on_hidden()
                self.destroy()
    
    def _allow_all(self):
        """Allow all pending apps."""
        for app_path in self.pending_apps.copy():
            self.on_allow(app_path)
        self.is_hidden = True
        if self.on_hidden:
            self.on_hidden()
        self.destroy()
    
    def _block_all(self):
        """Block all pending apps."""
        for app_path in self.pending_apps.copy():
            self.on_block(app_path)
        self.is_hidden = True
        if self.on_hidden:
            self.on_hidden()
        self.destroy()
    
    def _on_close(self):
        """Hide dialog on close (don't block apps)."""
        self._hide_dialog()
    
    def _postpone(self):
        """Postpone decision and hide dialog."""
        self._hide_dialog()
    
    def _hide_dialog(self):
        """Hide dialog (minimize) without making decisions."""
        self.withdraw()
        self.is_hidden = True
        self.was_minimized = True
        if self.on_hidden:
            self.on_hidden()
    
    def _show_dialog(self):
        """Show dialog (restore from minimized state)."""
        self.deiconify()
        self.lift()
        self.focus_force()
        self.is_hidden = False
        self.was_minimized = False
    
    def _update_count(self):
        """Update pending count label."""
        self.count_label.configure(text=f"Pending: {len(self.pending_apps)}")

class ListCard(ctk.CTkFrame):
    """Card widget for whitelist/blacklist items."""
    
    def __init__(self, parent, app_path: str, list_type: str, on_action, on_copy, ui_font_size: int = 12):
        super().__init__(parent, fg_color=COLORS['bg_medium'], corner_radius=8)
        
        self.app_path = app_path
        self.app_name = os.path.basename(app_path)
        self.list_type = list_type  # 'whitelist' or 'blacklist'
        self.on_action = on_action
        self.on_copy = on_copy
        self.ui_font_size = ui_font_size
        
        self._create_widgets()
    
    def _create_widgets(self):
        # Main info
        info_frame = ctk.CTkFrame(self, fg_color="transparent")
        info_frame.pack(fill="x", padx=10, pady=10)
        
        # Left side - icon and name
        left_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True)
        
        icon = "🟢" if self.list_type == "whitelist" else "🔴"
        ctk.CTkLabel(
            left_frame,
            text=f"{icon} {self.app_name}",
            font=("Segoe UI", self.ui_font_size, "bold"),
            text_color=COLORS['text_primary'],
            anchor="w"
        ).pack(fill="x")
        
        ctk.CTkLabel(
            left_frame,
            text=self.app_path,
            font=("Segoe UI", 9),
            text_color=COLORS['text_secondary'],
            anchor="w"
        ).pack(fill="x")
        
        # Right side - buttons
        btn_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        # Copy button
        ctk.CTkButton(
            btn_frame,
            text="📋",
            width=30,
            height=25,
            fg_color=COLORS['bg_light'],
            hover_color=COLORS['accent_blue'],
            font=("Segoe UI", 12),
            command=lambda: self.on_copy(self.app_name, self.app_path)
        ).pack(side="right", padx=2)
        
        if self.list_type == "whitelist":
            ctk.CTkButton(
                btn_frame,
                text="Block",
                width=60,
                height=25,
                fg_color=COLORS['danger'],
                font=("Segoe UI", 9),
                command=lambda: self.on_action("move_to_blacklist", self.app_path)
            ).pack(side="right", padx=2)
        else:
            ctk.CTkButton(
                btn_frame,
                text="Allow",
                width=60,
                height=25,
                fg_color=COLORS['success'],
                font=("Segoe UI", 9),
                command=lambda: self.on_action("move_to_whitelist", self.app_path)
            ).pack(side="right", padx=2)
        
        ctk.CTkButton(
            btn_frame,
            text="Forget",
            width=60,
            height=25,
            fg_color=COLORS['bg_light'],
            font=("Segoe UI", 9),
            command=lambda: self.on_action("forget", self.app_path)
        ).pack(side="right", padx=2)

class FirewallGUI:
    """Main application GUI."""
    
    def __init__(self, start_minimized: bool = False):
        self.root = ctk.CTk()
        self.root.title("🛡️ Firewall Manager - WinNetGuard")
        self.root.geometry(f"{WINDOW_DEFAULT_WIDTH}x{WINDOW_DEFAULT_HEIGHT}")
        self.root.minsize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        
        self.fw_manager = FirewallManager()
        self.app_registry = AppRegistry()
        self.monitor = NetworkMonitor(
            update_callback=self._on_connections_update,
            new_app_callback=self._on_new_app_detected,
            update_interval=self.app_registry.get_setting('connection_update_interval')
        )
        
        self.connection_rows = []
        self.new_apps_dialog = None  # Single dialog for all new apps
        self.last_connections_snapshot = []  # Track last displayed connections
        self.tray_icon = None  # System tray icon
        self.start_minimized = start_minimized
        self.dialog_minimized = False  # Track if dialog is hidden
        self.pending_btn = None  # Reference to pending apps button
        
        self._create_ui()
        self._setup_tray()
        self._load_lists()
        self.monitor.start()
        
        # Check for unknown apps with active connections on startup
        self.root.after(2000, self._check_unknown_apps_on_startup)
        
        # Start minimized or maximized
        if start_minimized:
            self.root.after(100, self._hide_window)
        else:
            self.root.after(100, lambda: self.root.state('zoomed'))
    
    def _create_ui(self):
        ui_font_size = self.app_registry.get_setting('ui_font_size')
        
        # Header
        header = ctk.CTkFrame(self.root, fg_color=COLORS['bg_medium'], height=60)
        header.pack(fill="x", padx=0, pady=0)
        header.pack_propagate(False)
        
        # Title and GitHub link
        title_frame = ctk.CTkFrame(header, fg_color="transparent")
        title_frame.pack(side="left", padx=20, pady=15)
        
        ctk.CTkLabel(
            title_frame,
            text="🛡️ Firewall Manager - WinNetGuard",
            font=("Segoe UI", 20, "bold"),
            text_color=COLORS['text_primary']
        ).pack(side="left")
        
        github_btn = ctk.CTkButton(
            title_frame,
            text="⭐",
            width=35,
            height=35,
            fg_color=COLORS['bg_light'],
            hover_color=COLORS['accent_blue'],
            font=("Segoe UI", 16),
            command=lambda: self._open_github()
        )
        github_btn.pack(side="left", padx=10)
        
        # Pending apps button (hidden by default, shown when dialog is minimized)
        self.pending_btn = ctk.CTkButton(
            header,
            text="📋 Pending Apps",
            fg_color=COLORS['accent_blue'],
            hover_color="#005a9e",
            command=self._show_new_apps_dialog
        )
        self.pending_btn.pack(side="right", padx=(0, 10))
        self._update_pending_button()  # Initially hide it
        
        # Emergency reset button
        ctk.CTkButton(
            header,
            text="⚠️ Emergency Reset",
            fg_color=COLORS['warning'],
            hover_color="#cc7000",
            command=self._emergency_reset
        ).pack(side="right", padx=20)
        
        # Main content with tabs
        content = ctk.CTkFrame(self.root, fg_color=COLORS['bg_dark'])
        content.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Bind click event to hide dialog when main window is clicked
        content.bind("<Button-1>", self._on_main_window_click)
        
        # Tab view
        self.tabview = ctk.CTkTabview(content, fg_color=COLORS['bg_light'])
        self.tabview.pack(fill="both", expand=True)
        
        # Create tabs
        self.tabview.add("Allowed Apps")
        self.tabview.add("Blocked Apps")
        self.tabview.add("Connections")
        self.tabview.add("Settings")
        
        # Allowed Apps tab
        self._create_whitelist_tab(self.tabview.tab("Allowed Apps"))
        
        # Blocked Apps tab
        self._create_blacklist_tab(self.tabview.tab("Blocked Apps"))
        
        # Connections tab
        self._create_connections_tab(self.tabview.tab("Connections"))
        
        # Settings tab
        self._create_settings_tab(self.tabview.tab("Settings"))
        
        # Status bar
        status_bar = ctk.CTkFrame(self.root, fg_color=COLORS['bg_medium'], height=30)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            status_bar,
            text="Status: ✅ Protected | Allowed: 0 | Blocked: 0 | Connections: 0",
            font=("Segoe UI", ui_font_size),
            text_color=COLORS['text_secondary']
        )
        self.status_label.pack(side="left", padx=15, pady=5)
        
        # Handle window close - minimize to tray
        self.root.protocol("WM_DELETE_WINDOW", self._hide_to_tray)
    
    def _create_whitelist_tab(self, parent):
        """Create allowed apps tab."""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="+ Add Application to Allow",
            fg_color=COLORS['success'],
            command=self._browse_application_to_allow
        ).pack(side="left")
        
        self.whitelist_container = ctk.CTkScrollableFrame(
            parent,
            fg_color=COLORS['bg_dark']
        )
        self.whitelist_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def _create_blacklist_tab(self, parent):
        """Create blocked apps tab."""
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            btn_frame,
            text="+ Add Application to Block",
            fg_color=COLORS['accent_blue'],
            command=self._browse_application
        ).pack(side="left")
        
        self.blacklist_container = ctk.CTkScrollableFrame(
            parent,
            fg_color=COLORS['bg_dark']
        )
        self.blacklist_container.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    
    def _create_connections_tab(self, parent):
        """Create connections monitoring tab."""
        self.connections_container = ctk.CTkScrollableFrame(
            parent,
            fg_color=COLORS['bg_dark']
        )
        self.connections_container.pack(fill="both", expand=True, padx=10, pady=10)
    
    def _create_settings_tab(self, parent):
        """Create settings tab."""
        ui_font_size = self.app_registry.get_setting('ui_font_size')
        
        settings_container = ctk.CTkScrollableFrame(
            parent,
            fg_color=COLORS['bg_dark']
        )
        settings_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # UI Font Size
        self._create_setting_row(
            settings_container,
            "Interface Font Size",
            "Base font size for UI elements (buttons, labels)",
            "ui_font_size",
            8, 20, 1,
            ui_font_size
        )
        
        # Process Font Size
        self._create_setting_row(
            settings_container,
            "Process List Font Size",
            "Font size for process names in connections list",
            "process_font_size",
            8, 20, 1,
            ui_font_size
        )
        
        # Update Interval
        self._create_setting_row(
            settings_container,
            "Connection Update Interval (seconds)",
            "How often to refresh active connections (higher = less CPU/memory)",
            "connection_update_interval",
            1.0, 10.0, 0.5,
            ui_font_size
        )
        
        # Max Connections
        self._create_setting_row(
            settings_container,
            "Max Connections to Display",
            "Maximum number of connections shown (lower = less memory)",
            "max_connections_display",
            10, 100, 10,
            ui_font_size
        )
        
        # Enable Notifications
        notif_frame = ctk.CTkFrame(settings_container, fg_color=COLORS['bg_medium'], corner_radius=8)
        notif_frame.pack(fill="x", pady=5, padx=5)
        
        left = ctk.CTkFrame(notif_frame, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(
            left,
            text="Enable New App Notifications",
            font=("Segoe UI", ui_font_size, "bold"),
            text_color=COLORS['text_primary'],
            anchor="w"
        ).pack(fill="x")
        
        ctk.CTkLabel(
            left,
            text="Show dialog when new apps are blocked (apps are blocked by default)",
            font=("Segoe UI", 9),
            text_color=COLORS['text_secondary'],
            anchor="w"
        ).pack(fill="x")
        
        self.notif_switch = ctk.CTkSwitch(
            notif_frame,
            text="",
            command=lambda: self._update_setting('enable_notifications', self.notif_switch.get())
        )
        self.notif_switch.pack(side="right", padx=15)
        if self.app_registry.get_setting('enable_notifications'):
            self.notif_switch.select()
        
        # Auto-allow Whitelisted (removed auto-block unknown, now default behavior)
        ctk.CTkLabel(
            settings_container,
            text="ℹ️ Default Behavior: All new apps are blocked automatically. Only whitelisted apps connect without prompt.",
            font=("Segoe UI", 9),
            text_color=COLORS['text_secondary'],
            wraplength=600
        ).pack(fill="x", pady=10, padx=20)
        
        # Apply button
        btn_frame = ctk.CTkFrame(settings_container, fg_color="transparent")
        btn_frame.pack(fill="x", pady=20, padx=5)
        
        ctk.CTkButton(
            btn_frame,
            text="Apply & Restart Required",
            fg_color=COLORS['accent_blue'],
            height=40,
            font=("Segoe UI", ui_font_size, "bold"),
            command=self._apply_settings
        ).pack(pady=10)
        
        ctk.CTkLabel(
            btn_frame,
            text="Note: Font size changes require app restart to take full effect",
            font=("Segoe UI", 9),
            text_color=COLORS['text_secondary']
        ).pack()
    
    def _create_setting_row(self, parent, title: str, description: str, setting_key: str, min_val, max_val, step, ui_font_size: int):
        """Create a setting row with slider."""
        frame = ctk.CTkFrame(parent, fg_color=COLORS['bg_medium'], corner_radius=8)
        frame.pack(fill="x", pady=5, padx=5)
        
        left = ctk.CTkFrame(frame, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True, padx=15, pady=15)
        
        ctk.CTkLabel(
            left,
            text=title,
            font=("Segoe UI", ui_font_size, "bold"),
            text_color=COLORS['text_primary'],
            anchor="w"
        ).pack(fill="x")
        
        ctk.CTkLabel(
            left,
            text=description,
            font=("Segoe UI", 9),
            text_color=COLORS['text_secondary'],
            anchor="w"
        ).pack(fill="x")
        
        right = ctk.CTkFrame(frame, fg_color="transparent")
        right.pack(side="right", padx=15)
        
        current_val = self.app_registry.get_setting(setting_key)
        
        value_label = ctk.CTkLabel(
            right,
            text=str(current_val),
            font=("Segoe UI", ui_font_size, "bold"),
            text_color=COLORS['accent_blue'],
            width=50
        )
        value_label.pack(side="right", padx=10)
        
        slider = ctk.CTkSlider(
            right,
            from_=min_val,
            to=max_val,
            number_of_steps=int((max_val - min_val) / step),
            width=200,
            command=lambda v: self._on_slider_change(setting_key, v, value_label)
        )
        slider.set(current_val)
        slider.pack(side="right")
    
    def _on_slider_change(self, setting_key: str, value: float, label: ctk.CTkLabel):
        """Handle slider value change."""
        # Round to appropriate precision
        if setting_key in ['ui_font_size', 'process_font_size', 'max_connections_display']:
            value = int(value)
        else:
            value = round(value, 1)
        
        label.configure(text=str(value))
        self.app_registry.update_setting(setting_key, value)
        
        # Apply connection interval immediately
        if setting_key == 'connection_update_interval':
            self.monitor.update_interval = value
    
    def _update_setting(self, key: str, value):
        """Update a boolean setting."""
        self.app_registry.update_setting(key, value)
    
    def _apply_settings(self):
        """Apply settings and restart application."""
        result = messagebox.askyesno(
            "Restart Required",
            "Settings have been saved.\n\n"
            "The application will now restart to apply all changes.\n\n"
            "Continue?"
        )
        
        if result:
            # Schedule restart after current instance closes
            import subprocess
            import tempfile
            
            # Create restart script that waits for mutex to be released
            restart_script = f"""
import time
import subprocess
import sys
import win32event
import win32api
import winerror

MUTEX_NAME = "Global\\\\FirewallManagerSingleInstance"

# Wait for mutex to be released (up to 5 seconds)
for i in range(10):
    try:
        test_mutex = win32event.CreateMutex(None, False, MUTEX_NAME)
        last_error = win32api.GetLastError()
        
        if last_error != winerror.ERROR_ALREADY_EXISTS:
            # Mutex is free, close it and start new instance
            win32api.CloseHandle(test_mutex)
            subprocess.Popen([r"{sys.executable}"] + {sys.argv})
            break
        else:
            # Still locked, wait
            win32api.CloseHandle(test_mutex)
            time.sleep(0.5)
    except:
        time.sleep(0.5)
"""
            
            # Write temp script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(restart_script)
                temp_script = f.name
            
            # Launch restart script in background
            subprocess.Popen([sys.executable, temp_script], 
                           creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0)
            
            # Close current instance
            self._quit_app()
    
    def _setup_tray(self):
        """Setup system tray icon."""
        # Create icon image
        def create_icon_image():
            width = 64
            height = 64
            image = Image.new('RGB', (width, height), (30, 30, 30))
            dc = ImageDraw.Draw(image)
            # Draw shield
            dc.rectangle([16, 16, 48, 48], fill=(0, 120, 212), outline=(255, 255, 255))
            return image
        
        # Create menu
        menu = pystray.Menu(
            pystray.MenuItem("Show", self._show_from_tray, default=True),
            pystray.MenuItem("Exit", self._quit_app)
        )
        
        # Create icon
        self.tray_icon = pystray.Icon(
            "firewall_manager",
            create_icon_image(),
            "Firewall Manager",
            menu
        )
        
        # Run in separate thread
        threading.Thread(target=self.tray_icon.run, daemon=True).start()
    
    def _hide_to_tray(self):
        """Hide window to system tray."""
        # Also hide dialog if it's showing
        if self.new_apps_dialog and not self.dialog_minimized:
            self.new_apps_dialog._hide_dialog()
        self.root.withdraw()
    
    def _on_main_window_click(self, event):
        """Hide dialog when main window is clicked."""
        if self.new_apps_dialog and not self.dialog_minimized:
            self.new_apps_dialog._hide_dialog()
    
    def _hide_window(self):
        """Hide window on startup (for --minimized mode)."""
        self.root.withdraw()
    
    def _restore_window(self):
        """Restore window from minimized/hidden state and bring to front."""
        self.root.deiconify()
        self.root.state('zoomed')  # Maximize window
        self.root.lift()
        self.root.focus_force()
        self.root.attributes('-topmost', True)
        self.root.after(100, lambda: self.root.attributes('-topmost', False))
    
    def _show_from_tray(self, icon=None, item=None):
        """Show window from system tray."""
        self.root.after(0, self._restore_window)
    
    def _quit_app(self, icon=None, item=None):
        """Quit application completely."""
        if self.tray_icon:
            self.tray_icon.stop()
        self.monitor.stop()
        self.root.quit()
    
    def _load_lists(self):
        """Load whitelist and blacklist."""
        ui_font_size = self.app_registry.get_setting('ui_font_size')
        
        # Clear whitelist - check if widgets still exist
        for widget in self.whitelist_container.winfo_children():
            try:
                widget.after_idle(widget.destroy)
            except:
                pass
        
        # Clear blacklist - check if widgets still exist
        for widget in self.blacklist_container.winfo_children():
            try:
                widget.after_idle(widget.destroy)
            except:
                pass
        
        # Load whitelist
        for app_path in self.app_registry.get_whitelist():
            card = ListCard(
                self.whitelist_container,
                app_path,
                "whitelist",
                self._handle_list_action,
                self._copy_app_info,
                ui_font_size
            )
            card.pack(fill="x", pady=3, padx=5)
        
        # Load blacklist
        for app_path in self.app_registry.get_blacklist():
            card = ListCard(
                self.blacklist_container,
                app_path,
                "blacklist",
                self._handle_list_action,
                self._copy_app_info,
                ui_font_size
            )
            card.pack(fill="x", pady=3, padx=5)
        
        self._update_status()
    
    def _handle_list_action(self, action: str, app_path: str):
        """Handle whitelist/blacklist actions."""
        if action == "move_to_whitelist":
            self.app_registry.add_to_whitelist(app_path)
            # Remove block rule
            self.fw_manager.remove_rule(app_path)
            self._load_lists()
        
        elif action == "move_to_blacklist":
            self.app_registry.add_to_blacklist(app_path)
            # Add block rule
            success, msg = self.fw_manager.add_block_rule(app_path)
            if not success:
                messagebox.showerror("Error", msg)
            self._load_lists()
        
        elif action == "forget":
            self.app_registry.forget_app(app_path)
            # Remove block rule
            self.fw_manager.remove_rule(app_path)
            # Clear from monitor's seen apps so it can be detected again
            if app_path in self.monitor.seen_apps:
                self.monitor.seen_apps.remove(app_path)
            self._load_lists()
    
    def _browse_application(self):
        """Browse for executable to block."""
        file_path = filedialog.askopenfilename(
            title="Select Application to Block",
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")]
        )
        
        if file_path:
            self._block_app(file_path)
    
    def _browse_application_to_allow(self):
        """Browse for executable to allow."""
        file_path = filedialog.askopenfilename(
            title="Select Application to Allow",
            filetypes=[("Executable Files", "*.exe"), ("All Files", "*.*")]
        )
        
        if file_path:
            self._allow_app(file_path)
    
    def _allow_app(self, app_path: str):
        """Allow an application (removes block rule)."""
        self.app_registry.add_to_whitelist(app_path)
        
        # Remove block rule if exists
        self.fw_manager.remove_rule(app_path)
        
        self._load_lists()
    
    def _block_app(self, app_path: str):
        """Block an application (with user feedback)."""
        # Safety check
        is_safe, reason = is_safe_to_block(app_path=app_path)
        if not is_safe:
            messagebox.showerror("Cannot Block", reason)
            return
        
        self.app_registry.add_to_blacklist(app_path)
        success, message = self.fw_manager.add_block_rule(app_path)
        
        if not success:
            messagebox.showerror("Error", message)
        else:
            messagebox.showinfo("Success", f"{os.path.basename(app_path)} blocked")
        
        self._load_lists()
    
    def _block_app_silent(self, app_path: str):
        """Block an application silently (no messagebox, for auto-blocking)."""
        # Safety check
        is_safe, reason = is_safe_to_block(app_path=app_path)
        if not is_safe:
            return
        
        self.app_registry.add_to_blacklist(app_path)
        self.fw_manager.add_block_rule(app_path)
        self._load_lists()
    
    def _confirm_block_app(self, app_path: str):
        """Confirm block for already-blocked app (just marks as known, no new rule)."""
        # App is already blocked, just ensure it's in blacklist
        if not self.app_registry.is_blacklisted(app_path):
            self.app_registry.add_to_blacklist(app_path)
            self._load_lists()
    
    def _on_new_app_detected(self, app_path: str):
        """Handle new application detection."""
        # Don't notify if already known
        if self.app_registry.is_known(app_path):
            return
        
        # Safety check - don't notify for system apps
        is_safe, _ = is_safe_to_block(app_path=app_path)
        if not is_safe:
            return
        
        # Block immediately by default (silently, no messagebox)
        self._block_app_silent(app_path)
        
        # Show notification if enabled
        if self.app_registry.get_setting('enable_notifications'):
            # Show in main thread
            self.root.after(0, lambda: self._add_to_new_apps_dialog(app_path))
    
    def _check_unknown_apps_on_startup(self):
        """Check for unknown apps with active connections on startup."""
        if not self.app_registry.get_setting('enable_notifications'):
            return
        
        # Get current connections
        connections = self.monitor.get_current_connections()
        unknown_apps = set()
        
        for conn in connections:
            # Skip if already known
            if self.app_registry.is_known(conn.process_path):
                continue
            
            # Skip if not safe to block (system apps)
            is_safe, _ = is_safe_to_block(app_path=conn.process_path)
            if not is_safe:
                continue
            
            # Skip if already blocked
            if self.app_registry.is_blacklisted(conn.process_path):
                continue
            
            unknown_apps.add(conn.process_path)
        
        # Show dialog for unknown apps
        if unknown_apps:
            for app_path in unknown_apps:
                # Block immediately (silently)
                self._block_app_silent(app_path)
                # Add to dialog
                self._add_to_new_apps_dialog(app_path)
    
    def _add_to_new_apps_dialog(self, app_path: str):
        """Add app to new apps dialog (or create dialog if needed)."""
        ui_font_size = self.app_registry.get_setting('ui_font_size')
        
        # Create dialog if doesn't exist or was destroyed
        if self.new_apps_dialog is None or not self.new_apps_dialog.winfo_exists():
            self.new_apps_dialog = NewAppsDialog(
                self.root,
                self._allow_app,
                self._confirm_block_app,  # Use confirm instead of block (app already blocked)
                self._copy_app_info,
                self._on_dialog_hidden,  # Callback when dialog is hidden
                ui_font_size
            )
            self.dialog_minimized = False
        
        # Add app to dialog
        self.new_apps_dialog.add_app(app_path)
        
        # Only show/bring to front if dialog isn't minimized
        if not self.dialog_minimized:
            # Restore main window if hidden
            if not self.root.winfo_viewable():
                self._restore_window()
            self.new_apps_dialog._show_dialog()
        else:
            # Update pending button with new count
            self._update_pending_button()
    
    def _open_github(self):
        """Open GitHub repository in browser."""
        import webbrowser
        webbrowser.open("https://github.com/sv222/WinNetGuard")
    
    def _emergency_reset(self):
        """Execute emergency reset."""
        result = messagebox.askyesno(
            "Emergency Reset",
            "This will:\n"
            "• Remove ALL firewall rules created by this app\n"
            "• Clear whitelist and blacklist\n\n"
            "Are you sure?"
        )
        
        if result:
            count, errors = emergency_reset()
            
            # Clear lists
            self.app_registry.whitelist.clear()
            self.app_registry.blacklist.clear()
            self.app_registry._save_settings()
            
            if errors:
                messagebox.showerror("Reset Completed with Errors", 
                                   f"Removed {count} rules.\n\nErrors:\n" + "\n".join(errors))
            else:
                messagebox.showinfo("Reset Complete", f"Successfully removed {count} rules and cleared all lists.")
            
            self._load_lists()
    
    def _on_connections_update(self, connections: List[Connection]):
        """Callback when connections are updated."""
        self.root.after(0, lambda: self._update_connections_display(connections))
    
    def _update_connections_display(self, connections: List[Connection]):
        """Update connections display (must run in main thread)."""
        # Always update status
        self._update_status(len(connections))
        
        # Only update display if connections tab is active (reduces flickering)
        if self.tabview.get() != "Connections":
            return
        
        # Create snapshot for comparison
        max_display = self.app_registry.get_setting('max_connections_display')
        current_snapshot = [(c.pid, c.remote_addr, c.remote_port) for c in connections[:max_display]]
        
        # Only rebuild if connections changed
        if current_snapshot != self.last_connections_snapshot:
            self.last_connections_snapshot = current_snapshot
            
            for widget in self.connections_container.winfo_children():
                try:
                    widget.after_idle(widget.destroy)
                except:
                    pass
            self.connection_rows.clear()
            
            # Show connections based on settings
            max_display = self.app_registry.get_setting('max_connections_display')
            process_font_size = self.app_registry.get_setting('process_font_size')
            
            for conn in connections[:max_display]:
                is_blocked = self.app_registry.is_blacklisted(conn.process_path)
                
                # Create connection card
                card = ctk.CTkFrame(self.connections_container, fg_color=COLORS['bg_medium'], corner_radius=4)
                card.pack(fill="x", pady=2, padx=5)
                
                # Left side - connection info
                left_frame = ctk.CTkFrame(card, fg_color="transparent")
                left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=5)
                
                status_icon = "🔴" if is_blocked else "🟢"
                info_text = f"{status_icon} {conn.process_name} → {conn.remote_addr}:{conn.remote_port}"
                
                ctk.CTkLabel(
                    left_frame,
                    text=info_text,
                    font=("Segoe UI", process_font_size, "bold"),
                    text_color=COLORS['text_primary'],
                    anchor="w"
                ).pack(fill="x")
                
                ctk.CTkLabel(
                    left_frame,
                    text=conn.process_path,
                    font=("Segoe UI", 9),
                    text_color=COLORS['text_secondary'],
                    anchor="w"
                ).pack(fill="x")
                
                # Right side - buttons and status
                right_frame = ctk.CTkFrame(card, fg_color="transparent")
                right_frame.pack(side="right", padx=10, pady=5)
                
                # Copy button
                ctk.CTkButton(
                    right_frame,
                    text="📋",
                    width=30,
                    height=25,
                    fg_color=COLORS['bg_light'],
                    hover_color=COLORS['accent_blue'],
                    font=("Segoe UI", 12),
                    command=lambda c=conn: self._copy_process_info(c)
                ).pack(side="left", padx=3)
                
                # Status label
                status_text = "BLOCKED" if is_blocked else "ALLOWED"
                ctk.CTkLabel(
                    right_frame,
                    text=status_text,
                    font=("Segoe UI", 9, "bold"),
                    text_color=COLORS['danger'] if is_blocked else COLORS['success']
                ).pack(side="left", padx=5)
                
                self.connection_rows.append(card)
    
    def _copy_process_info(self, conn: Connection):
        """Copy process info to clipboard."""
        text = f"app: {conn.process_name}, path: {conn.process_path}"
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()  # Required for clipboard to work
    
    def _copy_app_info(self, app_name: str, app_path: str):
        """Copy app info to clipboard."""
        text = f"app: {app_name}, path: {app_path}"
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()  # Required for clipboard to work
    
    def _on_dialog_hidden(self):
        """Callback when new apps dialog is hidden/minimized."""
        self.dialog_minimized = True
        # Check if dialog still exists (not destroyed)
        if self.new_apps_dialog and self.new_apps_dialog.winfo_exists():
            self._update_pending_button()
        else:
            # Dialog was destroyed, clear reference and hide button
            self.new_apps_dialog = None
            self.dialog_minimized = False
            self._update_pending_button()
    
    def _show_new_apps_dialog(self):
        """Restore hidden new apps dialog."""
        if self.new_apps_dialog and self.dialog_minimized and self.new_apps_dialog.winfo_exists():
            self.new_apps_dialog._show_dialog()
            self.dialog_minimized = False
            self._update_pending_button()
    
    def _update_pending_button(self):
        """Show or hide pending apps button based on dialog state."""
        if self.pending_btn is None:
            return
            
        if self.dialog_minimized and self.new_apps_dialog and len(self.new_apps_dialog.pending_apps) > 0:
            self.pending_btn.pack(side="right", padx=(0, 10))
            count = len(self.new_apps_dialog.pending_apps)
            self.pending_btn.configure(text=f"📋 Pending ({count})")
        else:
            self.pending_btn.pack_forget()
    
    def _update_status(self, conn_count: int = 0):
        """Update status bar."""
        allowed_count = len(self.app_registry.whitelist)
        blocked_count = len(self.app_registry.blacklist)
        self.status_label.configure(
            text=f"Status: ✅ Protected | Allowed: {allowed_count} | Blocked: {blocked_count} | Connections: {conn_count}"
        )
    
    def run(self):
        """Start the GUI."""
        self.root.mainloop()
        # Cleanup on exit
        if self.tray_icon:
            self.tray_icon.stop()
        self.monitor.stop()
