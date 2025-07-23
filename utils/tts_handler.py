import requests
import time
import re
import json
import base64
import logging
from urllib.parse import quote_plus

# Setup logging
logging.basicConfig(level=logging.INFO)

# Pollinations TTS API endpoints
POLLINATIONS_TTS_OPENAI_URL = "https://text.pollinations.ai/openai"

# Hardcoded auth token
POLLINATIONS_TTS_AUTH_TOKEN = "hmqLceX0_vncHxv0"

# Content policy error signal
CONTENT_POLICY_ERROR_SIGNAL = "CONTENT_POLICY_VIOLATION"

def sanitize_text_for_tts(text):
    """Clean text from problematic words that might trigger content policy"""
    # Basic text sanitization
    problematic_words = {
        'mengerikan': 'mengejutkan',
        'menyeramkan': 'aneh',
        'menakutkan': 'mengejutkan',
        'membunuh': 'mengalahkan',
        'mati': 'pingsan',
        'darah': 'cairan merah',
        'mayat': 'tubuh yang tidak bergerak',
        'hantu': 'sosok misterius',
        'setan': 'makhluk gelap',
        'iblis': 'entitas jahat',
        'kutukan': 'mantra',
        'terkutuk': 'terkena mantra',
        'brutal': 'kasar',
        'sadis': 'kejam',
        'bengis': 'galak',
        'berdarah': 'berwarna merah',
        'mencekam': 'menegangkan',
        'horor': 'misteri',
        'terror': 'ketakutan',
        'menghantui': 'mengikuti',
        'kerasukan': 'dipengaruhi',
        'panik': 'terkejut',
        'histeria': 'sangat terkejut',
        'trauma': 'terguncang',
        'shock': 'terkejut',
        'ngeri': 'aneh',
        'seram': 'misterius',
        'geram': 'kesal',
        'murka': 'marah',
        'amarah': 'kemarahan'
    }
    
    # Replace problematic words
    sanitized_text = text
    for problematic, replacement in problematic_words.items():
        pattern = r'\b' + re.escape(problematic) + r'\b'
        sanitized_text = re.sub(pattern, replacement, sanitized_text, flags=re.IGNORECASE)
    
    # Clean special characters
    sanitized_text = re.sub(r'[^\w\s\.,!?;:\-\(\)]', ' ', sanitized_text)
    
    # Clean extra spaces
    sanitized_text = re.sub(r'\s+', ' ', sanitized_text).strip()
    
    return sanitized_text

def generate_audio_from_text_with_token(text_input, bahasa="id-ID", voice="nova", voice_style="friendly", max_retries_override=2):
    """
    Generate audio from text using Pollinations API with hardcoded auth token
    
    Args:
        text_input (str): Text to convert to speech
        bahasa (str): Language code (e.g., 'id-ID')
        voice (str): Voice selection (e.g., 'nova', 'alloy', 'shimmer', etc.)
        voice_style (str): Voice style (e.g., 'friendly', 'calm', etc.)
        max_retries_override (int): Number of retry attempts
        
    Returns:
        - Audio content (binary) if successful
        - CONTENT_POLICY_ERROR_SIGNAL (str) if content policy violation
        - None if other error
    """
    if not text_input or not text_input.strip():
        logging.error("TTS Error: Text input cannot be empty")
        return None

    # Sanitize text before processing
    sanitized_text = sanitize_text_for_tts(text_input)
    logging.info(f"TTS: Original text: {text_input[:100]}...")
    logging.info(f"TTS: Sanitized text: {sanitized_text[:100]}...")

    # Language prompts mapping
    language_prompts = {
        "id-ID": "Bacakan teks berikut dengan jelas dan natural:",
        "en-US": "Read the following text clearly and naturally:",
        "de-DE": "Lesen Sie den folgenden Text klar und natürlich vor:",
        "es-ES": "Lee el siguiente texto de forma clara y natural:",
        "fr-FR": "Lisez le texte suivant de manière claire et naturelle:",
        "ja-JP": "次のテキストを明確で自然に読んでください：",
        "ko-KR": "다음 텍스트를 명확하고 자연스럽게 읽어주세요:",
        "ar-SA": "اقرأ النص التالي بوضوح وطبيعية:",
        "zh-CN": "请清晰自然地朗读以下文本："
    }
    
    # Select prompt based on language
    instruction_prompt = language_prompts.get(bahasa, language_prompts["id-ID"])
    
    # Combine instruction prompt with sanitized text
    final_text_for_tts = f"{instruction_prompt} {sanitized_text}"
    
    # Safe voice styles for fallback
    safe_voice_styles = ["friendly", "calm", "patient_teacher", "mellow_story"]
    risky_styles = ["horror_story", "noir_detective"]
    
    if voice_style in risky_styles:
        logging.info(f"TTS: Voice style '{voice_style}' might be risky, will try fallback if failed")
    
    effective_max_retries = max(1, max_retries_override)
    
    # Always use hardcoded auth token
    logging.info(f"TTS: Using hardcoded auth token for higher rate limit")
    return _generate_audio_with_openai_api(
        final_text_for_tts, voice, voice_style, POLLINATIONS_TTS_AUTH_TOKEN, 
        effective_max_retries, safe_voice_styles, risky_styles
    )

