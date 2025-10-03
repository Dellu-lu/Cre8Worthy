import os
import sys
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
from PIL import Image, ImageTk
import datetime
import data_utils  # Import the existing data_utils module
import csv
import traceback
from sys import exc_info

class AdminDashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("Admin Dashboard")
        # Apply styles *before* creating UI elements
        data_utils.apply_styles(root)
        self.root.geometry("1200x700")
        self.root.minsize(900, 600)

        # Set default CSV path
        self.default_csv = "art_pricing_data.csv"
        self.df = None
        self.csv_path = None

        # Sort variables
        self.sort_by = None
        self.sort_ascending = True

        # Attempt to load icon
        try:
            self.icons = data_utils.load_icons()
            if self.icons.get('app'):
                self.root.iconphoto(True, self.icons['app'])
        except Exception as e:
            print(f"Failed to load application icon: {e}")

        # Create main frames
        self.create_menu()
        self.create_main_layout()

        self.chart_windows = {}

        # Automatically load the default CSV file if it exists
        if os.path.exists(self.default_csv):
            self.load_csv(self.default_csv)

    def create_menu(self):
        """Create the menu bar with enhanced visualization options"""
        menubar = tk.Menu(self.root)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Export to Excel", command=self.export_to_excel)
        file_menu.add_command(label="Gemini Data View", command=self.open_gemini_data_view)  # Renamed from GPT to Gemini
        # Add button to choose file in the upper right corner of the file menu
        file_menu.add_command(label="Choose File", command=self.choose_file)
        file_menu.add_separator() 
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Enhanced visualization menu
        viz_menu = tk.Menu(menubar, tearoff=0)

        # Basic analysis submenu
        basic_menu = tk.Menu(viz_menu, tearoff=0)
        basic_menu.add_command(label="Price by Type", command=lambda: self.create_chart("type"))
        basic_menu.add_command(label="Price by Market", command=lambda: self.create_chart("market"))
        basic_menu.add_command(label="Market Demand", command=lambda: self.create_chart("demand"))
        basic_menu.add_command(label="Time Trends", command=lambda: self.create_chart("time"))
        viz_menu.add_cascade(label="Basic Analyses", menu=basic_menu)

        # Cost analysis submenu
        cost_menu = tk.Menu(viz_menu, tearoff=0)
        cost_menu.add_command(label="Cost Breakdown", command=lambda: self.create_chart("cost_breakdown"))
        cost_menu.add_command(label="Cost vs Final Price", command=lambda: self.create_chart("cost_vs_price"))
        viz_menu.add_cascade(label="Cost Analyses", menu=cost_menu)

        # Size and dimension analysis
        size_menu = tk.Menu(viz_menu, tearoff=0)
        size_menu.add_command(label="Price vs Area", command=lambda: self.create_chart("price_vs_area"))
        size_menu.add_command(label="Price vs Volume", command=lambda: self.create_chart("price_vs_volume"))
        size_menu.add_command(label="Price vs Weight", command=lambda: self.create_chart("price_vs_weight"))
        viz_menu.add_cascade(label="Dimension Analyses", menu=size_menu)

        # Advanced analysis
        adv_menu = tk.Menu(viz_menu, tearoff=0)
        adv_menu.add_command(label="Correlation Matrix", command=lambda: self.create_chart("correlation"))
        adv_menu.add_command(label="Time vs Price", command=lambda: self.create_chart("time_vs_price"))
        adv_menu.add_command(label="Artist Comparison", command=lambda: self.create_chart("artist_comparison"))
        viz_menu.add_cascade(label="Advanced Analyses", menu=adv_menu)
        
        # AI Analysis menu
        ai_menu = tk.Menu(viz_menu, tearoff=0)
        ai_menu.add_command(label="AI vs Calculated Price", command=lambda: self.create_chart("ai_price_comparison"))
        ai_menu.add_command(label="AI Price by Type", command=lambda: self.create_chart("ai_price_by_type"))
        viz_menu.add_cascade(label="AI Price Analysis", menu=ai_menu)

        menubar.add_cascade(label="Visualizations", menu=viz_menu)

        # Set the menubar
        self.root.config(menu=menubar)

    def choose_file(self):
        """Open a file dialog to choose a CSV file and load it."""
        filepath = filedialog.askopenfilename(
            title="Choose CSV file",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filepath:
            self.load_csv(filepath)

    def create_main_layout(self):
        """Create the main layout with side panel and main content area"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Top panel for controls
        self.control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        self.control_frame.pack(fill=tk.X, padx=5, pady=5)

        # Load and export buttons
        btn_frame = ttk.Frame(self.control_frame)
        btn_frame.pack(fill=tk.X, expand=True, pady=5)

        # Only export button (removing CSV load button)
        ttk.Button(btn_frame, text="Export to Excel", command=self.export_to_excel, style='Secondary.TButton').pack(side=tk.LEFT, padx=5)

        # Filter options
        filter_frame = ttk.Frame(self.control_frame)
        filter_frame.pack(fill=tk.X, expand=True, pady=5)

        ttk.Label(filter_frame, text="Filter by:").pack(side=tk.LEFT, padx=5)
        self.filter_var = tk.StringVar()
        self.filter_combobox = ttk.Combobox(filter_frame, textvariable=self.filter_var,
                                            values=["All", "Type", "Artist", "Market"])
        self.filter_combobox.pack(side=tk.LEFT, padx=5)
        self.filter_combobox.set("All")

        # Add a label for the filter entry
        ttk.Label(filter_frame, text="Search term:").pack(side=tk.LEFT, padx=(10, 5))
        self.filter_entry = ttk.Entry(filter_frame, width=20)
        self.filter_entry.pack(side=tk.LEFT, padx=5)

        ttk.Button(filter_frame, text="Apply", command=self.apply_filter).pack(side=tk.LEFT, padx=5)
        ttk.Button(filter_frame, text="Reset", command=self.reset_filter, style='Outline.TButton').pack(side=tk.LEFT, padx=5)

        # Table Frame (full width now)
        table_frame = ttk.LabelFrame(main_frame, text="Data", padding="10")
        table_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create Treeview for data
        self.create_treeview(table_frame)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready. Load a CSV file to get started.")
        # Use Muted style for less emphasis
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, style='Muted.TLabel')
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)

    def create_treeview(self, parent):
        """Create the treeview widget for displaying data"""
        # Create a frame for the treeview and scrollbar
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True)

        # Create scrollbars
        vscrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL)
        vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        hscrollbar = ttk.Scrollbar(frame, orient=tk.HORIZONTAL)
        hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Create the treeview with show="headings" to fix alignment issue
        self.tree = ttk.Treeview(frame,
                                 yscrollcommand=vscrollbar.set,
                                 xscrollcommand=hscrollbar.set,
                                 show="headings")  # This ensures header separation

        # Configure scrollbars
        vscrollbar.config(command=self.tree.yview)
        hscrollbar.config(command=self.tree.xview)

        # Pack the treeview
        self.tree.pack(fill=tk.BOTH, expand=True)

        # Configure placeholder columns
        self.tree['columns'] = ('message',)
        self.tree.column('message', width=200)
        self.tree.heading('message', text='Message')

        # Add column click binding for sorting
        self.tree.bind("<ButtonRelease-1>", self.on_column_click)

        # Insert placeholder message
        self.tree.insert('', 'end', values=('No data loaded. Please load a CSV file.',))

    def on_column_click(self, event):
        """Handle column header click for sorting"""
        if self.df is None:
            return

        region = self.tree.identify_region(event.x, event.y)
        if region != "heading":
            return

        column = self.tree.identify_column(event.x)
        column_index = int(column.replace('#', '')) - 1

        if column_index < 0:  # Skip the hidden column
            return

        # Get column name
        columns = list(self.df.columns)
        if column_index >= len(columns):
            return

        column_name = columns[column_index]

        # Toggle sort direction if clicking the same column
        if self.sort_by == column_name:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_by = column_name
            self.sort_ascending = True

        # Sort dataframe and update display
        self.df = self.df.sort_values(by=column_name, ascending=self.sort_ascending)
        self.update_treeview()

        # Update status
        direction = "ascending" if self.sort_ascending else "descending"
        self.status_var.set(f"Sorted by {column_name} ({direction})")

    def load_csv(self, filepath=None):
        """Load a CSV file and display its contents in the treeview"""
        try:
            # If filepath is not provided, open file dialog
            if not filepath:
                filepath = filedialog.askopenfilename(
                    title="Open CSV file",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
                )
                if not filepath:
                    return

            # Check if file exists
            if not os.path.exists(filepath):
                messagebox.showerror("Error", f"File {filepath} does not exist.")
                return

            self.csv_path = filepath
            self.df = pd.read_csv(filepath)

            # Standardize column names for better compatibility
            self.standardize_column_names()

            # Add index/order column
            self.df.insert(0, "Order", range(1, len(self.df) + 1))

            # Update the treeview
            self.update_treeview()

            # Update status
            self.status_var.set(f"File loaded: {os.path.basename(filepath)} - {len(self.df)} records")

        except Exception as e:
            messagebox.showerror("Error", f"Error loading file: {e}")
            print(f"Error details: {e}")
    
    def standardize_column_names(self):
        if self.df is None:
            return
    
        rename_map = {
            "Longueur": "Longueur (cm)",
            "Largeur": "Largeur (cm)",
            "Hauteur": "Hauteur (cm)",
            "Poids":   "Poids (kg)",
            "Matériaux": "Materials",
            "Coût Matériaux": "Cost Materials (€)",
            "Coût Livraison": "Cost Shipping (€)",
            "Coût Publicité": "Cost Ads (€)",
            "Temps Création": "Time (h)",
            "Prix Calculé": "Final Price (€)",
            "Demande Marché": "Market Demand (1-10)",
            "gemini_price": "AI Price Recommendation (€)",

            # Add these lines to handle English CSV column names
            "Time": "Time (h)",
            "Price": "Final Price (€)",
            "Demand": "Market Demand (1-10)",
            "AI Price": "AI Price Recommendation (€)"
        }
    
        self.df.rename(columns=rename_map, inplace=True)

    def update_treeview(self):
        """Update the treeview with the current dataframe"""
        if self.df is None:
            return

        # Clear existing data
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Configure columns - skip the first column (Order)
        columns = list(self.df.columns)[1:]  # Skip first column
        self.tree['columns'] = columns

        # Configure column headings and widths
        for col in columns:
            # Calculate appropriate width based on column content
            col_width = len(col) * 10  # Base width from column name
            if self.df[col].dtype == 'object':  # Text column
                max_content_width = self.df[col].astype(str).map(len).max() * 8
            else:  # Numeric column
                max_content_width = self.df[col].astype(str).map(len).max() * 10

            # Use the larger of the two widths, with a maximum of 200
            width = min(max(col_width, max_content_width), 200)

            self.tree.column(col, width=width)

            # Add sort indicator to column header if it's the current sort column
            if col == self.sort_by:
                indicator = "▲" if self.sort_ascending else "▼"
                self.tree.heading(col, text=f"{col} {indicator}", command=lambda c=col: self.sort_by_column(c))
            else:
                self.tree.heading(col, text=col, command=lambda c=col: self.sort_by_column(c))

        # Insert data - skip the first column (Order)
        for _, row in self.df.iterrows():
            values = [row[col] for col in columns]  # Skip first column values
            self.tree.insert('', 'end', values=values)

    def sort_by_column(self, column):
        """Sort the dataframe by a specific column"""
        if self.df is not None:
            # Toggle sort direction if clicking the same column again
            if self.sort_by == column:
                self.sort_ascending = not self.sort_ascending
            else:
                self.sort_by = column
                self.sort_ascending = True

            # Sort dataframe and update display
            self.df = self.df.sort_values(by=column, ascending=self.sort_ascending)
            self.update_treeview()

            # Update status
            direction = "ascending" if self.sort_ascending else "descending"
            self.status_var.set(f"Sorted by {column} ({direction})")

    def export_to_excel(self):
        """Export current dataframe to Excel using CSV as fallback if openpyxl isn't available"""
        if self.df is None:
            messagebox.showwarning("Warning", "No data to export.")
            return

        try:
            # Generate default filename with timestamp
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"export_{timestamp}"

            # Set the initial directory to the current working directory
            initial_dir = os.getcwd()

            # Try to export as Excel first
            filepath = filedialog.asksaveasfilename(
                title="Save as",
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv"), ("All files", "*.*")],
                initialdir=initial_dir,
                initialfile=default_filename
            )

            if not filepath:
                return  # User canceled

            try:
                # Export to Excel or CSV based on file extension
                if filepath.lower().endswith('.xlsx'):
                    try:
                        # Try Excel export
                        self.df.to_excel(filepath, index=False)
                        export_type = "Excel"
                    except ImportError:
                        # If openpyxl is missing, fall back to CSV
                        if messagebox.askyesno("Missing module",
                                              "The 'openpyxl' module is required for Excel export. "
                                              "Would you like to export as CSV instead?"):
                            csv_path = filepath.replace('.xlsx', '.csv')
                            self.df.to_csv(csv_path, index=False)
                            filepath = csv_path
                            export_type = "CSV"
                        else:
                            messagebox.showinfo("Information",
                                               "To use Excel export, install the 'openpyxl' module with:\n"
                                               "pip install openpyxl")
                            return
                else:
                    # Default to CSV for other extensions
                    self.df.to_csv(filepath, index=False)
                    export_type = "CSV"

                # Update status and show confirmation
                self.status_var.set(f"Data exported to: {os.path.basename(filepath)}")
                messagebox.showinfo("Success", f"Data successfully exported to {export_type} at {filepath}")

            except Exception as e:
                # Try CSV as fallback
                csv_path = default_filename + ".csv"
                csv_path = filedialog.asksaveasfilename(
                    title="Excel export failed. Save as CSV",
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                    initialdir=initial_dir,
                    initialfile=csv_path
                )

                if csv_path:
                    self.df.to_csv(csv_path, index=False)
                    self.status_var.set(f"Data exported to CSV: {os.path.basename(csv_path)}")
                    messagebox.showinfo("Success", f"Data successfully exported to CSV at {csv_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Error while exporting: {e}")
            print(f"Error details: {e}")

    def create_chart(self, chart_type):
        """Create different types of charts based on the data"""
        print(f"[DEBUG] Creating chart of type: {chart_type}")

        if self.df is None or self.df.empty:
            print("[DEBUG] No data available for visualization")
            messagebox.showwarning("Warning", "No data to visualize.")
            return

        try:
            # Create window ID based on chart type and timestamp
            import time
            window_id = f"{chart_type}_{int(time.time())}"

            # Create new window for visualization
            chart_window = tk.Toplevel(self.root)
            chart_window.title(f"Visualization - {chart_type}")
            chart_window.geometry("800x600")

            # Store reference to window
            self.chart_windows[window_id] = chart_window

            # Configure window close event to remove from dictionary
            chart_window.protocol("WM_DELETE_WINDOW", lambda id=window_id: self.close_chart_window(id))

            print(f"[DEBUG] Created external window for chart {window_id}")

            # Create figure and axis with larger size for external window
            fig, ax = plt.subplots(figsize=(10, 6), dpi=100)

            # Set chart title based on type
            title = ""
            print(f"[DEBUG] Available columns: {list(self.df.columns)}")

            # EXISTING CHART TYPES
            if chart_type == "type":
                # Existing code for type chart...
                print("[DEBUG] Processing 'type' chart")
                if 'Type de produit' in self.df.columns:
                    col_name = 'Type de produit'
                else:
                    col_name = 'Type'

                if 'Prix recommandé' in self.df.columns:
                    price_col = 'Prix recommandé'
                elif 'Prix Final (€)' in self.df.columns:
                    price_col = 'Prix Final (€)'
                else:
                    price_col = self.df.select_dtypes(include=['number']).columns[1]

                data = self.df.groupby(col_name)[price_col].mean().sort_values(ascending=False)
                sns.barplot(x=data.index, y=data.values, ax=ax)
                title = f'Average Price by Product Type ({price_col})'
                ax.set_xlabel('Product Type')
                ax.set_ylabel(f'{price_col} (€)')
                plt.xticks(rotation=45, ha='right')

            elif chart_type == "market":
                # Existing code for market chart...
                print("[DEBUG] Processing 'market' chart")
                if 'Marché' in self.df.columns:
                    market_col = 'Marché'
                elif 'Marché de vente' in self.df.columns:
                    market_col = 'Marché de vente'
                else:
                    print("[DEBUG] Market column not found")
                    messagebox.showinfo("Information", "Market column not found.")
                    self.close_chart_window(window_id)
                    return

                if 'Prix recommandé' in self.df.columns:
                    price_col = 'Prix recommandé'
                elif 'Prix Final (€)' in self.df.columns:
                    price_col = 'Prix Final (€)'
                else:
                    price_col = self.df.select_dtypes(include=['number']).columns[1]

                data = self.df.groupby(market_col)[price_col].mean().sort_values(ascending=False)
                sns.barplot(x=data.index, y=data.values, ax=ax)
                title = f'Average Price by Market ({price_col})'
                ax.set_xlabel('Market')
                ax.set_ylabel(f'{price_col} (€)')
                plt.xticks(rotation=45, ha='right')

            elif chart_type == "demand":
                # Existing code for demand chart...
                print("[DEBUG] Processing 'demand' chart")
                demand_col = None
                for col in self.df.columns:
                    if 'demande' in col.lower() or 'marché' in col.lower():
                        if self.df[col].dtype in ['int64', 'float64']:
                            demand_col = col
                            break

                if not demand_col:
                    print("[DEBUG] Demand column not found")
                    messagebox.showinfo("Information", "Demand column not found.")
                    self.close_chart_window(window_id)
                    return

                sns.histplot(self.df[demand_col], bins=10, kde=True, ax=ax)
                title = f'Market Demand Distribution ({demand_col})'
                ax.set_xlabel('Demand')
                ax.set_ylabel('Number of artworks')

            elif chart_type == "time":
                # Existing code for time chart...
                print("[DEBUG] Processing 'time' chart")
                date_col = None
                for col in self.df.columns:
                    if 'date' in col.lower():
                        date_col = col
                        break

                if not date_col:
                    print("[DEBUG] Date column not found")
                    messagebox.showinfo("Information", "Date column not found.")
                    self.close_chart_window(window_id)
                    return

                try:
                    self.df[date_col] = pd.to_datetime(self.df[date_col], errors='coerce')

                    if 'Prix recommandé' in self.df.columns:
                        price_col = 'Prix recommandé'
                    elif 'Prix Final (€)' in self.df.columns:
                        price_col = 'Prix Final (€)'
                    else:
                        price_col = self.df.select_dtypes(include=['number']).columns[1]

                    monthly_data = self.df.dropna(subset=[date_col]).groupby(
                        pd.Grouper(key=date_col, freq='ME'))[price_col].mean()

                    if len(monthly_data) <= 1:
                        print("[DEBUG] Not enough time data points")
                        messagebox.showinfo("Information",
                                            "Not enough time data points for meaningful visualization.")

                    monthly_data.plot(marker='o', ax=ax)
                    title = f'Price Trends Over Time ({price_col})'
                    ax.set_xlabel('Date')
                    ax.set_ylabel(f'{price_col} (€)')
                except Exception as e:
                    print(f"[DEBUG] Date conversion error: {e}")
                    messagebox.showinfo("Information", f"Date conversion error: {e}")
                    self.close_chart_window(window_id)
                    return

            # NEW CHART TYPES
            elif chart_type == "cost_breakdown":
                print("[DEBUG] Processing 'cost_breakdown' chart")
                # Find cost columns
                cost_cols = [col for col in self.df.columns if 'coût' in col.lower() or 'cost' in col.lower()]

                if not cost_cols:
                    print("[DEBUG] No cost columns found")
                    messagebox.showinfo("Information", "Cost columns not found.")
                    self.close_chart_window(window_id)
                    return

                print(f"[DEBUG] Found cost columns: {cost_cols}")

                # Create pie chart of average costs
                cost_data = self.df[cost_cols].mean()
                ax.pie(cost_data, labels=cost_data.index, autopct='%1.1f%%', startangle=90)
                ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
                title = 'Average Cost Breakdown'

            elif chart_type == "cost_vs_price":
                print("[DEBUG] Processing 'cost_vs_price' chart")
                # Calculate total cost and compare to price
                cost_cols = [col for col in self.df.columns if 'coût' in col.lower() or 'cost' in col.lower()]

                if not cost_cols:
                    print("[DEBUG] No cost columns found")
                    messagebox.showinfo("Information", "Cost columns not found.")
                    self.close_chart_window(window_id)
                    return

                # Calculate total cost
                self.df['Total Cost'] = self.df[cost_cols].sum(axis=1)

                if 'Prix Final (€)' in self.df.columns:
                    price_col = 'Prix Final (€)'
                elif 'Prix recommandé' in self.df.columns:
                    price_col = 'Prix recommandé'
                else:
                    print("[DEBUG] No price column found")
                    messagebox.showinfo("Information", "Price column not found.")
                    self.close_chart_window(window_id)
                    return

                # Calculate profit margin
                self.df['Margin'] = (self.df[price_col] - self.df['Total Cost']) / self.df[price_col] * 100

                # Create scatter plot with regression line
                sns.regplot(x='Total Cost', y=price_col, data=self.df, scatter_kws={"alpha": 0.5}, ax=ax)
                title = 'Total Cost vs Final Price'
                ax.set_xlabel('Total Cost (€)')
                ax.set_ylabel('Final Price (€)')

            elif chart_type == "price_vs_area":
                print("[DEBUG] Processing 'price_vs_area' chart")
                # Calculate area and compare to price
                if 'Longueur (cm)' in self.df.columns and 'Largeur (cm)' in self.df.columns:
                    self.df['Area (cm²)'] = self.df['Longueur (cm)'] * self.df['Largeur (cm)']

                    if 'Prix Final (€)' in self.df.columns:
                        price_col = 'Prix Final (€)'
                    elif 'Prix recommandé' in self.df.columns:
                        price_col = 'Prix recommandé'
                    else:
                        price_col = self.df.select_dtypes(include=['number']).columns[1]

                    sns.regplot(x='Area (cm²)', y=price_col, data=self.df, scatter_kws={"alpha": 0.5}, ax=ax)
                    title = 'Area vs Price'
                    ax.set_xlabel('Area (cm²)')
                    ax.set_ylabel(f'{price_col} (€)')
                else:
                    print("[DEBUG] Dimension columns not found")
                    messagebox.showinfo("Information", "Dimension columns not found.")
                    self.close_chart_window(window_id)
                    return

            elif chart_type == "price_vs_volume":
                print("[DEBUG] Processing 'price_vs_volume' chart")
                # Calculate volume and compare to price
                if all(col in self.df.columns for col in ['Longueur (cm)', 'Largeur (cm)', 'Hauteur (cm)']):
                    self.df['Volume (cm³)'] = self.df['Longueur (cm)'] * self.df['Largeur (cm)'] * self.df['Hauteur (cm)']

                    if 'Prix Final (€)' in self.df.columns:
                        price_col = 'Prix Final (€)'
                    elif 'Prix recommandé' in self.df.columns:
                        price_col = 'Prix recommandé'
                    else:
                        price_col = self.df.select_dtypes(include=['number']).columns[1]

                    sns.regplot(x='Volume (cm³)', y=price_col, data=self.df, scatter_kws={"alpha": 0.5}, ax=ax)
                    title = 'Volume vs Price'
                    ax.set_xlabel('Volume (cm³)')
                    ax.set_ylabel(f'{price_col} (€)')
                else:
                    print("[DEBUG] 3D dimension columns not found")
                    messagebox.showinfo("Information", "3D dimension columns not found.")
                    self.close_chart_window(window_id)
                    return

            elif chart_type == "artist_comparison":
                print("[DEBUG] Processing 'artist_comparison' chart")
                # Compare prices by artist
                if 'Artiste' in self.df.columns:
                    artist_col = 'Artiste'
                else:
                    artist_col = None
                    for col in self.df.columns:
                        if 'artiste' in col.lower() or 'artist' in col.lower():
                            artist_col = col
                            break

                if not artist_col:
                    print("[DEBUG] Artist column not found")
                    messagebox.showinfo("Information", "Artist column not found.")
                    self.close_chart_window(window_id)
                    return

                if 'Prix Final (€)' in self.df.columns:
                    price_col = 'Prix Final (€)'
                elif 'Prix recommandé' in self.df.columns:
                    price_col = 'Prix recommandé'
                else:
                    price_col = self.df.select_dtypes(include=['number']).columns[1]

                # Get the top 10 artists by average price
                top_artists = self.df.groupby(artist_col)[price_col].mean().nlargest(10).index

                # Filter dataframe to only include these artists
                artist_df = self.df[self.df[artist_col].isin(top_artists)]

                # Create boxplot
                sns.boxplot(x=artist_col, y=price_col, data=artist_df, ax=ax)
                title = 'Price Comparison by Artist (Top 10)'
                ax.set_xlabel('Artist')
                ax.set_ylabel(f'{price_col} (€)')
                plt.xticks(rotation=45, ha='right')

            # NEW AI PRICE COMPARISON CHARTS
            elif chart_type == "ai_price_comparison":
                print("[DEBUG] Processing 'ai_price_comparison' chart")
                
                # Find calculated price and AI recommendation columns
                calc_price_col = next((col for col in self.df.columns if 'final price' in col.lower() or 'prix final' in col.lower() or 'prix calculé' in col.lower()), None)
                ai_price_col = next((col for col in self.df.columns if 'ai price' in col.lower() or 'gemini_price' in col.lower() or 'ai price recommendation' in col.lower()), None)
                
                if not calc_price_col or not ai_price_col:
                    print(f"[DEBUG] Price columns not found: calc_price_col={calc_price_col}, ai_price_col={ai_price_col}")
                    messagebox.showinfo("Information", "Could not find calculated price or AI price recommendation columns.")
                    self.close_chart_window(window_id)
                    return
                
                # Extract AI price recommendations which often come with text
                try:
                    # Try to extract numeric values from AI price recommendations
                    # This handles cases where the AI gives ranges or textual descriptions
                    ai_prices = []
                    for price in self.df[ai_price_col]:
                        if isinstance(price, str):
                            # Try to extract a price range or single price
                            import re
                            matches = re.findall(r'(\d+(?:[.,]\d+)?)', price.replace(' ', ''))
                            if matches:
                                # If multiple numbers found, take the average 
                                # (assuming it might be a range like "100-200€")
                                values = [float(match.replace(',', '.')) for match in matches]
                                ai_prices.append(sum(values) / len(values))
                            else:
                                ai_prices.append(None)
                        else:
                            ai_prices.append(price)
                    
                    # Create a new column with extracted numeric values
                    self.df['AI Price (Numeric)'] = ai_prices
                    
                    # Create a new dataframe with only rows that have both prices
                    compare_df = self.df.dropna(subset=['AI Price (Numeric)', calc_price_col])
                    
                    if len(compare_df) < 2:
                        print("[DEBUG] Not enough data points with both prices")
                        messagebox.showinfo("Information", "Not enough data with both calculated and AI prices for comparison.")
                        self.close_chart_window(window_id)
                        return
                    
                    # Create a scatter plot with perfect correlation line for reference
                    max_price = max(compare_df['AI Price (Numeric)'].max(), compare_df[calc_price_col].max()) * 1.1
                    min_price = min(compare_df['AI Price (Numeric)'].min(), compare_df[calc_price_col].min()) * 0.9
                    
                    # Plot the reference line (perfect correlation)
                    ax.plot([min_price, max_price], [min_price, max_price], 'r--', alpha=0.7, label="Perfect match")
                    
                    # Plot the actual data points
                    sns.scatterplot(x='AI Price (Numeric)', y=calc_price_col, data=compare_df, alpha=0.7, ax=ax)
                    
                    # Add a regression line to show correlation
                    sns.regplot(x='AI Price (Numeric)', y=calc_price_col, data=compare_df, 
                               scatter=False, ci=None, line_kws={"color":"blue", "alpha":0.5}, ax=ax)
                    
                    # Calculate correlation coefficient
                    corr = compare_df['AI Price (Numeric)'].corr(compare_df[calc_price_col])
                    
                    title = f'AI vs Calculated Price Comparison (Correlation: {corr:.2f})'
                    ax.set_xlabel('AI Recommended Price (€)')
                    ax.set_ylabel('Calculated Price (€)')
                    
                    # Set equal axis limits for better visualization
                    ax.set_xlim(min_price, max_price)
                    ax.set_ylim(min_price, max_price)
                    ax.legend()
                    
                except Exception as e:
                    print(f"[DEBUG] Error processing AI prices: {e}")
                    import traceback
                    traceback.print_exc()
                    messagebox.showinfo("Information", f"Error processing AI price data: {e}")
                    self.close_chart_window(window_id)
                    return

            elif chart_type == "ai_price_by_type":
                print("[DEBUG] Processing 'ai_price_by_type' chart")
                
                # Find product type column
                type_col = next((col for col in self.df.columns if 'type' in col.lower() or 'produit' in col.lower()), None)
                calc_price_col = next((col for col in self.df.columns if 'final price' in col.lower() or 'prix final' in col.lower() or 'prix calculé' in col.lower()), None)
                ai_price_col = next((col for col in self.df.columns if 'ai price' in col.lower() or 'gemini_price' in col.lower() or 'ai price recommendation' in col.lower()), None)
                
                if not type_col or not calc_price_col or not ai_price_col:
                    print(f"[DEBUG] Required columns not found: type={type_col}, calc_price={calc_price_col}, ai_price={ai_price_col}")
                    messagebox.showinfo("Information", "Could not find required columns for AI price by type visualization.")
                    self.close_chart_window(window_id)
                    return
                
                try:
                    # Extract numeric values from AI price recommendations
                    ai_prices = []
                    for price in self.df[ai_price_col]:
                        if isinstance(price, str):
                            # Try to extract a price range or single price
                            import re
                            matches = re.findall(r'(\d+(?:[.,]\d+)?)', price.replace(' ', ''))
                            if matches:
                                # If multiple numbers found, take the average 
                                values = [float(match.replace(',', '.')) for match in matches]
                                ai_prices.append(sum(values) / len(values))
                            else:
                                ai_prices.append(None)
                        else:
                            ai_prices.append(price)
                    
                    # Create a new column with extracted numeric values
                    self.df['AI Price (Numeric)'] = ai_prices
                    
                    # Group by product type and calculate average AI and calculated prices
                    grouped = self.df.groupby(type_col).agg({
                        'AI Price (Numeric)': 'mean',
                        calc_price_col: 'mean'
                    }).reset_index()
                    
                    # Filter out groups with missing values
                    grouped = grouped.dropna()
                    
                    if len(grouped) < 2:
                        print("[DEBUG] Not enough product types with both prices")
                        messagebox.showinfo("Information", "Not enough product types with both calculated and AI prices.")
                        self.close_chart_window(window_id)
                        return
                    
                    # Get the product types sorted by calculated price
                    product_types = grouped.sort_values(calc_price_col, ascending=False)[type_col].tolist()
                    
                    # Prepare data for grouped bar chart
                    ai_prices = [grouped[grouped[type_col] == t]['AI Price (Numeric)'].values[0] for t in product_types]
                    calc_prices = [grouped[grouped[type_col] == t][calc_price_col].values[0] for t in product_types]
                    
                    # Create x positions
                    x = range(len(product_types))
                    width = 0.35
                    
                    # Create bar chart
                    ax.bar([i - width/2 for i in x], calc_prices, width, label='Calculated Price')
                    ax.bar([i + width/2 for i in x], ai_prices, width, label='AI Price')
                    
                    # Set labels
                    ax.set_xlabel('Product Type')
                    ax.set_ylabel('Average Price (€)')
                    ax.set_title('Calculated vs AI Price by Product Type')
                    ax.set_xticks(x)
                    ax.set_xticklabels(product_types, rotation=45, ha='right')
                    ax.legend()
                    
                    # Add percentage difference labels
                    for i in range(len(product_types)):
                        calc = calc_prices[i]
                        ai = ai_prices[i]
                        diff_pct = ((ai - calc) / calc) * 100
                        ax.annotate(f"{diff_pct:.1f}%", 
                                  xy=(i, max(calc, ai) + 50),
                                  ha='center', va='bottom',
                                  color='green' if diff_pct >= 0 else 'red',
                                  fontweight='bold')
                    
                    title = 'Calculated vs AI Price by Product Type'
                    
                except Exception as e:
                    print(f"[DEBUG] Error processing AI price by type: {e}")
                    import traceback
                    traceback.print_exc()
                    messagebox.showinfo("Information", f"Error processing AI price by type data: {e}")
                    self.close_chart_window(window_id)
                    return

            else:
                print(f"[DEBUG] Unknown chart type: {chart_type}")
                messagebox.showinfo("Information", f"Unknown chart type: {chart_type}")
                self.close_chart_window(window_id)
                return

            # Set title on the plot
            ax.set_title(title)
            plt.tight_layout()

            # Create chart window contents
            frame = ttk.Frame(chart_window, padding=10)
            frame.pack(fill=tk.BOTH, expand=True)

            # Add title label - use the title variable set within each chart type
            title_label = ttk.Label(frame, text=title, font=("Arial", 14, "bold"), style='Title.TLabel')
            title_label.pack(pady=5)

            # Embed the chart in the new window
            canvas = FigureCanvasTkAgg(fig, master=frame)
            canvas.draw()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # Add toolbar for interactive features
            from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk
            toolbar = NavigationToolbar2Tk(canvas, frame)
            toolbar.update()
            canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

            # Add save and close buttons
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(pady=10, fill=tk.X)

            save_btn = ttk.Button(btn_frame, text="Save Chart",
                                  command=lambda: self.save_chart(fig), style='Secondary.TButton') # Use Secondary style
            save_btn.pack(side=tk.LEFT, padx=5)

            close_btn = ttk.Button(btn_frame, text="Close",
                                   command=lambda id=window_id: self.close_chart_window(id), style='Outline.TButton') # Use Outline style
            close_btn.pack(side=tk.RIGHT, padx=5)

            print(f"[DEBUG] Chart successfully created and displayed")

            # Update status in main window
            self.status_var.set(f"Visualization created: {title}")

        except Exception as e:
            error_msg = f"Error creating chart: {e}"
            print(f"[DEBUG] {error_msg}")
            import traceback
            traceback.print_exc()
            messagebox.showerror("Error", error_msg)

            # Close chart window if it exists
            if 'window_id' in locals() and window_id in self.chart_windows:
                self.close_chart_window(window_id)

    def close_chart_window(self, window_id):
        """Close a chart window and remove it from tracking"""
        if window_id in self.chart_windows:
            print(f"[DEBUG] Closing chart window: {window_id}")
            self.chart_windows[window_id].destroy()
            del self.chart_windows[window_id]
        else:
            print(f"[DEBUG] Window ID not found: {window_id}")

    def save_chart(self, fig):
        """Save the chart to a file"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("All files", "*.*")],
                title="Save Chart"
            )
            if file_path:
                fig.savefig(file_path, dpi=300, bbox_inches='tight')
                print(f"[DEBUG] Chart saved to: {file_path}")
                messagebox.showinfo("Success", f"Chart saved as:\n{file_path}")
        except Exception as e:
            print(f"[DEBUG] Error saving chart: {e}")
            messagebox.showerror("Error", f"Unable to save chart: {e}")

    def apply_filter(self):
        """Apply filter to the dataframe"""
        if self.df is None or self.csv_path is None:
            return

        filter_type = self.filter_var.get()
        filter_value = self.filter_entry.get().strip()

        # Make a copy of the original dataframe
        try:
            original_df = pd.read_csv(self.csv_path)

            # Add index/order column to original data
            original_df.insert(0, "Order", range(1, len(original_df) + 1))

            if filter_type == "All" or not filter_value:
                self.df = original_df
            elif filter_type == "Type":
                # Try to find appropriate column
                if 'Type de produit' in original_df.columns:
                    self.df = original_df[original_df['Type de produit'].str.contains(filter_value, case=False, na=False)]
                elif 'Type' in original_df.columns:
                    self.df = original_df[original_df['Type'].str.contains(filter_value, case=False, na=False)]
            elif filter_type == "Artist":
                # Try to find appropriate column
                if 'Artiste' in original_df.columns:
                    self.df = original_df[original_df['Artiste'].str.contains(filter_value, case=False, na=False)]
                elif 'Nom de l\'artiste' in original_df.columns:
                    self.df = original_df[original_df['Nom de l\'artiste'].str.contains(filter_value, case=False, na=False)]
            elif filter_type == "Market":
                # Try to find appropriate column
                if 'Marché' in original_df.columns:
                    self.df = original_df[original_df['Marché'].str.contains(filter_value, case=False, na=False)]
                elif 'Marché de vente' in original_df.columns:
                    self.df = original_df[original_df['Marché de vente'].str.contains(filter_value, case=False, na=False)]

            # Update the treeview
            self.update_treeview()

            # Update status
            self.status_var.set(f"Filter applied: {filter_type} = '{filter_value}' - {len(self.df)} records")

        except Exception as e:
            messagebox.showerror("Error", f"Error applying filter: {e}")

    def reset_filter(self):
        """Reset the filter and show all data"""
        if self.csv_path:
            # Reload original data
            original_df = pd.read_csv(self.csv_path)

            # Add index/order column
            original_df.insert(0, "Order", range(1, len(original_df) + 1))

            self.df = original_df
            self.update_treeview()
            self.status_var.set(f"Filters reset - {len(self.df)} records")

            # Clear filter entry
            self.filter_entry.delete(0, tk.END)
            self.filter_combobox.set("All")            # Reset sorting
            self.sort_by = None
            self.sort_ascending = True
            
    def open_gemini_data_view(self):
        """Open an external window with a table showing all Gemini API interactions"""
        try:
            # Import here to avoid circular imports
            import gemini_api
            
            # Fetch all Gemini interactions
            interactions = gemini_api.get_all_interactions()
            
            if not interactions:
                messagebox.showinfo("Information", "No Gemini API interactions recorded yet.")
                return
                
            # Create a new window
            gemini_window = tk.Toplevel(self.root)
            gemini_window.title("Gemini Data View")
            gemini_window.geometry("1200x700")
            
            # Create a frame for the table
            frame = ttk.Frame(gemini_window, padding=10)
            frame.pack(fill=tk.BOTH, expand=True)
            
            # Add a title
            title_label = ttk.Label(
                frame, 
                text="Gemini API Interactions Throughout User Journey", 
                font=("Arial", 14, "bold"), 
                style='Title.TLabel'
            )
            title_label.pack(pady=5)
            
            # Add a description
            description = ttk.Label(
                frame, 
                text="This table shows all interactions with the Gemini AI model during the pricing calculation process.",
                style='Muted.TLabel'
            )
            description.pack(pady=(0, 10))
            
            # Create a frame for the treeview and scrollbar
            tree_frame = ttk.Frame(frame)
            tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
            
            # Create scrollbars
            vscrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
            vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            
            hscrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
            hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
            
            # Create the treeview
            tree = ttk.Treeview(
                tree_frame,
                yscrollcommand=vscrollbar.set,
                xscrollcommand=hscrollbar.set,
                show="headings"
            )
            
            # Configure scrollbars
            vscrollbar.config(command=tree.yview)
            hscrollbar.config(command=tree.xview)
            
            # Pack the treeview
            tree.pack(fill=tk.BOTH, expand=True)
            
            # Configure columns for the treeview
            columns = ['id', 'timestamp', 'request_type', 'prompt', 'response', 'duration']
            column_headings = ['ID', 'Timestamp', 'Request Type', 'Prompt', 'Response', 'Duration (sec)']
            
            tree['columns'] = columns
            
            # Configure column headings and widths
            column_widths = {
                'id': 60,
                'timestamp': 150,
                'request_type': 180,
                'prompt': 280,
                'response': 280,
                'duration': 100
            }
            
            for col, heading in zip(columns, column_headings):
                width = column_widths.get(col, 150)
                tree.column(col, width=width, minwidth=50)
                tree.heading(col, text=heading)
            
            # Insert data into the treeview
            for interaction in interactions:
                # Format the prompt and response for display (truncate if too long)
                prompt = interaction["prompt"]
                if len(prompt) > 200:
                    prompt = prompt[:197] + "..."
                
                response = interaction["response"]
                if len(response) > 200:
                    response = response[:197] + "..."
                
                # Format duration to 2 decimal places
                duration = f"{interaction['duration']:.2f}"
                
                # Display request type in a more user-friendly format
                request_type = interaction["request_type"].replace("_", " ").title()
                
                values = [
                    interaction["id"],
                    interaction["timestamp"],
                    request_type,
                    prompt,
                    response,
                    duration
                ]
                
                item_id = tree.insert('', 'end', values=values)
                
                # Set tags for different request types for color coding
                if "price" in interaction["request_type"].lower():
                    tree.item(item_id, tags=('price',))
                elif "validation" in interaction["request_type"].lower():
                    tree.item(item_id, tags=('validation',))
                elif "artist" in interaction["request_type"].lower():
                    tree.item(item_id, tags=('artist',))
            
            # Configure tag colors
            tree.tag_configure('price', background='#e6f7ff')
            tree.tag_configure('validation', background='#f6ffed')
            tree.tag_configure('artist', background='#fff7e6')
            
            # Add a details view frame
            details_frame = ttk.LabelFrame(frame, text="Interaction Details", padding=10)
            details_frame.pack(fill=tk.X, expand=False, pady=10)
            
            # Add text widgets for full prompt and response
            details_container = ttk.Frame(details_frame)
            details_container.pack(fill=tk.X, expand=True)
            details_container.columnconfigure(0, weight=1)
            details_container.columnconfigure(1, weight=1)
            
            # Prompt details
            prompt_frame = ttk.LabelFrame(details_container, text="Full Prompt")
            prompt_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
            
            prompt_text = tk.Text(prompt_frame, height=8, wrap="word")
            prompt_scroll = ttk.Scrollbar(prompt_frame, command=prompt_text.yview)
            prompt_text.configure(yscrollcommand=prompt_scroll.set)
            prompt_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            prompt_text.pack(fill=tk.BOTH, expand=True)
            prompt_text.config(state=tk.DISABLED)
            
            # Response details
            response_frame = ttk.LabelFrame(details_container, text="Full Response")
            response_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)
            
            response_text = tk.Text(response_frame, height=8, wrap="word")
            response_scroll = ttk.Scrollbar(response_frame, command=response_text.yview)
            response_text.configure(yscrollcommand=response_scroll.set)
            response_scroll.pack(side=tk.RIGHT, fill=tk.Y)
            response_text.pack(fill=tk.BOTH, expand=True)
            response_text.config(state=tk.DISABLED)
            
            # Function to display full details when a row is selected
            def on_tree_select(event):
                selected_items = tree.selection()
                if not selected_items:
                    return
                    
                # Get the selected item's ID
                item = selected_items[0]
                item_id = tree.item(item)['values'][0]
                
                # Find the corresponding interaction
                interaction = next((i for i in interactions if i["id"] == item_id), None)
                if not interaction:
                    return
                
                # Update the detail view
                prompt_text.config(state=tk.NORMAL)
                prompt_text.delete(1.0, tk.END)
                prompt_text.insert(tk.END, interaction["prompt"])
                prompt_text.config(state=tk.DISABLED)
                
                response_text.config(state=tk.NORMAL)
                response_text.delete(1.0, tk.END)
                response_text.insert(tk.END, interaction["response"])
                response_text.config(state=tk.DISABLED)
            
            # Bind the selection event
            tree.bind("<<TreeviewSelect>>", on_tree_select)
            
            # Add filter controls at the top
            filter_frame = ttk.Frame(frame)
            filter_frame.pack(fill=tk.X, pady=(5, 10))
            
            # Add request type filter
            ttk.Label(filter_frame, text="Filter by request type:").pack(side=tk.LEFT, padx=(0, 5))
            
            # Get unique request types
            request_types = sorted(set(i["request_type"] for i in interactions))
            request_types = ["All"] + [t.replace("_", " ").title() for t in request_types]
            
            filter_var = tk.StringVar()
            filter_var.set("All")
            
            filter_combo = ttk.Combobox(filter_frame, textvariable=filter_var, values=request_types, state="readonly", width=25)
            filter_combo.pack(side=tk.LEFT, padx=5)
            
            # Function to apply the filter
            def apply_filter(*args):
                selected_type = filter_var.get()
                
                # Clear the tree
                for item in tree.get_children():
                    tree.delete(item)
                
                # Filter interactions
                filtered_interactions = interactions
                if selected_type != "All":
                    # Convert the selected type back to the original format
                    original_type = selected_type.lower().replace(" ", "_")
                    filtered_interactions = [i for i in interactions if i["request_type"] == original_type]
                
                # Re-populate the tree
                for interaction in filtered_interactions:
                    prompt = interaction["prompt"]
                    if len(prompt) > 200:
                        prompt = prompt[:197] + "..."
                    
                    response = interaction["response"]
                    if len(response) > 200:
                        response = response[:197] + "..."
                    
                    duration = f"{interaction['duration']:.2f}"
                    request_type = interaction["request_type"].replace("_", " ").title()
                    
                    values = [
                        interaction["id"],
                        interaction["timestamp"],
                        request_type,
                        prompt,
                        response,
                        duration
                    ]
                    
                    item_id = tree.insert('', 'end', values=values)
                    
                    # Set tags for different request types
                    if "price" in interaction["request_type"].lower():
                        tree.item(item_id, tags=('price',))
                    elif "validation" in interaction["request_type"].lower():
                        tree.item(item_id, tags=('validation',))
                    elif "artist" in interaction["request_type"].lower():
                        tree.item(item_id, tags=('artist',))
            
            # Trace the filter variable
            filter_var.trace("w", apply_filter)
            
            # Add status bar
            status_bar = ttk.Label(frame, text=f"Total interactions: {len(interactions)}", relief=tk.SUNKEN, anchor=tk.W)
            status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
            
            # Add buttons at the bottom
            btn_frame = ttk.Frame(frame)
            btn_frame.pack(pady=10, fill=tk.X)
            
            # Export button
            export_btn = ttk.Button(
                btn_frame, 
                text="Export", 
                command=lambda: self.export_gemini_data(tree), 
                style='Secondary.TButton'
            )
            export_btn.pack(side=tk.LEFT, padx=5)
            
            # Close button
            close_btn = ttk.Button(
                btn_frame, 
                text="Close", 
                command=gemini_window.destroy, 
                style='Outline.TButton'            )
            close_btn.pack(side=tk.RIGHT, padx=5)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open Gemini Data View: {e}")
    
    def export_gemini_data(self, tree):
        """Export the Gemini data view to a CSV file"""
        try:
            # Get column IDs and headers
            columns = tree['columns']
            headers = [tree.heading(col)["text"] for col in columns]
            
            # Get data from treeview
            items = tree.get_children()
            data = []
            
            for item in items:
                values = tree.item(item)['values']
                data.append(values)
            
            # Create DataFrame
            export_df = pd.DataFrame(data, columns=headers)
            
            # Save to file
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"gemini_interactions_{timestamp}.csv"
            
            filepath = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="Export Gemini Data",
                initialfile=default_filename
            )
            
            if filepath:
                if filepath.lower().endswith('.csv'):
                    export_df.to_csv(filepath, index=False)
                elif filepath.lower().endswith('.xlsx'):
                    try:
                        export_df.to_excel(filepath, index=False)
                    except ImportError:
                        messagebox.showwarning("Warning", "Excel export requires the openpyxl library. Saving as CSV instead.")
                        filepath = filepath.replace('.xlsx', '.csv')
                        export_df.to_csv(filepath, index=False)
                    else:
                        # Default to CSV
                        if not filepath.lower().endswith('.csv'):
                            filepath += '.csv'
                        export_df.to_csv(filepath, index=False)                    
                messagebox.showinfo("Success", f"Gemini data exported to {filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Error exporting Gemini data: {e}")

# Function to open Gemini Data View directly from other modules
def open_gemini_data_view(root):
    """Open the Gemini Data View window from any module"""
    try:
        # Import here to avoid circular imports
        import gemini_api
        
        # Fetch all Gemini interactions
        interactions = gemini_api.get_all_interactions()
        
        if not interactions:
            messagebox.showinfo("Information", "No Gemini AI interactions recorded yet.")
            return
            
        # Create a new window
        gemini_window = tk.Toplevel(root)
        gemini_window.title("Gemini Data View")
        gemini_window.geometry("1200x700")
        
        # Create a frame for the table
        frame = ttk.Frame(gemini_window, padding=10)
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Add a title
        title_label = ttk.Label(
            frame, 
            text="Gemini API Interactions Throughout User Journey", 
            font=("Arial", 14, "bold"), 
            style='Title.TLabel'
        )
        title_label.pack(pady=5)
        
        # Add a description
        description = ttk.Label(
            frame, 
            text="This table shows all interactions with the Gemini AI model during the pricing calculation process.",
            style='Muted.TLabel'
        )
        description.pack(pady=(0, 10))
        
        # Create a frame for the treeview and scrollbar
        tree_frame = ttk.Frame(frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Create scrollbars
        vscrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        hscrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Create the treeview
        tree = ttk.Treeview(
            tree_frame,
            yscrollcommand=vscrollbar.set,
            xscrollcommand=hscrollbar.set,
            show="headings"
        )
        
        # Configure scrollbars
        vscrollbar.config(command=tree.yview)
        hscrollbar.config(command=tree.xview)
        
        # Pack the treeview
        tree.pack(fill=tk.BOTH, expand=True)
        
        # Configure columns for the treeview
        columns = ['id', 'timestamp', 'request_type', 'prompt', 'response', 'duration']
        column_headings = ['ID', 'Timestamp', 'Request Type', 'Prompt', 'Response', 'Duration (sec)']
        
        tree['columns'] = columns
        
        # Configure column headings and widths
        column_widths = {
            'id': 60,
            'timestamp': 150,
            'request_type': 180,
            'prompt': 280,
            'response': 280,
            'duration': 100
        }
        
        for col, heading in zip(columns, column_headings):
            width = column_widths.get(col, 150)
            tree.column(col, width=width, minwidth=50)
            tree.heading(col, text=heading)
        
        # Insert data into the treeview
        for interaction in interactions:
            # Format the prompt and response for display (truncate if too long)
            prompt = interaction["prompt"]
            if len(prompt) > 200:
                prompt = prompt[:197] + "..."
            
            response = interaction["response"]
            if len(response) > 200:
                response = response[:197] + "..."
            
            # Format duration to 2 decimal places
            duration = f"{interaction['duration']:.2f}"
            
            # Display request type in a more user-friendly format
            request_type = interaction["request_type"].replace("_", " ").title()
            
            values = [
                interaction["id"],
                interaction["timestamp"],
                request_type,
                prompt,
                response,
                duration
            ]
            
            item_id = tree.insert('', 'end', values=values)
            
            # Set tags for different request types for color coding
            if "price" in interaction["request_type"].lower():
                tree.item(item_id, tags=('price',))
            elif "validation" in interaction["request_type"].lower():
                tree.item(item_id, tags=('validation',))
            elif "artist" in interaction["request_type"].lower():
                tree.item(item_id, tags=('artist',))
        
        # Configure tag colors
        tree.tag_configure('price', background='#e6f7ff')
        tree.tag_configure('validation', background='#f6ffed')
        tree.tag_configure('artist', background='#fff7e6')
        
        # Add a details view frame
        details_frame = ttk.LabelFrame(frame, text="Interaction Details", padding=10)
        details_frame.pack(fill=tk.X, expand=False, pady=10)
        
        # Add text widgets for full prompt and response
        details_container = ttk.Frame(details_frame)
        details_container.pack(fill=tk.X, expand=True)
        details_container.columnconfigure(0, weight=1)
        details_container.columnconfigure(1, weight=1)
        
        # Prompt details
        prompt_frame = ttk.LabelFrame(details_container, text="Full Prompt")
        prompt_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        
        prompt_text = tk.Text(prompt_frame, height=8, wrap="word")
        prompt_scroll = ttk.Scrollbar(prompt_frame, command=prompt_text.yview)
        prompt_text.configure(yscrollcommand=prompt_scroll.set)
        prompt_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        prompt_text.pack(fill=tk.BOTH, expand=True)
        prompt_text.config(state=tk.DISABLED)
        
        # Response details
        response_frame = ttk.LabelFrame(details_container, text="Full Response")
        response_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)
        
        response_text = tk.Text(response_frame, height=8, wrap="word")
        response_scroll = ttk.Scrollbar(response_frame, command=response_text.yview)
        response_text.configure(yscrollcommand=response_scroll.set)
        response_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        response_text.pack(fill=tk.BOTH, expand=True)
        response_text.config(state=tk.DISABLED)
        
        # Function to display full details when a row is selected
        def on_tree_select(event):
            selected_items = tree.selection()
            if not selected_items:
                return
                
            # Get the selected item's ID
            item = selected_items[0]
            item_id = tree.item(item)['values'][0]
            
            # Find the corresponding interaction
            interaction = next((i for i in interactions if i["id"] == item_id), None)
            if not interaction:
                return
            
            # Update the detail view
            prompt_text.config(state=tk.NORMAL)
            prompt_text.delete(1.0, tk.END)
            prompt_text.insert(tk.END, interaction["prompt"])
            prompt_text.config(state=tk.DISABLED)
            
            response_text.config(state=tk.NORMAL)
            response_text.delete(1.0, tk.END)
            response_text.insert(tk.END, interaction["response"])
            response_text.config(state=tk.DISABLED)
        
        # Bind the selection event
        tree.bind("<<TreeviewSelect>>", on_tree_select)
        
        # Add filter controls at the top
        filter_frame = ttk.Frame(frame)
        filter_frame.pack(fill=tk.X, pady=(5, 10))
        
        # Add request type filter
        ttk.Label(filter_frame, text="Filter by request type:").pack(side=tk.LEFT, padx=(0, 5))
        
        # Get unique request types
        request_types = sorted(set(i["request_type"] for i in interactions))
        request_types = ["All"] + [t.replace("_", " ").title() for t in request_types]
        
        filter_var = tk.StringVar()
        filter_var.set("All")
        
        filter_combo = ttk.Combobox(filter_frame, textvariable=filter_var, values=request_types, state="readonly", width=25)
        filter_combo.pack(side=tk.LEFT, padx=5)
        
        # Function to apply the filter
        def apply_filter(*args):
            selected_type = filter_var.get()
            
            # Clear the tree
            for item in tree.get_children():
                tree.delete(item)
            
            # Filter interactions
            filtered_interactions = interactions
            if selected_type != "All":
                # Convert the selected type back to the original format
                original_type = selected_type.lower().replace(" ", "_")
                filtered_interactions = [i for i in interactions if i["request_type"] == original_type]
            
            # Re-populate the tree
            for interaction in filtered_interactions:
                prompt = interaction["prompt"]
                if len(prompt) > 200:
                    prompt = prompt[:197] + "..."
                
                response = interaction["response"]
                if len(response) > 200:
                    response = response[:197] + "..."
                
                duration = f"{interaction['duration']:.2f}"
                request_type = interaction["request_type"].replace("_", " ").title()
                
                values = [
                    interaction["id"],
                    interaction["timestamp"],
                    request_type,
                    prompt,
                    response,
                    duration
                ]
                
                item_id = tree.insert('', 'end', values=values)
                
                # Set tags for different request types
                if "price" in interaction["request_type"].lower():
                    tree.item(item_id, tags=('price',))
                elif "validation" in interaction["request_type"].lower():
                    tree.item(item_id, tags=('validation',))
                elif "artist" in interaction["request_type"].lower():
                    tree.item(item_id, tags=('artist',))
        
        # Trace the filter variable
        filter_var.trace("w", apply_filter)
        
        # Add status bar
        status_bar = ttk.Label(frame, text=f"Total interactions: {len(interactions)}", relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM, pady=(5, 0))
        
        # Add buttons at the bottom
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=10, fill=tk.X)
          # Export button
        export_btn = ttk.Button(
            btn_frame, 
            text="Export Data", 
            command=lambda: export_data_from_tree(tree),
            style='Secondary.TButton'
        )
        export_btn.pack(side=tk.LEFT, padx=5)
        
        # Close button
        close_btn = ttk.Button(
            btn_frame, 
            text="Close", 
            command=gemini_window.destroy, 
            style='Outline.TButton'
        )
        close_btn.pack(side=tk.RIGHT, padx=5)
        
        # Function to export data from the Gemini Data View
        def export_data_from_tree(tree):
            """Export the Gemini data to CSV"""
            try:
                # Get column IDs and headers
                columns = tree['columns']
                headers = [tree.heading(col)["text"] for col in columns]
                
                # Get data from treeview
                items = tree.get_children()
                data = []
                
                for item in items:
                    values = tree.item(item)['values']
                    data.append(values)
                
                # Create DataFrame
                import pandas as pd
                export_df = pd.DataFrame(data, columns=headers)
                
                # Save to file
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                default_filename = f"gemini_interactions_{timestamp}.csv"
                
                filepath = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")],
                    title="Export Gemini Data",
                    initialfile=default_filename
                )
                
                if filepath:
                    if filepath.lower().endswith('.csv'):
                        export_df.to_csv(filepath, index=False)
                    elif filepath.lower().endswith('.xlsx'):
                        try:
                            export_df.to_excel(filepath, index=False)
                        except ImportError:
                            messagebox.showwarning("Warning", "Excel export requires the openpyxl library. Saving as CSV instead.")
                            filepath = filepath.replace('.xlsx', '.csv')
                            export_df.to_csv(filepath, index=False)
                    else:
                        # Default to CSV
                        if not filepath.lower().endswith('.csv'):
                            filepath += '.csv'
                        export_df.to_csv(filepath, index=False)
                        
                    messagebox.showinfo("Success", f"Gemini data exported to {filepath}")
            
            except Exception as e:
                messagebox.showerror("Error", f"Error exporting Gemini data: {e}")
        
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open Gemini Data View: {e}")
        print(f"Exception details: {traceback.format_exc()}")

if __name__ == "__main__":
    # Make sure the data file exists
    data_utils.initialize_data_file()

    root = tk.Tk()
    app = AdminDashboard(root)
    root.mainloop()
