from moviepy.editor import *
import librosa
import numpy as np
import random
import os
import logging
import multiprocessing
import threading
from PIL import Image
from config import load_settings
from utils.gpu_utils import gpu_detector

# Setup logging
logging.basicConfig(level=logging.INFO)

class ThreadingDetector:
    """Auto-detect optimal threading configuration for maximum performance"""
    
    def __init__(self):
        self.cpu_count = multiprocessing.cpu_count()
        self.max_threads = self.cpu_count  # Use 100% of all threads
        self.memory_available = self._estimate_available_memory()
        self.threading_config = self._determine_threading_config()
        
    def _estimate_available_memory(self):
        """Estimate available system memory in GB"""
        try:
            import psutil
            memory = psutil.virtual_memory()
            return memory.available / (1024**3)  # Convert to GB
        except ImportError:
            # Fallback estimation based on CPU count
            if self.cpu_count <= 2:
                return 4  # Assume 4GB for low-end systems
            elif self.cpu_count <= 4:
                return 8  # Assume 8GB for mid-range systems
            else:
                return 16  # Assume 16GB+ for high-end systems
    
    def _determine_threading_config(self):
        """Determine maximum threading configuration for fastest rendering"""
        config = {
            'moviepy_threads': self.max_threads,  # Use all threads for MoviePy
            'image_processing_threads': self.max_threads,  # Use all threads for image processing
            'concurrent_clips': min(self.max_threads, 8),  # Limit concurrent clips to prevent memory issues
            'memory_conservative': self.memory_available < 4,  # Only conservative if very low memory
            'ffmpeg_threads': self.max_threads,  # Use all threads for FFmpeg
            'parallel_batches': max(1, self.max_threads // 2)  # Parallel batch processing
        }
        
        logging.info(f"🚀 MAXIMUM PERFORMANCE Threading Configuration:")
        logging.info(f"   CPU Cores: {self.cpu_count}")
        logging.info(f"   Using ALL {self.max_threads} threads for maximum speed")
        logging.info(f"   MoviePy Threads: {config['moviepy_threads']}")
        logging.info(f"   Image Processing Threads: {config['image_processing_threads']}")
        logging.info(f"   FFmpeg Threads: {config['ffmpeg_threads']}")
        logging.info(f"   Concurrent Clips: {config['concurrent_clips']}")
        logging.info(f"   Parallel Batches: {config['parallel_batches']}")
        logging.info(f"   Memory Conservative Mode: {config['memory_conservative']}")
        
        return config

# Global threading detector
threading_detector = ThreadingDetector()

def get_audio_duration(audio_path):
    """Get duration of audio file in seconds"""
    try:
        duration = librosa.get_duration(path=audio_path)
        return duration
    except Exception as e:
        print(f"Error getting audio duration: {e}")
        return 0

def apply_ken_burns_effect(clip, effect_type='zoom_in', intensity=0.08):
    """Apply Ken Burns effect on video clip with improved implementation to avoid border effects."""
    w, h = clip.size
    duration = clip.duration
    
    logging.debug(f"Applying {effect_type} effect with intensity {intensity} on clip size {w}x{h}")
    
    # Zoom factor for pan effects (based on reference script)
    zoom_factor = 1 + intensity * 3  # Convert intensity to larger zoom factor
    
    # Calculate movement range based on reference script
    travel_factor = intensity * 4  # Convert intensity to travel factor
    
    if effect_type in ['pan_right', 'pan_left', 'pan_up', 'pan_down']:
        # For pan effects, enlarge image first
        enlarged_clip = clip.resize(zoom_factor)
        enlarged_w, enlarged_h = enlarged_clip.size
        
        # Calculate maximum movement range
        max_range_x = max(0, (enlarged_w - w) / 2)
        max_range_y = max(0, (enlarged_h - h) / 2)
        
        # Apply travel factor
        range_x = max_range_x * travel_factor
        range_y = max_range_y * travel_factor
        
        # Center position
        center_x = (w - enlarged_w) / 2
        center_y = (h - enlarged_h) / 2
        
        def position_func(t):
            progress = t / duration
            if effect_type == 'pan_right':
                return (center_x - range_x * progress, center_y)
            elif effect_type == 'pan_left':
                return (center_x + range_x * progress, center_y)
            elif effect_type == 'pan_up':
                return (center_x, center_y + range_y * progress)
            elif effect_type == 'pan_down':
                return (center_x, center_y - range_y * progress)
            return ('center', 'center')
        
        # Create composite clip with changing position
        result_clip = CompositeVideoClip(
            [enlarged_clip.set_position(position_func)], 
            size=(w, h)
        ).set_duration(duration)
        
        return result_clip
    
    elif effect_type in ['zoom_in', 'zoom_out']:
        # For zoom effects, use resize with time function
        def resize_func(t):
            progress = t / duration
            if effect_type == 'zoom_in':
                return 1 + intensity * 3 * progress  # Zoom from 1x to zoom_factor
            elif effect_type == 'zoom_out':
                return zoom_factor - intensity * 3 * progress  # Zoom from zoom_factor to 1x
            return 1
        
        # Apply resize with time function and center position
        result_clip = CompositeVideoClip(
            [clip.resize(resize_func).set_position('center')],
            size=(w, h)
        ).set_duration(duration)
        
        return result_clip
    
    # Fallback: return original clip
    return clip

def process_image_batch(image_batch, target_size, temp_dir, start_index):
    """Process a batch of images in parallel with maximum threading"""
    processed_paths = []
    
    for i, image_path in enumerate(image_batch):
        try:
            # Load and resize image with maximum optimization
            img = Image.open(image_path)
            
            # Resize image maintaining aspect ratio and ensuring no borders
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
            
            # Save resized image with maximum compression for speed
            temp_img_path = os.path.join(temp_dir, f"resized_{start_index + i}.png")
            img.save(temp_img_path, optimize=True, compress_level=1)  # Fast compression
            processed_paths.append(temp_img_path)
            
        except Exception as e:
            logging.error(f"Error processing image {image_path}: {e}")
            processed_paths.append(None)
    
    return processed_paths

def create_clips_batch_parallel(image_paths, duration_per_image, effects, effect_types, effect_weights):
    """Create video clips from images using maximum parallel processing"""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    clips = []
    total_images = len(image_paths)
    max_workers = threading_detector.threading_config['concurrent_clips']
    
    logging.info(f"🎬 Creating clips with {max_workers} parallel workers")
    
    def create_single_clip(args):
        i, image_path = args
        if image_path is None:
            return None
            
        try:
            # Create image clip
            clip = ImageClip(image_path, duration=duration_per_image)
            
            # Check if effects are enabled
            if not effects.get('effects_enabled', True):
                return (i, clip)
            
            # Check if motion effects are enabled
            if not effects.get('motion_effects_enabled', True):
                # If motion effects disabled, use no effect
                chosen_effect = 'no_effect'
            else:
                # Choose effect based on unified probability system
                chosen_effect = random.choices(effect_types, weights=effect_weights)[0]
            
            # Apply the chosen effect
            if chosen_effect != 'no_effect':
                ken_burns_intensity = effects.get('ken_burns_intensity', 0.08)
                clip = apply_ken_burns_effect(clip, chosen_effect, ken_burns_intensity)
            
            return (i, clip)
            
        except Exception as e:
            logging.error(f"Error creating clip from {image_path}: {e}")
            return None
    
    # Process all clips in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        futures = []
        for i, image_path in enumerate(image_paths):
            future = executor.submit(create_single_clip, (i, image_path))
            futures.append(future)
        
        # Collect results maintaining order
        results = [None] * total_images
        for future in as_completed(futures):
            try:
                result = future.result()
                if result is not None:
                    i, clip = result
                    results[i] = clip
            except Exception as e:
                logging.error(f"Error in clip creation: {e}")
        
        # Filter out None values and maintain order
        clips = [clip for clip in results if clip is not None]
    
    return clips

def create_video_from_images(images, audio_path, output_path, aspect_ratio='landscape', custom_effects=None):
    """Create video from images with maximum threading for fastest rendering"""
    try:
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
        
        # Get audio duration
        audio_duration = get_audio_duration(audio_path)
        if audio_duration <= 0:
            raise ValueError("Invalid audio file")
        
        # Calculate duration per image
        num_images = len(images)
        duration_per_image = audio_duration / num_images
        
        # Load audio
        audio = AudioFileClip(audio_path)
        
        # Set resolution based on aspect ratio
        if aspect_ratio == 'portrait':
            target_size = (720, 1280)
        else:  # landscape
            target_size = (1280, 720)
        
        # Create temp directory for processed images
        temp_dir = "temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        # Process images with MAXIMUM parallel processing
        logging.info(f"🚀 MAXIMUM SPEED: Processing {num_images} images with ALL {threading_detector.threading_config['image_processing_threads']} threads")
        
        processed_image_paths = []
        
        # Calculate optimal batch size for maximum throughput
        batch_size = max(1, num_images // threading_detector.threading_config['parallel_batches'])
        
        # Use ALL available threads for parallel image processing
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        with ThreadPoolExecutor(max_workers=threading_detector.threading_config['image_processing_threads']) as executor:
            futures = []
            
            # Submit all batches in parallel
            for i in range(0, num_images, batch_size):
                batch_end = min(i + batch_size, num_images)
                image_batch = images[i:batch_end]
                
                future = executor.submit(process_image_batch, image_batch, target_size, temp_dir, i)
                futures.append(future)
            
            # Collect results as they complete
            for future in as_completed(futures):
                try:
                    batch_results = future.result()
                    processed_image_paths.extend(batch_results)
                except Exception as e:
                    logging.error(f"Error in image processing batch: {e}")
        
        # Filter out None values (failed processing)
        processed_image_paths = [path for path in processed_image_paths if path is not None]
        
        if not processed_image_paths:
            raise ValueError("No images were processed successfully")
        
        logging.info(f"✅ Successfully processed {len(processed_image_paths)} images at MAXIMUM SPEED")
        
        # Available effect types with their probabilities
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
        
        # Create video clips with MAXIMUM parallel processing
        logging.info(f"🎬 Creating video clips with MAXIMUM {threading_detector.threading_config['concurrent_clips']} parallel workers")
        clips = create_clips_batch_parallel(processed_image_paths, duration_per_image, effects, effect_types, effect_weights)
        
        if not clips:
            raise ValueError("No video clips were created successfully")
        
        # Apply fade transitions with parallel processing
        final_clips = []
        fade_duration = min(effects.get('fade_duration', 0.5), duration_per_image / 3)
        fade_probability = effects.get('fade_probability', 100)
        
        # Check if transition effects are enabled
        transition_effects_enabled = effects.get('transition_effects_enabled', True) and effects.get('effects_enabled', True)
        
        logging.info("🎭 Applying fade transitions with parallel processing")
        
        def apply_fade_to_clip(args):
            i, clip = args
            
            # Check if transition effects are enabled
            if not transition_effects_enabled:
                return clip
            
            # Check if fade should be applied
            apply_fade = random.randint(1, 100) <= fade_probability
            
            if apply_fade:
                if i == 0:
                    # First clip: fade in only
                    return clip.fadein(fade_duration)
                elif i == len(clips) - 1:
                    # Last clip: fade out only
                    return clip.fadeout(fade_duration)
                else:
                    # Middle clips: crossfade (fade in and out)
                    return clip.fadein(fade_duration).fadeout(fade_duration)
            
            return clip
        
        # Apply fades in parallel
        with ThreadPoolExecutor(max_workers=threading_detector.threading_config['concurrent_clips']) as executor:
            fade_futures = []
            for i, clip in enumerate(clips):
                future = executor.submit(apply_fade_to_clip, (i, clip))
                fade_futures.append(future)
            
            # Collect results maintaining order
            for future in fade_futures:
                try:
                    final_clips.append(future.result())
                except Exception as e:
                    logging.error(f"Error applying fade: {e}")
                    final_clips.append(clips[len(final_clips)])  # Use original clip as fallback
        
        # Concatenate all clips with optimized method
        logging.info("🔗 Concatenating video clips")
        if len(final_clips) > 1:
            final_video = concatenate_videoclips(final_clips, method="compose")
        else:
            final_video = final_clips[0]
        
        # Ensure video duration matches audio duration
        if final_video.duration != audio_duration:
            final_video = final_video.set_duration(audio_duration)
        
        # Add audio
        final_video = final_video.set_audio(audio)
        
        # Get GPU-optimized encoding parameters
        gpu_params = gpu_detector.get_gpu_acceleration_params()
        
        # Configure MoviePy with MAXIMUM threading
        logging.info(f"⚙️ Configuring MoviePy with MAXIMUM {threading_detector.threading_config['moviepy_threads']} threads")
        
        # Write video file with MAXIMUM performance settings
        write_params = {
            'fps': 30,
            'codec': gpu_params['codec'],
            'audio_codec': 'aac',
            'bitrate': '2000k',
            'temp_audiofile': 'temp/temp-audio.m4a',
            'remove_temp': True,
            'verbose': True,
            'logger': 'bar',
            'threads': threading_detector.threading_config['moviepy_threads']
        }
        
        # Add GPU-specific FFmpeg parameters with maximum threading
        ffmpeg_params = gpu_params.get('ffmpeg_params', [])
        
        # Add MAXIMUM threading parameters for FFmpeg
        ffmpeg_params.extend([
            '-threads', str(threading_detector.threading_config['ffmpeg_threads']),
            '-thread_type', 'slice+frame',  # Use both slice and frame threading
            '-slices', str(threading_detector.threading_config['ffmpeg_threads']),  # Maximum slices
        ])
        
        # Add additional performance optimizations
        if gpu_detector.has_gpu_acceleration():
            # GPU-specific optimizations
            if 'qsv' in gpu_params['codec']:
                ffmpeg_params.extend(['-async_depth', '4'])  # Intel QSV optimization
            elif 'nvenc' in gpu_params['codec']:
                ffmpeg_params.extend(['-2pass', '0', '-gpu', '0'])  # NVIDIA optimization
            elif 'amf' in gpu_params['codec']:
                ffmpeg_params.extend(['-usage', 'transcoding', '-preanalysis', '1'])  # AMD optimization
        else:
            # CPU optimizations for maximum speed
            ffmpeg_params.extend([
                '-x264-params', f'threads={threading_detector.threading_config["ffmpeg_threads"]}',
                '-preset', 'fast',  # Fast but stable encoding preset
                '-tune', 'fastdecode'    # Optimize for fast decoding
            ])
        
        write_params['ffmpeg_params'] = ffmpeg_params
        
        # Log the MAXIMUM performance configuration
        effects_status = "ENABLED" if effects.get('effects_enabled', True) else "DISABLED"
        motion_status = "ENABLED" if effects.get('motion_effects_enabled', True) and effects.get('effects_enabled', True) else "DISABLED"
        transition_status = "ENABLED" if effects.get('transition_effects_enabled', True) and effects.get('effects_enabled', True) else "DISABLED"
        
        if gpu_detector.has_gpu_acceleration():
            logging.info(f"🚀 MAXIMUM PERFORMANCE: GPU-accelerated encoding with {gpu_params['codec']}")
        else:
            logging.info(f"🚀 MAXIMUM PERFORMANCE: CPU encoding with {threading_detector.threading_config['ffmpeg_threads']} threads")
        
        print(f"\n🚀 MAXIMUM SPEED VIDEO RENDERING STARTED!")
        print(f"📊 Video duration: {audio_duration:.2f}s")
        print(f"🖼️ Total images: {num_images}")
        print(f"⚙️ Encoder: {gpu_params['codec']}")
        print(f"🎭 Video Effects: {effects_status}")
        print(f"🎬 Motion Effects: {motion_status}")
        print(f"🎞️ Transition Effects: {transition_status}")
        print(f"🧵 MoviePy Threads: {threading_detector.threading_config['moviepy_threads']}")
        print(f"🧵 FFmpeg Threads: {threading_detector.threading_config['ffmpeg_threads']}")
        print(f"🧵 Image Processing Threads: {threading_detector.threading_config['image_processing_threads']}")
        print(f"🧵 Concurrent Clips: {threading_detector.threading_config['concurrent_clips']}")
        print(f"💾 Memory mode: {'Conservative' if threading_detector.threading_config['memory_conservative'] else 'MAXIMUM PERFORMANCE'}")
        print(f"🔥 USING 100% OF ALL {threading_detector.max_threads} CPU THREADS!")
        print("=" * 60)
        
        final_video.write_videofile(output_path, **write_params)
        
        print("=" * 60)
        print("🎉 MAXIMUM SPEED VIDEO RENDERING COMPLETED!")
        
        # Clean up processed images
        logging.info("🧹 Cleaning up temporary files")
        for img_path in processed_image_paths:
            try:
                if os.path.exists(img_path):
                    os.remove(img_path)
            except Exception as e:
                logging.warning(f"Could not remove temp file {img_path}: {e}")
        
        # Clean up clips
        final_video.close()
        audio.close()
        for clip in clips:
            clip.close()
        for clip in final_clips:
            clip.close()
        
        # Force garbage collection
        import gc
        gc.collect()
        
        return True
        
    except Exception as e:
        logging.error(f"Error creating video: {e}")
        return False

def validate_audio_file(file_path):
    """Validate if file is a valid audio file"""
    try:
        duration = librosa.get_duration(path=file_path)
        return duration > 0
    except:
        return False
