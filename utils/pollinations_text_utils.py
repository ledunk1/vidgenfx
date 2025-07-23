import requests
import urllib.parse
import time
import logging
import threading
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)

# Pollinations Text API endpoint
POLLINATIONS_TEXT_URL = "https://text.pollinations.ai"

# Hardcoded auth token (same as TTS)
POLLINATIONS_TEXT_AUTH_TOKEN = "hmqLceX0_vncHxv0"

# Rate limiting: 1 concurrent request / 3 sec interval
class RateLimiter:
    def __init__(self, interval=3.0):
        self.interval = interval
        self.last_request_time = 0
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            
            if time_since_last < self.interval:
                wait_time = self.interval - time_since_last
                logging.info(f"⏱️ Rate limiting: waiting {wait_time:.1f}s before next request")
                time.sleep(wait_time)
            
            self.last_request_time = time.time()

# Global rate limiter instance
rate_limiter = RateLimiter(interval=3.0)

# Available text generation models
POLLINATIONS_TEXT_MODELS = {
    'openai': {
        'name': 'OpenAI (Default)',
        'description': 'General purpose, balanced performance'
    },
    'openai-fast': {
        'name': 'OpenAI Fast',
        'description': 'Faster responses, good quality'
    },
    'openai-large': {
        'name': 'OpenAI Large',
        'description': 'High quality, slower responses'
    },
    'openai-reasoning': {
        'name': 'OpenAI Reasoning',
        'description': 'Advanced reasoning capabilities'
    },
    'openai-roblox': {
        'name': 'OpenAI Roblox',
        'description': 'Specialized for gaming content'
    },
    'deepseek': {
        'name': 'DeepSeek',
        'description': 'Advanced reasoning model'
    },
    'deepseek-reasoning': {
        'name': 'DeepSeek Reasoning',
        'description': 'Enhanced reasoning capabilities'
    },
    'grok': {
        'name': 'Grok',
        'description': 'Conversational AI with humor'
    },
    'llamascout': {
        'name': 'LlamaScout',
        'description': 'Efficient and fast responses'
    },
    'mistral': {
        'name': 'Mistral',
        'description': 'European AI model, multilingual'
    },
    'phi': {
        'name': 'Phi',
        'description': 'Microsoft small language model'
    },
    'qwen-coder': {
        'name': 'Qwen Coder',
        'description': 'Specialized for coding tasks'
    },
    'searchgpt': {
        'name': 'SearchGPT',
        'description': 'Search-enhanced responses'
    },
    'bidara': {
        'name': 'Bidara',
        'description': 'Indonesian language model'
    },
    'elixposearch': {
        'name': 'ElixpoSearch',
        'description': 'Search-optimized model'
    },
    'evil': {
        'name': 'Evil',
        'description': 'Uncensored model'
    },
    'midijourney': {
        'name': 'MidiJourney',
        'description': 'Creative content generation'
    },
    'mirexa': {
        'name': 'Mirexa',
        'description': 'Balanced performance model'
    },
    'rtist': {
        'name': 'Rtist',
        'description': 'Artistic content generation'
    },
    'sur': {
        'name': 'Sur',
        'description': 'Specialized model'
    },
    'unity': {
        'name': 'Unity',
        'description': 'Game development focused'
    }
}

def generate_text_prompt(prompt: str, model: str = 'openai', system_prompt: Optional[str] = None, 
                        temperature: Optional[float] = None, seed: Optional[int] = None) -> str:
    """
    Generate text using Pollinations Text API with rate limiting
    
    Args:
        prompt (str): Text prompt for generation
        model (str): Model to use for generation
        system_prompt (str, optional): System prompt to guide behavior
        temperature (float, optional): Controls randomness (0.0 to 3.0)
        seed (int, optional): Seed for reproducible results
        
    Returns:
        str: Generated text
    """
    try:
        if not prompt or not prompt.strip():
            raise ValueError("Prompt cannot be empty")
        
        # Validate model
        if model not in POLLINATIONS_TEXT_MODELS:
            logging.warning(f"Unknown model '{model}', using 'openai' as fallback")
            model = 'openai'
        
        # Apply rate limiting
        rate_limiter.wait_if_needed()
        
        # URL encode the prompt
        encoded_prompt = urllib.parse.quote(prompt.strip())
        url = f"{POLLINATIONS_TEXT_URL}/{encoded_prompt}"
        
        # Build parameters
        params = {
            'model': model,
            'private': 'true',  # Prevent from appearing in public feed
            'referrer': 'VideoGenFX'  # Referrer for better rate limits
        }
        
        # Add optional parameters
        if system_prompt:
            params['system'] = system_prompt
        
        if temperature is not None:
            params['temperature'] = max(0.0, min(3.0, temperature))
        
        if seed is not None:
            params['seed'] = seed
        
        # Headers with auth token
        headers = {
            'Authorization': f'Bearer {POLLINATIONS_TEXT_AUTH_TOKEN}',
            'User-Agent': 'VideoGenFX/1.0'
        }
        
        logging.info(f"🤖 Generating text with Pollinations {POLLINATIONS_TEXT_MODELS[model]['name']}")
        logging.info(f"📝 Prompt: {prompt[:100]}...")
        
        # Make request with timeout
        response = requests.get(url, params=params, headers=headers, timeout=60)
        response.raise_for_status()
        
        generated_text = response.text.strip()
        
        if not generated_text:
            raise ValueError("Received empty response from API")
        
        logging.info(f"✅ Text generated successfully with {model} model ({len(generated_text)} chars)")
        return generated_text
        
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Pollinations Text API request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logging.error(f"Response status: {e.response.status_code}")
            logging.error(f"Response text: {e.response.text[:200]}")
        raise ValueError(f"Pollinations Text API error: {str(e)}")
    
    except Exception as e:
        logging.error(f"❌ Error generating text with Pollinations: {e}")
        raise