def _generate_audio_with_openai_api(text, voice, voice_style, auth_token, max_retries, safe_voice_styles, risky_styles):
    """Use OpenAI-compatible API with Bearer token authentication"""
    url = POLLINATIONS_TTS_OPENAI_URL
    
    # Payload according to OpenAI API format
    payload = {
        "model": "openai-audio",
        "modalities": ["text", "audio"],
        "audio": {
            "voice": voice,
            "format": "mp3"
        },
        "messages": [
            {
                "role": "user", 
                "content": text
            }
        ],
        "private": True  # For better privacy
    }
    
    # Headers with Bearer token
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {auth_token}"
    }
    
    for attempt in range(1, max_retries + 1):
        logging.info(f"TTS API with token (Attempt {attempt}/{max_retries}): Voice={voice}, Style={voice_style}")
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=120)
            
            if response.status_code >= 400:
                logging.error(f"Error from API with status code: {response.status_code}")
                error_text = response.text.lower()
                
                # Check specifically for content policy error
                if "content management policy" in error_text or "safety" in error_text or "content policy" in error_text:
                    logging.error("Content policy error detected from API with token")
                    
                    # If this is first attempt and voice style is risky, try with safer style
                    if attempt == 1 and voice_style in risky_styles:
                        logging.info(f"Trying with safer voice style...")
                        for safe_style in safe_voice_styles:
                            logging.info(f"Trying with voice style: {safe_style}")
                            # Update payload with safer style
                            safe_payload = payload.copy()
                            safe_payload["messages"][0]["content"] = f"[Style: {safe_style}] {text}"
                            
                            try:
                                safe_response = requests.post(url, json=safe_payload, headers=headers, timeout=120)
                                if safe_response.status_code == 200:
                                    response_data = safe_response.json()
                                    if "choices" in response_data and len(response_data["choices"]) > 0:
                                        choice = response_data["choices"][0]
                                        if "message" in choice and "audio" in choice["message"]:
                                            audio_base64 = choice["message"]["audio"]["data"]
                                            audio_binary = base64.b64decode(audio_base64)
                                            logging.info(f"Success with voice style: {safe_style}")
                                            return audio_binary
                            except Exception as e_safe:
                                logging.error(f"Failed with style {safe_style}: {e_safe}")
                                continue
                    
                    # If all styles failed, return signal
                    return CONTENT_POLICY_ERROR_SIGNAL
                else:
                    logging.error(f"Other error from API: {response.text[:200]}")
            
            # If successful (status 200)
            elif response.status_code == 200:
                try:
                    response_data = response.json()
                    
                    # Parse response according to OpenAI format
                    if "choices" in response_data and len(response_data["choices"]) > 0:
                        choice = response_data["choices"][0]
                        if "message" in choice and "audio" in choice["message"]:
                            audio_base64 = choice["message"]["audio"]["data"]
                            audio_binary = base64.b64decode(audio_base64)
                            logging.info(f"Audio successfully obtained from API with token (attempt {attempt})")
                            return audio_binary
                        else:
                            logging.error(f"Response format not matching: {response_data}")
                    else:
                        logging.error(f"Response does not contain choices: {response_data}")
                        
                except json.JSONDecodeError as e:
                    logging.error(f"Error parsing JSON response: {e}")
                except Exception as e:
                    logging.error(f"Error processing response: {e}")
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Connection error when contacting TTS API with token attempt {attempt}: {e}")
        
        # If loop hasn't ended, wait before trying again
        if attempt < max_retries:
            time.sleep(30)
    
    logging.error(f"Failed to generate audio with token after {max_retries} attempts")
    return None

def generate_audio_from_text(text_input, bahasa="id-ID", voice="nova", voice_style="friendly", max_retries_override=2, auth_token=None):
    """
    Wrapper function for compatibility with existing code
    auth_token parameter is ignored as token is hardcoded
    """
    # Ignore auth_token parameter and always use hardcoded token
    return generate_audio_from_text_with_token(
        text_input=text_input,
        bahasa=bahasa,
        voice=voice,
        voice_style=voice_style,
        max_retries_override=max_retries_override
    )