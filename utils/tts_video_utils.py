import os
import logging
from moviepy.editor import *
import librosa
import numpy as np
from utils.video_utils import apply_ken_burns_effect, threading_detector
from utils.gpu_utils import gpu_detector
from concurrent.futures import ThreadPoolExecutor, as_completed
from PIL import Image
import sys

# Import TTS handler from utils
try:
    from utils.tts_handler import generate_audio_from_text_with_token, CONTENT_POLICY_ERROR_SIGNAL
    TTS_AVAILABLE = True
    logging.info("✅ TTS handler imported successfully")
except ImportError as e:
    logging.error(f"❌ Failed to import TTS handler: {e}")
    TTS_AVAILABLE = False

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
        
        logging.info(f"🔍 TTS Utils Path resolution: {relative_path} -> {full_path}")
        return full_path
        
    except Exception as e:
        logging.error(f"❌ Error resolving path {relative_path}: {e}")
        # Fallback to relative path
        return os.path.normpath(relative_path)

def generate_tts_audio(text, output_path, voice='nova', voice_style='friendly', language='id-ID'):
    """Generate TTS audio using Pollinations TTS API"""
    try:
        if not TTS_AVAILABLE:
            logging.error("TTS handler not available")
            return False
        
        logging.info(f"🎤 Generating TTS audio for text: {text[:50]}...")
        
        # Generate audio using TTS handler
        audio_content = generate_audio_from_text_with_token(
            text_input=text,
            bahasa=language,
            voice=voice,
            voice_style=voice_style,
            max_retries_override=3
        )
        
        if audio_content is None:
            logging.error("Failed to generate TTS audio - returned None")
            return False
        
        if audio_content == CONTENT_POLICY_ERROR_SIGNAL:
            logging.error("Content policy violation in TTS")
            return False
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_path)
        os.makedirs(output_dir, exist_ok=True)
        
        # Save audio to file
        with open(output_path, 'wb') as f:
            f.write(audio_content)
        
        # Verify file was created and has content
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            logging.info(f"✅ TTS audio saved to: {output_path} ({os.path.getsize(output_path)} bytes)")
            return True
        else:
            logging.error(f"❌ TTS audio file not created or empty: {output_path}")
            return False
        
    except Exception as e:
        logging.error(f"❌ Error generating TTS audio: {e}")
        return False

def get_audio_duration_from_file(audio_path):
    """Get duration of audio file"""
    try:
        if not os.path.exists(audio_path):
            logging.error(f"Audio file does not exist: {audio_path}")
            return 0
            
        duration = librosa.get_duration(path=audio_path)
        logging.info(f"📊 Audio duration: {duration:.2f} seconds")
        return duration
    except Exception as e:
        logging.error(f"Error getting audio duration: {e}")
        return 0

