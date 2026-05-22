"""Global keyboard manager for launching onboard on-screen keyboard."""

from PyQt5.QtWidgets import QLineEdit, QTextEdit
from PyQt5.QtCore import Qt, QEvent
import subprocess
import os
import shutil


class KeyboardManager:
    """Manages onboard on-screen keyboard launch when text input fields are focused."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(KeyboardManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.onboard_process = None
        self.focused_widget = None
        
        # Check if onboard is available
        self.onboard_available = shutil.which('onboard') is not None
        if not self.onboard_available:
            print("WARNING: onboard is not installed. Install with: sudo apt-get install onboard")
        else:
            print("INFO: onboard is available and ready to use")
    
    def install_on_parent(self, parent_widget):
        """Install keyboard monitoring on all text input widgets in a parent."""
        self._install_recursive(parent_widget)
    
    def _install_recursive(self, widget):
        """Recursively install event filter on all text input widgets."""
        if isinstance(widget, (QLineEdit, QTextEdit)):
            print(f"DEBUG: Installing event filter on {widget.__class__.__name__}")
            widget.installEventFilter(self)
        
        # Recursively process child widgets
        for child in widget.children():
            self._install_recursive(child)
    
    def _launch_onboard(self):
        """Launch the onboard on-screen keyboard."""
        if not self.onboard_available:
            return
        
        try:
            # Check if onboard is already running
            if self.onboard_process is None or self.onboard_process.poll() is not None:
                print("DEBUG: Launching onboard...")
                # Launch with flags to make it stay on top and work better with fullscreen
                self.onboard_process = subprocess.Popen(
                    ['onboard', '--xid'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                print(f"DEBUG: Onboard process started with PID {self.onboard_process.pid}")
            else:
                print("DEBUG: Onboard is already running")
        except FileNotFoundError:
            print("Error: onboard executable not found")
        except Exception as e:
            print(f"Error launching onboard: {e}")
    
    def _close_onboard(self):
        """Close the onboard on-screen keyboard."""
        try:
            if self.onboard_process:
                print("DEBUG: Terminating onboard...")
                self.onboard_process.terminate()
                self.onboard_process = None
                print("DEBUG: Onboard terminated")
        except Exception as e:
            print(f"Error closing onboard: {e}")
    
    def eventFilter(self, obj, event):
        """Filter events to launch/close onboard on text input focus changes."""
        if event.type() == QEvent.FocusIn:
            if isinstance(obj, (QLineEdit, QTextEdit)):
                print(f"DEBUG: FocusIn event on {obj.__class__.__name__}")
                self.focused_widget = obj
                # Launch onboard keyboard
                self._launch_onboard()
                return False
        
        elif event.type() == QEvent.FocusOut:
            if self.focused_widget == obj:
                print(f"DEBUG: FocusOut event on {obj.__class__.__name__}")
                self.focused_widget = None
                # Close onboard keyboard when focus is lost
                self._close_onboard()
            return False
        
        return super().eventFilter(obj, event)


def get_keyboard_manager():
    """Get or create the singleton keyboard manager instance."""
    return KeyboardManager()
