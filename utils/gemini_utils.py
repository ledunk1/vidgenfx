import google.generativeai as genai
from config import load_settings
import re

def configure_gemini():
    """Configure Gemini API with API key from settings"""
    settings = load_settings()
    api_key = settings.get('gemini_api_key')
    if not api_key:
        raise ValueError("Gemini API key not found in settings")
    
    genai.configure(api_key=api_key)
    return True

def split_text_by_mode(text, mode='paragraph'):
    """Split text by paragraph or sentence"""
    text = text.strip()
    
    if mode == 'paragraph':
        # Split by double newlines or single newlines
        paragraphs = re.split(r'\n\s*\n|\n', text)
        return [p.strip() for p in paragraphs if p.strip()]
    
    elif mode == 'sentence':
        # Split by sentence endings
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    return [text]

def generate_image_prompt_with_gemini(text_segment, model='gemini-2.0-flash', template=None):
    """Generate image prompt from text using Gemini"""
    try:
        configure_gemini()
        
        # Create the model
        model_instance = genai.GenerativeModel(model)
        
        # Use template if provided
        if template:
            # Extract subject and action from text for template
            prompt_template = f"""
            Based on the following text, extract the main subject and action, then create a visual prompt using this template:
            
            Template: "{template}"
            Text: "{text_segment}"
            
            Replace {{subject}} and {{action}} placeholders in the template with appropriate content from the text.
            If the template doesn't have placeholders, incorporate the text content naturally.
            
            Return only the final image prompt, nothing else.
            """
        else:
            # Default prompt generation
            prompt_template = f"""
            Based on the following text, create a detailed visual prompt for image generation that captures the essence and mood of the content:

            Text: "{text_segment}"

            Create a descriptive prompt that includes:
            - Main subject or scene
            - Visual style (realistic, artistic, etc.)
            - Lighting and atmosphere
            - Composition details
            - Any relevant background elements

            Keep the prompt concise but descriptive (max 200 characters).
            Focus on visual elements that can be generated as an image.
            
            Return only the image prompt, nothing else.
            """
        
        response = model_instance.generate_content(prompt_template)
        return response.text.strip()
        
    except Exception as e:
        print(f"Error generating prompt with Gemini: {e}")
        # Fallback to simple prompt
        if template:
            # Simple template replacement
            fallback = template.replace('{subject}', 'person').replace('{action}', 'in scene')
            return f"{fallback}: {text_segment[:50]}..."
        return f"A scene depicting: {text_segment[:100]}..."

def generate_image_prompt(text_segment, provider='gemini', model=None, template=None):
    """
    Universal function to generate image prompt using different providers
    
    Args:
        text_segment (str): Text to convert to image prompt
        provider (str): Provider to use ('gemini' or 'pollinations')
        model (str): Model to use (provider-specific)
        template (str): Optional template for prompt generation
        
    Returns:
        str: Generated image prompt
    """
    try:
        if provider == 'gemini':
            # Use Gemini
            gemini_model = model or 'gemini-2.0-flash'
            return generate_image_prompt_with_gemini(text_segment, gemini_model, template)
        
        elif provider == 'pollinations':
            # Use Pollinations Text API
            from utils.pollinations_text_utils import generate_image_prompt_with_pollinations
            pollinations_model = model or 'openai'
            return generate_image_prompt_with_pollinations(text_segment, pollinations_model, template)
        
        else:
            raise ValueError(f"Unknown text provider: {provider}")
            
    except Exception as e:
        print(f"Error generating image prompt with {provider}: {e}")
        # Fallback to simple prompt
        if template:
            fallback = template.replace('{subject}', 'scene').replace('{action}', 'depicting')
            return f"{fallback}: {text_segment[:50]}..."
        return f"A scene depicting: {text_segment[:100]}..."

def estimate_reading_time(text, words_per_minute=150):
    """Estimate reading time for text in seconds"""
    word_count = len(text.split())
    minutes = word_count / words_per_minute
    return max(minutes * 60, 2.0)  # Minimum 2 seconds per segment