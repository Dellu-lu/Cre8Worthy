import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import gemini_api
import data_utils
import re
from validation import validate_text_input, validate_numeric_input, validate_type_product, validate_materials, validate_market
from pricing import calculate_price
from tooltip import ToolTip
import logging
import sys

# Configure logging
logger = logging.getLogger("UI")
logger.setLevel(logging.DEBUG)

# Remove all existing handlers to avoid duplicates
for handler in logger.handlers[:]:
    logger.removeHandler(handler)

# Check if handler already exists to avoid duplicate logs
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

class LoadingScreen:
    """Full-screen loading overlay for showing busy state during AI operations"""
    def __init__(self, parent, message="Processing..."):
        self.parent = parent
        
        # Create a semi-transparent overlay frame
        self.overlay = tk.Frame(parent)
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.overlay.configure(bg="#f0f0f0")
        
        # Container for loading elements
        self.container = tk.Frame(self.overlay, bg="#ffffff", bd=2, relief=tk.RAISED)
        self.container.place(relx=0.5, rely=0.5, anchor=tk.CENTER, 
                            relwidth=0.4, relheight=0.3)
        
        # Create the spinner in the container
        self.spinner = LoadingSpinner(self.container, size=60)
        self.spinner.place(relx=0.5, rely=0.35, anchor=tk.CENTER)
        
        # Message label
        self.message_var = tk.StringVar(value=message)
        self.message = tk.Label(self.container, textvariable=self.message_var,
                              font=("Arial", 12), bg="#ffffff")
        self.message.place(relx=0.5, rely=0.7, anchor=tk.CENTER)
        
        # Start the spinner animation
        self.spinner.start()
        
    def update_message(self, message):
        """Update the loading screen message"""
        self.message_var.set(message)
        self.parent.update_idletasks()
    
    def hide(self):
        """Hide the loading screen"""
        self.spinner.stop()
        self.overlay.place_forget()

