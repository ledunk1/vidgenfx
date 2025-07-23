from flask import Flask, render_template
from dotenv import load_dotenv
import os
import atexit
import sys
import tkinter as tk
import webbrowser
import threading

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
    # For local GUI, we'll use 127.0.0.1, but keep this for flexibility
    host = os.getenv('HOST', '127.0.0.1')
    port = int(os.getenv('PORT', 5000))
    
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

# --- BAGIAN YANG DIMODIFIKASI ---
if __name__ == '__main__':
    # Dapatkan host dan port untuk aplikasi Flask
    host, port = get_host_and_port()
    debug_mode = not is_production()
    
    print(f"🌐 Starting VideoGenFX on http://{host}:{port}")
    print(f"🔧 Debug mode: {'ON' if debug_mode else 'OFF'}")
    print(f"🏭 Environment: {'Production' if is_production() else 'Development'}")
    
    # Fungsi untuk menjalankan aplikasi Flask
    def run_app():
        app.run(
            host=host,
            port=port,
            debug=debug_mode,
            threaded=True,
            use_reloader=False  # Penting: reloader harus dimatikan saat berjalan di thread
        )

    # Jalankan Flask dalam thread terpisah agar tidak memblokir GUI Tkinter
    flask_thread = threading.Thread(target=run_app)
    flask_thread.daemon = True
    flask_thread.start()

    # --- Setup GUI Tkinter ---
    def open_browser():
        """Fungsi untuk membuka browser ke alamat server Flask."""
        webbrowser.open_new(f"http://{host}:{port}")

    # Buat jendela utama Tkinter
    root = tk.Tk()
    root.title("VideoGenFX Launcher")
    root.geometry("350x150") # Atur ukuran jendela
    root.resizable(False, False) # Buat jendela tidak bisa di-resize

    # Atur style
    root.configure(bg='#2e2e2e')
    main_font = ("Segoe UI", 11)
    button_font = ("Segoe UI", 10, "bold")

    # Tambahkan label
    label = tk.Label(
        root,
        text=f"Server berjalan di http://{host}:{port}",
        font=main_font,
        bg='#2e2e2e',
        fg='white'
    )
    label.pack(pady=20)

    # Tambahkan tombol
    button = tk.Button(
        root,
        text="Buka di Browser",
        command=open_browser,
        font=button_font,
        bg='#4a90e2',
        fg='white',
        relief='flat',
        padx=15,
        pady=8,
        cursor="hand2"
    )
    button.pack(pady=10)

    # Jalankan loop utama Tkinter
    root.mainloop()
