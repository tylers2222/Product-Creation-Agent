from customtkinter import *
from PIL import Image
import sys
import os
import requests
import threading
import time
import json
from datetime import datetime, date
import hashlib
from dotenv import load_dotenv
import logging

# Import local models (standalone GUI - no backend dependencies)
from models import PromptVariant, Variant, Option, InventoryAtStores, format_product_input

load_dotenv()

# ========================================
# LOGGING CONFIGURATION
# ========================================
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# PyInstaller resource path helper
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ========================================
# API CONFIGURATION
# ========================================
# Reads from config.json if exists, otherwise uses default
API_BASE_URL = os.getenv("API_BASE_URL")
logger.info(f"API Base URL: {API_BASE_URL}")

# ========================================
# AUTHENTICATION CONFIGURATION
# ========================================
# Set your password here
CORRECT_PASSWORD = "999999"

# File to track daily logins (in same directory as this script)
# For PyInstaller, we need to save to a writable location
if getattr(sys, 'frozen', False):
    # Running as compiled executable - use user's home directory
    SCRIPT_DIR = os.path.expanduser("~/.evelyn_faye_agent")
    os.makedirs(SCRIPT_DIR, exist_ok=True)
else:
    # Running as normal Python script
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGIN_TRACKING_FILE = os.path.join(SCRIPT_DIR, "login_tracking.json")

def get_device_id():
    """Get a unique identifier for this device"""
    # Use MAC address as device identifier
    import uuid
    return str(uuid.getnode())