def process_tts_image_batch(image_batch, target_size, temp_dir, start_index):
    """Process a batch of images for TTS video with maximum threading"""
    processed_paths = []
    
    for i, image_path in enumerate(image_batch):
        try:
            if not os.path.exists(image_path):
                logging.error(f"Image file does not exist: {image_path}")
                processed_paths.append(None)
                continue
                
            # Load and resize image
            img = Image.open(image_path)
            
            # Resize image maintaining aspect ratio
            img_ratio = img.width / img.height
            target_ratio = target_size[0] / target_size[1]
            
            if img_ratio > target_ratio:
                # Image is wider, fit to height and crop width
                new_height = target_size[1]
                new_width = int(new_height * img_ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                # Crop to target width
                left = (new_width - target_size[0]) // 2
                img = img.crop((left, 0, left + target_size[0], new_height))
            else:
                # Image is taller, fit to width and crop height
                new_width = target_size[0]
                new_height = int(new_width / img_ratio)
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                # Crop to target height
                top = (new_height - target_size[1]) // 2
                img = img.crop((0, top, new_width, top + target_size[1]))
            
            # Save resized image
            temp_img_path = os.path.join(temp_dir, f"tts_resized_{start_index + i}.png")
            img.save(temp_img_path, optimize=True, compress_level=1)
            processed_paths.append(temp_img_path)
            
        except Exception as e:
            logging.error(f"Error processing TTS image {image_path}: {e}")
            processed_paths.append(None)
    
    return processed_paths

def create_single_tts_clip_with_multiple_images(segment_data, effects):
    """Create a single TTS video clip from segment data with multiple images"""
    try:
        image_paths = segment_data.get('image_paths', [])
        audio_path = segment_data.get('audio_path')
        index = segment_data.get('index', 0)
        
        if not image_paths or not audio_path:
            logging.error(f"Missing paths for segment {index}: images={len(image_paths)}, audio={audio_path}")
            return None
            
        if not os.path.exists(audio_path):
            logging.error(f"Audio file does not exist for segment {index}: {audio_path}")
            return None
        
        # Verify all image files exist
        valid_image_paths = []
        for img_path in image_paths:
            if os.path.exists(img_path):
                valid_image_paths.append(img_path)
            else:
                logging.warning(f"Image file does not exist: {img_path}")
        
        if not valid_image_paths:
            logging.error(f"No valid image files for segment {index}")
            return None
        
        # Get audio duration
        audio_duration = get_audio_duration_from_file(audio_path)
        if audio_duration <= 0:
            logging.error(f"Invalid audio duration for segment {index}: {audio_duration}")
            return None
        
        # Load audio
        audio_clip = AudioFileClip(audio_path)
        
        # Calculate duration per image
        duration_per_image = audio_duration / len(valid_image_paths)
        
        logging.info(f"🎬 Creating clip for segment {index} with {len(valid_image_paths)} images, {duration_per_image:.2f}s each")
        
        # Create clips for each image
        image_clips = []
        for i, image_path in enumerate(valid_image_paths):
            try:
                # Create image clip with calculated duration
                image_clip = ImageClip(image_path, duration=duration_per_image)
                
                # Check if effects are enabled
                if not effects.get('effects_enabled', True):
                    image_clips.append(image_clip)
                    continue
                
                # Check if motion effects are enabled
                if not effects.get('motion_effects_enabled', True):
                    # If motion effects disabled, use no effect
                    chosen_effect = 'no_effect'
                else:
                    # Apply Ken Burns effect (random choice based on effects settings)
                    import random
                    effect_types = ['zoom_in', 'zoom_out', 'pan_right', 'pan_left', 'pan_up', 'pan_down', 'no_effect']
                    effect_weights = [
                        effects.get('zoom_in_probability', 30),
                        effects.get('zoom_out_probability', 30),
                        effects.get('pan_right_probability', 10),
                        effects.get('pan_left_probability', 10),
                        effects.get('pan_up_probability', 10),
                        effects.get('pan_down_probability', 10),
                        effects.get('no_effect_probability', 0)
                    ]
                    
                    chosen_effect = random.choices(effect_types, weights=effect_weights)[0]
                
                if chosen_effect != 'no_effect':
                    ken_burns_intensity = effects.get('ken_burns_intensity', 0.08)
                    image_clip = apply_ken_burns_effect(image_clip, chosen_effect, ken_burns_intensity)
                
                image_clips.append(image_clip)
                logging.info(f"✅ Created image clip {i+1}/{len(valid_image_paths)} for segment {index} with effect: {chosen_effect}")
                
            except Exception as e:
                logging.error(f"❌ Error creating image clip {i+1} for segment {index}: {e}")
                continue
        
        if not image_clips:
            logging.error(f"No image clips created for segment {index}")
            return None
        
        # Concatenate all image clips
        if len(image_clips) > 1:
            final_video_clip = concatenate_videoclips(image_clips, method="compose")
        else:
            final_video_clip = image_clips[0]
        
        # Ensure video duration matches audio duration
        if abs(final_video_clip.duration - audio_duration) > 0.1:  # Allow small tolerance
            final_video_clip = final_video_clip.set_duration(audio_duration)
        
        # Combine with audio
        final_clip = final_video_clip.set_audio(audio_clip)
        
        logging.info(f"✅ Created TTS clip for segment {index} with {len(valid_image_paths)} images, total duration: {audio_duration:.2f}s")
        return (index, final_clip)
        
    except Exception as e:
        logging.error(f"❌ Error creating TTS clip for segment {segment_data.get('index', 'unknown')}: {e}")
        return None

def create_tts_clips_parallel(segments, effects, target_size, temp_dir):
    """Create video clips from TTS segments with parallel processing and multiple images"""
    clips = []
    max_workers = min(threading_detector.threading_config['concurrent_clips'], len(segments))
    
    logging.info(f"🎬 Creating TTS clips with {max_workers} parallel workers for {len(segments)} segments")
    
    # Process all clips in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for segment_data in segments:
            future = executor.submit(create_single_tts_clip_with_multiple_images, segment_data, effects)
            futures.append(future)
        
        # Collect results maintaining order
        results = [None] * len(segments)
        for future in as_completed(futures):
            try:
                result = future.result()
                if result is not None:
                    index, clip = result
                    results[index - 1] = clip  # index is 1-based
            except Exception as e:
                logging.error(f"Error in TTS clip creation: {e}")
        
        # Filter out None values and maintain order
        clips = [clip for clip in results if clip is not None]
    
    logging.info(f"✅ Successfully created {len(clips)} TTS clips out of {len(segments)} segments")
    return clips

def create_video_from_tts_segments(segments, output_path, aspect_ratio='landscape', custom_effects=None):
    """Create video from TTS segments with multiple images per segment"""
    try:
        from config import load_settings
        
        logging.info(f"🚀 Starting TTS video creation with {len(segments)} segments")
        
        # Count total images
        total_images = sum(len(seg.get('image_paths', [])) for seg in segments)
        logging.info(f"📊 Total images to process: {total_images}")
        
        # Load settings for video effects
        settings = load_settings()
        effects = custom_effects or settings.get('video_effects', {
            'effects_enabled': True,
            'motion_effects_enabled': True,
            'transition_effects_enabled': True,
            'zoom_in_probability': 30,
            'zoom_out_probability': 30,
            'pan_right_probability': 10,
            'pan_left_probability': 10,
            'pan_up_probability': 10,
            'pan_down_probability': 10,
            'no_effect_probability': 0,
            'fade_probability': 100,
            'ken_burns_intensity': 0.08,
            'fade_duration': 0.5
        })
        
        # Set resolution based on aspect ratio
        if aspect_ratio == 'portrait':
            target_size = (720, 1280)
        else:  # landscape
            target_size = (1280, 720)
        
        # Create temp directory for processed images using absolute path
        temp_dir = get_absolute_path("temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        # Validate segments
        valid_segments = []
        for segment in segments:
            if (segment.get('image_paths') and segment.get('audio_path') and 
                len(segment['image_paths']) > 0 and os.path.exists(segment['audio_path'])):
                valid_segments.append(segment)
            else:
                logging.warning(f"Skipping invalid segment {segment.get('index', 'unknown')}")
        
        if not valid_segments:
            raise ValueError("No valid TTS segments found")
        
        logging.info(f"📊 Processing {len(valid_segments)} valid segments with {total_images} total images")
        
        # Create video clips from TTS segments
        logging.info(f"🎬 Creating TTS video clips with multiple images per segment")
        clips = create_tts_clips_parallel(valid_segments, effects, target_size, temp_dir)
        
        if not clips:
            raise ValueError("No TTS video clips were created successfully")
        
        # Apply fade transitions
        final_clips = []
        fade_duration = min(effects.get('fade_duration', 0.5), 0.5)  # Max 0.5s fade
        fade_probability = effects.get('fade_probability', 100)
        
        # Check if transition effects are enabled
        transition_effects_enabled = effects.get('transition_effects_enabled', True) and effects.get('effects_enabled', True)
        
        logging.info("🎭 Applying fade transitions to TTS clips")
        
        import random
        for i, clip in enumerate(clips):
            if not transition_effects_enabled:
                final_clips.append(clip)
                continue
                
            apply_fade = random.randint(1, 100) <= fade_probability
            
            if apply_fade:
                if i == 0:
                    # First clip: fade in only
                    final_clips.append(clip.fadein(fade_duration))
                elif i == len(clips) - 1:
                    # Last clip: fade out only
                    final_clips.append(clip.fadeout(fade_duration))
                else:
                    # Middle clips: crossfade
                    final_clips.append(clip.fadein(fade_duration).fadeout(fade_duration))
            else:
                final_clips.append(clip)
        
        # Concatenate all clips
        logging.info("🔗 Concatenating TTS video clips")
        if len(final_clips) > 1:
            final_video = concatenate_videoclips(final_clips, method="compose")
        else:
            final_video = final_clips[0]
        
        # Get GPU-optimized encoding parameters
        gpu_params = gpu_detector.get_gpu_acceleration_params()
        
        # Configure write parameters
        write_params = {
            'fps': 30,
            'codec': gpu_params['codec'],
            'audio_codec': 'aac',
            'bitrate': '2000k',
            'temp_audiofile': get_absolute_path('temp/temp-tts-audio.m4a'),
            'remove_temp': True,
            'verbose': True,
            'logger': 'bar',
            'threads': threading_detector.threading_config['moviepy_threads']
        }
        
        # Add GPU-specific FFmpeg parameters
        ffmpeg_params = gpu_params.get('ffmpeg_params', [])
        ffmpeg_params.extend([
            '-threads', str(threading_detector.threading_config['ffmpeg_threads']),
            '-thread_type', 'slice+frame',
            '-slices', str(threading_detector.threading_config['ffmpeg_threads']),
        ])
        
        write_params['ffmpeg_params'] = ffmpeg_params
        
        # Log performance configuration
        effects_status = "ENABLED" if effects.get('effects_enabled', True) else "DISABLED"
        motion_status = "ENABLED" if effects.get('motion_effects_enabled', True) and effects.get('effects_enabled', True) else "DISABLED"
        transition_status = "ENABLED" if effects.get('transition_effects_enabled', True) and effects.get('effects_enabled', True) else "DISABLED"
        
        logging.info(f"🚀 TTS Video Rendering with {gpu_params['codec']}")
        logging.info(f"🧵 Using {threading_detector.threading_config['moviepy_threads']} threads")
        
        print(f"\n🚀 TTS VIDEO RENDERING STARTED!")
        print(f"📊 Total segments: {len(valid_segments)}")
        print(f"🖼️ Total images: {total_images}")
        print(f"⚙️ Encoder: {gpu_params['codec']}")
        print(f"🎭 Video Effects: {effects_status}")
        print(f"🎬 Motion Effects: {motion_status}")
        print(f"🎞️ Transition Effects: {transition_status}")
        print(f"🧵 Threads: {threading_detector.threading_config['moviepy_threads']}")
        print("=" * 60)
        
        # Write video file
        final_video.write_videofile(output_path, **write_params)
        
        print("=" * 60)
        print("🎉 TTS VIDEO RENDERING COMPLETED!")
        
        # Clean up
        logging.info("🧹 Cleaning up TTS temporary files")
        
        # Close clips
        final_video.close()
        for clip in clips:
            clip.close()
        for clip in final_clips:
            clip.close()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        return True
        
    except Exception as e:
        logging.error(f"❌ Error creating TTS video: {e}")
        return False

def validate_tts_settings(voice, voice_style, language):
    """Validate TTS settings"""
    valid_voices = ['nova', 'alloy', 'echo', 'fable', 'onyx', 'shimmer']
    valid_styles = ['friendly', 'calm', 'patient_teacher', 'mellow_story']
    valid_languages = ['id-ID', 'en-US', 'de-DE', 'es-ES', 'fr-FR', 'ja-JP', 'ko-KR', 'ar-SA', 'zh-CN']
    
    return (voice in valid_voices and 
            voice_style in valid_styles and 
            language in valid_languages)

def check_tts_availability():
    """Check if TTS functionality is available"""
    return TTS_AVAILABLE