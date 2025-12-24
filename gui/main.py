from customtkinter import *
from PIL import Image
import sys
import os

# Add parent directory to path to import agent modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from agents.agent.prompts import PromptVariant, Variant, Option, format_product_input

app = CTk()
app.geometry("1500x980")

app.grid_rowconfigure(0, weight=1)
app.grid_columnconfigure(0, weight=1, uniform="cols")
app.grid_columnconfigure(1, weight=1, uniform="cols")

def page_1(parent):
    """Login page with 6-digit passcode authentication"""
    
    # Create left frame with image
    left_frame = CTkFrame(
        master=parent,
    )
    left_frame.grid(row=0, column=0, sticky="nsew", padx=(10,5), pady=(10,10))

    # Load the original image
    original_image = Image.open("images/login_image.png")

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

    def check_login():
        """Validate passcode"""
        passcode = get_passcode()
        if len(passcode) != 6:
            return False
        # Add your validation logic here

        if passcode == "123456":
            show_frame(page_two)
        return True

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
    
    # Configure main_content_area grid for title, description, text display, and button
    main_content_area.grid_rowconfigure(0, weight=0)  # Title row - fixed height
    main_content_area.grid_rowconfigure(1, weight=0)  # Description row - fixed height
    main_content_area.grid_rowconfigure(2, weight=1)  # Text area row - expands
    main_content_area.grid_rowconfigure(3, weight=0)  # Button row - fixed height
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
        command=lambda: print("Send Request clicked")  # Placeholder for POST request
    )
    send_request_btn.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
    
    # Helper function to update the query text
    def update_query_display(query_text):
        """Update the text display area with new query text"""
        text_display_area.configure(state="normal")  # Enable editing
        text_display_area.delete("1.0", "end")  # Clear existing text
        text_display_area.insert("1.0", query_text)  # Insert new text
        text_display_area.configure(state="disabled")  # Make read-only again
        text_display_area.see("1.0")  # Scroll to top

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
                
                variant = Variant(
                    option_1=option_1,
                    option_2=option_2,
                    option_3=option_3,
                    sku=sku_val,
                    barcode=str(variant_data.get("barcode", "")),
                    price=price_val
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
    
    def update_option_name(option_key, name):
        """Update option name"""
        option_data[option_key]["name"] = name
    
    def update_option_value(option_key, value_idx, value):
        """Update an option value"""
        if value_idx < len(option_data[option_key]["values"]):
            option_data[option_key]["values"][value_idx] = value
    
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
    
    def generate_sku_base():
        """Generate base SKU number"""
        return 922000
    
    def generate_barcode_base():
        """Generate base barcode"""
        return "0810095637971"
    
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
        base_sku = generate_sku_base()
        base_barcode = generate_barcode_base()
        
        for idx, combo in enumerate(combinations):
            variant_data = {
                "option_1_name": option_data["option_1"]["name"] or "Option 1",
                "option_1_value": combo[0],
                "option_2_name": (option_data["option_2"]["name"] or "Option 2") if len(combo) > 1 else "",
                "option_2_value": combo[1] if len(combo) > 1 else "",
                "option_3_name": (option_data["option_3"]["name"] or "Option 3") if len(combo) > 2 else "",
                "option_3_value": combo[2] if len(combo) > 2 else "",
                "sku": str(base_sku + idx),
                "barcode": str(int(base_barcode) + idx) if base_barcode.isdigit() else f"{base_barcode}{idx}",
                "price": ""
            }
            form_data["variants"].append(variant_data)
            create_variant_display(idx, variant_data)
        
        generate_query()
    
    def create_variant_display(variant_idx, variant_data):
        """Create UI for a single variant"""
        variant_frame = CTkFrame(variants_display_frame, fg_color="#1a1a1a", corner_radius=5)
        variant_frame.pack(fill="x", padx=5, pady=3)
        
        # Variant header with combination (using option names)
        combo_text = f"{variant_data.get('option_1_name', 'Option 1')}: {variant_data.get('option_1_value', '')}"
        if variant_data.get("option_2_value"):
            combo_text += f" + {variant_data.get('option_2_name', 'Option 2')}: {variant_data['option_2_value']}"
        if variant_data.get("option_3_value"):
            combo_text += f" + {variant_data.get('option_3_name', 'Option 3')}: {variant_data['option_3_value']}"
        
        variant_header = CTkLabel(variant_frame, text=combo_text, font=("Helvetica", 11, "bold"), text_color="#a8d5ba")
        variant_header.pack(anchor="w", padx=10, pady=(8, 5))
        
        # SKU, Barcode, Price in a row
        details_frame = CTkFrame(variant_frame, fg_color="transparent")
        details_frame.pack(fill="x", padx=10, pady=5)
        
        # SKU
        sku_label = CTkLabel(details_frame, text="SKU", font=("Helvetica", 10), text_color="#909090")
        sku_label.pack(side="left", padx=(0, 5))
        sku_entry = CTkEntry(details_frame, fg_color="#0F0F0F", border_color="#4a6b5a", text_color="#e0e0e0", width=100, height=30)
        sku_entry.insert(0, variant_data["sku"])
        sku_entry.pack(side="left", padx=(0, 10))
        sku_entry.bind("<KeyRelease>", lambda e, idx=variant_idx: update_variant_field(idx, "sku", sku_entry.get()))
        
        # Barcode
        barcode_label = CTkLabel(details_frame, text="Barcode", font=("Helvetica", 10), text_color="#909090")
        barcode_label.pack(side="left", padx=(0, 5))
        barcode_entry = CTkEntry(details_frame, fg_color="#0F0F0F", border_color="#4a6b5a", text_color="#e0e0e0", width=120, height=30)
        barcode_entry.insert(0, variant_data["barcode"])
        barcode_entry.pack(side="left", padx=(0, 10))
        barcode_entry.bind("<KeyRelease>", lambda e, idx=variant_idx: update_variant_field(idx, "barcode", barcode_entry.get()))
        
        # Price
        price_label = CTkLabel(details_frame, text="Price", font=("Helvetica", 10), text_color="#909090")
        price_label.pack(side="left", padx=(0, 5))
        price_entry = CTkEntry(details_frame, placeholder_text="49.95", fg_color="#0F0F0F", border_color="#4a6b5a", text_color="#e0e0e0", width=80, height=30)
        if variant_data["price"]:
            price_entry.insert(0, variant_data["price"])
        price_entry.pack(side="left", padx=(0, 10))
        price_entry.bind("<KeyRelease>", lambda e, idx=variant_idx: update_variant_field(idx, "price", price_entry.get()))
        
        # Remove button
        remove_btn = CTkButton(details_frame, text="Remove", width=70, height=30, fg_color="#5a1a1a", hover_color="#7a2a2a", text_color="#ffffff", command=lambda idx=variant_idx: remove_variant(idx))
        remove_btn.pack(side="left")
        
        # Store variant widgets
        variant_widgets = {
            "frame": variant_frame,
            "sku": sku_entry,
            "barcode": barcode_entry,
            "price": price_entry
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

# Show page 1 initially
show_frame(page_two)

app.mainloop()