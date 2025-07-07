import requests
import urllib.parse
import time
import logging
import os
from config import load_settings

# Setup logging
logging.basicConfig(level=logging.INFO)

# Pollinations Image API endpoint
POLLINATIONS_IMAGE_URL = "https://image.pollinations.ai/prompt"

# Available models (hanya flux dan turbo)
POLLINATIONS_MODELS = {
    'flux': {
        'name': 'Flux (Default)',
        'description': 'High-quality general purpose model',
        'delay': 5,  # 5 seconds delay as requested
        'supports_transparent': False,
        'supports_image_to_image': False
    },
    'turbo': {
        'name': 'Turbo (Fast)',
        'description': 'Faster generation with good quality',
        'delay': 5,  # 5 seconds delay as requested
        'supports_transparent': False,
        'supports_image_to_image': False
    }
}

def generate_pollinations_image(prompt, model='flux', width=1024, height=1024, seed=None, 
                               enhance=False, safe=False, transparent=False, 
                               input_image_url=None, private=True):
    """
    Generate image using Pollinations API
    
    Args:
        prompt (str): Text description of the image
        model (str): Model for generation ('flux', 'turbo')
        width (int): Width of the generated image in pixels
        height (int): Height of the generated image in pixels
        seed (int): Seed for reproducible results
        enhance (bool): Enhance the prompt using LLM
        safe (bool): Strict NSFW filtering
        transparent (bool): Generate with transparent background (not supported)
        input_image_url (str): URL of input image for image-to-image generation (not supported)
        private (bool): Prevent image from appearing in public feed
        
    Returns:
        dict: {'image_data': bytes, 'model': str, 'prompt': str, 'seed': int}
    """
    try:
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        # Validate model
        if model not in POLLINATIONS_MODELS:
            logging.warning(f"Unknown model '{model}', using 'flux' as fallback")
            model = 'flux'
        
        model_config = POLLINATIONS_MODELS[model]
        
        # Disable unsupported features
        if transparent:
            logging.warning(f"Model '{model}' doesn't support transparency, disabling")
            transparent = False
        
        if input_image_url:
            logging.warning(f"Model '{model}' doesn't support image-to-image, ignoring input image")
            input_image_url = None
        
        # Encode prompt for URL
        encoded_prompt = urllib.parse.quote(prompt.strip())
        url = f"{POLLINATIONS_IMAGE_URL}/{encoded_prompt}"
        
        # Build parameters
        params = {
            'model': model,
            'width': width,
            'height': height,
            'private': 'true' if private else 'false',
            'enhance': 'true' if enhance else 'false',
            'safe': 'true' if safe else 'false'
        }
        
        # Add optional parameters
        if seed is not None:
            params['seed'] = seed
        
        # Add referrer for better rate limits
        params['referrer'] = 'VideoGenFX'
        
        logging.info(f"🎨 Generating image with Pollinations {model_config['name']}")
        logging.info(f"📝 Prompt: {prompt[:100]}...")
        logging.info(f"📐 Size: {width}x{height}")
        
        # Apply delay for turbo and flux models
        if model_config['delay'] > 0:
            logging.info(f"⏱️ Applying {model_config['delay']}s delay for {model} model")
            time.sleep(model_config['delay'])
        
        # Make request with extended timeout
        response = requests.get(url, params=params, timeout=300)
        response.raise_for_status()
        
        # Check if response is actually an image
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            # Try to get error message from response
            error_text = response.text[:200] if response.text else "Unknown error"
            raise ValueError(f"API returned non-image content: {error_text}")
        
        image_data = response.content
        
        if len(image_data) == 0:
            raise ValueError("Received empty image data")
        
        logging.info(f"✅ Image generated successfully with {model} model ({len(image_data)} bytes)")
        
        return {
            'image_data': image_data,
            'model': model,
            'prompt': prompt,
            'seed': seed,
            'width': width,
            'height': height,
            'content_type': content_type
        }
        
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Pollinations API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"Response status: {e.response.status_code}")
            logging.error(f"Response text: {e.response.text[:200]}")
        raise ValueError(f"Pollinations API error: {str(e)}")
    
    except Exception as e:
        logging.error(f"❌ Error generating image with Pollinations: {e}")
        raise

def save_pollinations_image(image_data, filename, content_type='image/jpeg'):
    """Save Pollinations image data to file"""
    try:
        # Determine file extension from content type
        if 'png' in content_type:
            if not filename.endswith('.png'):
                filename = filename.rsplit('.', 1)[0] + '.png'
        elif 'jpeg' in content_type or 'jpg' in content_type:
            if not filename.endswith(('.jpg', '.jpeg')):
                filename = filename.rsplit('.', 1)[0] + '.jpg'
        
        with open(filename, 'wb') as f:
            f.write(image_data)
        
        logging.info(f"💾 Pollinations image saved: {filename} ({len(image_data)} bytes)")
        return True
        
    except Exception as e:
        logging.error(f"❌ Error saving Pollinations image: {e}")
        return False

def get_pollinations_models():
    """Get available Pollinations models"""
    return POLLINATIONS_MODELS

def validate_pollinations_params(width, height, model):
    """Validate Pollinations API parameters"""
    # Validate dimensions
    if width < 64 or width > 2048:
        raise ValueError("Width must be between 64 and 2048 pixels")
    
    if height < 64 or height > 2048:
        raise ValueError("Height must be between 64 and 2048 pixels")
    
    # Validate model
    if model not in POLLINATIONS_MODELS:
        raise ValueError(f"Invalid model. Available models: {list(POLLINATIONS_MODELS.keys())}")
    
    return True

def convert_aspect_ratio_to_dimensions(aspect_ratio, base_size=1024):
    """Convert aspect ratio string to width/height dimensions"""
    aspect_ratios = {
        'IMAGE_ASPECT_RATIO_LANDSCAPE': (1280, 720),
        'IMAGE_ASPECT_RATIO_PORTRAIT': (720, 1280),
        'IMAGE_ASPECT_RATIO_SQUARE': (1024, 1024)
    }
    
    return aspect_ratios.get(aspect_ratio, (1024, 1024))

def enhance_prompt_for_pollinations(prompt, style_hint=None):
    """Enhance prompt for better Pollinations results"""
    enhanced = prompt.strip()
    
    # Add style hints if provided
    if style_hint:
        enhanced = f"{enhanced}, {style_hint}"
    
    # Add quality enhancers for better results
    quality_terms = [
        "high quality",
        "detailed",
        "professional",
        "8k resolution"
    ]
    
    # Only add if not already present
    enhanced_lower = enhanced.lower()
    for term in quality_terms:
        if term not in enhanced_lower:
            enhanced += f", {term}"
            break  # Add only one quality term
    
    return enhanced