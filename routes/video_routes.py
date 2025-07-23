from flask import Blueprint, request, jsonify, send_file
import os
import uuid
from werkzeug.utils import secure_filename
from utils.gemini_utils import split_text_by_mode, generate_image_prompt
from utils.video_utils import get_audio_duration, create_video_from_images, validate_audio_file
from utils.imagefx_utils import generate_image, save_image_from_base64
from utils.pollinations_utils import generate_pollinations_image, save_pollinations_image, convert_aspect_ratio_to_dimensions
from utils.file_utils import create_zip_archive
from config import UPLOAD_FOLDER, OUTPUT_FOLDER, load_prompt_templates
import sys

def get_absolute_path(relative_path):
    """Get absolute path, handling PyInstaller and different environments"""
    try:
        # Get the directory where the executable or script is located
        if getattr(sys, 'frozen', False):
            # If running from PyInstaller executable
            base_path = os.path.dirname(sys.executable)
        else:
            # Normal Python execution - get project root
            base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        # Combine with relative path
        full_path = os.path.join(base_path, relative_path)
        
        # Normalize path for Windows
        full_path = os.path.normpath(full_path)
        
        return full_path
        
    except Exception as e:
        print(f"Error resolving path {relative_path}: {e}")
        # Fallback to relative path
        return os.path.normpath(relative_path)

video_bp = Blueprint('video', __name__)

