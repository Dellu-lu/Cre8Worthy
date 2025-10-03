"""
Data utilities for the Cre8Worthy application.
"""
import os
import csv
from PIL import Image, ImageTk
from datetime import datetime
from config import DATA_FILE

def initialize_data_file():
    """Initialize the data file with headers if it doesn't exist."""
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            writer.writerow([
                "Date", "Artist", "Market", "Type", "Materials",
                "Length (cm)", "Width (cm)", "Height (cm)", "Weight (kg)",
                "Material Cost (€)", "Shipping Cost (€)", "Advertising Cost (€)",
                "Creation Time (h)", "Final Price (€)", "Market Demand (1-10)", "AI Price Recommendation (€)"
            ])

def save_to_file(data):
    """Save data to the CSV file."""
    with open(DATA_FILE, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(data)
    return True

def hex_with_opacity(hex_color, opacity=1.0):
    """Convert a hex color to a format with opacity that can be used in tkinter"""
    if (hex_color.startswith('#')):
        hex_color = hex_color[1:]
    
    # Parse hex color
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    
    # Return color in format that tkinter can use with opacity
    return f"#{r:02x}{g:02x}{b:02x}{int(opacity * 255):02x}"

def load_icons(icon_scales=None):
    """Load application icons with custom scaling."""
    if icon_scales is None:
        icon_scales = {
            'app': (32, 32),
            'normal': (24, 24),
            'small': (16, 16)
        }

    icon_dir = "icons"
    icons = {}
    icon_files = {
        'cost': ('cost.png', 'normal'),
        'time': ('time.png', 'normal'),
        'artist': ('artist.png', 'normal'),
        'market': ('market.png', 'normal'),
        'material': ('material.png', 'normal'),
        'product': ('product.png', 'normal'),
        'length': ('length.png', 'small'),
        'width': ('width.png', 'small'),
        'height': ('height.png', 'small'),
        'weight': ('weight.png', 'small'),
        'calculate': ('calculate.png', 'normal'),
        'result': ('result.png', 'normal'),
        'app': ('app_icon.png', 'app')
    }

    for name, (file, size_type) in icon_files.items():
        try:
            path = os.path.join(icon_dir, file)
            img = Image.open(path)
            img = img.resize(icon_scales[size_type], Image.LANCZOS)
            icons[name] = ImageTk.PhotoImage(img)
        except Exception as e:
            print(f"Failed to load icon {file}: {e}")
            icons[name] = None
    return icons

def format_save_data(timestamp, artist, market, product_type, materials_text,
                    length, width, height, weight, material_cost, shipping_cost,
                    ad_cost, time_spent, final_price, market_demand, ai_price=None):
    """Format data for saving to CSV file."""
    return [
        timestamp, artist, market, product_type, materials_text,
        length, width, height, weight, material_cost, shipping_cost, ad_cost,
        time_spent, final_price, market_demand, ai_price
    ]
