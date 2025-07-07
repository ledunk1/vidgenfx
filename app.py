from flask import Flask, render_template
from dotenv import load_dotenv
import os
import atexit
import sys

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
    # For VPS deployment
    host = os.getenv('HOST', '0.0.0.0')  # Listen on all interfaces for VPS
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
    debug_mode = not is_production()
    
    print(f"🌐 Starting VideoGenFX on http://{host}:{port}")
    print(f"🔧 Debug mode: {'ON' if debug_mode else 'OFF'}")
    print(f"🏭 Environment: {'Production' if is_production() else 'Development'}")
    
    app.run(
        host=host,
        port=port,
        debug=debug_mode,
        threaded=True  # Enable threading for better performance
    )