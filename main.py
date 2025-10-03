import tkinter as tk
from tkinter import ttk, messagebox
import gemini_api
import data_utils
import ui
import admin
import logging
from tkinter import simpledialog
from styles import apply_styles
from pricing import calculate_price

def main():
    # Enable debug logging
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    # Set debug level for UI and Gemini API modules
    logging.getLogger("UI").setLevel(logging.DEBUG)
    logging.getLogger("GeminiAPI").setLevel(logging.DEBUG)
    
    # Initialize application
    root = tk.Tk()
    root.title("Cre8Worthy")
    # Apply styles *before* creating UI elements that use them
    apply_styles(root)  # Use the function from styles.py
    root.configure(padx=20, pady=20)  # Increased padding for better aesthetics
    
    # Set fixed window size for balanced layout
    root.minsize(900, 700)
    
    # Make root window resizable proportionally
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    # Initialize data file
    data_utils.initialize_data_file()
    
    # Create menu bar
    menubar = tk.Menu(root)
    # File menu
    file_menu = tk.Menu(menubar, tearoff=0)
    file_menu.add_command(label="Gemini Data View", command=lambda: open_gemini_data_view(root))
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="Tools", menu=file_menu)
    
    # Admin menu
    admin_menu = tk.Menu(menubar, tearoff=0)
    admin_menu.add_command(label="Open Admin Dashboard", command=lambda: open_admin_dashboard(root))
    menubar.add_cascade(label="Admin", menu=admin_menu)
    
    # Help menu with tooltip info
    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(label="Tooltips Info", command=show_tooltips_info)
    menubar.add_cascade(label="Help", menu=help_menu)
    
    # Set the menubar
    root.config(menu=menubar)
    
    # Create the UI without icons
    app = ui.PricingCalculatorUI(root)

    # Center window on screen for better presentation
    center_window(root, 900, 700)
    
    # Ensure proper tab order for keyboard navigation
    root.option_add('*takeFocus', True)

    # Start the main loop
    root.mainloop()

def open_gemini_data_view(root):
    """Open the Gemini Data View to display AI interaction history"""
    admin.open_gemini_data_view(root)

def open_admin_dashboard(root=None):
    """Open the admin dashboard with additional tools"""
    # Check for password - simple protection for admin functions
    password = simpledialog.askstring("Admin Access", "Enter admin password:", show='*')
    if password == "0000":  # Simple password for demo purposes
        if root:
            admin_window = tk.Toplevel(root)
            admin_window.title("Admin Dashboard")
            admin_window.minsize(600, 400)
            
            # Add admin tools here
            ttk.Label(admin_window, text="Admin Dashboard", font=("Arial", 16, "bold")).pack(pady=20)
            
            # Button to open Gemini Data View
            ttk.Button(admin_window, text="Open Gemini Data View", 
                      command=lambda: admin.open_gemini_data_view(root)).pack(pady=10)
            
            # Center the admin window
            center_window(admin_window, 600, 400)
        else:
            messagebox.showerror("Error", "Cannot open admin dashboard without root window")
    else:
        messagebox.showerror("Access Denied", "Incorrect password")

def show_tooltips_info():
    """Show information about tooltips in the application"""
    info = """
    Tooltips Help
    
    This application includes helpful tooltips throughout the interface. 
    Look for the blue ℹ icons next to fields for more information.
    
    Hover your mouse over these icons to see detailed explanations 
    about each feature.
    
    Main tooltips are available for:
    - Artist name field
    - Target market field
    - Product type selection 
    - Material selections
    - Cost fields
    - Calculation buttons
    """
    messagebox.showinfo("Tooltips Information", info)

def center_window(window, width, height):
    """Center a window on the screen with the given width and height."""
    # Get screen dimensions
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    # Calculate position
    x = (screen_width - width) // 2
    y = (screen_height - height) // 2
    
    # Set window size and position
    window.geometry(f'{width}x{height}+{x}+{y}')

if __name__ == "__main__":
    main()
