from flask import Flask, render_template
from dotenv import load_dotenv
import os
import atexit
import sys
import threading
import webbrowser
import time
import requests
from tkinter import Tk, Button, Label, Frame, messagebox
from tkinter import ttk

# Import routes
from routes.main_routes import main_bp
from routes.api_routes import api_bp
from routes.video_routes import video_bp
from routes.file_routes import file_bp
from routes.tts_video_routes import tts_video_bp
from routes.pollinations_routes import pollinations_bp

# Import GPU detection
from utils.gpu_utils import gpu_detector

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Register blueprints
app.register_blueprint(main_bp)
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(video_bp, url_prefix='/video')
app.register_blueprint(file_bp, url_prefix='/files')
app.register_blueprint(tts_video_bp, url_prefix='/tts-video')
app.register_blueprint(pollinations_bp, url_prefix='/pollinations')

# Global variables for server status
server_running = False
server_url = ""
root = None

def get_absolute_path(relative_path):
    """Get absolute path, handling PyInstaller and different environments"""
    try:
        # Get the directory where the executable or script is located
        if getattr(sys, 'frozen', False):
            # If running from PyInstaller executable
            base_path = os.path.dirname(sys.executable)
        else:
            # Normal Python execution - get project root
            base_path = os.path.dirname(os.path.abspath(__file__))
        
        # Combine with relative path
        full_path = os.path.join(base_path, relative_path)
        
        # Normalize path for Windows
        full_path = os.path.normpath(full_path)
        
        return full_path
        
    except Exception as e:
        print(f"Error resolving path {relative_path}: {e}")
        # Fallback to relative path
        return os.path.normpath(relative_path)

# Create necessary directories with absolute paths
os.makedirs(get_absolute_path('uploads'), exist_ok=True)
os.makedirs(get_absolute_path('outputs/images'), exist_ok=True)
os.makedirs(get_absolute_path('outputs/videos'), exist_ok=True)
os.makedirs(get_absolute_path('outputs/audio'), exist_ok=True)
os.makedirs(get_absolute_path('temp'), exist_ok=True)

def get_host_and_port():
    """Get host and port for deployment"""
    # For VPS deployment
    host = os.getenv('HOST', '127.0.0.1')  # Default to localhost for GUI mode
    port = int(os.getenv('PORT', 5000))  # Use PORT env var for cloud deployment
    
    return host, port

def is_production():
    """Check if running in production environment"""
    return os.getenv('FLASK_ENV') == 'production' or os.getenv('ENVIRONMENT') == 'production'

def startup_tasks():
    """Tasks to run when the application starts"""
    print("🚀 VideoGenFX Server Starting...")
    print("🔍 Detecting GPU hardware...")
    
    # GPU detection is already done in gpu_utils import
    if gpu_detector.has_gpu_acceleration():
        print("✅ GPU acceleration available for faster video processing")
    else:
        print("ℹ️ Using CPU processing (consider adding GPU for better performance)")

