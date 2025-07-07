from flask import Blueprint, request, jsonify, send_file
import os
import uuid
import sys
from werkzeug.utils import secure_filename
from utils.gemini_utils import split_text_by_mode, generate_image_prompt
from utils.imagefx_utils import generate_image, save_image_from_base64
from utils.pollinations_utils import generate_pollinations_image, save_pollinations_image, convert_aspect_ratio_to_dimensions
from utils.tts_video_utils import generate_tts_audio, create_video_from_tts_segments, check_tts_availability
from utils.file_utils import create_zip_archive
from config import OUTPUT_FOLDER, UPLOAD_FOLDER, load_prompt_templates
import logging
import random

tts_video_bp = Blueprint('tts_video', __name__)

ALLOWED_TEXT_EXTENSIONS = {'txt'}

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

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
        
        logging.info(f"🔍 Path resolution: {relative_path} -> {full_path}")
        return full_path
        
    except Exception as e:
        logging.error(f"❌ Error resolving path {relative_path}: {e}")
        # Fallback to relative path
        return os.path.normpath(relative_path)

@tts_video_bp.route('/upload-text-file', methods=['POST'])
def upload_text_file():
    """Upload and process text file for TTS video generation"""
    try:
        # Check TTS availability first
        if not check_tts_availability():
            return jsonify({"error": "TTS functionality is not available. Please check TTS handler installation."}), 500
        
        # Check if file is present
        if 'text_file' not in request.files:
            return jsonify({"error": "Text file is required"}), 400
        
        text_file = request.files['text_file']
        
        # Validate file
        if text_file.filename == '':
            return jsonify({"error": "No file selected"}), 400
        
        if not allowed_file(text_file.filename, ALLOWED_TEXT_EXTENSIONS):
            return jsonify({"error": "Invalid file type. Only .txt files are allowed"}), 400
        
        # Generate unique session ID
        session_id = str(uuid.uuid4())
        session_folder = get_absolute_path(os.path.join(UPLOAD_FOLDER, session_id))
        os.makedirs(session_folder, exist_ok=True)
        
        # Save file
        text_filename = secure_filename(text_file.filename)
        text_path = os.path.join(session_folder, text_filename)
        text_file.save(text_path)
        
        # Read text content
        with open(text_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        # Get text statistics
        word_count = len(text_content.split())
        char_count = len(text_content)
        
        logging.info(f"✅ Text file uploaded: {text_filename} ({word_count} words, {char_count} chars)")
        
        return jsonify({
            "success": True,
            "session_id": session_id,
            "text_content": text_content,
            "text_filename": text_filename,
            "word_count": word_count,
            "char_count": char_count
        })
        
    except Exception as e:
        logging.error(f"❌ Error uploading text file: {e}")
        return jsonify({"error": str(e)}), 500

def generate_multiple_images_for_segment(segment, count, text_provider, text_model, image_provider, image_model, aspect_ratio, template, segment_index, images_folder):
    """Generate multiple images for a single segment using selected providers and save ALL of them"""
    saved_image_paths = []
    
    logging.info(f"🎨 Generating {count} image(s) for segment {segment_index} using text:{text_provider}/{text_model}, image:{image_provider}/{image_model}")
    
    for i in range(count):
        try:
            # Generate different prompts for variety
            if i == 0:
                # First image uses original prompt
                image_prompt = generate_image_prompt(
                    text_segment=segment,
                    provider=text_provider,
                    model=text_model,
                    template=template
                )
            else:
                # Subsequent images use variations for more diversity
                variation_templates = [
                    f"Alternative perspective: {segment}",
                    f"Different angle of: {segment}",
                    f"Another view showing: {segment}",
                    f"Creative interpretation: {segment}",
                    f"Artistic representation: {segment}"
                ]
                variation_base = random.choice(variation_templates)
                image_prompt = generate_image_prompt(
                    text_segment=variation_base,
                    provider=text_provider,
                    model=text_model,
                    template=template
                )
            
            # Generate image based on provider
            if image_provider == 'imagefx':
                # Use ImageFX
                image_result = generate_image(image_prompt, aspect_ratio, image_model)
                
                # Save image
                image_filename = f"image_{segment_index:03d}_{i+1:02d}.png"
                image_path = os.path.join(images_folder, image_filename)
                
                if save_image_from_base64(image_result['image_data'], image_path):
                    saved_image_paths.append({
                        'path': image_path,
                        'prompt': image_prompt,
                        'variation_index': i + 1,
                        'text_provider': text_provider,
                        'text_model': text_model,
                        'image_provider': 'imagefx',
                        'image_model': image_model
                    })
                    logging.info(f"✅ Generated and saved ImageFX image variation {i+1}/{count} for segment {segment_index}: {image_filename}")
                else:
                    logging.error(f"❌ Failed to save ImageFX image variation {i+1}/{count} for segment {segment_index}")
                    
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
                image_filename = f"image_{segment_index:03d}_{i+1:02d}{extension}"
                image_path = os.path.join(images_folder, image_filename)
                
                if save_pollinations_image(pollinations_result['image_data'], image_path, content_type):
                    saved_image_paths.append({
                        'path': image_path,
                        'prompt': image_prompt,
                        'variation_index': i + 1,
                        'text_provider': text_provider,
                        'text_model': text_model,
                        'image_provider': 'pollinations',
                        'image_model': image_model
                    })
                    logging.info(f"✅ Generated and saved Pollinations image variation {i+1}/{count} for segment {segment_index}: {image_filename}")
                else:
                    logging.error(f"❌ Failed to save Pollinations image variation {i+1}/{count} for segment {segment_index}")
            
        except Exception as e:
            logging.error(f"❌ Failed to generate image variation {i+1}/{count} for segment {segment_index}: {e}")
            continue
    
    if saved_image_paths:
        logging.info(f"🎉 Successfully generated and saved {len(saved_image_paths)}/{count} images for segment {segment_index}")
        return saved_image_paths
    else:
        logging.error(f"❌ No images generated successfully for segment {segment_index}")
        return []

def get_fallback_images(processed_segments, current_index):
    """Get fallback images from other segments"""
    # Try to get from previous segment first
    for i in range(current_index - 1, -1, -1):
        if (i < len(processed_segments) and 
            processed_segments[i].get('status') == 'success' and 
            processed_segments[i].get('image_paths')):
            logging.info(f"📸 Using fallback images from segment {i+1} for segment {current_index+1}")
            return processed_segments[i]['image_paths']
    
    # If no previous segment, try next segments
    for i in range(current_index + 1, len(processed_segments)):
        if (processed_segments[i].get('status') == 'success' and 
            processed_segments[i].get('image_paths')):
            logging.info(f"📸 Using fallback images from segment {i+1} for segment {current_index+1}")
            return processed_segments[i]['image_paths']
    
    return []

@tts_video_bp.route('/generate-tts-video', methods=['POST'])
def generate_tts_video():
    """Generate video from text using TTS + AI images with multiple providers and multiple images per segment"""
    try:
        # Check TTS availability first
        if not check_tts_availability():
            return jsonify({"error": "TTS functionality is not available. Please check TTS handler installation."}), 500
        
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
        
        # Random image generation settings
        random_images_per_paragraph = data.get('random_images_per_paragraph', 1)
        
        # TTS Settings
        tts_voice = data.get('tts_voice', 'nova')
        tts_voice_style = data.get('tts_voice_style', 'friendly')
        tts_language = data.get('tts_language', 'id-ID')
        
        if not all([session_id, text_content]):
            return jsonify({"error": "Session ID and text content are required"}), 400
        
        # Validate random images count
        if random_images_per_paragraph < 1 or random_images_per_paragraph > 5:
            return jsonify({"error": "Random images per paragraph must be between 1 and 5"}), 400
        
        # Set default image model if not provided
        if not image_model:
            if image_provider == 'imagefx':
                image_model = 'IMAGEN_3_5'
            elif image_provider == 'pollinations':
                image_model = 'flux'
        
        logging.info(f"🚀 Starting TTS video generation for session: {session_id}")
        logging.info(f"📝 Text length: {len(text_content)} chars")
        logging.info(f"🎤 TTS settings: voice={tts_voice}, style={tts_voice_style}, lang={tts_language}")
        logging.info(f"🤖 Text provider: {text_provider}, model: {text_model}")
        logging.info(f"🎨 Image provider: {image_provider}, model: {image_model}")
        logging.info(f"🎲 Random images per paragraph: {random_images_per_paragraph} (Mode: {mode})")
        
        # Create output folders with absolute paths
        images_folder = get_absolute_path(os.path.join(OUTPUT_FOLDER, 'images', session_id))
        videos_folder = get_absolute_path(os.path.join(OUTPUT_FOLDER, 'videos', session_id))
        audio_folder = get_absolute_path(os.path.join(OUTPUT_FOLDER, 'audio', session_id))
        
        os.makedirs(images_folder, exist_ok=True)
        os.makedirs(videos_folder, exist_ok=True)
        os.makedirs(audio_folder, exist_ok=True)
        
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
        logging.info(f"📊 Split text into {len(segments)} segments using mode: {mode}")
        
        # Process each segment: Generate TTS + Multiple Images
        processed_segments = []
        generation_log = []
        total_images_generated = 0
        
        for i, segment in enumerate(segments):
            try:
                logging.info(f"🔄 Processing segment {i+1}/{len(segments)}: {segment[:50]}...")
                
                segment_data = {
                    'index': i + 1,
                    'text': segment,
                    'audio_path': None,
                    'image_paths': [],
                    'image_prompts': [],
                    'status': 'processing',
                    'images_generated': 0,
                    'fallback_used': False,
                    'text_provider_used': text_provider,
                    'text_model_used': text_model,
                    'image_provider_used': image_provider,
                    'image_model_used': image_model
                }
                
                # Generate TTS audio for this segment
                audio_filename = f"audio_{i+1:03d}.mp3"
                audio_path = os.path.join(audio_folder, audio_filename)
                
                logging.info(f"🎤 Generating TTS audio for segment {i+1}")
                audio_success = generate_tts_audio(
                    text=segment,
                    output_path=audio_path,
                    voice=tts_voice,
                    voice_style=tts_voice_style,
                    language=tts_language
                )
                
                if audio_success:
                    segment_data['audio_path'] = audio_path
                    logging.info(f"✅ TTS audio generated for segment {i+1}")
                else:
                    raise Exception("Failed to generate TTS audio")
                
                # Generate multiple images for paragraph mode
                images_to_generate = random_images_per_paragraph if mode == 'paragraph' else 1
                
                # Generate and save ALL images using selected providers
                generated_images = generate_multiple_images_for_segment(
                    segment, images_to_generate, text_provider, text_model, 
                    image_provider, image_model, aspect_ratio, template, 
                    i+1, images_folder
                )
                
                if generated_images:
                    # Store ALL generated images
                    segment_data['image_paths'] = [img['path'] for img in generated_images]
                    segment_data['image_prompts'] = [img['prompt'] for img in generated_images]
                    segment_data['images_generated'] = len(generated_images)
                    segment_data['status'] = 'success'
                    total_images_generated += len(generated_images)
                    
                    logging.info(f"✅ Segment {i+1} processed successfully - Generated and saved {len(generated_images)} images using {text_provider}/{image_provider}")
                else:
                    raise Exception("No images were generated successfully")
                
                processed_segments.append(segment_data)
                
                generation_log.append({
                    'index': i + 1,
                    'text_segment': segment,
                    'image_prompts': segment_data['image_prompts'],
                    'audio_generated': True,
                    'image_generated': True,
                    'images_count': segment_data['images_generated'],
                    'text_provider_used': text_provider,
                    'text_model_used': text_model,
                    'image_provider_used': image_provider,
                    'image_model_used': image_model,
                    'status': 'success'
                })
                
            except Exception as e:
                logging.error(f"❌ Error processing segment {i+1}: {e}")
                
                # Try to use fallback images from other segments
                fallback_images = get_fallback_images(processed_segments, i)
                
                if fallback_images and segment_data.get('audio_path'):
                    # Copy fallback images to current segment
                    import shutil
                    copied_images = []
                    
                    for j, fallback_path in enumerate(fallback_images):
                        try:
                            image_filename = f"image_{i+1:03d}_{j+1:02d}_fallback.png"
                            image_path = os.path.join(images_folder, image_filename)
                            shutil.copy2(fallback_path, image_path)
                            copied_images.append(image_path)
                        except Exception as copy_error:
                            logging.error(f"❌ Failed to copy fallback image {j+1}: {copy_error}")
                            continue
                    
                    if copied_images:
                        segment_data['image_paths'] = copied_images
                        segment_data['status'] = 'success'
                        segment_data['fallback_used'] = True
                        segment_data['image_prompts'] = ["Fallback image from another segment"] * len(copied_images)
                        segment_data['images_generated'] = len(copied_images)
                        
                        processed_segments.append(segment_data)
                        
                        generation_log.append({
                            'index': i + 1,
                            'text_segment': segment,
                            'image_prompts': ['Used fallback images from another segment'],
                            'audio_generated': True,
                            'image_generated': True,
                            'images_count': len(copied_images),
                            'fallback_used': True,
                            'text_provider_used': 'fallback',
                            'image_provider_used': 'fallback',
                            'status': 'success'
                        })
                        
                        logging.info(f"✅ Segment {i+1} recovered using {len(copied_images)} fallback images")
                        continue
                
                # If fallback also failed, log as error
                generation_log.append({
                    'index': i + 1,
                    'text_segment': segment,
                    'status': 'error',
                    'error': str(e),
                    'fallback_attempted': len(fallback_images) > 0 if fallback_images else False,
                    'text_provider_used': text_provider,
                    'image_provider_used': image_provider
                })
        
        if not processed_segments:
            return jsonify({"error": "No segments were processed successfully"}), 500
        
        # Calculate final statistics
        segments_with_fallback = sum(1 for seg in processed_segments if seg.get('fallback_used', False))
        total_images_in_video = sum(len(seg.get('image_paths', [])) for seg in processed_segments)
        
        logging.info(f"📊 Final Statistics:")
        logging.info(f"   - Successfully processed: {len(processed_segments)}/{len(segments)} segments")
        logging.info(f"   - Total images generated: {total_images_generated}")
        logging.info(f"   - Total images in video: {total_images_in_video}")
        logging.info(f"   - Segments with fallback: {segments_with_fallback}")
        logging.info(f"   - Text provider used: {text_provider}/{text_model}")
        logging.info(f"   - Image provider used: {image_provider}/{image_model}")
        logging.info(f"   - Random images per paragraph: {random_images_per_paragraph}")
        
        # Create video from TTS segments
        video_filename = f"tts_video_{session_id}.mp4"
        video_path = os.path.join(videos_folder, video_filename)
        
        # Determine aspect ratio for video
        video_aspect = 'portrait' if 'PORTRAIT' in aspect_ratio else 'landscape'
        
        # Create video with TTS audio segments
        logging.info(f"🎬 Creating video from TTS segments with {total_images_in_video} total images")
        video_success = create_video_from_tts_segments(processed_segments, video_path, video_aspect, video_effects)
        
        if video_success:
            logging.info(f"🎉 TTS video generation completed successfully!")
            
            return jsonify({
                "success": True,
                "session_id": session_id,
                "video_path": video_path,
                "video_filename": video_filename,
                "segments_processed": len(processed_segments),
                "total_segments": len(segments),
                "total_images_generated": total_images_generated,
                "total_images_in_video": total_images_in_video,
                "segments_with_fallback": segments_with_fallback,
                "random_images_per_paragraph": random_images_per_paragraph,
                "mode_used": mode,
                "text_provider_used": text_provider,
                "text_model_used": text_model,
                "image_provider_used": image_provider,
                "image_model_used": image_model,
                "generation_log": generation_log,
                "video_effects_used": video_effects,
                "tts_settings": {
                    "voice": tts_voice,
                    "voice_style": tts_voice_style,
                    "language": tts_language
                }
            })
        else:
            return jsonify({"error": "Failed to create video"}), 500
            
    except Exception as e:
        logging.error(f"❌ Error in TTS video generation: {e}")
        return jsonify({"error": str(e)}), 500

@tts_video_bp.route('/download-tts-video/<session_id>')
def download_tts_video(session_id):
    """Download generated TTS video with proper error handling and path resolution"""
    try:
        # Use absolute path resolution for executable compatibility
        videos_folder = get_absolute_path(os.path.join(OUTPUT_FOLDER, 'videos', session_id))
        video_filename = f"tts_video_{session_id}.mp4"
        video_path = os.path.join(videos_folder, video_filename)
        
        logging.info(f"🎬 Attempting to download TTS video: {video_path}")
        
        # Check if video file exists
        if not os.path.exists(video_path):
            logging.error(f"❌ Video file not found: {video_path}")
            
            # Try alternative paths for debugging
            alternative_paths = [
                os.path.join(OUTPUT_FOLDER, 'videos', session_id, video_filename),
                os.path.join('outputs', 'videos', session_id, video_filename),
                os.path.abspath(os.path.join(OUTPUT_FOLDER, 'videos', session_id, video_filename))
            ]
            
            for alt_path in alternative_paths:
                alt_abs_path = get_absolute_path(alt_path)
                logging.info(f"🔍 Checking alternative path: {alt_abs_path}")
                if os.path.exists(alt_abs_path):
                    logging.info(f"✅ Found video at alternative path: {alt_abs_path}")
                    video_path = alt_abs_path
                    break
            else:
                # List directory contents for debugging
                try:
                    if os.path.exists(videos_folder):
                        files = os.listdir(videos_folder)
                        logging.info(f"📁 Files in videos folder: {files}")
                    else:
                        logging.error(f"❌ Videos folder does not exist: {videos_folder}")
                        
                        # Check parent directory
                        parent_dir = os.path.dirname(videos_folder)
                        if os.path.exists(parent_dir):
                            parent_files = os.listdir(parent_dir)
                            logging.info(f"📁 Files in parent directory {parent_dir}: {parent_files}")
                except Exception as list_error:
                    logging.error(f"❌ Error listing directory: {list_error}")
                
                return jsonify({"error": "Video file not found"}), 404
        
        # Check if file is not empty
        file_size = os.path.getsize(video_path)
        if file_size == 0:
            logging.error(f"❌ Video file is empty: {video_path}")
            return jsonify({"error": "Video file is empty"}), 404
        
        logging.info(f"✅ Serving TTS video file: {video_path} ({file_size} bytes)")
        
        # Send file with proper headers for video streaming
        return send_file(
            video_path, 
            as_attachment=False,  # Don't force download, allow streaming
            download_name=video_filename,
            mimetype='video/mp4'
        )
        
    except Exception as e:
        logging.error(f"❌ Error downloading TTS video for session {session_id}: {e}")
        return jsonify({"error": f"Error downloading video: {str(e)}"}), 500

@tts_video_bp.route('/download-tts-assets/<session_id>')
def download_tts_assets(session_id):
    """Download all assets (images + audio) as ZIP"""
    try:
        # Create ZIP with all assets using absolute paths
        images_folder = get_absolute_path(os.path.join(OUTPUT_FOLDER, 'images', session_id))
        audio_folder = get_absolute_path(os.path.join(OUTPUT_FOLDER, 'audio', session_id))
        
        if not (os.path.exists(images_folder) or os.path.exists(audio_folder)):
            return jsonify({"error": "Assets not found"}), 404
        
        # Create temporary folder for ZIP creation
        temp_folder = get_absolute_path(os.path.join('temp', f'tts_assets_{session_id}'))
        os.makedirs(temp_folder, exist_ok=True)
        
        # Copy images
        if os.path.exists(images_folder):
            images_temp = os.path.join(temp_folder, 'images')
            os.makedirs(images_temp, exist_ok=True)
            import shutil
            for file in os.listdir(images_folder):
                shutil.copy2(os.path.join(images_folder, file), images_temp)
        
        # Copy audio
        if os.path.exists(audio_folder):
            audio_temp = os.path.join(temp_folder, 'audio')
            os.makedirs(audio_temp, exist_ok=True)
            for file in os.listdir(audio_folder):
                shutil.copy2(os.path.join(audio_folder, file), audio_temp)
        
        zip_name = f"tts_assets_{session_id}.zip"
        zip_path = create_zip_archive(temp_folder, zip_name)
        
        if zip_path and os.path.exists(zip_path):
            return send_file(zip_path, as_attachment=True, download_name=zip_name)
        else:
            return jsonify({"error": "Failed to create ZIP file"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@tts_video_bp.route('/check-tts-status')
def check_tts_status():
    """Check TTS availability status"""
    try:
        tts_available = check_tts_availability()
        return jsonify({
            "success": True,
            "tts_available": tts_available,
            "message": "TTS is available" if tts_available else "TTS handler not available"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "tts_available": False,
            "error": str(e)
        }), 500