def generate_image_prompt_with_pollinations(text_segment: str, model: str = 'openai', 
                                          template: Optional[str] = None) -> str:
    """
    Generate image prompt from text using Pollinations Text API
    
    Args:
        text_segment (str): Text to convert to image prompt
        model (str): Pollinations model to use
        template (str, optional): Template for prompt generation
        
    Returns:
        str: Generated image prompt
    """
    try:
        # Create system prompt for image generation
        if template:
            system_prompt = f"""You are an expert at creating visual prompts for AI image generation.
Based on the text provided, extract the main subject and action, then create a visual prompt using this template:

Template: "{template}"

Replace {{subject}} and {{action}} placeholders in the template with appropriate content from the text.
If the template doesn't have placeholders, incorporate the text content naturally.

Return only the final image prompt, nothing else. Keep it under 200 characters."""
        else:
            system_prompt = """You are an expert at creating visual prompts for AI image generation.
Based on the text provided, create a detailed visual prompt that captures the essence and mood of the content.

Include:
- Main subject or scene
- Visual style (realistic, artistic, etc.)
- Lighting and atmosphere
- Composition details
- Any relevant background elements

Keep the prompt concise but descriptive (max 200 characters).
Focus on visual elements that can be generated as an image.
Return only the image prompt, nothing else."""
        
        # Generate the image prompt
        image_prompt = generate_text_prompt(
            prompt=f"Create a visual prompt for this text: {text_segment}",
            model=model,
            system_prompt=system_prompt,
            temperature=0.7  # Slightly creative but consistent
        )
        
        return image_prompt.strip()
        
    except Exception as e:
        logging.error(f"Error generating image prompt with Pollinations: {e}")
        # Fallback to simple prompt
        if template:
            fallback = template.replace('{subject}', 'scene').replace('{action}', 'depicting')
            return f"{fallback}: {text_segment[:50]}..."
        return f"A scene depicting: {text_segment[:100]}..."

def get_pollinations_text_models() -> Dict[str, Dict[str, str]]:
    """Get available Pollinations text models"""
    return POLLINATIONS_TEXT_MODELS

def validate_text_generation_params(model: str, temperature: Optional[float] = None) -> bool:
    """Validate text generation parameters"""
    # Validate model
    if model not in POLLINATIONS_TEXT_MODELS:
        return False
    
    # Validate temperature
    if temperature is not None and (temperature < 0.0 or temperature > 3.0):
        return False
    
    return True

def test_pollinations_text_api(test_prompt: str = "Hello, how are you?") -> Dict[str, Any]:
    """Test Pollinations Text API with multiple models"""
    results = []
    
    # Test with a few key models
    test_models = ['openai', 'mistral', 'deepseek', 'grok']
    
    for model in test_models:
        try:
            start_time = time.time()
            
            response = generate_text_prompt(
                prompt=test_prompt,
                model=model
            )
            
            end_time = time.time()
            generation_time = end_time - start_time
            
            results.append({
                'model': model,
                'success': True,
                'response': response[:100] + "..." if len(response) > 100 else response,
                'generation_time': round(generation_time, 2),
                'response_length': len(response)
            })
            
        except Exception as e:
            results.append({
                'model': model,
                'success': False,
                'error': str(e),
                'generation_time': None
            })
    
    return {
        'test_prompt': test_prompt,
        'results': results,
        'total_models_tested': len(test_models),
        'successful_models': len([r for r in results if r['success']])
    }