def check_server_status(url):
    """Check if the server is running"""
    try:
        response = requests.get(f"{url}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def wait_for_server(url, max_attempts=30):
    """Wait for the server to be ready"""
    for attempt in range(max_attempts):
        if check_server_status(url):
            return True
        time.sleep(1)
    return False

def open_browser():
    """Open the browser to the server URL"""
    global server_url
    if server_url:
        try:
            webbrowser.open(server_url)
            messagebox.showinfo("Success", f"Browser opened to {server_url}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open browser: {e}")
    else:
        messagebox.showwarning("Warning", "Server URL not available")

def stop_server():
    """Stop the server (close the application)"""
    global root
    if messagebox.askyesno("Confirm", "Are you sure you want to stop the server?"):
        if root:
            root.quit()
        sys.exit(0)

def update_server_status(status_label, url_label, open_btn, host, port):
    """Update server status in the UI"""
    global server_running, server_url
    
    server_url = f"http://{host}:{port}"
    
    def check_status():
        global server_running
        startup_checks = 0
        max_startup_checks = 15  # Check for 30 seconds during startup
        
        while startup_checks < max_startup_checks:
            try:
                if check_server_status(server_url):
                    server_running = True
                    status_label.config(text="🟢 Server Running", foreground="green")
                    url_label.config(text=f"URL: {server_url}")
                    open_btn.config(state="normal")
                    print(f"✅ Server is ready at {server_url}")
                    break
                else:
                    startup_checks += 1
                    time.sleep(2)
                    
            except Exception as e:
                startup_checks += 1
                time.sleep(2)
        
        # If server didn't start after max attempts
        if not server_running:
            status_label.config(text="❌ Server Failed to Start", foreground="red")
            print("❌ Server failed to start within timeout period")
    
    # Start status checking in a separate thread
    status_thread = threading.Thread(target=check_status, daemon=True)
    status_thread.start()

def create_gui(host, port):
    """Create the Tkinter GUI"""
    global root
    
    root = Tk()
    root.title("VideoGenFX Server Control")
    root.geometry("400x500")
    root.resizable(False, False)
    
    # Main frame
    main_frame = Frame(root, padx=20, pady=20)
    main_frame.pack(fill="both", expand=True)
    
    # Title
    title_label = Label(main_frame, text="VideoGenFX Server", font=("Arial", 16, "bold"))
    title_label.pack(pady=(0, 20))
    
    # Status frame
    status_frame = Frame(main_frame)
    status_frame.pack(fill="x", pady=(0, 10))
    
    status_label = Label(status_frame, text="🟡 Starting Server...", font=("Arial", 12))
    status_label.pack()
    
    # URL frame
    url_frame = Frame(main_frame)
    url_frame.pack(fill="x", pady=(0, 20))
    
    url_label = Label(url_frame, text=f"URL: http://{host}:{port}", font=("Arial", 10))
    url_label.pack()
    
    # GPU info
    gpu_info = "🎮 GPU Acceleration: " + ("Enabled" if gpu_detector.has_gpu_acceleration() else "Disabled")
    gpu_label = Label(main_frame, text=gpu_info, font=("Arial", 10))
    gpu_label.pack(pady=(0, 20))
    
    # Buttons frame
    buttons_frame = Frame(main_frame)
    buttons_frame.pack(fill="x", pady=(0, 20))
    
    # Open browser button
    open_btn = Button(
        buttons_frame,
        text="🌐 Open in Browser",
        command=open_browser,
        bg="#4CAF50",
        fg="white",
        font=("Arial", 12, "bold"),
        height=2,
        state="disabled"
    )
    open_btn.pack(fill="x", pady=(0, 10))
    
    # Stop server button
    stop_btn = Button(
        buttons_frame,
        text="⛔ Stop Server",
        command=stop_server,
        bg="#f44336",
        fg="white",
        font=("Arial", 12, "bold"),
        height=2
    )
    stop_btn.pack(fill="x")
    
    # Instructions
    instructions = Label(
        main_frame,
        text="Click 'Open in Browser' when server is running\nClose this window to stop the server",
        font=("Arial", 9),
        fg="gray"
    )
    instructions.pack(pady=(20, 0))
    
    # Start server status monitoring
    update_server_status(status_label, url_label, open_btn, host, port)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", stop_server)
    
    return root

def run_flask_server():
    """Run the Flask server in a separate thread"""
    host, port = get_host_and_port()
    debug_mode = not is_production()
    
    # For Flask server, always use 0.0.0.0 to listen on all interfaces
    flask_host = '0.0.0.0'
    
    print(f"🌐 Starting VideoGenFX on http://{flask_host}:{port}")
    print(f"🔧 Debug mode: {'ON' if debug_mode else 'OFF'}")
    print(f"🏭 Environment: {'Production' if is_production() else 'Development'}")
    
    # Disable Flask's default logging for health checks
    import logging
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    
    try:
        app.run(
            host=flask_host,
            port=port,
            debug=False,  # Disable debug mode when running with GUI
            threaded=True,
            use_reloader=False  # Disable reloader to prevent conflicts with GUI
        )
    except Exception as e:
        print(f"❌ Flask server error: {e}")
        global server_running
        server_running = False

# Run startup tasks immediately (Flask 3.0+ compatible)
startup_tasks()

@app.route('/health')
def health_check():
    """Health check endpoint for monitoring"""
    return {
        'status': 'healthy',
        'gpu_acceleration': gpu_detector.has_gpu_acceleration(),
        'available_encoders': gpu_detector.available_encoders
    }

# Register cleanup function
def cleanup():
    """Cleanup function to run on app shutdown"""
    print("🛑 VideoGenFX Server Shutting Down...")

atexit.register(cleanup)

if __name__ == '__main__':
    host, port = get_host_and_port()
    
    # Check if running in GUI mode (default) or console mode
    console_mode = '--console' in sys.argv or '--no-gui' in sys.argv
    
    if console_mode:
        # Run in console mode (original behavior)
        debug_mode = not is_production()
        
        print(f"🌐 Starting VideoGenFX on http://{host}:{port}")
        print(f"🔧 Debug mode: {'ON' if debug_mode else 'OFF'}")
        print(f"🏭 Environment: {'Production' if is_production() else 'Development'}")
        
        app.run(
            host=host,
            port=port,
            debug=debug_mode,
            threaded=True
        )
    else:
        # Run with GUI
        print("🖥️ Starting VideoGenFX with GUI...")
        
        # Initialize global variables
        server_running = False
        server_url = ""
        
        # Start Flask server in a separate thread
        flask_thread = threading.Thread(target=run_flask_server, daemon=True)
        flask_thread.start()
        
        # Small delay to let server start
        time.sleep(1)
        
        # Create and run GUI
        try:
            gui = create_gui(host, port)
            gui.mainloop()
        except KeyboardInterrupt:
            print("\n🛑 Stopping server...")
        except Exception as e:
            print(f"❌ GUI Error: {e}")
        finally:
            sys.exit(0)