"""
Tooltip functionality for the Cre8Worthy application.
"""
import tkinter as tk
from tkinter import ttk

class ToolTip:
    """
    Creates a tooltip for a given widget.
    """
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip_window = None
        self.x = self.y = 0
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<Motion>", self.motion)
        self.widget.bind("<ButtonPress>", self.leave)
        self.delay = 1000  # Tooltip delay in milliseconds
        self.id = None
    
    def enter(self, event=None):
        self.schedule()
    
    def leave(self, event=None):
        self.unschedule()
        self.hide()
    
    def motion(self, event=None):
        self.x = event.x
        self.y = event.y
        if self.tooltip_window:
            self.tooltip_window.geometry(f"+{event.x_root+10}+{event.y_root+10}")
    
    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.delay, self.show)
    
    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None
    
    def show(self, event=None):
        if self.tooltip_window:
            return
            
        # Get screen position
        x_root = self.widget.winfo_rootx() + self.x + 10
        y_root = self.widget.winfo_rooty() + self.y + 10
        
        # Create a toplevel window
        self.tooltip_window = tk.Toplevel(self.widget)
        self.tooltip_window.wm_overrideredirect(True)  # Remove window decorations
        self.tooltip_window.wm_geometry(f"+{x_root}+{y_root}")
        
        # Use a subtle background color with border
        frame = ttk.Frame(self.tooltip_window, borderwidth=1, relief="solid")
        frame.pack(fill="both", expand=True)
        
        # Create label for tooltip content
        label = ttk.Label(
            frame, 
            text=self.text, 
            justify="left", 
            wraplength=300,
            padding=(5, 3),
            background="#fffbe6"  # Light yellow background
        )
        label.pack()
    
    def hide(self):
        if self.tooltip_window:
            self.tooltip_window.destroy()
            self.tooltip_window = None

def add_tooltip(widget, text):
    """Helper function to create a tooltip for a widget"""
    return ToolTip(widget, text)
