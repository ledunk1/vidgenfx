import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
import threading
import subprocess
import sys
import os
import time
import requests
from PIL import Image, ImageTk

class VideoGenFXGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("VideoGenFX - AI Video Generator")
        self.root.geometry("600x500")
        self.root.resizable(True, True)
        
        # Set window icon (if available)
        try:
            self.root.iconbitmap("static/favicon.ico")
        except:
            pass
        
        # Use dark theme by default for modern look
        self.is_dark_theme = True
        
        # Configure style
        self.setup_styles()
        
        # Server process
        self.server_process = None
        self.server_url = "http://localhost:5000"
        
        # Create GUI
        self.create_widgets()
        
        # Start server automatically
        self.start_server()
        
        # Center window
        self.center_window()
    
    def setup_styles(self):
        """Setup modern styling with proper contrast for the GUI"""
        style = ttk.Style()
        
        if self.is_dark_theme:
            # Dark theme colors
            self.bg_color = "#1e293b"
            self.fg_color = "#f8fafc"
            self.secondary_fg = "#cbd5e1"
            self.accent_color = "#4f46e5"
            self.accent_hover = "#4338ca"
            self.success_color = "#10b981"
            self.warning_color = "#f59e0b"
            self.danger_color = "#ef4444"
            self.card_bg = "#334155"
            self.border_color = "#475569"
        else:
            # Light theme colors
            self.bg_color = "#ffffff"
            self.fg_color = "#1e293b"
            self.secondary_fg = "#64748b"
            self.accent_color = "#4f46e5"
            self.accent_hover = "#4338ca"
            self.success_color = "#059669"
            self.warning_color = "#d97706"
            self.danger_color = "#dc2626"
            self.card_bg = "#f8fafc"
            self.border_color = "#e2e8f0"
        
        self.root.configure(bg=self.bg_color)
        
        # Configure main button style (Open Browser)
        style.configure("Primary.TButton",
                       background=self.accent_color,
                       foreground="black",
                       borderwidth=2,
                       relief="solid",
                       focuscolor="none",
                       padding=(25, 15),
                       font=("Segoe UI", 11, "bold"))
        
        style.map("Primary.TButton",
                 background=[("active", self.accent_hover),
                           ("pressed", "#3730a3"),
                           ("disabled", "#94a3b8")],
                 foreground=[("disabled", "#64748b")],
                 relief=[("pressed", "sunken")])
        
        # Configure secondary button style
        style.configure("Secondary.TButton",
                       background=self.card_bg,
                       foreground="black",
                       borderwidth=2,
                       relief="solid",
                       focuscolor="none",
                       padding=(15, 8),
                       font=("Segoe UI", 9))
        
        style.map("Secondary.TButton",
                 background=[("active", self.border_color),
                           ("pressed", self.secondary_fg)],
                 relief=[("pressed", "sunken")])
        
        # Configure success button style
        style.configure("Success.TButton",
                       background=self.success_color,
                       foreground="black",
                       borderwidth=2,
                       relief="solid",
                       focuscolor="none",
                       padding=(15, 8),
                       font=("Segoe UI", 9))
        
        style.map("Success.TButton",
                 background=[("active", "#047857"),
                           ("pressed", "#065f46")])
        
        # Configure warning button style
        style.configure("Warning.TButton",
                       background=self.warning_color,
                       foreground="black",
                       borderwidth=2,
                       relief="solid",
                       focuscolor="none",
                       padding=(15, 8),
                       font=("Segoe UI", 9))
        
        style.map("Warning.TButton",
                 background=[("active", "#b45309"),
                           ("pressed", "#92400e")])
        
        # Configure danger button style
        style.configure("Danger.TButton",
                       background=self.danger_color,
                       foreground="black",
                       borderwidth=2,
                       relief="solid",
                       focuscolor="none",
                       padding=(15, 8),
                       font=("Segoe UI", 9))
        
        style.map("Danger.TButton",
                 background=[("active", "#b91c1c"),
                           ("pressed", "#991b1b")])
        
        # Configure label styles
        style.configure("Modern.TLabel",
                       background=self.bg_color,
                       foreground=self.fg_color,
                       font=("Segoe UI", 10))
        
        style.configure("Title.TLabel",
                       background=self.bg_color,
                       foreground=self.fg_color,
                       font=("Segoe UI", 18, "bold"))
        
        style.configure("Subtitle.TLabel",
                       background=self.bg_color,
                       foreground=self.secondary_fg,
                       font=("Segoe UI", 10))
        
        style.configure("Small.TLabel",
                       background=self.bg_color,
                       foreground=self.secondary_fg,
                       font=("Segoe UI", 8))
        
        # Configure frame styles
        style.configure("Card.TFrame",
                       background=self.card_bg,
                       relief="solid",
                       borderwidth=1)
        
        style.configure("Modern.TFrame",
                       background=self.bg_color)
        
        # Configure LabelFrame style
        style.configure("Modern.TLabelframe",
                       background=self.bg_color,
                       foreground=self.fg_color,
                       borderwidth=2,
                       relief="solid")
        
        style.configure("Modern.TLabelframe.Label",
                       background=self.bg_color,
                       foreground=self.fg_color,
                       font=("Segoe UI", 10, "bold"))
    
    def create_widgets(self):
        """Create and layout GUI widgets"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, style="Modern.TFrame")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Header section
        self.create_header(main_frame)
        
        # Status section
        self.create_status_section(main_frame)
        
        # Action buttons section
        self.create_action_section(main_frame)
        
        # Features section
        self.create_features_section(main_frame)
        
        # Footer
        self.create_footer(main_frame)
    
    def create_header(self, parent):
        """Create header with logo and title"""
        header_frame = ttk.Frame(parent, style="Modern.TFrame")
        header_frame.pack(fill=tk.X, pady=(0, 30))
        
        # Logo/Icon (using text for now)
        icon_label = ttk.Label(header_frame, text="🎬", font=("Segoe UI", 36), 
                              background=self.bg_color)
        icon_label.pack()
        
        # Title
        title_label = ttk.Label(header_frame, text="VideoGenFX", style="Title.TLabel")
        title_label.pack(pady=(10, 5))
        
        # Subtitle
        subtitle_label = ttk.Label(header_frame, 
                                  text="AI-Powered Video Generator with GPU Acceleration",
                                  style="Subtitle.TLabel")
        subtitle_label.pack()
    
    def create_status_section(self, parent):
        """Create server status section"""
        status_frame = ttk.LabelFrame(parent, text="Server Status", 
                                     style="Modern.TLabelframe", padding=20)
        status_frame.pack(fill=tk.X, pady=(0, 20))
        
        # Status indicator
        self.status_frame_inner = ttk.Frame(status_frame, style="Modern.TFrame")
        self.status_frame_inner.pack(fill=tk.X)
        
        self.status_label = ttk.Label(self.status_frame_inner, 
                                     text="🔄 Starting server...", 
                                     style="Modern.TLabel",
                                     font=("Segoe UI", 11))
        self.status_label.pack(side=tk.LEFT)
        
        # URL label
        self.url_label = ttk.Label(status_frame, 
                                  text=f"Server URL: {self.server_url}",
                                  style="Subtitle.TLabel")
        self.url_label.pack(pady=(10, 0))
    
    def create_action_section(self, parent):
        """Create main action buttons with high contrast"""
        action_frame = ttk.Frame(parent, style="Modern.TFrame")
        action_frame.pack(fill=tk.X, pady=(0, 30))
        
        # Open Browser button (main action) - High contrast primary button
        self.browser_btn = ttk.Button(action_frame,
                                     text="🌐 Open VideoGenFX in Browser",
                                     style="Primary.TButton",
                                     command=self.open_browser,
                                     state=tk.DISABLED)
        self.browser_btn.pack(fill=tk.X, pady=(0, 15))
        
        # Secondary buttons frame
        secondary_frame = ttk.Frame(action_frame, style="Modern.TFrame")
        secondary_frame.pack(fill=tk.X)
        
        # Create a grid for better layout
        secondary_frame.columnconfigure(0, weight=1)
        secondary_frame.columnconfigure(1, weight=1)
        secondary_frame.columnconfigure(2, weight=1)
        
        # Restart server button
        restart_btn = ttk.Button(secondary_frame,
                                text="🔄 Restart Server",
                                style="Success.TButton",
                                command=self.restart_server)
        restart_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5))
        
        # Stop server button
        stop_btn = ttk.Button(secondary_frame,
                             text="⏹️ Stop Server",
                             style="Danger.TButton",
                             command=self.stop_server)
        stop_btn.grid(row=0, column=1, sticky="ew", padx=5)
        
        # Settings button
        settings_btn = ttk.Button(secondary_frame,
                                 text="⚙️ Settings",
                                 style="Secondary.TButton",
                                 command=self.open_settings)
        settings_btn.grid(row=0, column=2, sticky="ew", padx=(5, 0))
    
    def create_features_section(self, parent):
        """Create features showcase with better contrast"""
        features_frame = ttk.LabelFrame(parent, text="Features", 
                                       style="Modern.TLabelframe", padding=20)
        features_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        features = [
            ("🤖", "AI-Powered", "Uses Gemini AI for intelligent prompt generation"),
            ("🎨", "ImageFX Integration", "High-quality image generation with Google ImageFX"),
            ("🎬", "Auto Video Editing", "Ken Burns effects, transitions, and audio sync"),
            ("⚡", "GPU Acceleration", "Hardware-accelerated encoding for faster processing"),
            ("📱", "Multiple Formats", "Support for portrait and landscape videos"),
            ("🎵", "Audio Sync", "Automatic synchronization with narration")
        ]
        
        # Create grid of features
        for i, (icon, title, desc) in enumerate(features):
            row = i // 2
            col = i % 2
            
            feature_frame = ttk.Frame(features_frame, style="Card.TFrame")
            feature_frame.grid(row=row, column=col, sticky="ew", padx=8, pady=8)
            
            # Inner frame for padding
            inner_frame = ttk.Frame(feature_frame, style="Modern.TFrame")
            inner_frame.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
            
            # Icon
            icon_label = ttk.Label(inner_frame, text=icon, font=("Segoe UI", 20),
                                  background=self.card_bg if hasattr(self, 'card_bg') else self.bg_color)
            icon_label.pack(side=tk.LEFT, padx=(0, 15))
            
            # Text
            text_frame = ttk.Frame(inner_frame, style="Modern.TFrame")
            text_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            title_label = ttk.Label(text_frame, text=title, 
                                   style="Modern.TLabel", 
                                   font=("Segoe UI", 10, "bold"))
            title_label.pack(anchor=tk.W)
            
            desc_label = ttk.Label(text_frame, text=desc, 
                                  style="Small.TLabel", 
                                  font=("Segoe UI", 9))
            desc_label.pack(anchor=tk.W)
        
        # Configure grid weights
        features_frame.columnconfigure(0, weight=1)
        features_frame.columnconfigure(1, weight=1)
    
    def create_footer(self, parent):
        """Create footer with additional info"""
        footer_frame = ttk.Frame(parent, style="Modern.TFrame")
        footer_frame.pack(fill=tk.X, pady=(10, 0))
        
        footer_label = ttk.Label(footer_frame,
                                text="VideoGenFX v1.0 - Transform your text into stunning videos",
                                style="Small.TLabel",
                                font=("Segoe UI", 9))
        footer_label.pack()
    
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def start_server(self):
        """Start the Flask server in a separate thread"""
        def run_server():
            try:
                # Check if server is already running
                if self.check_server_status():
                    self.update_status("✅ Server already running", True)
                    return
                
                # Start new server process
                self.server_process = subprocess.Popen([
                    sys.executable, "app.py"
                ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Wait for server to start
                max_attempts = 30
                for attempt in range(max_attempts):
                    time.sleep(1)
                    if self.check_server_status():
                        self.update_status("✅ Server running", True)
                        return
                    
                    # Update status with dots animation
                    dots = "." * ((attempt % 3) + 1)
                    self.update_status(f"🔄 Starting server{dots}", False)
                
                # If we get here, server failed to start
                self.update_status("❌ Failed to start server", False)
                
            except Exception as e:
                self.update_status(f"❌ Error: {str(e)}", False)
        
        # Run in separate thread to avoid blocking GUI
        threading.Thread(target=run_server, daemon=True).start()
    
    def check_server_status(self):
        """Check if the server is responding"""
        try:
            response = requests.get(self.server_url, timeout=2)
            return response.status_code == 200
        except:
            return False
    
    def update_status(self, message, server_ready):
        """Update status label and enable/disable browser button"""
        self.status_label.config(text=message)
        if server_ready:
            self.browser_btn.config(state=tk.NORMAL)
            # Change button text to indicate it's ready
            self.browser_btn.config(text="🌐 Open VideoGenFX in Browser (Ready!)")
        else:
            self.browser_btn.config(state=tk.DISABLED)
            self.browser_btn.config(text="🌐 Open VideoGenFX in Browser")
    
    def open_browser(self):
        """Open the web application in default browser"""
        try:
            webbrowser.open(self.server_url)
            # Show success message
            messagebox.showinfo("Success", "VideoGenFX opened in your default browser!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open browser: {str(e)}")
    
    def restart_server(self):
        """Restart the Flask server"""
        self.update_status("🔄 Restarting server...", False)
        self.stop_server()
        time.sleep(2)
        self.start_server()
    
    def stop_server(self):
        """Stop the Flask server"""
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
            except:
                try:
                    self.server_process.kill()
                except:
                    pass
            finally:
                self.server_process = None
        
        self.update_status("⏹️ Server stopped", False)
    
    def open_settings(self):
        """Open settings in browser"""
        if self.check_server_status():
            webbrowser.open(f"{self.server_url}/settings")
        else:
            messagebox.showwarning("Warning", "Server is not running. Please start the server first.")
    
    def on_closing(self):
        """Handle window closing event"""
        if messagebox.askokcancel("Quit", "Do you want to quit? This will stop the server."):
            self.stop_server()
            self.root.destroy()
    
    def run(self):
        """Start the GUI application"""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()

def main():
    """Main entry point"""
    try:
        app = VideoGenFXGUI()
        app.run()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to start application: {str(e)}")

if __name__ == "__main__":
    main()