def load_login_data():
    """Load login tracking data"""
    if os.path.exists(LOGIN_TRACKING_FILE):
        try:
            with open(LOGIN_TRACKING_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_login_data(data):
    """Save login tracking data"""
    with open(LOGIN_TRACKING_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def check_daily_login():
    """Check if user has logged in today on this device"""
    device_id = get_device_id()
    today = str(date.today())
    
    login_data = load_login_data()
    device_data = login_data.get(device_id, {})
    
    # Check if last login was today
    last_login = device_data.get("last_login")
    return last_login == today

def record_login():
    """Record that user logged in today on this device"""
    device_id = get_device_id()
    today = str(date.today())
    now = datetime.now().isoformat()
    
    login_data = load_login_data()
    
    if device_id not in login_data:
        login_data[device_id] = {
            "first_login": now,
            "total_logins": 0,
            "login_dates": []
        }
    
    device_data = login_data[device_id]
    device_data["last_login"] = today
    device_data["last_login_time"] = now
    device_data["total_logins"] = device_data.get("total_logins", 0) + 1
    
    # Track unique login dates
    if "login_dates" not in device_data:
        device_data["login_dates"] = []
    if today not in device_data["login_dates"]:
        device_data["login_dates"].append(today)
    
    save_login_data(login_data)
    print(f"✅ Login recorded for device {device_id[:8]}... on {today}")
    print(f"   Total logins: {device_data['total_logins']}")
    print(f"   Unique days: {len(device_data['login_dates'])}")

# Initialize the app
app = CTk()
app.geometry("1500x980")

app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure(0, weight=1, uniform="cols")
app.grid_columnconfigure(1, weight=1, uniform="cols")

# Global variable to track if user needs to log in
needs_login = not check_daily_login()

def page_1(parent):
    """Login page with 6-digit passcode authentication"""
    
    # Create left frame with image
    left_frame = CTkFrame(
        master=parent,
    )
    left_frame.grid(row=0, column=0, sticky="nsew", padx=(10,5), pady=(10,10))

    # Load the original image
    original_image = Image.open(resource_path("images/login_image.png"))

    # Create initial CTkImage
    login_image = CTkImage(
        dark_image=original_image,
        size=(500,980)
    )

    login_label = CTkLabel(left_frame, image=login_image, text="")
    login_label.pack(fill="both", expand=True)

    def resize_image(event=None):
        # Get the frame dimensions
        frame_width = left_frame.winfo_width()
        frame_height = left_frame.winfo_height()
        
        if frame_width > 1 and frame_height > 1:  # Ensure valid dimensions
            # Update the CTkImage size
            login_image.configure(size=(frame_width, frame_height))

    # Bind resize event to the frame
    left_frame.bind("<Configure>", resize_image)
    
    # Create right frame with login form
    right_frame = CTkFrame(
        master=parent,
        fg_color="#1a1a1a"  # Softer dark background
    )
    right_frame.grid(row=0, column=1, sticky="nsew", padx=(5,10), pady=(10,10))

    # Configure right_frame grid for centering
    right_frame.grid_rowconfigure(0, weight=1)  # Top spacer
    right_frame.grid_rowconfigure(1, weight=0)  # Content
    right_frame.grid_rowconfigure(2, weight=1)  # Bottom spacer
    right_frame.grid_columnconfigure(0, weight=1)

    # Login container
    login_container = CTkFrame(right_frame, fg_color="#1a1a1a")
    login_container.grid(row=1, column=0, padx=40, pady=20)

    # Welcome title
    welcome_label = CTkLabel(
        login_container,
        text="Welcome Back",
        font=("Helvetica", 32, "bold"),
        text_color="#a8d5ba"  # Soft sage green
    )
    welcome_label.pack(pady=(0, 5))

    # Subtitle
    subtitle_label = CTkLabel(
        login_container,
        text="Sign in to your account",
        font=("Helvetica", 14),
        text_color="#909090"  # Lighter gray
    )
    subtitle_label.pack(pady=(0, 40))

    # Passcode label
    passcode_label = CTkLabel(
        login_container,
        text="Enter 6-Digit Passcode",
        font=("Helvetica", 12),
        text_color="#7fa88f",
    )
    passcode_label.pack(pady=(0, 15))

    # Passcode entry frame
    passcode_frame = CTkFrame(login_container, fg_color="#1a1a1a")
    passcode_frame.pack(pady=(0, 10))

    # Create 6 entry boxes for passcode
    passcode_entries = []

    def on_passcode_key(event, index):
        """Auto-focus next box when digit is entered"""
        entry = passcode_entries[index]
        value = entry.get()
        
        # Only allow digits
        if value and not value.isdigit():
            entry.delete(0, 'end')
            return
        
        # Move to next box if digit entered
        if len(value) == 1 and index < 5:
            passcode_entries[index + 1].focus()
        
        # Limit to 1 character
        if len(value) > 1:
            entry.delete(1, 'end')

    def on_backspace(event, index):
        """Move to previous box on backspace if current is empty"""
        entry = passcode_entries[index]
        if len(entry.get()) == 0 and index > 0:
            passcode_entries[index - 1].focus()
            passcode_entries[index - 1].delete(0, 'end')

    for i in range(6):
        entry = CTkEntry(
            passcode_frame,
            width=50,
            height=60,
            font=("Helvetica", 24, "bold"),
            fg_color="#242424",
            border_color="#4a6b5a",
            border_width=2,
            text_color="#e0e0e0",
            justify="center",
            show="•"
        )
        entry.pack(side="left", padx=5)
        passcode_entries.append(entry)
        
        # Bind key events
        entry.bind("<KeyRelease>", lambda e, idx=i: on_passcode_key(e, idx))
        entry.bind("<BackSpace>", lambda e, idx=i: on_backspace(e, idx))

    # Focus first entry
    passcode_entries[0].focus()

    def get_passcode():
        """Get the complete passcode"""
        return "".join(entry.get() for entry in passcode_entries)

    # Error message label
    error_label = CTkLabel(
        login_container,
        text="",
        font=("Helvetica", 11),
        text_color="#ff4444"
    )
    error_label.pack(pady=(0, 10))

    def check_login():
        """Validate passcode"""
        passcode = get_passcode()
        if len(passcode) != 6:
            error_label.configure(text="⚠️ Please enter 6 digits")
            return False
        
        # Check password
        if passcode == CORRECT_PASSWORD:
            # Record login
            record_login()
            error_label.configure(text="")
            show_frame(page_two)
            return True
        else:
            error_label.configure(text="❌ Incorrect password")
            # Clear all entries
            for entry in passcode_entries:
                entry.delete(0, 'end')
            passcode_entries[0].focus()
            return False

    # Login button
    login_button = CTkButton(
        login_container,
        text="Sign In",
        font=("Helvetica", 16, "bold"),
        width=350,
        height=50,
        fg_color="#4a6b5a",
        hover_color="#5c7d6c",
        text_color="#ffffff",
        corner_radius=10,
        command=check_login
    )
    login_button.pack(pady=(20, 20))

    # Divider
    divider_frame = CTkFrame(login_container, fg_color="#1a1a1a")
    divider_frame.pack(fill="x", pady=20)

    left_line = CTkFrame(divider_frame, height=1, fg_color="#3a3a3a")
    left_line.pack(side="left", fill="x", expand=True, padx=(0, 10))

    or_label = CTkLabel(divider_frame, text="OR", text_color="#707070", font=("Helvetica", 11))
    or_label.pack(side="left")

    right_line = CTkFrame(divider_frame, height=1, fg_color="#3a3a3a")
    right_line.pack(side="left", fill="x", expand=True, padx=(10, 0))

    # Sign up section
    signup_frame = CTkFrame(login_container, fg_color="#1a1a1a")
    signup_frame.pack()

    signup_text = CTkLabel(
        signup_frame,
        text="Don't have an account?",
        font=("Helvetica", 12),
        text_color="#909090"
    )
    signup_text.pack(side="left", padx=(0, 5))

    signup_button = CTkButton(
        signup_frame,
        text="Sign Up",
        font=("Helvetica", 12, "bold"),
        fg_color="transparent",
        text_color="#7fa88f",
        hover_color="#242424",
        width=60,
        height=20
    )
    signup_button.pack(side="left")
    
    # Return both frames as a tuple
    return (left_frame, right_frame)

def page_2(parent):
    """Page 2 - Main application page"""
    agents = ["Products Generation Agent"]

    page_2_frame = CTkFrame(parent, fg_color="#1a1a1a")
    page_2_frame.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=(10,10), pady=(10,10))

    # Configure frame grid
    page_2_frame.grid_rowconfigure(0, weight=0)  # Nav bar row - fixed height
    page_2_frame.grid_rowconfigure(1, weight=1)  # Content row - expands
    page_2_frame.grid_columnconfigure(0, weight=0, minsize=300)  # Sidebar column - fixed width
    page_2_frame.grid_columnconfigure(1, weight=1)  # Content column - expands
    
    # Nav bar at the top (spans both columns)
    page_2_nav_bar = CTkFrame(master=page_2_frame, fg_color="#0F0F0F", height=100)
    page_2_nav_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=(0,0), pady=(0,0))
    page_2_nav_bar.grid_propagate(False)  # Maintain fixed height

    # Left sidebar for buttons (below nav bar)
    page_2_sidebar = CTkFrame(page_2_frame, fg_color="#0F0F0F", corner_radius=0)
    page_2_sidebar.grid(row=1, column=0, sticky="nsew", padx=(0,0), pady=(0,0))
    
    # Add buttons to sidebar
    sidebar_title = CTkLabel(page_2_sidebar, text="🤖 Agent View", font=("Helvetica", 20, "bold"), text_color="#7fa88f")
    sidebar_title.pack(pady=(20, 10), padx=10)

    # Store buttons for selection management
    selected_button = None
    agent_buttons = []
    
    # Map agent names to titles and descriptions
    agent_info = {
        "Products Generation Agent": {
            "title": "📦 Products Generation Agent",
            "description": "Generate product listings for your Shopify store"
        },
    }
    
    def toggle_button(clicked_btn, agent_name):
        """Set clicked button as selected, deselect others, and update title"""
        global selected_button
        selected_button = clicked_btn
        
        for btn in agent_buttons:
            if btn == clicked_btn:
                btn.configure(fg_color="#2a3a2f")  # Light background for selected
            else:
                btn.configure(fg_color="transparent")  # Reset others
        
        # Update title and description based on selected agent
        if agent_name in agent_info:
            info = agent_info[agent_name]
            main_content_title.configure(text=info["title"])
            main_content_description.configure(text=info["description"])
            
            # Show product generation form if that agent is selected
            if agent_name == "Products Generation Agent":
                scrollable_frame.grid()  # Show form
                generate_query()  # Update query display
            else:
                scrollable_frame.grid_remove()  # Hide form for other agents
                update_query_display(f"Select 'Products Generation Agent' to use this feature.\n\nAgent: {agent_name}")

    for idx, agent in enumerate(agents):
        # First button: 20px top, 0px bottom. Others: 0px both sides
        y_padding = (20, 0) if idx == 0 else (0, 0)
        # Set first button as selected (light background), others transparent
        initial_color = "#2a3a2f" if idx == 0 else "transparent"
        btn_product_generation_agent = CTkButton(
            page_2_sidebar, 
            text=agent, 
            corner_radius=0, 
            height=50, 
            fg_color=initial_color, 
            border_color="#696969", 
            hover_color="#003D0F",
            command=lambda agent_name=agent, idx=idx: toggle_button(agent_buttons[idx], agent_name)
        )
        btn_product_generation_agent.pack(fill="x", pady=y_padding)
        agent_buttons.append(btn_product_generation_agent)

    # Main content area (below nav bar, right of sidebar)
    page_2_content = CTkFrame(page_2_frame, fg_color="#1a1a1a")
    page_2_content.grid(row=1, column=1, sticky="nsew", padx=(0,0), pady=(0,0))
    
    # ========================================
    # GRID LAYOUT EXPLANATION:
    # ========================================
    # Step 1: Configure the PARENT frame's grid (page_2_content)
    #   - This tells grid how to divide space
    #   - weight=1 means "expand to fill space"
    #   - weight=0 means "stay at minimum size"
    #   - minsize=400 means "minimum 400px wide"
    #
    # Step 2: Place child frames using .grid(row=X, column=Y)
    #   - row=0, column=0 = top-left
    #   - row=0, column=1 = top-right
    #   - sticky="nsew" = expand in all directions
    # ========================================
    
    page_2_content.grid_rowconfigure(0, weight=1)  # Row 0 expands vertically
    page_2_content.grid_columnconfigure(0, weight=1)  # Column 0 expands (left side)
    page_2_content.grid_columnconfigure(1, weight=0, minsize=400)  # Column 1 fixed 400px (right side)
    
    # Left area (where main content goes - can be changed by sidebar buttons)
    main_content_area = CTkFrame(page_2_content, fg_color="#1a1a1a")
    main_content_area.grid(row=0, column=0, sticky="nsew")
    
    # Configure main_content_area grid for title, description, text display, status, and button
    main_content_area.grid_rowconfigure(0, weight=0)  # Title row - fixed height
    main_content_area.grid_rowconfigure(1, weight=0)  # Description row - fixed height
    main_content_area.grid_rowconfigure(2, weight=1)  # Text area row - expands
    main_content_area.grid_rowconfigure(3, weight=0)  # Status label row - fixed height
    main_content_area.grid_rowconfigure(4, weight=0)  # Button row - fixed height
    main_content_area.grid_columnconfigure(0, weight=1)  # Column expands
    
    # Title that sits above the text box (updates based on selected button)
    first_agent = agents[0] if agents else "Agent"
    initial_title = agent_info.get(first_agent, {}).get("title", "Agent View")
    main_content_title = CTkLabel(
        main_content_area,
        text=initial_title,
        font=("Helvetica", 24, "bold"),
        text_color="#a8d5ba"
    )
    main_content_title.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 5))
    
    # Description below title
    initial_description = agent_info.get(first_agent, {}).get("description", "")
    main_content_description = CTkLabel(
        main_content_area,
        text=initial_description,
        font=("Helvetica", 14),
        text_color="#909090"
    )
    main_content_description.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 15))
    
    # Text display area - shows the query that will be sent to AI agent
    # This is a read-only text box that displays the formatted query
    text_display_area = CTkTextbox(
        main_content_area,
        width=400,
        height=500,
        fg_color="#0F0F0F",
        border_color="#4a6b5a",
        border_width=2,
        corner_radius=5,
        font=("Helvetica", 12),
        text_color="#e0e0e0",
        wrap="word"  # Wrap text at word boundaries
    )
    text_display_area.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 15))
    text_display_area.insert("1.0", "Query will appear here...\n\nFill out the form on the right to generate the query.")
    text_display_area.configure(state="disabled")  # Make it read-only
    
    # Status label for showing request progress
    status_label = CTkLabel(
        main_content_area,
        text="",
        font=("Helvetica", 12),
        text_color="#a8d5ba"
    )
    status_label.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 10))
    
    # Send Request button - full width underneath text box
    send_request_btn = CTkButton(
        main_content_area,
        text="Send Request",
        height=50,
        fg_color="#4a6b5a",
        hover_color="#5c7d6c",
        text_color="#ffffff",
        font=("Helvetica", 14, "bold"),
        corner_radius=5,
        command=lambda: send_request()
    )
    send_request_btn.grid(row=4, column=0, sticky="ew", padx=20, pady=(0, 20))
    
    # Helper function to update the query text
    def update_query_display(query_text):
        """Update the text display area with new query text"""
        text_display_area.configure(state="normal")  # Enable editing
        text_display_area.delete("1.0", "end")  # Clear existing text
        text_display_area.insert("1.0", query_text)  # Insert new text
        text_display_area.configure(state="disabled")  # Make read-only again
        text_display_area.see("1.0")  # Scroll to top
    
    def update_status(message, color="#a8d5ba"):
        """Update status label with message and color"""
        status_label.configure(text=message, text_color=color)
    
    def build_request_payload():
        """Build the JSON payload from form_data"""
        logger.debug("Building request payload from form_data")
        logger.debug(f"Form data: {json.dumps(form_data, indent=2, default=str)}")
        
        try:
            # Build variants list
            variants_list = []
            for variant_data in form_data["variants"]:
                # Skip if option_1_value is empty
                if not variant_data.get("option_1_value"):
                    continue
                    
                # Create Option objects
                option_1 = Option(
                    option_name=variant_data.get("option_1_name", "Option 1"),
                    option_value=variant_data.get("option_1_value", "")
                )
                option_2 = None
                option_3 = None
                
                if variant_data.get("option_2_value"):
                    option_2 = Option(
                        option_name=variant_data.get("option_2_name", "Option 2"),
                        option_value=variant_data["option_2_value"]
                    )
                if variant_data.get("option_3_value"):
                    option_3 = Option(
                        option_name=variant_data.get("option_3_name", "Option 3"),
                        option_value=variant_data["option_3_value"]
                    )
                
                # Parse SKU, barcode, price, weight
                try:
                    sku_val = int(variant_data.get("sku", 0)) if variant_data.get("sku") and str(variant_data.get("sku")).strip() else 0
                except (ValueError, TypeError):
                    sku_val = 0
                
                try:
                    price_val = float(variant_data.get("price", 0.0)) if variant_data.get("price") and str(variant_data.get("price")).strip() else 0.0
                except (ValueError, TypeError):
                    price_val = 0.0
                
                try:
                    weight_val = float(variant_data.get("product_weight", 0.0)) if variant_data.get("product_weight") and str(variant_data.get("product_weight")).strip() else 0.0
                except (ValueError, TypeError):
                    weight_val = 0.0
                
                # Get inventory values
                try:
                    city_inv = int(variant_data.get("inventory_city", "")) if variant_data.get("inventory_city") and str(variant_data.get("inventory_city")).strip() else None
                except (ValueError, TypeError):
                    city_inv = None
                
                try:
                    south_inv = int(variant_data.get("inventory_south_melbourne", "")) if variant_data.get("inventory_south_melbourne") and str(variant_data.get("inventory_south_melbourne")).strip() else None
                except (ValueError, TypeError):
                    south_inv = None
                
                # Create InventoryAtStores if inventory data exists
                inventory_at_stores = None
                if city_inv is not None or south_inv is not None:
                    inventory_at_stores = InventoryAtStores(
                        city=city_inv,
                        south_melbourne=south_inv
                    )
                
                variant = Variant(
                    option1_value=option_1,
                    option2_value=option_2,
                    option3_value=option_3,
                    sku=sku_val,
                    barcode=str(variant_data.get("barcode", "")),
                    price=price_val,
                    product_weight=weight_val,
                    inventory_at_stores=inventory_at_stores
                )
                logger.debug(f"Created variant: {variant.model_dump()}")
                variants_list.append(variant)
            
            logger.debug(f"Total variants created: {len(variants_list)}")
            
            # Create PromptVariant object
            prompt_variant = PromptVariant(
                brand_name=form_data.get("brand_name", ""),
                product_name=form_data.get("product_name", ""),
                variants=variants_list
            )
            
            payload = prompt_variant.model_dump()
            logger.debug(f"Final payload: {json.dumps(payload, indent=2, default=str)}")
            return payload
        except Exception as e:
            logger.error(f"Error building payload: {str(e)}", exc_info=True)
            update_status(f"Error building payload: {str(e)}", "#ff4444")
            return None
    
    def show_success_popup(product_url):
        """Show a popup with the Shopify product URL"""
        import webbrowser
        from tkinter import Toplevel
        
        # Create popup window
        popup = Toplevel(app)
        popup.title("✅ Product Created Successfully!")
        popup.geometry("600x250")
        popup.configure(bg="#1a1a1a")
        
        # Center the popup
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (600 // 2)
        y = (popup.winfo_screenheight() // 2) - (250 // 2)
        popup.geometry(f"600x250+{x}+{y}")
        
        # Make it stay on top
        popup.attributes('-topmost', True)
        
        # Success icon and message
        success_label = CTkLabel(
            popup, 
            text="🎉 Product Created Successfully!",
            font=("Helvetica", 20, "bold"),
            text_color="#44ff44"
        )
        success_label.pack(pady=(30, 20))
        
        # URL label
        url_label = CTkLabel(
            popup,
            text="Your product is now live on Shopify:",
            font=("Helvetica", 12),
            text_color="#e0e0e0"
        )
        url_label.pack(pady=(0, 10))
        
        # URL text box (read-only, but selectable)
        url_textbox = CTkTextbox(
            popup,
            height=40,
            width=550,
            fg_color="#0F0F0F",
            border_color="#4a6b5a",
            border_width=2,
            text_color="#4a9eff",
            font=("Helvetica", 11)
        )
        url_textbox.pack(pady=(0, 20))
        url_textbox.insert("1.0", product_url)
        url_textbox.configure(state="disabled")  # Make read-only
        
        # Buttons frame
        buttons_frame = CTkFrame(popup, fg_color="transparent")
        buttons_frame.pack(pady=(0, 20))
        
        # Open URL button
        def open_url():
            webbrowser.open(product_url)
            popup.destroy()
        
        open_btn = CTkButton(
            buttons_frame,
            text="🔗 Open in Browser",
            width=180,
            height=40,
            fg_color="#4a6b5a",
            hover_color="#5c7d6c",
            text_color="#ffffff",
            font=("Helvetica", 13, "bold"),
            command=open_url
        )
        open_btn.pack(side="left", padx=10)
        
        # Close button
        close_btn = CTkButton(
            buttons_frame,
            text="Close",
            width=120,
            height=40,
            fg_color="#555555",
            hover_color="#666666",
            text_color="#ffffff",
            font=("Helvetica", 13),
            command=popup.destroy
        )
        close_btn.pack(side="left", padx=10)
    
    def poll_status(request_id):
        """Poll the job status endpoint every 20 seconds"""
        logger.info(f"Starting polling for request_id: {request_id}")
        poll_url = f"{API_BASE_URL}/internal/product_generation/{request_id}"
        logger.debug(f"Poll URL: {poll_url}")
        timeout_seconds = 600  # 10 minutes
        start_time = time.time()
        
        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                logger.warning(f"Polling timed out after {timeout_seconds}s for request_id: {request_id}")
                app.after(0, lambda: update_status("⏱️ Request timed out after 10 minutes", "#ff9944"))
                app.after(0, lambda: send_request_btn.configure(state="normal"))
                break
            
            try:
                logger.debug(f"Polling status (elapsed: {int(elapsed)}s)...")
                # Increased timeout to 250 seconds for polling requests
                response = requests.get(poll_url, timeout=250)
                logger.debug(f"Poll response status: {response.status_code}")
                
                if response.status_code == 200:
                    # Parse outer response
                    outer_response = response.json()
                    logger.debug(f"Poll response data: {outer_response}")
                    
                    # The "data" field contains a JSON string, so parse it again
                    if "data" in outer_response:
                        job_data = json.loads(outer_response["data"])
                        logger.debug(f"Job data: {job_data}")
                    else:
                        job_data = outer_response  # Fallback
                        logger.debug("No 'data' field, using outer_response as job_data")
                    
                    if job_data.get("completed"):
                        product_url = job_data.get("url_of_job", "")
                        logger.info(f"Job completed! Product URL: {product_url}")
                        app.after(0, lambda: update_status("✅ Product created successfully!", "#44ff44"))
                        app.after(0, lambda: send_request_btn.configure(state="normal"))
                        app.after(0, lambda url=product_url: show_success_popup(url))
                        break
                    else:
                        # Still processing
                        logger.debug(f"Job still processing (elapsed: {int(elapsed)}s)")
                        app.after(0, lambda: update_status(f"⏳ Processing... ({int(elapsed)}s)", "#a8d5ba"))
                else:
                    logger.error(f"Error polling status: {response.status_code}")
                    logger.debug(f"Poll error response: {response.text}")
                    app.after(0, lambda s=response.status_code: update_status(f"❌ Error polling status: {s}", "#ff4444"))
                    app.after(0, lambda: send_request_btn.configure(state="normal"))
                    break
            except requests.exceptions.Timeout:
                # Timeout on this poll - continue to next poll attempt
                logger.warning(f"Poll request timed out (elapsed: {int(elapsed)}s), retrying...")
                app.after(0, lambda: update_status(f"⏳ Still processing... ({int(elapsed)}s, retrying)", "#a8d5ba"))
            except Exception as e:
                logger.error(f"Polling error: {type(e).__name__}: {str(e)}", exc_info=True)
                app.after(0, lambda e=e: update_status(f"❌ Polling error: {str(e)}", "#ff4444"))
                app.after(0, lambda: send_request_btn.configure(state="normal"))
                break
            
            logger.debug("Waiting 20 seconds before next poll...")
            time.sleep(20)  # Wait 20 seconds before next poll
    
    def send_request():
        """Send POST request to create product"""
        logger.debug("send_request() called")
        
        # Validate form data
        if not form_data.get("brand_name") or not form_data.get("product_name"):
            logger.warning("Missing brand or product name")
            update_status("⚠️ Please fill in brand and product name", "#ff9944")
            return
        
        if not form_data.get("variants") or len(form_data.get("variants", [])) == 0:
            logger.warning("No variants provided")
            update_status("⚠️ Please add at least one variant", "#ff9944")
            return
        
        # Validate each variant has SKU, barcode, and price filled
        for idx, variant in enumerate(form_data.get("variants", [])):
            if not variant.get("sku") or not str(variant.get("sku")).strip():
                logger.warning(f"Variant {idx + 1} missing SKU")
                update_status(f"⚠️ Variant {idx + 1} is missing SKU", "#ff9944")
                return
            if not variant.get("barcode") or not str(variant.get("barcode")).strip():
                logger.warning(f"Variant {idx + 1} missing barcode")
                update_status(f"⚠️ Variant {idx + 1} is missing barcode", "#ff9944")
                return
            if not variant.get("price") or not str(variant.get("price")).strip():
                logger.warning(f"Variant {idx + 1} missing price")
                update_status(f"⚠️ Variant {idx + 1} is missing price", "#ff9944")
                return
        
        logger.info("Validation passed, building payload")
        
        # Build payload
        payload = build_request_payload()
        if not payload:
            logger.error("Failed to build payload")
            return  # Error message already shown by build_request_payload
        
        # Disable button during request
        send_request_btn.configure(state="disabled")
        update_status("📤 Sending request...", "#a8d5ba")
        
        def make_request():
            try:
                url = f"{API_BASE_URL}/internal/product_generation"
                logger.info(f"Sending POST request to: {url}")
                logger.debug(f"Request payload: {json.dumps(payload, indent=2, default=str)}")
                
                response = requests.post(url, json=payload, timeout=30)
                
                logger.info(f"Response status code: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                
                if response.status_code == 200:
                    logger.info("Request successful (200 OK)")
                    response_data = response.json()
                    logger.debug(f"Response data: {response_data}")
                    request_id = response_data.get("request_id")
                    
                    if request_id:
                        logger.info(f"Received request_id: {request_id}")
                        app.after(0, lambda: update_status(f"✅ Request submitted! ID: {request_id[:8]}...", "#44ff44"))
                        # Start polling in background thread
                        poll_thread = threading.Thread(target=poll_status, args=(request_id,), daemon=True)
                        poll_thread.start()
                    else:
                        logger.error("No request_id in response")
                        app.after(0, lambda: update_status("❌ No request_id in response", "#ff4444"))
                        app.after(0, lambda: send_request_btn.configure(state="normal"))
                else:
                    logger.error(f"Request failed with status {response.status_code}")
                    # Print full error response
                    try:
                        error_text = response.text
                        logger.error(f"Error response text: {error_text}")
                        try:
                            error_json = response.json()
                            logger.error(f"Error response JSON: {json.dumps(error_json, indent=2)}")
                        except:
                            logger.debug("Could not parse error response as JSON")
                    except Exception as parse_err:
                        logger.error(f"Could not read error response: {parse_err}")
                    
                    app.after(0, lambda: update_status(f"❌ Request failed: {response.status_code}", "#ff4444"))
                    app.after(0, lambda: send_request_btn.configure(state="normal"))
            except Exception as e:
                logger.error(f"Exception during request: {type(e).__name__}: {str(e)}", exc_info=True)
                app.after(0, lambda e=e: update_status(f"❌ Error: {str(e)}", "#ff4444"))
                app.after(0, lambda: send_request_btn.configure(state="normal"))
        
        # Run request in background thread to avoid freezing GUI
        logger.debug("Starting request thread")
        request_thread = threading.Thread(target=make_request, daemon=True)
        request_thread.start()

    # Right area (template/form area - stays fixed)
    template_fill_frame = CTkFrame(page_2_content, fg_color="#0F0F0F", corner_radius=0)
    template_fill_frame.grid(row=0, column=1, sticky="nsew")
    
    # Configure template frame for scrolling
    template_fill_frame.grid_rowconfigure(1, weight=1)
    template_fill_frame.grid_columnconfigure(0, weight=1)
    
    # Title for template area
    template_label = CTkLabel(template_fill_frame, text="📝 Variables To Fill", font=("Helvetica", 20, "bold"), text_color="#7fa88f")
    template_label.grid(row=0, column=0, sticky="w", padx=20, pady=(20, 10))
    
    # Scrollable frame for form fields
    scrollable_frame = CTkScrollableFrame(template_fill_frame, fg_color="#0F0F0F")
    scrollable_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
    
    # Store form data
    form_data = {
        "brand_name": "",
        "product_name": "",
        "variants": []  # List of variant dicts
    }
    
    # Form fields storage
    form_widgets = {
        "brand_entry": None,
        "product_entry": None,
        "variant_frames": []  # Store variant frame widgets
    }
    
    def generate_query():
        """Generate the query string from form data and update display"""
        try:
            # Build variants list
            variants_list = []
            for variant_data in form_data["variants"]:
                # Skip if option_1_value is empty
                if not variant_data.get("option_1_value"):
                    continue
                    
                # Create Option objects using stored option names
                option_1 = Option(
                    option_name=variant_data.get("option_1_name", "Option 1"),
                    option_value=variant_data.get("option_1_value", "")
                )
                option_2 = None
                option_3 = None
                
                if variant_data.get("option_2_value"):
                    option_2 = Option(
                        option_name=variant_data.get("option_2_name", "Option 2"),
                        option_value=variant_data["option_2_value"]
                    )
                if variant_data.get("option_3_value"):
                    option_3 = Option(
                        option_name=variant_data.get("option_3_name", "Option 3"),
                        option_value=variant_data["option_3_value"]
                    )
                
                # Create Variant - handle empty SKU/barcode/price gracefully
                try:
                    sku_val = int(variant_data.get("sku", 0)) if variant_data.get("sku") and str(variant_data.get("sku")).strip() else 0
                except (ValueError, TypeError):
                    sku_val = 0
                
                try:
                    price_val = float(variant_data.get("price", 0.0)) if variant_data.get("price") and str(variant_data.get("price")).strip() else 0.0
                except (ValueError, TypeError):
                    price_val = 0.0
                
                try:
                    weight_val = float(variant_data.get("product_weight", 0.0)) if variant_data.get("product_weight") and str(variant_data.get("product_weight")).strip() else 0.0
                except (ValueError, TypeError):
                    weight_val = 0.0
                
                # Get inventory values for this specific variant
                try:
                    city_inv = int(variant_data.get("inventory_city", "")) if variant_data.get("inventory_city") and str(variant_data.get("inventory_city")).strip() else None
                except (ValueError, TypeError):
                    city_inv = None
                
                try:
                    south_inv = int(variant_data.get("inventory_south_melbourne", "")) if variant_data.get("inventory_south_melbourne") and str(variant_data.get("inventory_south_melbourne")).strip() else None
                except (ValueError, TypeError):
                    south_inv = None
                
                # Create InventoryAtStores if inventory data exists for this variant
                inventory_at_stores = None
                if city_inv is not None or south_inv is not None:
                    inventory_at_stores = InventoryAtStores(
                        city=city_inv,
                        south_melbourne=south_inv
                    )
                
                variant = Variant(
                    option1_value=option_1,
                    option2_value=option_2,
                    option3_value=option_3,
                    sku=sku_val,
                    barcode=str(variant_data.get("barcode", "")),
                    price=price_val,
                    product_weight=weight_val,
                    inventory_at_stores=inventory_at_stores
                )
                variants_list.append(variant)
            
            # Create PromptVariant
            if form_data["brand_name"] and form_data["product_name"] and variants_list:
                prompt_variant = PromptVariant(
                    brand_name=form_data["brand_name"],
                    product_name=form_data["product_name"],
                    variants=variants_list
                )
                # Generate formatted query
                query_text = format_product_input(prompt_variant)
                update_query_display(query_text)
            else:
                # Show helpful placeholder
                missing = []
                if not form_data["brand_name"]:
                    missing.append("Brand Name")
                if not form_data["product_name"]:
                    missing.append("Product Name")
                if not variants_list:
                    missing.append("Variants (click 'Generate All Variants')")
                
                template_text = "📝 Fill out the form to generate your query\n\n"
                if missing:
                    template_text += f"Missing: {', '.join(missing)}\n\n"
                template_text += "Steps:\n"
                template_text += "1. Enter Brand Name and Product Name\n"
                template_text += "2. For each Option:\n"
                template_text += "   - Enter the option name (e.g., 'Size', 'Flavour')\n"
                template_text += "   - Add option values using the '+' button\n"
                template_text += "3. Click 'Generate All Variants'\n"
                template_text += "4. Fill in SKU, Barcode, and Price for each variant"
                update_query_display(template_text)
        except Exception as e:
            update_query_display(f"Error generating query: {str(e)}")
    
    # Brand Name Field
    brand_label = CTkLabel(scrollable_frame, text="Brand Name", font=("Helvetica", 12, "bold"), text_color="#7fa88f", anchor="w")
    brand_label.pack(fill="x", padx=10, pady=(10, 5))
    brand_entry = CTkEntry(scrollable_frame, placeholder_text="Enter brand name", fg_color="#1a1a1a", border_color="#4a6b5a", text_color="#e0e0e0")
    brand_entry.pack(fill="x", padx=10, pady=(0, 15))
    brand_entry.bind("<KeyRelease>", lambda e: update_form_field("brand_name", brand_entry.get()))
    form_widgets["brand_entry"] = brand_entry
    
    # Product Name Field
    product_label = CTkLabel(scrollable_frame, text="Product Name", font=("Helvetica", 12, "bold"), text_color="#7fa88f", anchor="w")
    product_label.pack(fill="x", padx=10, pady=(0, 5))
    product_entry = CTkEntry(scrollable_frame, placeholder_text="Enter product name", fg_color="#1a1a1a", border_color="#4a6b5a", text_color="#e0e0e0")
    product_entry.pack(fill="x", padx=10, pady=(0, 15))
    product_entry.bind("<KeyRelease>", lambda e: update_form_field("product_name", product_entry.get()))
    form_widgets["product_entry"] = product_entry
    
    # Variants Section
    variants_label = CTkLabel(scrollable_frame, text="Variant Options", font=("Helvetica", 14, "bold"), text_color="#7fa88f", anchor="w")
    variants_label.pack(fill="x", padx=10, pady=(10, 10))
    
    def update_form_field(field, value):
        """Update form data and regenerate query"""
        form_data[field] = value
        generate_query()
    
    # Store option data
    option_data = {
        "option_1": {"name": "", "values": []},
        "option_2": {"name": "", "values": []},
        "option_3": {"name": "", "values": []}
    }
    
    # Store option widgets
    option_widgets = {
        "option_1": {"name_entry": None, "value_frames": []},
        "option_2": {"name_entry": None, "value_frames": []},
        "option_3": {"name_entry": None, "value_frames": []}
    }
    
    def add_option_value(option_key):
        """Add a new value field for an option"""
        value_idx = len(option_data[option_key]["values"])
        option_data[option_key]["values"].append("")
        
        # Get the container frame (first element is the container)
        container = option_widgets[option_key]["value_frames"][0]["frame"]
        
        # Create value frame
        value_frame = CTkFrame(container, fg_color="transparent")
        value_frame.pack(fill="x", padx=5, pady=2)
        
        # Value entry
        value_entry = CTkEntry(value_frame, placeholder_text=f"Value {value_idx + 1}", 
                              fg_color="#0F0F0F", border_color="#4a6b5a", text_color="#e0e0e0", 
                              height=30, width=200)
        value_entry.pack(side="left", padx=(0, 5))
        value_entry.bind("<KeyRelease>", lambda e, opt=option_key, idx=value_idx: update_option_value(opt, idx, value_entry.get()))
        
        # Remove button
        remove_btn = CTkButton(value_frame, text="×", width=30, height=30, 
                               fg_color="#5a1a1a", hover_color="#7a2a2a", text_color="#ffffff",
                               command=lambda opt=option_key, idx=value_idx: remove_option_value(opt, idx))
        remove_btn.pack(side="left")
        
        # Store widget (skip first element which is container)
        if len(option_widgets[option_key]["value_frames"]) == 1:
            # First value, add after container
            option_widgets[option_key]["value_frames"].append({
                "frame": value_frame,
                "entry": value_entry
            })
        else:
            option_widgets[option_key]["value_frames"].append({
                "frame": value_frame,
                "entry": value_entry
            })
    
    def remove_option_value(option_key, value_idx):
        """Remove an option value"""
        if value_idx < len(option_data[option_key]["values"]):
            # Remove widget (skip first element which is container)
            widget_idx = value_idx + 1  # +1 because first element is container
            if widget_idx < len(option_widgets[option_key]["value_frames"]):
                option_widgets[option_key]["value_frames"][widget_idx]["frame"].destroy()
                option_widgets[option_key]["value_frames"].pop(widget_idx)
            # Remove data
            option_data[option_key]["values"].pop(value_idx)
            # Re-index remaining entries
            for i in range(value_idx, len(option_data[option_key]["values"])):
                widget_idx = i + 1
                if widget_idx < len(option_widgets[option_key]["value_frames"]):
                    option_widgets[option_key]["value_frames"][widget_idx]["entry"].configure(placeholder_text=f"Value {i + 1}")
            generate_variants()  # Regenerate variants after removing a value
    
    def update_option_name(option_key, name):
        """Update option name"""
        option_data[option_key]["name"] = name
        generate_variants()  # Regenerate variants when option name changes
    
    def update_option_value(option_key, value_idx, value):
        """Update an option value"""
        if value_idx < len(option_data[option_key]["values"]):
            option_data[option_key]["values"][value_idx] = value
            generate_variants()  # Auto-generate variants when values change
    
    def create_option_section(option_key, label_text, required=True):
        """Create UI section for an option (name + values with + button)"""
        # Option section frame
        option_section = CTkFrame(scrollable_frame, fg_color="#1a1a1a", corner_radius=5)
        option_section.pack(fill="x", padx=10, pady=5)
        
        # Option label
        option_label = CTkLabel(option_section, text=label_text, font=("Helvetica", 12, "bold"), text_color="#7fa88f", anchor="w")
        option_label.pack(fill="x", padx=10, pady=(10, 5))
        
        # Option name field
        name_frame = CTkFrame(option_section, fg_color="transparent")
        name_frame.pack(fill="x", padx=10, pady=(0, 5))
        
        name_label = CTkLabel(name_frame, text="Name:", font=("Helvetica", 10), text_color="#909090")
        name_label.pack(side="left", padx=(0, 5))
        name_entry = CTkEntry(name_frame, placeholder_text="e.g., Size", fg_color="#0F0F0F", 
                             border_color="#4a6b5a", text_color="#e0e0e0", height=30, width=150)
        name_entry.pack(side="left")
        name_entry.bind("<KeyRelease>", lambda e, opt=option_key: update_option_name(opt, name_entry.get()))
        option_widgets[option_key]["name_entry"] = name_entry
        
        # Values container frame
        values_container = CTkFrame(option_section, fg_color="transparent")
        values_container.pack(fill="x", padx=10, pady=(5, 5))
        
        # Store container for adding values
        option_widgets[option_key]["value_frames"] = [{"frame": values_container}]  # First element is container
        
        # Add first value field
        add_option_value(option_key)
        
        # Add value button
        add_btn = CTkButton(option_section, text="+ Add Value", width=120, height=30,
                           fg_color="#4a6b5a", hover_color="#5c7d6c", text_color="#ffffff",
                           command=lambda opt=option_key: add_option_value(opt))
        add_btn.pack(padx=10, pady=(0, 10))
    
    # Create Option 1 (Required)
    create_option_section("option_1", "Option 1 (Required)", required=True)
    
    # Create Option 2 (Optional)
    create_option_section("option_2", "Option 2 (Optional)", required=False)
    
    # Create Option 3 (Optional)
    create_option_section("option_3", "Option 3 (Optional)", required=False)
    
    # Frame to hold generated variants
    variants_display_frame = CTkFrame(scrollable_frame, fg_color="transparent")
    variants_display_frame.pack(fill="both", expand=True, padx=10, pady=(10, 10))
    
    def generate_variants():
        """Generate all variant combinations from option lists"""
        # Clear existing variants
        form_data["variants"] = []
        for widget_set in form_widgets["variant_frames"]:
            widget_set["frame"].destroy()
        form_widgets["variant_frames"] = []
        
        # Get option values (filter out empty)
        opt1_values = [v for v in option_data["option_1"]["values"] if v.strip()]
        opt2_values = [v for v in option_data["option_2"]["values"] if v.strip()]
        opt3_values = [v for v in option_data["option_3"]["values"] if v.strip()]
        
        if not opt1_values:
            return  # Need at least Option 1 values
        
        # Generate all combinations (Cartesian product)
        import itertools
        
        # Build lists for product
        option_lists = [opt1_values]
        if opt2_values:
            option_lists.append(opt2_values)
        if opt3_values:
            option_lists.append(opt3_values)
        
        # Generate all combinations
        combinations = list(itertools.product(*option_lists))
        
        # Create variant for each combination
        for idx, combo in enumerate(combinations):
            variant_data = {
                "option_1_name": option_data["option_1"]["name"] or "Option 1",
                "option_1_value": combo[0],
                "option_2_name": (option_data["option_2"]["name"] or "Option 2") if len(combo) > 1 else "",
                "option_2_value": combo[1] if len(combo) > 1 else "",
                "option_3_name": (option_data["option_3"]["name"] or "Option 3") if len(combo) > 2 else "",
                "option_3_value": combo[2] if len(combo) > 2 else "",
                "sku": "",  # User must fill this in
                "barcode": "",  # User must fill this in
                "price": "",
                "product_weight": "",
                "inventory_city": "",
                "inventory_south_melbourne": ""
            }
            form_data["variants"].append(variant_data)
            create_variant_display(idx, variant_data)
        
        generate_query()
    
    def create_variant_display(variant_idx, variant_data):
        """Create UI for a single variant"""
        variant_frame = CTkFrame(variants_display_frame, fg_color="#1a1a1a", corner_radius=5)
        variant_frame.pack(fill="x", padx=5, pady=3)
        
        # Header frame with variant name and close button
        header_frame = CTkFrame(variant_frame, fg_color="transparent")
        header_frame.pack(fill="x", padx=10, pady=(8, 5))
        
        # Variant header with combination (using option names)
        combo_text = f"{variant_data.get('option_1_name', 'Option 1')}: {variant_data.get('option_1_value', '')}"
        if variant_data.get("option_2_value"):
            combo_text += f" + {variant_data.get('option_2_name', 'Option 2')}: {variant_data['option_2_value']}"
        if variant_data.get("option_3_value"):
            combo_text += f" + {variant_data.get('option_3_name', 'Option 3')}: {variant_data['option_3_value']}"
        
        variant_header = CTkLabel(header_frame, text=combo_text, font=("Helvetica", 11, "bold"), text_color="#a8d5ba")
        variant_header.pack(side="left", anchor="w")
        
        # Close button (X) on the right side of header
        close_btn = CTkButton(header_frame, text="×", width=30, height=30, 
                             fg_color="#5a1a1a", hover_color="#ff4444", text_color="#ffffff",
                             font=("Helvetica", 16, "bold"),
                             command=lambda idx=variant_idx: remove_variant(idx))
        close_btn.pack(side="right")
        
        # SKU, Barcode row
        details_frame = CTkFrame(variant_frame, fg_color="transparent")
        details_frame.pack(fill="x", padx=10, pady=5)
        
        # SKU
        sku_label = CTkLabel(details_frame, text="SKU", font=("Helvetica", 10), text_color="#909090")
        sku_label.pack(side="left", padx=(0, 5))
        sku_entry = CTkEntry(details_frame, placeholder_text="Required", fg_color="#0F0F0F", border_color="#4a6b5a", text_color="#e0e0e0", width=100, height=30)
        if variant_data["sku"]:
            sku_entry.insert(0, variant_data["sku"])
        sku_entry.pack(side="left", padx=(0, 10))
        sku_entry.bind("<KeyRelease>", lambda e, idx=variant_idx: update_variant_field(idx, "sku", sku_entry.get()))
        
        # Barcode
        barcode_label = CTkLabel(details_frame, text="Barcode", font=("Helvetica", 10), text_color="#909090")
        barcode_label.pack(side="left", padx=(0, 5))
        barcode_entry = CTkEntry(details_frame, placeholder_text="Required", fg_color="#0F0F0F", border_color="#4a6b5a", text_color="#e0e0e0", width=150, height=30)
        if variant_data["barcode"]:
            barcode_entry.insert(0, variant_data["barcode"])
        barcode_entry.pack(side="left", padx=(0, 10))
        barcode_entry.bind("<KeyRelease>", lambda e, idx=variant_idx: update_variant_field(idx, "barcode", barcode_entry.get()))
        
        # Price, Weight row
        price_weight_frame = CTkFrame(variant_frame, fg_color="transparent")
        price_weight_frame.pack(fill="x", padx=10, pady=5)
        
        # Price
        price_label = CTkLabel(price_weight_frame, text="Price ($)", font=("Helvetica", 10), text_color="#909090")
        price_label.pack(side="left", padx=(0, 5))
        price_entry = CTkEntry(price_weight_frame, placeholder_text="49.95", fg_color="#0F0F0F", border_color="#4a6b5a", text_color="#e0e0e0", width=100, height=30)
        if variant_data["price"]:
            price_entry.insert(0, variant_data["price"])
        price_entry.pack(side="left", padx=(0, 10))
        price_entry.bind("<KeyRelease>", lambda e, idx=variant_idx: update_variant_field(idx, "price", price_entry.get()))
        
        # Weight (kg)
        weight_label = CTkLabel(price_weight_frame, text="Weight (kg)", font=("Helvetica", 10), text_color="#909090")
        weight_label.pack(side="left", padx=(0, 5))
        weight_entry = CTkEntry(price_weight_frame, placeholder_text="0.91", fg_color="#0F0F0F", border_color="#4a6b5a", text_color="#e0e0e0", width=100, height=30)
        if variant_data["product_weight"]:
            weight_entry.insert(0, variant_data["product_weight"])
        weight_entry.pack(side="left", padx=(0, 10))
        weight_entry.bind("<KeyRelease>", lambda e, idx=variant_idx: update_variant_field(idx, "product_weight", weight_entry.get()))
        
        # Inventory row
        inventory_frame = CTkFrame(variant_frame, fg_color="transparent")
        inventory_frame.pack(fill="x", padx=10, pady=(5, 5))
        
        # City inventory
        city_inv_label = CTkLabel(inventory_frame, text="City Inv.", font=("Helvetica", 10), text_color="#909090")
        city_inv_label.pack(side="left", padx=(0, 5))
        city_inv_entry = CTkEntry(inventory_frame, placeholder_text="100", fg_color="#0F0F0F", border_color="#4a6b5a", text_color="#e0e0e0", width=80, height=30)
        if variant_data["inventory_city"]:
            city_inv_entry.insert(0, variant_data["inventory_city"])
        city_inv_entry.pack(side="left", padx=(0, 10))
        city_inv_entry.bind("<KeyRelease>", lambda e, idx=variant_idx: update_variant_field(idx, "inventory_city", city_inv_entry.get()))
        
        # South Melbourne inventory
        south_inv_label = CTkLabel(inventory_frame, text="South Melb. Inv.", font=("Helvetica", 10), text_color="#909090")
        south_inv_label.pack(side="left", padx=(0, 5))
        south_inv_entry = CTkEntry(inventory_frame, placeholder_text="100", fg_color="#0F0F0F", border_color="#4a6b5a", text_color="#e0e0e0", width=80, height=30)
        if variant_data["inventory_south_melbourne"]:
            south_inv_entry.insert(0, variant_data["inventory_south_melbourne"])
        south_inv_entry.pack(side="left", padx=(0, 10))
        south_inv_entry.bind("<KeyRelease>", lambda e, idx=variant_idx: update_variant_field(idx, "inventory_south_melbourne", south_inv_entry.get()))
        
        # Store variant widgets
        variant_widgets = {
            "frame": variant_frame,
            "sku": sku_entry,
            "barcode": barcode_entry,
            "price": price_entry,
            "weight": weight_entry,
            "city_inv": city_inv_entry,
            "south_inv": south_inv_entry
        }
        form_widgets["variant_frames"].append(variant_widgets)
    
    def update_variant_field(variant_idx, field, value):
        """Update a specific variant field"""
        if variant_idx < len(form_data["variants"]):
            form_data["variants"][variant_idx][field] = value
            generate_query()
    
    def remove_variant(variant_idx):
        """Remove a variant from the form"""
        if variant_idx < len(form_data["variants"]):
            # Remove widget
            if variant_idx < len(form_widgets["variant_frames"]):
                form_widgets["variant_frames"][variant_idx]["frame"].destroy()
                form_widgets["variant_frames"].pop(variant_idx)
            # Remove data
            form_data["variants"].pop(variant_idx)
            # Re-number remaining variants
            for i, widget_set in enumerate(form_widgets["variant_frames"]):
                if i < len(form_data["variants"]):
                    v = form_data["variants"][i]
                    combo_text = f"{v.get('option_1_name', 'Option 1')}: {v.get('option_1_value', '')}"
                    if v.get("option_2_value"):
                        combo_text += f" + {v.get('option_2_name', 'Option 2')}: {v['option_2_value']}"
                    if v.get("option_3_value"):
                        combo_text += f" + {v.get('option_3_name', 'Option 3')}: {v['option_3_value']}"
                    widget_set["frame"].winfo_children()[0].configure(text=combo_text)
            generate_query()
    
    # Generate Variants Button
    generate_variants_btn = CTkButton(scrollable_frame, text="🔄 Generate All Variants", width=200, height=40, 
                                     fg_color="#4a6b5a", hover_color="#5c7d6c", text_color="#ffffff",
                                     font=("Helvetica", 13, "bold"),
                                     command=generate_variants)
    generate_variants_btn.pack(pady=15, padx=10)
    
    # Set initial state based on first agent
    first_agent = agents[0] if agents else None
    if first_agent == "Products Generation Agent":
        scrollable_frame.grid()  # Show form
        generate_query()  # Generate initial query
    else:
        scrollable_frame.grid_remove()  # Hide form
        update_query_display(f"Select 'Products Generation Agent' to use this feature.\n\nAgent: {first_agent}")
    
    return page_2_frame

def show_frame(page_to_show):
    """Show the specified page and hide all others"""
    # Hide all pages
    for page in [page_one, page_two]:
        # Handle both single frames and tuples of frames
        if isinstance(page, tuple):
            for frame in page:
                frame.grid_remove()
        else:
            page.grid_remove()
    
    # Show the requested page
    if isinstance(page_to_show, tuple):
        for frame in page_to_show:
            frame.grid()
            frame.tkraise()
    else:
        page_to_show.grid()
        page_to_show.tkraise()

# Load pages
page_one = page_1(app)  # Returns tuple: (left_frame, right_frame)
page_two = page_2(app)  # Returns single frame

def main():
    """Main entry point for the GUI application"""
    # Show page 1 (login) if user hasn't logged in today, otherwise page 2
    if needs_login:
        show_frame(page_one)
        print("🔒 Daily login required")
    else:
        show_frame(page_two)
        print("✅ Already logged in today - skipping login page")
    
    app.mainloop()

if __name__ == "__main__":
    main()