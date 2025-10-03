"""
UI styling configuration for the Cre8Worthy application.
"""
import tkinter as tk
from tkinter import ttk

def hex_with_opacity(hex_color, opacity=1.0):
    """Convert a hex color to a format with opacity that can be used in tkinter"""
    if hex_color.startswith('#'):
        hex_color = hex_color[1:]
    
    # Parse hex color
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # Return color in format that tkinter can use with opacity
    return f"#{r:02x}{g:02x}{b:02x}{int(opacity * 255):02x}"

def apply_styles(root):
    """Apply styles to the Tkinter application."""
    style = ttk.Style(root)
    # Use 'clam' theme as a base, it's often more customizable
    try:
        style.theme_use('clam')
    except tk.TclError:
        print("Clam theme not available, using default.")
        style.theme_use('default')

    # Define colors
    primary_color = "#2563eb"
    primary_dark = "#1d4ed8"
    primary_light = "#3b82f6"
    secondary_color = "#10b981"
    secondary_dark = "#059669"
    secondary_light = "#34d399"
    background_color = "#f0f4f8"  
    surface_color = "#ffffff"     
    surface_hover = "#f1f5f9"
    text_primary_color = "#1e293b"
    text_secondary_color = "#64748b"
    text_disabled_color = "#94a3b8"
    border_color = "#e2e8f0"
    error_color = "#ef4444"
    warning_color = "#f59e0b"
    success_color = "#10b981"
    text_on_primary = "#ffffff"
    text_on_secondary = "#ffffff"

    # Spacing values
    spacing_xs = 3
    spacing_sm = 6
    spacing_md = 12
    spacing_lg = 18
    spacing_xl = 24
    spacing_2xl = 36

    # Border radius values
    radius_sm = 2
    radius_md = 3
    radius_lg = 6

    # Font configurations
    default_font = ('Segoe UI', 10)
    heading_font = ('Segoe UI', 10, 'bold')
    title_font = ('Segoe UI', 12, 'bold')
    small_font = ('Segoe UI', 9)

    # Configure base styles
    style.configure('.',
                   background=background_color,
                   foreground=text_primary_color,
                   fieldbackground=background_color,
                   borderwidth=1,
                   font=default_font)

    # Frame styles
    style.configure('TFrame', background=background_color)
    style.configure('Surface.TFrame', background=surface_color)

    # Label styles
    style.configure('TLabel', 
                   background=background_color, 
                   foreground=text_primary_color, 
                   padding=spacing_sm)
    style.configure('TLabelFrame', 
                   background=background_color, 
                   bordercolor=border_color, 
                   padding=spacing_md)
    style.configure('TLabelFrame.Label', 
                   background=background_color,
                   foreground=text_primary_color, 
                   font=heading_font)

    # Specialized label styles
    style.configure('Title.TLabel', 
                   font=title_font, 
                   background=background_color,
                   padding=spacing_sm)
    style.configure('Heading.TLabel', 
                   font=heading_font, 
                   background=background_color)
    style.configure('Small.TLabel', 
                   font=small_font, 
                   background=background_color)
    style.configure('Error.TLabel', 
                   foreground=error_color, 
                   background=background_color)
    style.configure('Warning.TLabel', 
                   foreground=warning_color, 
                   background=background_color)
    style.configure('Status.TLabel', 
                   foreground=success_color, 
                   background=background_color)
    style.configure('Muted.TLabel', 
                   foreground=text_secondary_color, 
                   background=background_color)

    # Button styles
    style.configure('TButton',
                   background=primary_color,
                   foreground=text_on_primary,
                   bordercolor=primary_color,
                   borderwidth=1,
                   padding=(spacing_md, spacing_sm),
                   relief=tk.FLAT,
                   font=heading_font)
    style.map('TButton',
             background=[('active', primary_dark), ('pressed', primary_dark), ('disabled', surface_color)],
             foreground=[('disabled', text_disabled_color)],
             bordercolor=[('disabled', border_color)],
             relief=[('pressed', tk.FLAT)])

    # Secondary button
    style.configure('Secondary.TButton',
                   background=secondary_color,
                   foreground=text_on_secondary,
                   bordercolor=secondary_color)
    style.map('Secondary.TButton',
             background=[('active', secondary_dark), ('pressed', secondary_dark), ('disabled', surface_color)],
             foreground=[('disabled', text_disabled_color)],
             bordercolor=[('disabled', border_color)])

    # Outline button
    style.configure('Outline.TButton',
                   background=background_color,
                   foreground=text_primary_color,
                   bordercolor=border_color,
                   borderwidth=1,
                   relief=tk.SOLID)
    style.map('Outline.TButton',
             background=[('active', surface_hover), ('pressed', surface_hover)],
             foreground=[('disabled', text_disabled_color)],
             bordercolor=[('active', primary_color), ('pressed', primary_color), ('disabled', border_color)])

    # Small button variant
    style.configure('Small.TButton',
                   font=small_font,
                   padding=(spacing_sm, spacing_xs))
    style.configure('Small.Secondary.TButton',
                   font=small_font,
                   padding=(spacing_sm, spacing_xs),
                   background=secondary_color,
                   foreground=text_on_secondary)
    style.configure('Small.Outline.TButton',
                   font=small_font,
                   padding=(spacing_sm, spacing_xs),
                   background=background_color,
                   foreground=text_primary_color,
                   bordercolor=border_color)

    # Icon button
    style.configure('Icon.TButton',
                   padding=spacing_sm)

    # Entry styles
    style.configure('TEntry',
                   background=background_color,
                   foreground=text_primary_color,
                   fieldbackground=surface_color,
                   bordercolor=border_color,
                   borderwidth=1,
                   padding=spacing_sm)
    style.map('TEntry',
             bordercolor=[('focus', primary_color), ('disabled', border_color)],
             fieldbackground=[('disabled', surface_color)])

    # Combobox styles
    style.configure('TCombobox',
                   background=background_color,
                   foreground=text_primary_color,
                   fieldbackground=surface_color,
                   bordercolor=border_color,
                   borderwidth=1,
                   padding=spacing_sm)
    style.map('TCombobox',
             bordercolor=[('focus', primary_color), ('disabled', border_color)],
             fieldbackground=[('disabled', surface_color)])

    # Checkbutton styles
    style.configure('TCheckbutton',
                   background=background_color,
                   foreground=text_primary_color)
    style.map('TCheckbutton',
             background=[('disabled', surface_color)],
             foreground=[('disabled', text_disabled_color)])

    # Radiobutton styles
    style.configure('TRadiobutton',
                   background=background_color,
                   foreground=text_primary_color)
    style.map('TRadiobutton',
             background=[('disabled', surface_color)],
             foreground=[('disabled', text_disabled_color)])

    # Scale styles
    style.configure('TScale',
                   background=background_color,
                   foreground=text_primary_color,
                   bordercolor=border_color)
    style.map('TScale',
             background=[('disabled', surface_color)],
             foreground=[('disabled', text_disabled_color)])

    # Progressbar styles
    style.configure('TProgressbar',
                   background=primary_color,
                   bordercolor=border_color,
                   troughcolor=surface_color)
    style.map('TProgressbar',
             background=[('disabled', text_disabled_color)])

    # Notebook styles
    style.configure('TNotebook',
                   background=background_color,
                   bordercolor=border_color)
    style.configure('TNotebook.Tab',
                   background=surface_color,
                   foreground=text_primary_color,
                   padding=(spacing_md, spacing_sm))
    style.map('TNotebook.Tab',
             background=[('selected', primary_color), ('active', surface_hover)],
             foreground=[('selected', text_on_primary), ('disabled', text_disabled_color)]) 