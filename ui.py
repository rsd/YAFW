import os
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
from version import __version__

# Configure global CustomTkinter settings
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")  # fallback theme

# Color palette definition for a premium look
BG_COLOR = "#121214"
CARD_BG = "#1e1e24"
ACCENT_COLOR = "#7c5dfa"      # Sleek violet
ACCENT_HOVER = "#9067f9"
TEXT_COLOR = "#f4f4f6"
TEXT_MUTED = "#8e8e9f"
BORDER_COLOR = "#2a2a32"

class YafwApp(ctk.CTk):
    def __init__(self, on_start_processing, on_cancel_processing):
        super().__init__()
        
        self.on_start_processing = on_start_processing
        self.on_cancel_processing = on_cancel_processing
        
        self.selected_file_path = None
        self.intro_image_path = None
        self.advanced_visible = False
        
        # Configure Main Window
        self.title("YAFW - Video Optimizer")
        self.geometry("640x700")
        self.minsize(580, 620)
        self.configure(fg_color=BG_COLOR)
        
        # Set Window Icon (topbar and taskbar on Windows)
        try:
            import sys
            import ctypes
            # Force Windows to associate the taskbar shortcut with this window explicitly
            if sys.platform == "win32":
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("yafw.videooptimizer.1.1")
            
            is_frozen = getattr(sys, 'frozen', False)
            if is_frozen:
                bundle_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
                icon_path = os.path.join(bundle_dir, "assets", "icon.ico")
            else:
                icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "icon.ico")
                
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
        except Exception:
            pass
        
        # Grid Configuration
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Main Container
        self.main_container = ctk.CTkFrame(self, fg_color=BG_COLOR, corner_radius=0)
        self.main_container.grid(row=0, column=0, sticky="nsew", padx=24, pady=24)
        self.main_container.grid_columnconfigure(0, weight=1)
        
        # Title Header
        self.create_header()
        
        # File Picker / Drop Zone Target
        self.create_file_picker()
        
        # Option Cards (Cut, Speed, Boost)
        self.create_option_cards()
        
        # Noise Preset Selection
        self.create_noise_preset_menu()
        
        # Intro Image Overlay Section
        self.create_intro_image_section()
        
        # Collapsible Advanced Settings Panel
        self.create_advanced_settings()
        
        # Progress / Output Area
        self.create_progress_area()
        
        # Large Action Button
        self.create_action_buttons()

    def create_header(self):
        header_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 20))
        header_frame.grid_columnconfigure(0, weight=1)
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="YAFW", 
            font=ctk.CTkFont(family="Inter", size=28, weight="bold"),
            text_color=TEXT_COLOR
        )
        title_label.grid(row=0, column=0, sticky="w")
        
        subtitle_label = ctk.CTkLabel(
            header_frame, 
            text=f"Yet Another FFmpeg Wrapper v{__version__} • Lecture & Zoom Optimizer", 
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=TEXT_MUTED
        )
        subtitle_label.grid(row=1, column=0, sticky="w", pady=(2, 0))

    def create_file_picker(self):
        # File picker box simulating a drag-and-drop zone
        self.picker_frame = ctk.CTkFrame(
            self.main_container, 
            fg_color=CARD_BG, 
            bg_color=BG_COLOR,
            border_color=BORDER_COLOR, 
            border_width=1,
            corner_radius=12,
            height=120
        )
        self.picker_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
        self.picker_frame.grid_propagate(False)
        self.picker_frame.grid_columnconfigure(0, weight=1)
        self.picker_frame.grid_rowconfigure(0, weight=1)
        
        # Interaction overlay
        self.picker_btn = ctk.CTkButton(
            self.picker_frame,
            text="Select Video File\n(Click to browse movies)",
            font=ctk.CTkFont(family="Inter", size=14, weight="normal"),
            text_color=TEXT_COLOR,
            fg_color="transparent",
            bg_color=CARD_BG,
            hover_color=BORDER_COLOR,
            corner_radius=12,
            command=self.browse_file
        )
        self.picker_btn.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)

    def create_option_cards(self):
        # Frame containing three option blocks side by side
        options_frame = ctk.CTkFrame(self.main_container, fg_color=BG_COLOR)
        options_frame.grid(row=2, column=0, sticky="ew", pady=(0, 16))
        
        # Configure columns equally
        options_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="equal")
        
        # Card 1: Cut Silences
        self.card_cut = ctk.CTkFrame(options_frame, fg_color=CARD_BG, bg_color=BG_COLOR, border_color=BORDER_COLOR, border_width=1, corner_radius=10)
        self.card_cut.grid(row=0, column=0, padx=(0, 8), sticky="nsew")
        self.card_cut.grid_columnconfigure(0, weight=1)
        self.cut_label = tk.Label(self.card_cut, text="Cut Silences", font=("Inter", 13, "bold"), fg=TEXT_COLOR, bg=CARD_BG)
        self.cut_label.grid(row=0, column=0, pady=(12, 4))
        self.cut_switch = ctk.CTkSwitch(self.card_cut, text="", progress_color=ACCENT_COLOR, fg_color="#3a3a44", bg_color=CARD_BG, width=45, command=self.toggle_cut_settings)
        self.cut_switch.select() # Default ON
        self.cut_switch.grid(row=1, column=0, pady=(0, 12))
        
        # Card 2: Speed Up 1.2x
        self.card_speed = ctk.CTkFrame(options_frame, fg_color=CARD_BG, bg_color=BG_COLOR, border_color=BORDER_COLOR, border_width=1, corner_radius=10)
        self.card_speed.grid(row=0, column=1, padx=4, sticky="nsew")
        self.card_speed.grid_columnconfigure(0, weight=1)
        self.speed_label = tk.Label(self.card_speed, text="Speed Up (1.2x)", font=("Inter", 13, "bold"), fg=TEXT_COLOR, bg=CARD_BG)
        self.speed_label.grid(row=0, column=0, pady=(12, 4))
        self.speed_switch = ctk.CTkSwitch(self.card_speed, text="", progress_color=ACCENT_COLOR, fg_color="#3a3a44", bg_color=CARD_BG, width=45)
        self.speed_switch.select() # Default ON
        self.speed_switch.grid(row=1, column=0, pady=(0, 12))
        
        # Card 3: Voice Boost
        self.card_boost = ctk.CTkFrame(options_frame, fg_color=CARD_BG, bg_color=BG_COLOR, border_color=BORDER_COLOR, border_width=1, corner_radius=10)
        self.card_boost.grid(row=0, column=2, padx=(8, 0), sticky="nsew")
        self.card_boost.grid_columnconfigure(0, weight=1)
        self.boost_label = tk.Label(self.card_boost, text="Voice Boost", font=("Inter", 13, "bold"), fg=TEXT_COLOR, bg=CARD_BG)
        self.boost_label.grid(row=0, column=0, pady=(12, 4))
        self.boost_switch = ctk.CTkSwitch(self.card_boost, text="", progress_color=ACCENT_COLOR, fg_color="#3a3a44", bg_color=CARD_BG, width=45)
        self.boost_switch.select() # Default ON
        self.boost_switch.grid(row=1, column=0, pady=(0, 12))

    def create_noise_preset_menu(self):
        # Simple dropdown configuration for noise levels
        self.preset_frame = ctk.CTkFrame(self.main_container, fg_color=BG_COLOR)
        self.preset_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))
        self.preset_frame.grid_columnconfigure(1, weight=1)
        
        preset_label = ctk.CTkLabel(
            self.preset_frame, 
            text="Noise Sensitivity Preset:", 
            font=ctk.CTkFont(family="Inter", size=13),
            text_color=TEXT_COLOR,
            bg_color=BG_COLOR
        )
        preset_label.grid(row=0, column=0, sticky="w", padx=(0, 12))
        
        self.preset_menu = ctk.CTkOptionMenu(
            self.preset_frame,
            values=["Quiet Room (Low -35dB)", "Normal Room (Medium -30dB)", "Noisy Room (High -25dB)"],
            fg_color=CARD_BG,
            bg_color=BG_COLOR,
            button_color=BORDER_COLOR,
            button_hover_color=ACCENT_COLOR,
            dropdown_fg_color=CARD_BG,
            dropdown_hover_color=ACCENT_COLOR,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(family="Inter", size=13),
            corner_radius=8
        )
        self.preset_menu.set("Normal Room (Medium -30dB)")
        self.preset_menu.grid(row=0, column=1, sticky="ew")

    def create_advanced_settings(self):
        # Header button to toggle view
        self.advanced_header = ctk.CTkButton(
            self.main_container,
            text="▼ Advanced Settings",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=TEXT_MUTED,
            fg_color="transparent",
            bg_color=BG_COLOR,
            hover=False,
            anchor="w",
            command=self.toggle_advanced
        )
        self.advanced_header.grid(row=5, column=0, sticky="ew", pady=(0, 10))
        
        # Advanced Content Card (Hidden by default)
        self.advanced_frame = ctk.CTkFrame(
            self.main_container, 
            fg_color=CARD_BG, 
            bg_color=BG_COLOR,
            border_color=BORDER_COLOR, 
            border_width=1,
            corner_radius=10
        )
        
        # Structure inside advanced frame
        self.advanced_frame.grid_columnconfigure(1, weight=1)
        
        # CRF Slider (H.265 quality)
        crf_title = ctk.CTkLabel(self.advanced_frame, text="Quality (CRF):", font=ctk.CTkFont(family="Inter", size=12), text_color=TEXT_COLOR, bg_color=CARD_BG)
        crf_title.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 8))
        
        slider_frame = ctk.CTkFrame(self.advanced_frame, fg_color=CARD_BG, bg_color=CARD_BG)
        slider_frame.grid(row=0, column=1, sticky="ew", padx=(0, 16), pady=(16, 8))
        slider_frame.grid_columnconfigure(0, weight=1)
        
        self.crf_slider = ctk.CTkSlider(
            slider_frame, 
            from_=18, 
            to=35, 
            number_of_steps=17, 
            button_color=ACCENT_COLOR, 
            button_hover_color=ACCENT_HOVER,
            progress_color=ACCENT_COLOR,
            bg_color=CARD_BG,
            command=self.update_crf_val
        )
        self.crf_slider.set(26)
        self.crf_slider.grid(row=0, column=0, sticky="ew")
        
        self.crf_val_lbl = ctk.CTkLabel(
            slider_frame, 
            text="26 (Highly Compressed)", 
            font=ctk.CTkFont(family="Inter", size=11), 
            text_color=TEXT_MUTED,
            bg_color=CARD_BG,
            width=140
        )
        self.crf_val_lbl.grid(row=0, column=1, padx=(12, 0))
 
        # FFmpeg Preset
        preset_title = ctk.CTkLabel(self.advanced_frame, text="Encoding Preset:", font=ctk.CTkFont(family="Inter", size=12), text_color=TEXT_COLOR, bg_color=CARD_BG)
        preset_title.grid(row=1, column=0, sticky="w", padx=16, pady=8)
        self.adv_preset_menu = ctk.CTkOptionMenu(
            self.advanced_frame,
            values=["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow"],
            fg_color=BG_COLOR,
            bg_color=CARD_BG,
            button_color=BORDER_COLOR,
            button_hover_color=ACCENT_COLOR,
            dropdown_fg_color=CARD_BG,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(family="Inter", size=12),
            corner_radius=8
        )
        self.adv_preset_menu.set("medium")
        self.adv_preset_menu.grid(row=1, column=1, sticky="ew", padx=(0, 16), pady=8)
 
        # Custom Silence Threshold
        thresh_title = ctk.CTkLabel(self.advanced_frame, text="Silence Threshold:", font=ctk.CTkFont(family="Inter", size=12), text_color=TEXT_COLOR, bg_color=CARD_BG)
        thresh_title.grid(row=2, column=0, sticky="w", padx=16, pady=8)
        
        thresh_frame = ctk.CTkFrame(self.advanced_frame, fg_color=CARD_BG, bg_color=CARD_BG)
        thresh_frame.grid(row=2, column=1, sticky="ew", padx=(0, 16), pady=8)
        thresh_frame.grid_columnconfigure(0, weight=1)
        
        self.thresh_entry = ctk.CTkEntry(
            thresh_frame, 
            placeholder_text="-30dB", 
            fg_color=BG_COLOR, 
            border_color=BORDER_COLOR,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(family="Inter", size=12),
            bg_color=CARD_BG,
            corner_radius=8
        )
        self.thresh_entry.insert(0, "-30dB")
        self.thresh_entry.grid(row=0, column=0, sticky="ew")
        
        thresh_hint = ctk.CTkLabel(thresh_frame, text="dB or %", font=ctk.CTkFont(family="Inter", size=11), text_color=TEXT_MUTED, bg_color=CARD_BG)
        thresh_hint.grid(row=0, column=1, padx=(12, 0))
 
        # Margin Size
        margin_title = ctk.CTkLabel(self.advanced_frame, text="Cut Margin:", font=ctk.CTkFont(family="Inter", size=12), text_color=TEXT_COLOR, bg_color=CARD_BG)
        margin_title.grid(row=3, column=0, sticky="w", padx=16, pady=(8, 16))
        
        margin_frame = ctk.CTkFrame(self.advanced_frame, fg_color=CARD_BG, bg_color=CARD_BG)
        margin_frame.grid(row=3, column=1, sticky="ew", padx=(0, 16), pady=(8, 16))
        margin_frame.grid_columnconfigure(0, weight=1)
        
        self.margin_slider = ctk.CTkSlider(
            margin_frame, 
            from_=0.0, 
            to=1.0, 
            number_of_steps=20, 
            button_color=ACCENT_COLOR, 
            button_hover_color=ACCENT_HOVER,
            progress_color=ACCENT_COLOR,
            bg_color=CARD_BG,
            command=self.update_margin_val
        )
        self.margin_slider.set(0.2)
        self.margin_slider.grid(row=0, column=0, sticky="ew")
        
        self.margin_val_lbl = ctk.CTkLabel(
            margin_frame, 
            text="0.20s", 
            font=ctk.CTkFont(family="Inter", size=11), 
            text_color=TEXT_MUTED,
            bg_color=CARD_BG,
            width=50
        )
        self.margin_val_lbl.grid(row=0, column=1, padx=(12, 0))

    def create_progress_area(self):
        # Progress area is hidden initially
        self.progress_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        self.progress_frame.grid_columnconfigure(0, weight=1)
        
        self.status_lbl = ctk.CTkLabel(
            self.progress_frame,
            text="Optimizing and encoding video...",
            font=ctk.CTkFont(family="Inter", size=13, weight="normal"),
            text_color=TEXT_COLOR,
            anchor="w"
        )
        self.status_lbl.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            progress_color=ACCENT_COLOR,
            fg_color="#1d1d22",
            height=10
        )
        self.progress_bar.set(0.0)
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(0, 12))

    def create_action_buttons(self):
        # Bottom area buttons
        self.actions_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.actions_frame.grid(row=7, column=0, sticky="ew", pady=(20, 0))
        self.actions_frame.grid_columnconfigure(0, weight=1)
        
        self.optimize_btn = ctk.CTkButton(
            self.actions_frame,
            text="Optimize Video",
            font=ctk.CTkFont(family="Inter", size=15, weight="bold"),
            text_color="#ffffff",
            fg_color=ACCENT_COLOR,
            hover_color=ACCENT_HOVER,
            height=48,
            corner_radius=10,
            command=self.on_optimize_clicked
        )
        self.optimize_btn.grid(row=0, column=0, sticky="ew")
        
        self.cancel_btn = ctk.CTkButton(
            self.actions_frame,
            text="Cancel Processing",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            text_color=TEXT_COLOR,
            fg_color="#e03131",
            hover_color="#fa5252",
            height=40,
            corner_radius=10,
            command=self.on_cancel_clicked
        )
        # Cancel button is hidden by default

    def toggle_advanced(self):
        if self.advanced_visible:
            self.advanced_frame.grid_forget()
            self.advanced_header.configure(text="▼ Advanced Settings")
            self.advanced_visible = False
        else:
            self.advanced_frame.grid(row=6, column=0, sticky="ew", pady=(0, 16))
            self.advanced_header.configure(text="▲ Advanced Settings")
            self.advanced_visible = True

    def create_intro_image_section(self):
        # Frame containing intro image settings
        self.intro_frame = ctk.CTkFrame(
            self.main_container, 
            fg_color=CARD_BG, 
            bg_color=BG_COLOR,
            border_color=BORDER_COLOR, 
            border_width=1,
            corner_radius=12
        )
        self.intro_frame.grid(row=4, column=0, sticky="ew", pady=(0, 20))
        self.intro_frame.grid_columnconfigure(1, weight=1)
        self.intro_frame.grid_columnconfigure(2, weight=0)
        
        # Row 0: Switch
        self.intro_switch = ctk.CTkSwitch(
            self.intro_frame,
            text="Overlay Intro Image (First 1s)",
            font=ctk.CTkFont(family="Inter", size=13, weight="bold"),
            progress_color=ACCENT_COLOR,
            fg_color="#3a3a44",
            bg_color=CARD_BG,
            command=self.toggle_intro_image_settings
        )
        self.intro_switch.select()  # Default ON
        self.intro_switch.grid(row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(12, 8))
        
        # Row 1: File Picker Button
        self.intro_picker_btn = ctk.CTkButton(
            self.intro_frame,
            text="Select Intro Image (PNG/JPG)",
            font=ctk.CTkFont(family="Inter", size=12),
            text_color=TEXT_MUTED,
            fg_color=BG_COLOR,
            hover_color=BORDER_COLOR,
            corner_radius=8,
            command=self.browse_intro_image
        )
        self.intro_picker_btn.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(16, 8), pady=(0, 12))
        
        # Row 1 (Col 2): Scale Mode Dropdown
        self.intro_scale_menu = ctk.CTkOptionMenu(
            self.intro_frame,
            values=["Use as is", "Scale to Fit (No Crop)", "Scale to Fill (Crop)"],
            fg_color=BG_COLOR,
            bg_color=CARD_BG,
            button_color=BORDER_COLOR,
            button_hover_color=ACCENT_COLOR,
            dropdown_fg_color=CARD_BG,
            text_color=TEXT_COLOR,
            font=ctk.CTkFont(family="Inter", size=12),
            corner_radius=8,
            width=180
        )
        self.intro_scale_menu.set("Scale to Fit (No Crop)")
        self.intro_scale_menu.grid(row=1, column=2, sticky="e", padx=(8, 16), pady=(0, 12))

    def browse_intro_image(self):
        file_path = filedialog.askopenfilename(
            title="Select Intro Image",
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.jfif *.gif *.webp"), ("All files", "*.*")]
        )
        if file_path:
            self.intro_image_path = file_path
            filename = os.path.basename(file_path)
            self.intro_picker_btn.configure(
                text=f"Image: {filename}",
                text_color=ACCENT_COLOR
            )

    def toggle_intro_image_settings(self):
        if self.intro_switch.get():
            self.intro_picker_btn.configure(state="normal")
            self.intro_scale_menu.configure(state="normal")
        else:
            self.intro_picker_btn.configure(state="disabled")
            self.intro_scale_menu.configure(state="disabled")

    def toggle_cut_settings(self):
        # Disable/enable noise preset menu if Cutting silences is toggled
        if self.cut_switch.get():
            self.preset_menu.configure(state="normal")
            self.thresh_entry.configure(state="normal")
            self.margin_slider.configure(state="normal")
        else:
            self.preset_menu.configure(state="disabled")
            self.thresh_entry.configure(state="disabled")
            self.margin_slider.configure(state="disabled")

    def update_crf_val(self, val):
        val = int(val)
        desc = "Medium"
        if val <= 20:
            desc = "Near Lossless"
        elif val <= 24:
            desc = "High Quality"
        elif val <= 28:
            desc = "Highly Compressed"
        else:
            desc = "Extreme Compression"
        self.crf_val_lbl.configure(text=f"{val} ({desc})")

    def update_margin_val(self, val):
        self.margin_val_lbl.configure(text=f"{val:.2f}s")

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.mkv *.mov *.avi *.webm"), ("All files", "*.*")]
        )
        if file_path:
            self.selected_file_path = file_path
            filename = os.path.basename(file_path)
            self.picker_btn.configure(
                text=f"Selected File:\n{filename}",
                text_color=ACCENT_COLOR
            )

    def get_config(self):
        # Extract configurations to feed the processor
        cut_silence = bool(self.cut_switch.get())
        speed_up = bool(self.speed_switch.get())
        voice_boost = bool(self.boost_switch.get())
        
        # Silence threshold and margin resolution
        if self.advanced_visible:
            noise_threshold = self.thresh_entry.get().strip()
            crf = int(self.crf_slider.get())
            preset = self.adv_preset_menu.get()
            margin = float(self.margin_slider.get())
        else:
            # Map presets
            preset_val = self.preset_menu.get()
            if "Quiet" in preset_val:
                noise_threshold = "-35dB"
            elif "Noisy" in preset_val:
                noise_threshold = "-25dB"
            else:
                noise_threshold = "-30dB"
            
            crf = 26  # default optimized for slide presentations
            preset = "medium"
            margin = 0.2
            
        intro_image_enabled = bool(self.intro_switch.get())
        intro_mode_val = self.intro_scale_menu.get()
        if "Fit" in intro_mode_val:
            intro_mode = "fit"
        elif "Fill" in intro_mode_val:
            intro_mode = "fill"
        else:
            intro_mode = "as_is"

        return {
            "cut_silence": cut_silence,
            "speed_up": speed_up,
            "voice_boost": voice_boost,
            "noise_threshold": noise_threshold,
            "crf": crf,
            "preset": preset,
            "margin": margin,
            "intro_image_enabled": intro_image_enabled,
            "intro_image_path": self.intro_image_path,
            "intro_image_scale_mode": intro_mode
        }

    def on_optimize_clicked(self):
        if not self.selected_file_path:
            tk.messagebox.showwarning("No File Selected", "Please select a video file to optimize.")
            return
            
        if self.intro_switch.get() and not self.intro_image_path:
            tk.messagebox.showwarning("No Image Selected", "Please select an intro image or disable the intro image overlay.")
            return
            
        # Select output destination
        default_name = "optimized_" + os.path.basename(self.selected_file_path)
        output_path = filedialog.asksaveasfilename(
            title="Save Optimized Video As",
            initialfile=default_name,
            filetypes=[("MP4 Video", "*.mp4"), ("All files", "*.*")]
        )
        
        if not output_path:
            return
            
        # Configure GUI for Processing state
        self.set_processing_ui(True)
        
        # Start backend processing
        self.on_start_processing(self.selected_file_path, output_path, self.get_config())

    def on_cancel_clicked(self):
        if tk.messagebox.askyesno("Cancel Processing", "Are you sure you want to stop processing?"):
            self.on_cancel_processing()
            self.set_processing_ui(False)

    def set_processing_ui(self, is_processing):
        if is_processing:
            # Hide controls
            self.picker_frame.grid_forget()
            self.card_cut.master.grid_forget()
            self.preset_frame.grid_forget()
            self.intro_frame.grid_forget()
            self.advanced_header.grid_forget()
            if self.advanced_visible:
                self.advanced_frame.grid_forget()
                
            # Show progress
            self.progress_frame.grid(row=1, column=0, sticky="ew", pady=40)
            self.progress_bar.set(0.0)
            self.status_lbl.configure(text="Initializing optimization...")
            
            # Update action buttons
            self.optimize_btn.grid_forget()
            self.cancel_btn.grid(row=0, column=0, sticky="ew")
        else:
            # Hide progress
            self.progress_frame.grid_forget()
            
            # Show controls
            self.picker_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))
            self.card_cut.master.grid(row=2, column=0, sticky="ew", pady=(0, 16))
            self.preset_frame.grid(row=3, column=0, sticky="ew", pady=(0, 20))
            self.intro_frame.grid(row=4, column=0, sticky="ew", pady=(0, 20))
            self.advanced_header.grid(row=5, column=0, sticky="ew", pady=(0, 10))
            if self.advanced_visible:
                self.advanced_frame.grid(row=6, column=0, sticky="ew", pady=(0, 16))
                
            # Update action buttons
            self.cancel_btn.grid_forget()
            self.optimize_btn.grid(row=0, column=0, sticky="ew")

    def update_progress(self, percent, status_text):
        self.progress_bar.set(percent / 100.0)
        self.status_lbl.configure(text=status_text)
        
        # When complete or error, reset the UI
        if percent == 100 or percent <= 0:
            if "Error" in status_text or "failed" in status_text or "cancelled" in status_text:
                tk.messagebox.showerror("Processing Failed", status_text)
            elif percent == 100:
                tk.messagebox.showinfo("Optimization Complete", "Your optimized video has been exported successfully!")
            
            self.set_processing_ui(False)