ALLOWED_AUDIO_EXTENSIONS = {'mp3', 'wav', 'ogg', 'm4a', 'aac'}
ALLOWED_TEXT_EXTENSIONS = {'txt'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

@video_bp.route('/upload-files', methods=['POST'])
def upload_files():
    try:
        # Check if files are present
        if 'text_file' not in request.files or 'audio_file' not in request.files:
            return jsonify({"error": "Both text and audio files are required"}), 400
        
        text_file = request.files['text_file']
        audio_file = request.files['audio_file']
        
        # Validate files
        if text_file.filename == '' or audio_file.filename == '':
            return jsonify({"error": "No files selected"}), 400
        
        if not (allowed_file(text_file.filename, ALLOWED_TEXT_EXTENSIONS) and 
                allowed_file(audio_file.filename, ALLOWED_AUDIO_EXTENSIONS)):
            return jsonify({"error": "Invalid file types"}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        session_folder = get_absolute_path(os.path.join(UPLOAD_FOLDER, session_id))
        os.makedirs(session_folder, exist_ok=True)
        
        # Save files
        text_filename = secure_filename(text_file.filename)
        audio_filename = secure_filename(audio_file.filename)
        
        text_path = os.path.join(session_folder, text_filename)
        audio_path = os.path.join(session_folder, audio_filename)
        
        text_file.save(text_path)
        audio_file.save(audio_path)
        
        # Validate audio file
        if not validate_audio_file(audio_path):
            return jsonify({"error": "Invalid audio file"}), 400
        
        # Read text content
        with open(text_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        # Get audio duration
        audio_duration = get_audio_duration(audio_path)
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "text_content": text_content,
            "audio_duration": audio_duration,
            "text_filename": text_filename,
            "audio_filename": audio_filename
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@video_bp.route('/generate-video', methods=['POST'])
def generate_video():
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        text_content = data.get('text_content')
        mode = data.get('mode', 'paragraph')
        template_id = data.get('template_id')
        
        # Text generation settings
        text_provider = data.get('text_provider', 'gemini')
        text_model = data.get('text_model')
        
        # Legacy support for gemini_model parameter
        if not text_model and 'gemini_model' in data:
            if text_provider == 'gemini':
                text_model = data['gemini_model']
        
        # Set default models based on provider
        if not text_model:
            if text_provider == 'gemini':
                text_model = 'gemini-2.0-flash'
            elif text_provider == 'pollinations':
                text_model = 'openai'
        
        # Image generation settings
        image_provider = data.get('image_provider', 'imagefx')
        image_model = data.get('image_model')
        aspect_ratio = data.get('aspect_ratio', 'IMAGE_ASPECT_RATIO_LANDSCAPE')
        video_effects = data.get('video_effects', {})
        
        if not all([session_id, text_content]):
            return jsonify({"error": "Missing required parameters"}), 400
        
        # Set default image model if not provided
        if not image_model:
            if image_provider == 'imagefx':
                image_model = 'IMAGEN_3_5'
            elif image_provider == 'pollinations':
                image_model = 'flux'
        
        # Create output folders with absolute paths
        session_folder = get_absolute_path(os.path.join(UPLOAD_FOLDER, session_id))
        images_folder = get_absolute_path(os.path.join(OUTPUT_FOLDER, 'images', session_id))
        videos_folder = get_absolute_path(os.path.join(OUTPUT_FOLDER, 'videos', session_id))
        
        os.makedirs(images_folder, exist_ok=True)
        os.makedirs(videos_folder, exist_ok=True)
        
        # Get template if specified
        template = None
        if template_id:
            templates_data = load_prompt_templates()
            for t in templates_data['templates']:
                if t['id'] == template_id:
                    template = t['template']
                    break
        
        # Split text by mode
        segments = split_text_by_mode(text_content, mode)
        
        # Generate images for each segment using selected providers
        image_paths = []
        generation_log = []
        
        for i, segment in enumerate(segments):
            try:
                # Generate prompt using selected text provider
                image_prompt = generate_image_prompt(
                    text_segment=segment,
                    provider=text_provider,
                    model=text_model,
                    template=template
                )
                
                # Generate image using selected image provider
                if image_provider == 'imagefx':
                    # Use ImageFX
                    image_result = generate_image(image_prompt, aspect_ratio, image_model)
                    
                    # Save image
                    image_filename = f"image_{i+1:03d}.png"
                    image_path = os.path.join(images_folder, image_filename)
                    
                    if save_image_from_base64(image_result['image_data'], image_path):
                        image_paths.append(image_path)
                        generation_log.append({
                            'index': i + 1,
                            'text_segment': segment,
                            'image_prompt': image_prompt,
                            'image_path': image_path,
                            'text_provider': text_provider,
                            'text_model': text_model,
                            'image_provider': 'imagefx',
                            'image_model': image_model,
                            'status': 'success'
                        })
                    else:
                        generation_log.append({
                            'index': i + 1,
                            'text_segment': segment,
                            'image_prompt': image_prompt,
                            'text_provider': text_provider,
                            'image_provider': 'imagefx',
                            'status': 'error',
                            'error': 'Failed to save image'
                        })
                        
                elif image_provider == 'pollinations':
                    # Use Pollinations
                    width, height = convert_aspect_ratio_to_dimensions(aspect_ratio)
                    
                    pollinations_result = generate_pollinations_image(
                        prompt=image_prompt,
                        model=image_model,
                        width=width,
                        height=height,
                        private=True
                    )
                    
                    # Save image
                    content_type = pollinations_result.get('content_type', 'image/jpeg')
                    extension = '.png' if 'png' in content_type else '.jpg'
                    image_filename = f"image_{i+1:03d}{extension}"
                    image_path = os.path.join(images_folder, image_filename)
                    
                    if save_pollinations_image(pollinations_result['image_data'], image_path, content_type):
                        image_paths.append(image_path)
                        generation_log.append({
                            'index': i + 1,
                            'text_segment': segment,
                            'image_prompt': image_prompt,
                            'image_path': image_path,
                            'text_provider': text_provider,
                            'text_model': text_model,
                            'image_provider': 'pollinations',
                            'image_model': image_model,
                            'status': 'success'
                        })
                    else:
                        generation_log.append({
                            'index': i + 1,
                            'text_segment': segment,
                            'image_prompt': image_prompt,
                            'text_provider': text_provider,
                            'image_provider': 'pollinations',
                            'status': 'error',
                            'error': 'Failed to save image'
                        })
                    
            except Exception as e:
                generation_log.append({
                    'index': i + 1,
                    'text_segment': segment,
                    'text_provider': text_provider,
                    'image_provider': image_provider,
                    'status': 'error',
                    'error': str(e)
                })
        
        if not image_paths:
            return jsonify({"error": "No images were generated successfully"}), 500
        
        # Create video
        audio_path = None
        for filename in os.listdir(session_folder):
            if filename.lower().endswith(('.mp3', '.wav', '.ogg', '.m4a', '.aac')):
                audio_path = os.path.join(session_folder, filename)
                break
        
        if not audio_path:
            return jsonify({"error": "Audio file not found"}), 500
        
        # Determine aspect ratio for video
        video_aspect = 'portrait' if 'PORTRAIT' in aspect_ratio else 'landscape'
        
        video_filename = f"video_{session_id}.mp4"
        video_path = os.path.join(videos_folder, video_filename)
        
        # Create video with custom effects
        if create_video_from_images(image_paths, audio_path, video_path, video_aspect, video_effects):
            return jsonify({
                "success": True,
                "session_id": session_id,
                "video_path": video_path,
                "video_filename": video_filename,
                "images_generated": len(image_paths),
                "total_segments": len(segments),
                "text_provider_used": text_provider,
                "text_model_used": text_model,
                "image_provider_used": image_provider,
                "image_model_used": image_model,
                "generation_log": generation_log,
                "video_effects_used": video_effects
            })
        else:
            return jsonify({"error": "Failed to create video"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@video_bp.route('/download-video/<session_id>')
def download_video(session_id):
    """Download generated video with proper path resolution"""
    try:
        # Use absolute path resolution for executable compatibility
        videos_folder = get_absolute_path(os.path.join(OUTPUT_FOLDER, 'videos', session_id))
        video_filename = f"video_{session_id}.mp4"
        video_path = os.path.join(videos_folder, video_filename)
        
        print(f"🎬 Attempting to download video: {video_path}")
        
        # Check if video file exists
        if not os.path.exists(video_path):
            print(f"❌ Video file not found: {video_path}")
            
            # Try alternative paths for debugging
            alternative_paths = [
                os.path.join(OUTPUT_FOLDER, 'videos', session_id, video_filename),
                os.path.join('outputs', 'videos', session_id, video_filename),
                os.path.abspath(os.path.join(OUTPUT_FOLDER, 'videos', session_id, video_filename))
            ]
            
            for alt_path in alternative_paths:
                alt_abs_path = get_absolute_path(alt_path)
                print(f"🔍 Checking alternative path: {alt_abs_path}")
                if os.path.exists(alt_abs_path):
                    print(f"✅ Found video at alternative path: {alt_abs_path}")
                    video_path = alt_abs_path
                    break
            else:
                # List directory contents for debugging
                try:
                    if os.path.exists(videos_folder):
                        files = os.listdir(videos_folder)
                        print(f"📁 Files in videos folder: {files}")
                    else:
                        print(f"❌ Videos folder does not exist: {videos_folder}")
                        
                        # Check parent directory
                        parent_dir = os.path.dirname(videos_folder)
                        if os.path.exists(parent_dir):
                            parent_files = os.listdir(parent_dir)
                            print(f"📁 Files in parent directory {parent_dir}: {parent_files}")
                except Exception as list_error:
                    print(f"❌ Error listing directory: {list_error}")
                
                return jsonify({"error": "Video file not found"}), 404
        
        # Check if file is not empty
        file_size = os.path.getsize(video_path)
        if file_size == 0:
            print(f"❌ Video file is empty: {video_path}")
            return jsonify({"error": "Video file is empty"}), 404
        
        print(f"✅ Serving video file: {video_path} ({file_size} bytes)")
        
        # Send file with proper headers for video streaming
        return send_file(
            video_path, 
            as_attachment=False,  # Don't force download, allow streaming
            download_name=video_filename,
            mimetype='video/mp4'
        )
        
    except Exception as e:
        print(f"❌ Error downloading video for session {session_id}: {e}")
        return jsonify({"error": f"Error downloading video: {str(e)}"}), 500