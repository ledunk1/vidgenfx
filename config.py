import os
import json
import sys

SETTINGS_FILE = 'settings.json'
TEMPLATES_FILE = 'prompt_templates.json'

# Get absolute paths for executable compatibility
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

# Use absolute paths for directories
UPLOAD_FOLDER = get_absolute_path('uploads')
OUTPUT_FOLDER = get_absolute_path('outputs')
TEMP_FOLDER = get_absolute_path('temp')

# Video settings
VIDEO_SETTINGS = {
    'fps': 30,
    'codec': 'libx264',
    'audio_codec': 'aac',
    'bitrate': '2000k'
}

# Default video effects settings with unified probability system and enable/disable toggles
DEFAULT_VIDEO_EFFECTS = {
    'effects_enabled': True,  # Master toggle for all effects
    'motion_effects_enabled': True,  # Toggle for motion effects
    'transition_effects_enabled': True,  # Toggle for transition effects
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
}

# Aspect ratios
ASPECT_RATIOS = {
    'portrait': {
        'name': 'Portrait (9:16)',
        'value': 'IMAGE_ASPECT_RATIO_PORTRAIT',
        'resolution': (720, 1280)
    },
    'landscape': {
        'name': 'Landscape (16:9)',
        'value': 'IMAGE_ASPECT_RATIO_LANDSCAPE',
        'resolution': (1280, 720)
    },
    'square': {
        'name': 'Square (1:1)',
        'value': 'IMAGE_ASPECT_RATIO_SQUARE',
        'resolution': (1024, 1024)
    }
}

# Gemini models
GEMINI_MODELS = {
    'gemini-2.0-flash': 'Gemini 2.0 Flash',
    'gemini-2.0-flash-exp': 'Gemini 2.0 Flash Experimental'
}

# ImageFX models
IMAGEFX_MODELS = {
    'IMAGEN_3_5': 'Imagen 3.5',
    'IMAGEN_3_1': 'Imagen 3.1'
}

# Pollinations models (hanya flux dan turbo)
POLLINATIONS_MODELS = {
    'flux': 'Flux (Default)',
    'turbo': 'Turbo (Fast)'
}

# Pollinations Text models
POLLINATIONS_TEXT_MODELS = {
    'openai': 'OpenAI (Default)',
    'openai-fast': 'OpenAI Fast',
    'openai-large': 'OpenAI Large',
    'openai-reasoning': 'OpenAI Reasoning',
    'openai-roblox': 'OpenAI Roblox',
    'deepseek': 'DeepSeek',
    'deepseek-reasoning': 'DeepSeek Reasoning',
    'grok': 'Grok',
    'llamascout': 'LlamaScout',
    'mistral': 'Mistral',
    'phi': 'Phi',
    'qwen-coder': 'Qwen Coder',
    'searchgpt': 'SearchGPT',
    'bidara': 'Bidara',
    'elixposearch': 'ElixpoSearch',
    'evil': 'Evil',
    'midijourney': 'MidiJourney',
    'mirexa': 'Mirexa',
    'rtist': 'Rtist',
    'sur': 'Sur',
    'unity': 'Unity'
}

# Text generation providers
TEXT_PROVIDERS = {
    'gemini': {
        'name': 'Google Gemini',
        'models': GEMINI_MODELS,
        'requires_auth': True,
        'description': 'Google\'s advanced AI model'
    },
    'pollinations': {
        'name': 'Pollinations Text',
        'models': POLLINATIONS_TEXT_MODELS,
        'requires_auth': False,
        'description': 'Multiple AI models via Pollinations API'
    }
}

# Image generation providers
IMAGE_PROVIDERS = {
    'imagefx': {
        'name': 'ImageFX (Google)',
        'models': IMAGEFX_MODELS,
        'requires_auth': True
    },
    'pollinations': {
        'name': 'Pollinations (Free)',
        'models': POLLINATIONS_MODELS,
        'requires_auth': False
    }
}

def load_settings():
    settings_path = get_absolute_path(SETTINGS_FILE)
    if os.path.exists(settings_path):
        with open(settings_path, 'r') as f:
            settings = json.load(f)
            # Merge with default video effects if not present
            if 'video_effects' not in settings:
                settings['video_effects'] = DEFAULT_VIDEO_EFFECTS
            else:
                # Ensure new unified settings are present
                for key, value in DEFAULT_VIDEO_EFFECTS.items():
                    if key not in settings['video_effects']:
                        settings['video_effects'][key] = value
            
            # Add default providers if not present
            if 'default_image_provider' not in settings:
                settings['default_image_provider'] = 'imagefx'
            
            if 'default_text_provider' not in settings:
                settings['default_text_provider'] = 'gemini'
            
            return settings
    return {
        'video_effects': DEFAULT_VIDEO_EFFECTS,
        'default_image_provider': 'imagefx',
        'default_text_provider': 'gemini'
    }

def save_settings(settings):
    settings_path = get_absolute_path(SETTINGS_FILE)
    with open(settings_path, 'w') as f:
        json.dump(settings, f, indent=2)

def load_prompt_templates():
    templates_path = get_absolute_path(TEMPLATES_FILE)
    if os.path.exists(templates_path):
        with open(templates_path, 'r') as f:
            return json.load(f)
    return {
        "templates": [
            {
                "id": 1,
                "name": "Cinematic Style",
                "template": "Cinematic shot of {subject}, {action}, dramatic lighting, film grain, professional photography",
                "description": "Creates cinematic-style images with dramatic lighting"
            },
            {
                "id": 2,
                "name": "Natural Documentary",
                "template": "Documentary style photo of {subject} {action}, natural lighting, candid moment, realistic",
                "description": "Natural documentary-style photography"
            },
            {
                "id": 3,
                "name": "Artistic Portrait",
                "template": "Artistic portrait of {subject}, {action}, soft lighting, shallow depth of field, professional studio",
                "description": "Professional artistic portrait style"
            }
        ]
    }

def save_prompt_templates(templates):
    templates_path = get_absolute_path(TEMPLATES_FILE)
    with open(templates_path, 'w') as f:
        json.dump(templates, f, indent=2)