class LoadingSpinner:
    """Loading spinner widget for showing busy state during operations"""
    def __init__(self, parent, size=30):
        self.parent = parent
        self.size = size
        self.canvas = tk.Canvas(parent, width=size, height=size, bg='white', 
                               highlightthickness=0)
        self.angle = 0
        self.is_running = False
        self.canvas.pack()
    
    def start(self):
        """Start the spinner animation"""
        self.is_running = True
        self.canvas.delete("spinner")
        self._animate()
        return self
    
    def stop(self):
        """Stop the spinner animation"""
        self.is_running = False
        self.canvas.delete("spinner")
        return self
    
    def _animate(self):
        """Draw the spinner animation frame"""
        if not self.is_running:
            return
            
        self.canvas.delete("spinner")
        center = self.size // 2
        radius = (self.size // 2) - 5            # Draw spinner segments with different colors
        for i in range(8):
            angle = self.angle + (i * 45)
            # Use a series of blue shades instead of opacity which might not be supported
            colors = ["#2563eb", "#2563eb", "#3b74ec", "#517eee", "#668fef", "#7c9ff1", "#91b0f3", "#a7c0f5"]
            color = colors[i % len(colors)]
            
            x1 = center + int(radius * 0.6 * (0.5 * (i == 0 or i == 1 or i == 7))) * (1 if i <= 4 else -1)
            y1 = center + int(radius * 0.6 * (0.5 * (i >= 0 and i <= 2))) * (1 if i >= 2 and i <= 6 else -1)
            x2 = center + int(radius * (0.5 * (i == 0 or i == 1 or i == 7))) * (1 if i <= 4 else -1)
            y2 = center + int(radius * (0.5 * (i >= 0 and i <= 2))) * (1 if i >= 2 and i <= 6 else -1)
            
            self.canvas.create_line(
                x1, y1, x2, y2,
                width=3, fill=color, tags="spinner"
            )
        
        self.angle = (self.angle + 30) % 360
        if self.is_running:
            self.parent.after(100, self._animate)

class PricingCalculatorUI:
    def __init__(self, root, icons=None):
        # Store root and icons first - with default value
        self.root = root
        self.icons = icons if icons else {}  # Ensure icons is at least an empty dict

        logger.debug("Initializing PricingCalculatorUI")

        # Initialize variables
        self.error_labels = {}
        self.entries = {}
        self.var_type = tk.StringVar()
        self.var_quality = tk.StringVar()
        self.var_video_type = tk.StringVar()  # For video specification
        self.var_photo_type = tk.StringVar()  # For photography specification
        self.var_custom_type = tk.StringVar()  # For custom product type storage
          # Additional product specification variables - removed painting, sculpture, and installation
        # Only keeping video and photography related variables
        
        self.type_produit = ""  # Main variable to store product type consistently
        self.canvas_saved_selection = []
        self.other_saved_selection = []
        self.duration_frame = None
        self.entry_duration = None
        self.error_duration = None
        self.quality_combo = None
        self.error_quality = None
        self.input_timer = None  # Timer for checking "Other" product type input
        self.last_other_value = ""  # Track last input value to avoid redundant API calls
        self.typing_pause_interval = 1000  # Time in milliseconds to wait after typing stops

        # Create top container frame with proper weight configuration
        self.top_container = ttk.Frame(self.root)
        self.top_container.pack(fill="both", expand=True)
        
        # Configure grid weights for top container
        self.top_container.columnconfigure(0, weight=1)
        self.top_container.rowconfigure(0, weight=1)        # Create main layout
        self.create_main_layout()
        
        # Now call other setup methods
        self.create_artist_section()
        self.create_cost_section()
        self.create_materials_section()
        
        # Bind mousewheel for scrolling
        self.root.bind("<MouseWheel>", self.on_mousewheel)
        self.create_error_section()
        self.create_button_section()
        self.create_result_section()

        # Configure layout - ensure equal weight for columns
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        # Configure layout - give more weight to material and result sections
        self.main_frame.rowconfigure(0, weight=0)  # Header row
        self.main_frame.rowconfigure(1, weight=3)  # Materials row
        self.main_frame.rowconfigure(2, weight=0)  # Error section
        self.main_frame.rowconfigure(3, weight=0)  # Buttons row
        self.main_frame.rowconfigure(4, weight=5)  # Results section (increase weight for more vertical space)
        self.main_frame.rowconfigure(5, weight=0)  # Bottom row (for reset button)

        # Bind the Other type entry field created in create_artist_section
        self.entry_other_type.bind("<FocusOut>", self.update_additional_costs_for_other_type)
        self.var_type.trace("w", self.toggle_other_type_entry)

        # Add label & error tracking for market
        self.error_labels["market"] = ttk.Label(self.artist_frame, text="", style='Error.TLabel') # Use Error style
        self.error_labels["market"].grid(row=1, column=2, sticky="w", padx=5, pady=5)
        
        # Add error label for artist
        self.error_labels["artist"] = ttk.Label(self.artist_frame, text="", style='Error.TLabel') # Use Error style
        self.error_labels["artist"].grid(row=0, column=2, sticky="w", padx=5, pady=5)

    def create_main_layout(self):
        # Create a canvas with scrollbars for scrollable content
        self.main_canvas = tk.Canvas(self.top_container, highlightthickness=0)
        self.main_canvas.pack(fill="both", expand=True, side="left")
        
        # Add vertical scrollbar
        self.vsb = ttk.Scrollbar(self.top_container, orient="vertical", command=self.main_canvas.yview)
        self.vsb.pack(side="right", fill="y")
        
        # Configure canvas to use scrollbar
        self.main_canvas.configure(yscrollcommand=self.vsb.set)
        
        # Create a frame inside the canvas for all content
        self.main_frame = ttk.Frame(self.main_canvas, padding="10")
        
        # Create window in canvas for the main frame
        self.canvas_window = self.main_canvas.create_window((0, 0), window=self.main_frame, anchor="nw", tags="self.main_frame")
        
        # Configure the main frame with proper weights
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=1)  # Artist & Cost section
        self.main_frame.rowconfigure(1, weight=2)  # Materials section (middle)
        self.main_frame.rowconfigure(2, weight=0)  # Error section
        self.main_frame.rowconfigure(3, weight=0)  # Middle divider (where calculate button will be)
        self.main_frame.rowconfigure(4, weight=5)  # Results section (increase weight for more vertical space)
        self.main_frame.rowconfigure(5, weight=0)  # Bottom row (for reset button)
        
        # Bind canvas resize event
        self.main_canvas.bind("<Configure>", self.on_canvas_configure)
        self.main_frame.bind("<Configure>", self.on_frame_configure)

    def create_artist_section(self):
        self.artist_frame = ttk.LabelFrame(self.main_frame, text="Market and Type", padding="10")
        self.artist_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5), pady=5)
        self.artist_frame.columnconfigure(1, weight=1)
        self.artist_frame.rowconfigure(0, weight=1)
        self.artist_frame.rowconfigure(1, weight=1)
        self.artist_frame.rowconfigure(2, weight=1)
        self.artist_frame.rowconfigure(3, weight=1)
        self.artist_frame.rowconfigure(4, weight=1)

        # Artist name with tooltip
        artist_label_frame = ttk.Frame(self.artist_frame)
        artist_label_frame.grid(row=0, column=0, sticky='e', padx=5, pady=5)
        artist_label = ttk.Label(artist_label_frame, text="Artist name:")
        artist_label.pack(side="left")
        artist_info = ttk.Label(artist_label_frame, text=" ℹ", foreground="blue", cursor="question_arrow")
        artist_info.pack(side="left")
        ToolTip(artist_info, "Enter the artist's name. If the artist is recognized, this may influence the price recommendation.")
        
        self.entry_artist = ttk.Entry(self.artist_frame)
        self.entry_artist.grid(row=0, column=1, sticky='ew', padx=5, pady=5)

        # Market with tooltip
        market_label_frame = ttk.Frame(self.artist_frame)
        market_label_frame.grid(row=1, column=0, sticky='e', padx=5, pady=5)
        market_label = ttk.Label(market_label_frame, text="Target market:")
        market_label.pack(side="left")
        market_info = ttk.Label(market_label_frame, text=" ℹ", foreground="blue", cursor="question_arrow")
        market_info.pack(side="left")
        ToolTip(market_info, "Specify the geographical market where the art will be sold. Different markets have different pricing expectations.")
        
        self.entry_market = ttk.Entry(self.artist_frame)
        self.entry_market.grid(row=1, column=1, sticky='ew', padx=5, pady=5)

        # Product type with tooltip
        product_label_frame = ttk.Frame(self.artist_frame)
        product_label_frame.grid(row=2, column=0, sticky="e", padx=5, pady=5)
        product_label = ttk.Label(product_label_frame, text="Product type:")
        product_label.pack(side="left")
        product_info = ttk.Label(product_label_frame, text=" ℹ", foreground="blue", cursor="question_arrow")
        product_info.pack(side="left")
        ToolTip(product_info, "Select the type of art piece. This affects which fields are shown for dimension input and pricing calculations.")
        
        self.type_combo = ttk.Combobox(
            self.artist_frame,
            textvariable=self.var_type,
            values=["Painting", "Sculpture", "Photography", "Video", "Installation", "Other"],
            state="readonly"
        )
        self.type_combo.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        # Create center container for specialty frames
        self.specialty_container = ttk.Frame(self.artist_frame)
        self.specialty_container.grid(row=4, column=0, columnspan=2, sticky="nsew", padx=0, pady=5)
        self.specialty_container.columnconfigure(0, weight=1)  # Center the contents
        self.specialty_container.rowconfigure(0, weight=1)
        self.specialty_container.rowconfigure(1, weight=1)

        # "Other" type entry, properly aligned with other entry fields
        self.other_type_frame = ttk.Frame(self.specialty_container)
        self.other_type_frame.grid(row=2, column=0, sticky="n", pady=5)
        
        # Simple frame like other entry fields
        other_spec_frame = ttk.Frame(self.other_type_frame)
        other_spec_frame.pack(fill="x", expand=True)
        other_spec_frame.columnconfigure(1, weight=1)
        
        # Input field with label and tooltip
        other_label_frame = ttk.Frame(other_spec_frame)
        other_label_frame.grid(row=0, column=0, sticky="e", padx=5, pady=5)
        other_label = ttk.Label(other_label_frame, text="Specify product type:")
        other_label.pack(side="left")
        other_info = ttk.Label(other_label_frame, text=" ℹ", foreground="blue", cursor="question_arrow")
        other_info.pack(side="left")
        ToolTip(other_info, "Enter a custom art type. Gemini AI will analyze if it's a valid artistic product and determine appropriate dimensions.")
        
        self.entry_other_type = ttk.Entry(other_spec_frame, width=30)
        self.entry_other_type.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # Status indicator
        self.typing_status = ttk.Label(other_spec_frame, text="Type and wait for analysis...", foreground="blue")
        self.typing_status.grid(row=1, column=0, columnspan=3, pady=(0, 5))
        
        # Hide frame by default
        self.other_type_frame.grid_forget()        # We've removed painting, sculpture, and installation detail frames
        # Only leaving photography and video specification frames
        
        # Creating placeholders for variables we're keeping for compatibility
        self.painting_spec_frame = None
        self.sculpture_spec_frame = None
        self.installation_spec_frame = None
        
        # These placeholders ensure that any code referencing these frames won't crash
        
        # Photography specification box - centered with better styling
        self.photography_spec_frame = ttk.Frame(self.specialty_container)
        self.photography_spec_frame.grid(row=0, column=0, sticky="n", pady=5)
        
        # Add a proper grouping for photography details
        photo_details_frame = ttk.LabelFrame(self.photography_spec_frame, text="Photography Details", padding="5")
        photo_details_frame.pack(fill="x", expand=True)
        photo_details_frame.columnconfigure(1, weight=1)

        # Photo type selection
        ttk.Label(photo_details_frame, text="Photo Type:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.photo_type_combo = ttk.Combobox(
            photo_details_frame,
            textvariable=self.var_photo_type,
            values=["Physical", "Digital"],
            state="readonly"
        )
        self.photo_type_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # Photo style selection
        ttk.Label(photo_details_frame, text="Style:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.photo_style_combo = ttk.Combobox(
            photo_details_frame,
            values=["Portrait", "Landscape", "Abstract", "Documentary", "Fashion", "Wildlife", "Architecture"],
            state="readonly"
        )
        self.photo_style_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # Connect photo type change to update dimension units
        self.var_photo_type.trace("w", lambda *args: self.update_cost_fields_labels("Photography"))

        # Hide frame by default
        self.photography_spec_frame.grid_forget()
        
        # Video specification box - centered with better styling
        self.video_spec_frame = ttk.Frame(self.specialty_container)
        self.video_spec_frame.grid(row=1, column=0, sticky="n", pady=5)
        
        # Add a proper grouping for video details
        video_details_frame = ttk.LabelFrame(self.video_spec_frame, text="Video Details", padding="5")
        video_details_frame.pack(fill="x", expand=True)
        video_details_frame.columnconfigure(1, weight=1)

        # Video type selection
        ttk.Label(video_details_frame, text="Video Type:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
        self.video_type_combo = ttk.Combobox(
            video_details_frame,
            textvariable=self.var_video_type,
            values=["Short Film", "Animation", "Documentary", "Music Video", "Advertisement", "Educational", "Other"],
            state="readonly"
        )
        self.video_type_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        # Video style selection
        ttk.Label(video_details_frame, text="Style:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
        self.video_style_combo = ttk.Combobox(
            video_details_frame,
            values=["Cinematic", "Animated", "Vlog", "Minimalist", "Abstract", "Vintage", "Modern"],
            state="readonly"
        )
        self.video_style_combo.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        # Connect video type to update duration field visibility
        self.var_video_type.trace("w", lambda *args: self.toggle_video_duration())

        # Hide frame by default
        self.video_spec_frame.grid_forget()
        
        self.var_type.trace("w", self.toggle_other_type_entry)

    def create_cost_section(self):
        # Right side - costs and time
        self.cost_frame = ttk.LabelFrame(self.main_frame, text="Costs and Time", padding="10")
        self.cost_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0), pady=5)
        self.cost_frame.columnconfigure(1, weight=1)
        for i in range(12):
            self.cost_frame.rowconfigure(i, weight=1)
        
        # Store cost label references for later update
        self.cost_labels = {}
        cost_fields = [
            ("Material cost (€):", 'materiaux', 'cost', "The estimated cost of all materials used in creating this art piece."),
            ("Delivery cost (€):", 'livraison', 'cost', "The cost of packaging and shipping the art piece to buyers."),
            ("Advertising cost (€):", 'pub', 'cost', "Marketing and promotion expenses to increase visibility of your art."),
            ("Creation time (hours):", 'temps', 'time', "The total time spent creating the art piece, including planning and preparation.")
        ]        # Create standard fields first
        for i, (text, key, icon_key, tooltip_text) in enumerate(cost_fields, start=1):
            frame = ttk.Frame(self.cost_frame)
            frame.grid(row=i, column=0, sticky='e', padx=5, pady=5)
            label = ttk.Label(frame, text=text)
            label.pack(side="left")
            # Add info icon for tooltip
            if tooltip_text:
                question_label = ttk.Label(frame, text=" ℹ", foreground="blue", cursor="question_arrow")
                question_label.pack(side="left")
                ToolTip(question_label, tooltip_text)
            
            self.cost_labels[key] = label  # Save label ref for update later
            entry = ttk.Entry(self.cost_frame)
            entry.grid(row=i, column=1, sticky='ew', padx=5, pady=5)
            self.entries[key] = entry
            error_label = ttk.Label(self.cost_frame, text="", style='Error.TLabel') # Use Error style
            error_label.grid(row=i, column=2, sticky='w', padx=5, pady=0)
            self.error_labels[key] = error_label
        
        # Now continue with the dimension fields
        current_row = 5  # Start after the standard cost fields
        
        # Create dimension fields separately for better control
        # Length field
        self.length_frame = ttk.Frame(self.cost_frame)
        self.length_frame.grid(row=current_row, column=0, sticky='e', padx=5, pady=5)
        self.length_label = ttk.Label(self.length_frame, text="Length (cm):")
        self.length_label.pack(side="left")
        self.cost_labels['longueur'] = self.length_label  # Save for later updates
        
        self.entry_length = ttk.Entry(self.cost_frame)
        self.entry_length.grid(row=current_row, column=1, sticky='ew', padx=5, pady=5)
        self.entries['longueur'] = self.entry_length
        
        self.error_length = ttk.Label(self.cost_frame, text="", style='Error.TLabel') # Use Error style
        self.error_length.grid(row=current_row, column=2, sticky='w', padx=5, pady=0)
        self.error_labels['longueur'] = self.error_length

        # Width field
        current_row += 1
        self.width_frame = ttk.Frame(self.cost_frame)
        self.width_frame.grid(row=current_row, column=0, sticky='e', padx=5, pady=5)
        self.width_label = ttk.Label(self.width_frame, text="Width (cm):")
        self.width_label.pack(side="left")
        self.cost_labels['largeur'] = self.width_label  # Save for later updates
        
        self.entry_width = ttk.Entry(self.cost_frame)
        self.entry_width.grid(row=current_row, column=1, sticky='ew', padx=5, pady=5)
        self.entries['largeur'] = self.entry_width
        
        self.error_width = ttk.Label(self.cost_frame, text="", style='Error.TLabel') # Use Error style
        self.error_width.grid(row=current_row, column=2, sticky='w', padx=5, pady=0)
        self.error_labels['largeur'] = self.error_width

        # Add height field (initially hidden)
        current_row += 1
        self.height_frame = ttk.Frame(self.cost_frame)
        self.height_frame.grid(row=current_row, column=0, sticky='e', padx=5, pady=5)
        ttk.Label(self.height_frame, text="Height (cm):").pack(side="left")
        
        self.entry_height = ttk.Entry(self.cost_frame)
        self.entry_height.grid(row=current_row, column=1, sticky='ew', padx=5, pady=5)
        self.entries['hauteur'] = self.entry_height
        
        self.error_height = ttk.Label(self.cost_frame, text="", style='Error.TLabel') # Use Error style
        self.error_height.grid(row=current_row, column=2, sticky='w', padx=5, pady=0)
        self.error_labels['hauteur'] = self.error_height
        
        # Hide height fields initially
        self.height_frame.grid_remove()
        self.entry_height.grid_remove()
        self.error_height.grid_remove()

        # Add weight field (initially hidden)
        current_row += 1
        self.weight_frame = ttk.Frame(self.cost_frame)
        self.weight_frame.grid(row=current_row, column=0, sticky='e', padx=5, pady=5)
        ttk.Label(self.weight_frame, text="Weight (kg):").pack(side="left")
        
        self.entry_weight = ttk.Entry(self.cost_frame)
        self.entry_weight.grid(row=current_row, column=1, sticky='ew', padx=5, pady=5)
        self.entries['poids'] = self.entry_weight
        
        self.error_weight = ttk.Label(self.cost_frame, text="", style='Error.TLabel') # Use Error style
        self.error_weight.grid(row=current_row, column=2, sticky='w', padx=5, pady=0)
        self.error_labels['poids'] = self.error_weight
        
        # Hide weight fields initially
        self.weight_frame.grid_remove()
        self.entry_weight.grid_remove()
        self.error_weight.grid_remove()

        # Add quality selection for digital products (initially hidden)
        current_row += 1
        self.quality_frame = ttk.Frame(self.cost_frame)
        self.quality_frame.grid(row=current_row, column=0, sticky='e', padx=5, pady=5)
        ttk.Label(self.quality_frame, text="Resolution:").pack(side="left")
        
        self.quality_combo = ttk.Combobox(self.cost_frame, textvariable=self.var_quality,
                                          values=["SD (480p)", "HD (720p)", "Full HD (1080p)",
                                                 "2K (1440p)", "4K (2160p)", "8K (4320p)"],
                                          state='readonly')
        self.quality_combo.grid(row=current_row, column=1, sticky='ew', padx=5, pady=5)
        
        self.error_quality = ttk.Label(self.cost_frame, text="", style='Error.TLabel') # Use Error style
        self.error_quality.grid(row=current_row, column=2, sticky='w', padx=5, pady=0)
        self.error_labels['quality'] = self.error_quality
        
        # Hide quality fields initially
        self.quality_frame.grid_remove()
        self.quality_combo.grid_remove()
        self.error_quality.grid_remove()

        # Add duration field (initially hidden)
        current_row += 1
        self.duration_frame = ttk.Frame(self.cost_frame)
        self.duration_frame.grid(row=current_row, column=0, sticky='e', padx=5, pady=5)
        ttk.Label(self.duration_frame, text="Duration (minutes):").pack(side="left")
        
        self.entry_duration = ttk.Entry(self.cost_frame)
        self.entry_duration.grid(row=current_row, column=1, sticky='ew', padx=5, pady=5)
        self.entries['duration'] = self.entry_duration
        
        self.error_duration = ttk.Label(self.cost_frame, text="", style='Error.TLabel') # Use Error style
        self.error_duration.grid(row=current_row, column=2, sticky='w', padx=5, pady=0)
        self.error_labels['duration'] = self.error_duration
        
        # Hide duration fields initially
        self.duration_frame.grid_remove()
        self.entry_duration.grid_remove()
        self.error_duration.grid_remove()
        # Advanced cost factors have been completely removed

    def update_cost_fields_labels(self, product_type):
        physical_var = self.var_photo_type.get()
        print(physical_var)
        
        # Make sure we have a valid product type
        if not product_type:
            return
            
        # Get product requirements from API
        try:
            requirements = gemini_api.get_product_type_requirements(product_type)
            # Convert requirements to dictionary if it's a string
            if isinstance(requirements, str):
                requirements = {
                    "is_digital": "digital" in requirements.lower(),
                    "is_3d": any(term in requirements.lower() for term in ["3d", "three-dimensional", "sculpture", "installation"]),
                    "needs_height": any(term in requirements.lower() for term in []),
                    "needs_weight": any(term in requirements.lower() for term in ["weight", "mass", "size", "dimensions", "physical"]),
                    "needs_duration": any(term in requirements.lower() for term in ["video", "videography", "film", "filmography"]),
                    "needs_resolution": "resolution" in requirements.lower() or "quality" in requirements.lower()
                }
        except Exception as e:
            logging.error(f"Error getting requirements: {str(e)}")
            requirements = {
                "is_digital": False,
                "is_3d": False,
                "is_2d": False,
                "needs_height": False,
                "needs_weight": False,
                "needs_duration": False,
                "needs_resolution": False
            }

        # Check digital status
        is_digital_photo = product_type == "Photography" and self.var_photo_type.get() == "Digital"
        is_digital = product_type in ["Digital", "Video"] or is_digital_photo
        is_3d = product_type in ["Sculpture", "Installation", "Ceramics"] or requirements.get("is_3d", False)
        
        # Show/hide and configure fields based on product type and requirements
        if is_digital:
            # Digital products use pixels
            self.cost_labels['longueur'].config(text="Length (pixels):")
            self.cost_labels['largeur'].config(text="Width (pixels):")
            # Show quality/resolution field if required
            if requirements.get("needs_resolution") or product_type == "Photography":
                self.quality_frame.grid(row=10, column=0, sticky='e', padx=5, pady=5)
                self.quality_combo.grid(row=10, column=1, sticky='ew', padx=5, pady=5)
                self.error_quality.grid(row=10, column=2, sticky='w', padx=5, pady=0)
            # Show duration field if required
            if requirements.get("needs_duration"):
                self.duration_frame.grid(row=9, column=0, sticky='e', padx=5, pady=5)
                self.entry_duration.grid(row=9, column=1, sticky='ew', padx=5, pady=5)
                self.error_duration.grid(row=9, column=2, sticky='w', padx=5, pady=0)
            # Never show weight for digital, photography, or video
            self.weight_frame.grid_remove()
            self.entry_weight.grid_remove()
            self.error_weight.grid_remove()
        else:
            # Physical products use centimeters
            self.cost_labels['longueur'].config(text="Length (cm):")
            self.cost_labels['largeur'].config(text="Width (cm):")
            # Show height field if required
            if requirements.get("needs_height"):
                self.height_frame.grid(row=7, column=0, sticky='e', padx=5, pady=5)
                self.entry_height.grid(row=7, column=1, sticky='ew', padx=5, pady=5)
                self.error_height.grid(row=7, column=2, sticky='w', padx=5, pady=0)
            # Show weight field only for 3D art types
            if product_type in ["Sculpture", "Installation", "Ceramics"] or requirements.get("is_3d", False):
                self.weight_frame.grid(row=8, column=0, sticky='e', padx=5, pady=5)
                self.entry_weight.grid(row=8, column=1, sticky='ew', padx=5, pady=5)
                self.error_weight.grid(row=8, column=2, sticky='w', padx=5, pady=0)
            else:
                self.weight_frame.grid_remove()
                self.entry_weight.grid_remove()
                self.error_weight.grid_remove()
            # Show duration field if required
            if requirements.get("needs_duration"):
                self.duration_frame.grid(row=9, column=0, sticky='e', padx=5, pady=5)
                self.entry_duration.grid(row=9, column=1, sticky='ew', padx=5, pady=5)
                self.error_duration.grid(row=9, column=2, sticky='w', padx=5, pady=0)


    def create_materials_section(self):
        materials_title_frame = ttk.Frame()
        materials_title_text = "Materials Used"
        materials_title = ttk.Label(materials_title_frame, text=materials_title_text)
        materials_title.pack(side="left")
        materials_info = ttk.Label(materials_title_frame, text=" ℹ", foreground="blue", cursor="question_arrow")
        materials_info.pack(side="left")
        ToolTip(materials_info, "Select materials from both lists. Gemini AI will verify if these materials are commonly used together for your selected art type. Unusual but valid combinations may result in unique pricing adjustments.")
        
        self.materials_frame = ttk.LabelFrame(self.main_frame, labelwidget=materials_title_frame, padding="10")
        self.materials_frame.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=5)
        self.materials_frame.columnconfigure(0, weight=1)
        self.materials_frame.rowconfigure(0, weight=1)

        # Container for the two listboxes
        listbox_container = ttk.Frame(self.materials_frame)
        listbox_container.pack(fill="both", expand=True, pady=5)
        listbox_container.columnconfigure(0, weight=1)
        listbox_container.columnconfigure(1, weight=1)
        listbox_container.rowconfigure(0, weight=1)

        # Left side - Canvas materials
        canvas_frame = ttk.LabelFrame(listbox_container, text="Canvas Materials")
        canvas_frame.pack(side=tk.LEFT, fill="both", expand=True, padx=(0, 5))
        canvas_frame.columnconfigure(0, weight=1)
        canvas_frame.rowconfigure(0, weight=1)

        canvas_listbox_frame = ttk.Frame(canvas_frame)
        canvas_listbox_frame.pack(fill="both", expand=True, pady=5)
        canvas_listbox_frame.columnconfigure(0, weight=1)
        canvas_listbox_frame.rowconfigure(0, weight=1)

        self.listbox_canvas = tk.Listbox(canvas_listbox_frame, selectmode=tk.MULTIPLE, exportselection=False, height=5)
        canvas_scrollbar = ttk.Scrollbar(canvas_listbox_frame, orient="vertical", command=self.listbox_canvas.yview)
        self.listbox_canvas.configure(yscrollcommand=canvas_scrollbar.set)
        canvas_scrollbar.pack(side="right", fill="y")
        self.listbox_canvas.pack(side="left", fill="both", expand=True)

        # Add canvas materials
        for mat in ["Canvas", "Cotton", "Linen", "Silk", "Paper", "Other"]:
            self.listbox_canvas.insert(tk.END, mat)

        # Right side - Other materials
        other_frame = ttk.LabelFrame(listbox_container, text="Other Materials")
        other_frame.pack(side=tk.RIGHT, fill="both", expand=True, padx=(5, 0))
        other_frame.columnconfigure(0, weight=1)
        other_frame.rowconfigure(0, weight=1)

        other_listbox_frame = ttk.Frame(other_frame)
        other_listbox_frame.pack(fill="both", expand=True, pady=5)
        other_listbox_frame.columnconfigure(0, weight=1)
        other_listbox_frame.rowconfigure(0, weight=1)

        self.listbox_other = tk.Listbox(other_listbox_frame, selectmode=tk.MULTIPLE, exportselection=False, height=5)
        other_scrollbar = ttk.Scrollbar(other_listbox_frame, orient="vertical", command=self.listbox_other.yview)
        self.listbox_other.configure(yscrollcommand=other_scrollbar.set)
        other_scrollbar.pack(side="right", fill="y")
        self.listbox_other.pack(side="left", fill="both", expand=True)

        # Add other materials
        for mat in ["Wood", "Acrylic", "Oil", "Clay", "Metal", "Glass", "Plastic", "Other"]:
            self.listbox_other.insert(tk.END, mat)

        # Custom‐materials container with title on top
        self.other_material_frame = ttk.Frame(self.materials_frame)
        ttk.Label(self.other_material_frame, text="Specify other materials:").pack(anchor="w", pady=(0,5))
        # inner container
        custom = ttk.Frame(self.other_material_frame)
        custom.pack(fill="x", expand=True)

        # Canvas‐Other custom entry (hidden initially)
        self.canvas_material_frame = ttk.Frame(custom)
        ttk.Label(self.canvas_material_frame, text="Canvas:").pack(side="left", padx=5)
        self.entry_canvas_material = ttk.Entry(self.canvas_material_frame)
        self.entry_canvas_material.pack(side="left", fill="x", expand=True)
        self.canvas_material_frame.pack_forget()

        # Other‐Other custom entry (hidden initially)
        self.other_material_frame_entry = ttk.Frame(custom)
        ttk.Label(self.other_material_frame_entry, text="Other:").pack(side="left", padx=5)
        self.entry_other_material = ttk.Entry(self.other_material_frame_entry)
        self.entry_other_material.pack(side="left", fill="x", expand=True)
        self.other_material_frame_entry.pack_forget()

        # start hidden
        self.other_material_frame.pack_forget()

        # Bind events to update custom material entries
        self.listbox_canvas.bind('<<ListboxSelect>>', lambda e: self.update_material_entry())
        self.listbox_other.bind('<<ListboxSelect>>', lambda e: self.update_material_entry())

        # Bind events to save selection when focus changes
        self.listbox_canvas.bind('<FocusOut>', self.save_canvas_selection)
        self.listbox_canvas.bind('<FocusIn>', self.restore_canvas_selection)
        self.listbox_other.bind('<FocusOut>', self.save_other_selection)
        self.listbox_other.bind('<FocusIn>', self.restore_other_selection)

    def create_error_section(self):
        # Global error message area
        self.global_error_frame = ttk.Frame(self.main_frame)
        self.global_error_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        self.global_error_label = ttk.Label(self.global_error_frame, text="", style='Error.TLabel', wraplength=600) # Use Error style
        self.global_error_label.pack(fill="x", expand=True)
        
    def create_button_section(self):
        # Calculate button in the middle with tooltip
        self.calc_button = ttk.Button(self.main_frame, text="Calculate Price", command=self.calculate_price)
        self.calc_button.grid(row=3, column=0, columnspan=2, pady=10)
        ToolTip(self.calc_button, "Calculate the recommended price based on all entered information. This will consult Gemini AI to validate materials, analyze the artist, and recommend a price range.")
        
        # Reset button in the lower left corner with tooltip
        self.reset_button = ttk.Button(self.main_frame, text="Reset", command=self.reset_form, style='Outline.TButton') # Use Outline style
        self.reset_button.grid(row=5, column=0, sticky="w", padx=10, pady=10)
        ToolTip(self.reset_button, "Clear all fields and results to start over.")        
    
    def create_result_section(self):
        # Result area
        self.result_frame = ttk.LabelFrame(self.main_frame, text="Results", padding="10")
        self.result_frame.grid(row=4, column=0, columnspan=2, sticky="nsew", pady=5)
        self.result_frame.columnconfigure(0, weight=1)
        self.result_frame.rowconfigure(0, weight=1)

        # Result text
        self.result_text = tk.Text(self.result_frame, wrap=tk.WORD, height=14, width=50)
        self.result_text.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        self.result_text.config(state=tk.DISABLED)

        # Scrollbar for result text
        result_scrollbar = ttk.Scrollbar(self.result_frame, orient="vertical", command=self.result_text.yview)
        result_scrollbar.grid(row=0, column=1, sticky="ns", pady=5)
        self.result_text.config(yscrollcommand=result_scrollbar.set)

    def setup_ui(self):
        # ... existing UI setup code ...
        
        # Make sure the Calculate Price button is properly connected
        self.calculate_button = ttk.Button(
            self.bottom_frame, 
            text="Calculate Price",
            command=self.calculate_price  # Ensure this is properly connected
        )
        self.calculate_button.pack(pady=20)
        
        # Make sure the results text widget is properly initialized
        self.results_frame = ttk.LabelFrame(self.root, text="Results")
        self.results_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create the results text widget with proper scrollbar
        self.results_text = tk.Text(self.results_frame, height=10, wrap=tk.WORD)
        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(self.results_frame, command=self.results_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.results_text.config(yscrollcommand=scrollbar.set)

    def reset_form(self):
        # Clear all entries
        for entry in self.entries.values():
            if entry:  # Safety check
                entry.delete(0, tk.END)
        # Clear all comboboxes
        if hasattr(self, 'type_combo'):
            self.type_combo.set("")
        if hasattr(self, 'photo_type_combo'):
            self.photo_type_combo.set("")
        if hasattr(self, 'photo_style_combo'):
            self.photo_style_combo.set("")
        if hasattr(self, 'video_type_combo'):
            self.video_type_combo.set("")
        if hasattr(self, 'video_style_combo'):
            self.video_style_combo.set("")
        if hasattr(self, 'quality_combo'):
            self.quality_combo.set("")
        # Clear type selection
        self.var_type.set("")
        self.var_photo_type.set("")
        self.var_video_type.set("")
        self.var_quality.set("")
        self.var_custom_type.set("")
        # Clear material selections
        self.listbox_canvas.selection_clear(0, tk.END)
        self.listbox_other.selection_clear(0, tk.END)
        # Clear custom material entries
        if hasattr(self, 'entry_canvas_material'):
            self.entry_canvas_material.delete(0, tk.END)
        if hasattr(self, 'entry_other_material'):
            self.entry_other_material.delete(0, tk.END)
        # Clear result
        if hasattr(self, 'result_text'):
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.config(state=tk.DISABLED)
        # Clear error messages
        for label in self.error_labels.values():
            if label:  # Safety check
                label.config(text="")
        self.clear_global_error()
        # Hide optional fields
        self.other_type_frame.grid_forget()
        self.other_material_frame.pack_forget()
        if hasattr(self, 'height_frame'):
            self.height_frame.grid_forget()
        if hasattr(self, 'entry_height'):
            self.entry_height.grid_forget()
        if hasattr(self, 'weight_frame'):
            self.weight_frame.grid_forget()
        if hasattr(self, 'entry_weight'):
            self.entry_weight.grid_forget()
        if hasattr(self, 'duration_frame'):
            self.duration_frame.grid_forget()
        if hasattr(self, 'entry_duration'):
            self.entry_duration.grid_forget()
        if hasattr(self, 'quality_frame'):
            self.quality_frame.grid_forget()
        if hasattr(self, 'quality_combo'):
            self.quality_combo.grid_forget()
        if hasattr(self, 'error_quality'):
            self.error_quality.grid_forget()
        # Remove dynamically added fields for custom product types
        if hasattr(self, 'additional_cost_rows'):
            for widget in self.additional_cost_rows:
                widget.destroy()
            self.additional_cost_rows = []
        if hasattr(self, 'additional_fields_entries'):
            self.additional_fields_entries = {}
        # Reset focus to the first field
        if hasattr(self, 'entry_artist'):
            self.entry_artist.focus_set()

    def toggle_other_type_entry(self, *args):
        """Handle changes in the product type selection"""
        # Get product type from var_type and store it in self.type_produit
        product_type = self.var_type.get()
        self.type_produit = product_type
          
        # Hide all product-specific frames first
        self.photography_spec_frame.grid_forget()
        self.video_spec_frame.grid_forget()
        
        if (product_type == "Other"):
            # Show custom product type input field
            self.other_type_frame.grid(row=3, column=0, columnspan=2, sticky='ew', padx=5, pady=5)
            
            # Create and show loading spinner next to the product type field
            self.type_spinner = LoadingSpinner(self.other_type_frame, size=20)
            self.type_spinner.canvas.place(relx=0.05, rely=0.5, anchor=tk.W)
            self.type_spinner.start()
            
            # Setup timer for automatic input checking
            self.entry_other_type.bind("<KeyRelease>", self.start_input_check_timer)
            
            # Update status text
            self.typing_status.config(text="Type your custom product type...", foreground="blue")
        else:
            # Hide the custom product type field when not "Other"
            self.other_type_frame.grid_forget()
            
            # Cancel any pending timer when switching away from Other
            if self.input_timer:
                self.root.after_cancel(self.input_timer)
                self.input_timer = None
                
            # Stop and remove spinner if it exists
            if hasattr(self, 'type_spinner'):
                self.type_spinner.stop()
                
            # Show specification frames based on product type
            if product_type == "Photography":
                self.photography_spec_frame.grid()
            elif product_type == "Video":
                self.video_spec_frame.grid()
        
        # Clear error messages when changing product type
        self.clear_global_error()
        
        # Update relevant cost fields based on product type
        self.update_cost_fields_labels(product_type)
        
        # Update material section based on product type
        self.update_materials_section_for_product_type(product_type)
        
        # Get product type requirements via api
        final_type = ""
        if product_type == "Other":
            final_type = self.entry_other_type.get().strip()
            if final_type:
                # If we have a valid custom type, update self.type_produit
                self.type_produit = final_type
        else:
            final_type = product_type
                

    def update_additional_costs_for_other_type(self, event=None):
        """
        When a user enters a custom product type, ask Gemini for required fields and dynamically update the UI.
        This function loops through the response from Gemini to create appropriate UI elements.
        """
        logger.debug("==== UPDATING UI FOR CUSTOM PRODUCT TYPE ====")
        # Clear previous additional fields if they exist
        if hasattr(self, 'additional_cost_rows'):
            for widget in self.additional_cost_rows:
                widget.destroy()
                
        # Reset previously created fields
        if hasattr(self, 'additional_fields_entries'):
            self.additional_fields_entries = {}
                
        self.additional_cost_rows = []
        self.additional_fields_entries = {}
        
        # Get the custom product type
        custom_type = self.entry_other_type.get().strip()
        if not custom_type:
            logger.debug("Empty custom type, skipping UI update")
            return
            
        logger.debug(f"Custom product type entered: {custom_type}")
        
        # Display a temporary status message
        self.global_error_label.config(text="Analyzing product type requirements...", foreground="blue")
        self.root.update()  # Force UI update
        
        try:
            # Get product requirements from Gemini
            logger.debug("Getting product requirements from Gemini API")
            requirements = gemini_api.get_product_type_requirements(custom_type)
            logger.debug(f"Requirements received: {requirements}")
            # Convert requirements to dictionary if it's a string
            if isinstance(requirements, str):
                req_str = requirements.lower()
                requirements = {
                    "is_digital": "digital" in req_str,
                    "is_3d": any(term in req_str for term in ["3d", "three-dimensional", "sculpture", "installation"]),
                    "needs_height": "height" in req_str or "dimension" in req_str,
                    "needs_weight": "weight" in req_str or "mass" in req_str,
                    "needs_duration": "duration" in req_str or "length" in req_str,
                    "needs_resolution": "resolution" in req_str or "quality" in req_str
                }
            # Clear status message
            self.clear_global_error()
            
            # Update all relevant fields based on Gemini response
            row_count = 10  # Start after standard fields
            
            # First, determine if it's digital to update dimension units
            is_digital = requirements.get("is_digital", False)
            if is_digital:
                logger.debug("Product identified as digital, updating dimension units to pixels")
                self.cost_labels['longueur'].config(text="Length (pixels):")
                self.cost_labels['largeur'].config(text="Width (pixels):")
            else:
                logger.debug("Product identified as physical, using cm for dimensions")
                self.cost_labels['longueur'].config(text="Length (cm):")
                self.cost_labels['largeur'].config(text="Width (cm):")
            
            # Loop through requirements and handle each one
            for field_name, is_required in requirements.items():
                if (field_name == "is_digital" or field_name == "is_2d" or field_name == "is_3d"):
                    continue  # Skip metadata fields
                    
                if is_required:
                    # Create UI elements based on the requirement type
                    field_key = field_name.replace("needs_", "")
                    logger.debug(f"Adding field for {field_key} (required: {is_required})")
                    
                    # Create frame for the field
                    field_frame = ttk.Frame(self.cost_frame)
                    field_frame.grid(row=row_count, column=0, sticky='e', padx=5, pady=5)
                    
                    # Create label
                    display_name = field_key.capitalize()
                    if field_key == "height":
                        label = ttk.Label(field_frame, text="Height (cm):")
                    elif field_key == "weight":
                        label = ttk.Label(field_frame, text="Weight (kg):")
                    elif field_key == "resolution":
                        label = ttk.Label(field_frame, text="Resolution:")
                    elif field_key == "duration":
                        label = ttk.Label(field_frame, text="Duration (min):")
                    else:
                        label = ttk.Label(field_frame, text=f"{display_name}:")
                        
                    label.pack(side="left")
                    
                    # Create entry or combobox
                    if field_key == "resolution":
                        entry = ttk.Combobox(
                            self.cost_frame,
                            values=["SD (480p)", "HD (720p)", "Full HD (1080p)", 
                                    "2K (1440p)", "4K (2160p)", "8K (4320p)"],
                            state="readonly"
                        )
                    else:
                        entry = ttk.Entry(self.cost_frame)
                        
                    entry.grid(row=row_count, column=1, sticky='ew', padx=5, pady=5)
                    
                    # Create error label
                    error_label = ttk.Label(self.cost_frame, text="", foreground="red")
                    error_label.grid(row=row_count, column=2, sticky='w', padx=5, pady=0)
                    
                    # Store references
                    self.entries[field_key] = entry
                    self.error_labels[field_key] = error_label
                    self.additional_cost_rows.append(field_frame)
                    self.additional_fields_entries[field_key] = entry
                    
                    row_count += 1
            logger.debug("==== FINISHED CUSTOM PRODUCT TYPE UI UPDATE ====")
                    
        except Exception as e:
            error_msg = f"Error analyzing product type: {str(e)}"
            logger.error(error_msg)
            self.display_global_error(error_msg)

    def update_material_entry(self, *args):
        show_can = any(self.listbox_canvas.get(i)=="Other" for i in self.listbox_canvas.curselection())
        show_oth = any(self.listbox_other.get(i)=="Other" for i in self.listbox_other.curselection())

        if show_can or show_oth:
            self.other_material_frame.pack(fill="x", expand=True, pady=5)
            # toggle each entry
            if show_can:
                self.canvas_material_frame.pack(side="left", fill="x", expand=True, padx=(0,5))
            else:
                self.canvas_material_frame.pack_forget()

            if show_oth:
                self.other_material_frame_entry.pack(side="right", fill="x", expand=True, padx=(5,0))
            else:
                self.other_material_frame_entry.pack_forget()
        else:
            self.other_material_frame.pack_forget()

    def save_canvas_selection(self, event):
        self.canvas_saved_selection = list(self.listbox_canvas.curselection())
        
    def restore_canvas_selection(self, event):
        if self.canvas_saved_selection:
            for i in self.canvas_saved_selection:
                self.listbox_canvas.selection_set(i)
            
    def save_other_selection(self, event):
        self.other_saved_selection = list(self.listbox_other.curselection())
        
    def restore_other_selection(self, event):
        if self.other_saved_selection:
            for i in self.other_saved_selection:
                self.listbox_other.selection_set(i)
            
    def display_global_error(self, message):
        self.global_error_label.config(text=message)
        
    def clear_global_error(self):
        self.global_error_label.config(text="")
        
    def get_all_materials(self):
        materials = []
        
        # Get canvas materials
        canvas_indices = self.listbox_canvas.curselection()
        for i in canvas_indices:
            mat = self.listbox_canvas.get(i)
            if (mat == "Other"):
                custom_mat = self.entry_canvas_material.get().strip()
                if custom_mat:
                    materials.append(custom_mat)
            else:
                materials.append(mat)
        
        # Get other materials
        other_indices = self.listbox_other.curselection()
        for i in other_indices:
            mat = self.listbox_other.get(i)
            if (mat == "Other"):
                custom_mat = self.entry_other_material.get().strip()
                if custom_mat:
                    materials.append(custom_mat)
            else:
                materials.append(mat)
        
        return materials    
    
    def calculate_price(self):
        """Calculate price and display results"""
        try:
            # Clear previous results and show calculating message
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "Calculating price...")
            self.result_text.config(state=tk.DISABLED)
            self.root.update()

            # Get all input values
            values = {}
            for key, entry in self.entries.items():
                if entry and entry.winfo_exists():
                    try:
                        values[key] = float(entry.get())
                    except ValueError:
                        values[key] = 0

            # Get selected materials
            selected_materials = self.get_all_materials()

            # Get product type
            product_type = self.var_type.get()
            if product_type == "Other":
                product_type = self.entry_other_type.get().strip()

            # Get artist and market
            artist = self.entry_artist.get().strip()
            market = self.entry_market.get().strip()

            # Validate inputs
            if not artist:
                raise ValueError("Please enter an artist name")
            if not market:
                raise ValueError("Please enter a target market")
            if not product_type:
                raise ValueError("Please select or specify a product type")
            if not selected_materials:
                raise ValueError("Please select at least one material")

            # Determine if product is 3D
            is_3d = product_type in ["Sculpture", "Installation"] or (
                hasattr(self, 'height_frame') and self.height_frame.winfo_ismapped()
            )

            # Calculate price using pricing module
            result = calculate_price(
                values=values,
                type_produit=product_type,
                artiste=artist,
                marche=market,
                materiaux_selectionnes=selected_materials,
                is_3d=is_3d
            )

            # Format and display results
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            
            # Create formatted result text
            result_text = f"Price Calculation Results:\n\n"
            result_text += f"Base Price: €{result['prix']:.2f}\n"
            result_text += f"Market Demand: {result['demande_marche']}/10\n"
            result_text += f"Dimensions: {result['dimensions']}\n"
            result_text += f"Materials: {result['materiaux']}\n"
            if result['artiste_connu']:
                result_text += "Artist Status: Known artist\n"
            if result.get('height'):
                result_text += f"Height: {result['height']} cm\n"
            if result.get('weight'):
                result_text += f"Weight: {result['weight']} kg\n"
            result_text += f"\nAI Price Recommendation: €{result['gemini_price']}"

            # Insert formatted text
            self.result_text.insert(tk.END, result_text)
            self.result_text.config(state=tk.DISABLED)

            # Log the calculation
            self.log_calculation(artist, product_type, result['prix'])

        except ValueError as ve:
            # Display validation errors
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"Error: {str(ve)}")
            self.result_text.config(state=tk.DISABLED)
            self.display_global_error(str(ve))
            
        except Exception as e:
            # Display other errors
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, f"Error calculating price: {str(e)}")
            self.result_text.config(state=tk.DISABLED)
            self.display_global_error(f"Error calculating price: {str(e)}")
            logging.error(f"Price calculation error: {str(e)}")

    def log_calculation(self, artist, product_type, price):
        """Log the calculation details"""
        try:
            # Get current timestamp
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Create log entry
            log_entry = {
                "timestamp": timestamp,
                "artist": artist,
                "product_type": product_type,
                "price": price
            }
            
            # Log to file using data_utils
            data_utils.save_calculation(log_entry)
            
        except Exception as e:
            logging.error(f"Failed to log calculation: {str(e)}")
    
    def toggle_video_duration(self, *args):
        """Handle video duration field visibility based on video type"""
        video_type = self.var_video_type.get()
        
        # Different video types may need different duration handling
        if video_type:
            # Show duration field with appropriate label based on video type
            self.duration_frame.grid(row=9, column=0, sticky='e', padx=5, pady=5)
            self.entry_duration.grid(row=9, column=1, sticky='ew', padx=5, pady=5)
            self.error_duration.grid(row=9, column=2, sticky='w', padx=5, pady=0)
            
            # Adjust label based on video type
            duration_label = "Duration (sec):" if video_type == "Advertisement" else "Duration (min):"
              # Check if the duration frame has enough children before accessing
            if len(self.duration_frame.winfo_children()) > 0:
                # Find the label in the children
                for child in self.duration_frame.winfo_children():
                    if isinstance(child, ttk.Label):
                        child.config(text=duration_label)
                        break
                      # Advanced cost toggle method removed
            if video_type in ["Short Film", "Documentary", "Animation"]:
                self.quality_frame.grid(row=10, column=0, sticky='e', padx=5, pady=5)
                self.quality_combo.grid(row=10, column=1, sticky='ew', padx=5, pady=5)
                self.error_quality.grid(row=10, column=2, sticky='w', padx=5, pady=0)
            else:
                # Hide resolution field for other types
                self.quality_frame.grid_forget()
                self.quality_combo.grid_forget()
                self.error_quality.grid_forget()

    def start_input_check_timer(self, event=None):
        """
        Implements detection of finished typing using an inactivity timeout.
        Similar to the curses example, this detects when the user stops typing
        for the specified timeout period and then processes the input.
        """
        logger.debug("==== START INPUT CHECK TIMER ====")
        # Cancel any existing timer
        if self.input_timer:
            self.root.after_cancel(self.input_timer)
        
        # Update status to show that we're monitoring typing
        self.typing_status.config(text="Typing detected... (will analyze when finished)", foreground="blue")
        
        # Get current value
        current_value = self.entry_other_type.get().strip()
        logger.debug(f"Current input value: '{current_value}'")
        
        # If empty, don't do anything
        if not current_value:
            logger.debug("Empty input, not starting timer")
            self.typing_status.config(text="Please type a product type", foreground="gray")
            return
            
        # Set a timer to check if typing has stopped after the specified timeout
        logger.debug(f"Setting timer for {self.typing_pause_interval}ms to check if typing finished")
        self.input_timer = self.root.after(self.typing_pause_interval, lambda: self.finish_typing(current_value))

    def finish_typing(self, value):
        """
        Called when typing appears to have stopped (after timeout period).
        This is similar to the processing that happens in the curses example
        after the inactivity timeout.
        """
        logger.debug("==== FINISH TYPING CALLBACK ====")
        # If value hasn't changed since we started the timer
        current_value = self.entry_other_type.get().strip()
        logger.debug(f"Timer value: '{value}', Current value: '{current_value}'")
        
        if value == current_value:
            # Process the input now that typing appears complete
            logger.debug("Input appears stable, proceeding with analysis")
            self.typing_status.config(text="Analyzing product type...", foreground="blue")
            self.last_other_value = value
            
            # Process the input
            self.update_additional_costs_for_other_type()
        else:
            # Value changed during our wait, so restart the timer
            logger.debug("Input changed during wait, restarting timer")
            self.start_input_check_timer()

    def update_materials_section_for_product_type(self, product_type):
        """
        Updates the materials section based on the product type.
        For digital products, shows digital-specific materials instead of physical ones.
        Now, asks the API for recommended materials for the selected product type.
        """
        # First check if this is a digital product
        is_digital_photo = product_type == "Photography" and self.var_photo_type.get() == "Digital"
        is_digital = product_type in ["Digital", "Video"] or is_digital_photo

        # Clear previous selections when switching product types
        self.listbox_canvas.selection_clear(0, tk.END)
        self.listbox_other.selection_clear(0, tk.END)

        # Get the labels for the material frames to update them
        canvas_frame_parent = self.listbox_canvas.master.master
        other_frame_parent = self.listbox_other.master.master

        # Ask the API for recommended materials for this product type
        try:
            api_materials = gemini_api.get_recommended_materials(product_type)
            # Always expect a dict with 'canvas' and 'other' keys
            if not isinstance(api_materials, dict):
                api_materials = {}
            canvas_materials = api_materials.get('canvas')
            other_materials = api_materials.get('other')
            # Use defaults if missing or empty
            if not canvas_materials:
                canvas_materials = ["Canvas", "Cotton", "Linen", "Silk", "Paper", "Other"]
            if not other_materials:
                other_materials = ["Wood", "Acrylic", "Oil", "Clay", "Metal", "Glass", "Plastic", "Other"]
        except Exception as e:
            logging.error(f"Error getting recommended materials from API: {e}")
            canvas_materials = ["Canvas", "Cotton", "Linen", "Silk", "Paper", "Other"]
            other_materials = ["Wood", "Acrylic", "Oil", "Clay", "Metal", "Glass", "Plastic", "Other"]

        # Update material section labels
        if is_digital:
            canvas_frame_parent.config(text="Digital Assets")
            other_frame_parent.config(text="Digital Effects")
        else:
            canvas_frame_parent.config(text="Canvas Materials")
            other_frame_parent.config(text="Other Materials")

        # Clear the existing items in listboxes
        self.listbox_canvas.delete(0, tk.END)
        self.listbox_other.delete(0, tk.END)

        # Add new materials from API or defaults
        for mat in canvas_materials:
            self.listbox_canvas.insert(tk.END, mat)
        for mat in other_materials:
            self.listbox_other.insert(tk.END, mat)

    def submit_other_type(self):
        """
        Handles the submission of the custom product type.
        This method is called when typing in the custom product type field.
        """
        custom_type = self.entry_other_type.get().strip()
        
        if not custom_type:
            self.typing_status.config(text="Please enter a product type", foreground="red")
            return
            
        # Create and display the full loading screen
        loading_screen = LoadingScreen(self.root, message=f"Analyzing art type: {custom_type}...")
        self.root.update_idletasks()  # Force UI update to show the loading screen
        
        try:
            # Validate if the product type is recognized as an artistic product
            is_valid = gemini_api.verify_artistic_product(custom_type)
            
            if not is_valid:
                self.typing_status.config(text=f"'{custom_type}' is not recognized as a valid artistic product", foreground="red")
                return
                
            # Store the custom type in the variables
            self.var_custom_type.set(custom_type)
            self.type_produit = custom_type  # Set the main product type variable
            
            # Update status message
            self.typing_status.config(text=f"Custom type '{custom_type}' submitted", foreground="green")
            
            # Get product requirements for the custom type
            loading_screen.update_message(f"Getting requirements for {custom_type}...")
            requirements = gemini_api.get_product_type_requirements(custom_type)
            
            # Apply the same changes as in toggle_other_type_entry for the custom type
            # Handle optional cost fields (height, weight, duration, quality)
            if requirements.get("needs_height", False) or requirements.get("is_3d", False):
                self.height_frame.grid(row=7, column=0, sticky='e', padx=5, pady=5)
                self.entry_height.grid(row=7, column=1, sticky='ew', padx=5, pady=5)
                self.error_height.grid(row=7, column=2, sticky='w', padx=5, pady=0)
            else:
                self.height_frame.grid_forget()
                self.entry_height.grid_forget()
                self.error_height.grid_forget()
            
            # Handle weight field visibility
            if requirements.get("needs_weight", False) or requirements.get("is_3d", False):
                self.weight_frame.grid(row=8, column=0, sticky='e', padx=5, pady=5)
                self.entry_weight.grid(row=8, column=1, sticky='ew', padx=5, pady=5)
                self.error_weight.grid(row=8, column=2, sticky='w', padx=5, pady=0)
            else:
                self.weight_frame.grid_forget()
                self.entry_weight.grid_forget()
                self.error_weight.grid_forget()
            
            # Handle duration field visibility
            if requirements.get("needs_duration", False):
                self.duration_frame.grid(row=9, column=0, sticky='e', padx=5, pady=5)
                self.entry_duration.grid(row=9, column=1, sticky='ew', padx=5, pady=5)
                self.error_duration.grid(row=9, column=2, sticky='w', padx=5, pady=0)
            else:
                self.duration_frame.grid_forget()
                self.entry_duration.grid_forget()
                self.error_duration.grid_forget()
            
            # Handle resolution field visibility
            if requirements.get("needs_resolution", False):
                self.quality_frame.grid(row=10, column=0, sticky='e', padx=5, pady=5)
                self.quality_combo.grid(row=10, column=1, sticky='ew', padx=5, pady=5)
                self.error_quality.grid(row=10, column=2, sticky='w', padx=5, pady=0)
            else:
                self.quality_frame.grid_forget()
                self.quality_combo.grid_forget()
                self.error_quality.grid_forget()
                
            # Update material section based on product type requirements
            is_digital = requirements.get("is_digital", False)
            if is_digital:
                self.cost_labels['longueur'].config(text="Length (pixels):")
                self.cost_labels['largeur'].config(text="Width (pixels):")
                self.update_materials_section_for_digital(custom_type)
            else:
                self.cost_labels['longueur'].config(text="Length (cm):")
                self.cost_labels['largeur'].config(text="Width (cm):")
                self.update_materials_section_for_physical()
                
            # Clear any previous error messages
            self.clear_global_error()
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.typing_status.config(text=error_msg, foreground="red")
        
        finally:
            # Hide the loading screen
            loading_screen.hide()

    def update_materials_section_for_digital(self, product_type):
        """
        Updates the materials section specifically for digital products.
        This is called by the submit_other_type method when a custom digital product is submitted.
        """
        # Get the labels for the material frames to update them
        canvas_frame_parent = self.listbox_canvas.master.master
        other_frame_parent = self.listbox_other.master.master
        
        # Update material section labels for digital products
        canvas_frame_parent.config(text="Digital Assets")
        other_frame_parent.config(text="Digital Effects")
        
        # Clear the existing items in listboxes
        self.listbox_canvas.delete(0, tk.END)
        self.listbox_other.delete(0, tk.END)
        
        # For custom digital products, use generic digital formats
        for mat in ["Source File", "PNG", "JPEG", "PDF", "SVG", "GIF", "Other"]:
            self.listbox_canvas.insert(tk.END, mat)
            
        # Generic digital techniques for custom product
        for mat in ["Digital Drawing", "Generated", "Edited", "Animated", "Interactive", "Coded", "Other"]:
            self.listbox_other.insert(tk.END, mat)

    def update_materials_section_for_physical(self):
        """
        Updates the materials section for physical products.
        This is called by the submit_other_type method when a custom physical product is submitted.
        """
        # Get the labels for the material frames to update them
        canvas_frame_parent = self.listbox_canvas.master.master
        other_frame_parent = self.listbox_other.master.master
        
        # Reset to original physical materials
        canvas_frame_parent.config(text="Canvas Materials")
        other_frame_parent.config(text="Other Materials")
        
        # Clear the existing items in listboxes
        self.listbox_canvas.delete(0, tk.END)
        self.listbox_other.delete(0, tk.END)
        
        # Add physical canvas materials
        for mat in ["Canvas", "Cotton", "Linen", "Silk", "Paper", "Other"]:
            self.listbox_canvas.insert(tk.END, mat)
            
        # Add physical other materials
        for mat in ["Wood", "Acrylic", "Oil", "Clay", "Metal", "Glass", "Plastic", "Other"]:
            self.listbox_other.insert(tk.END, mat)

    def store_specified_type(self):
        """Store the user-specified product type in the same variable used for dropdown selection"""
        # Get the text from entry field
        specified_type = self.type_entry.get().strip()
        
        # Validate input
        if not specified_type:
            # Show error if empty
            tk.messagebox.showerror("Error", "Please specify a product type")
            return
        
        # Store the value in the type_produit variable (same as used for dropdown)
        self.type_produit = specified_type
        
        # Update the var_type StringVar to match the custom input
        # This keeps the UI state consistent with the stored value
        self.var_type.set("Other")  # Set dropdown to "Other"
        
        # Optional: provide feedback to user
        tk.messagebox.showinfo("Success", f"Product type '{specified_type}' has been stored")
        
        # Optional: clear the entry field after submission
        self.type_entry.delete(0, tk.END)
        
        # Update materials section for the new product type
        self.update_materials_section_for_product_type(self.type_produit)

    def on_frame_configure(self, event=None):
        """Reset the scroll region to encompass the inner frame"""
        self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        
    def on_canvas_configure(self, event=None):
        """When canvas is resized, resize the inner frame to match"""
        canvas_width = event.width
        self.main_canvas.itemconfig(self.canvas_window, width=canvas_width)
        
    def on_mousewheel(self, event):
        """Handle mousewheel scrolling"""
        self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def update_photo_fields(self, *args):
        """Update the visibility of photography fields based on the selected type"""
        photo_type = self.var_photo_type.get()
        
        if photo_type == "Digital":
            # Show resolution field for digital photos
            self.photo_resolution_combo.grid()
            # Hide physical print-related fields
            self.photo_print_size_combo.grid_remove()
            self.photo_print_material_combo.grid_remove()
        elif photo_type == "Physical":
            # Hide resolution field for physical photos
            self.photo_resolution_combo.grid_remove()
            # Show print-related fields
            self.photo_print_size_combo.grid()
            self.photo_print_material_combo.grid()
        else:
            # Hide all fields if no type is selected
            self.photo_resolution_combo.grid_remove()
            self.photo_print_size_combo.grid_remove()
            self.photo_print_material_combo.grid_remove()


