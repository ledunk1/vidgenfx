import requests
import base64
from config import load_settings
import os

def generate_image(prompt, aspect_ratio="IMAGE_ASPECT_RATIO_LANDSCAPE", model="IMAGEN_3_5"):
    """Generate image using ImageFX API"""
    settings = load_settings()
    auth_token = settings.get('imagefx_auth_token')
    
    if not auth_token:
        raise ValueError("ImageFX auth token not found in settings")

    if not auth_token.startswith("Bearer"):
        auth_token = f"Bearer {auth_token}"

    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'text/plain;charset=UTF-8',
        'dnt': '1',
        'origin': 'https://labs.google',
        'priority': 'u=1, i',
        'referer': 'https://labs.google/',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="133", "Chromium";v="133"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36',
        'authorization': auth_token
    }

    data = {
        "userInput": {
            "candidatesCount": 1,
            "prompts": [prompt],
            "seed": None,
        },
        "clientContext": {
            "sessionId": ";1740656431200",
            "tool": "IMAGE_FX"
        },
        "modelInput": {
            "modelNameType": model
        },
        "aspectRatio": aspect_ratio
    }

    try:
        response = requests.post(
            "https://aisandbox-pa.googleapis.com/v1:runImageFx",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        result = response.json()
        
        # Extract first image
        if 'imagePanels' in result and result['imagePanels']:
            for panel in result['imagePanels']:
                if 'generatedImages' in panel and panel['generatedImages']:
                    image_data = panel['generatedImages'][0]
                    return {
                        'image_data': image_data['encodedImage'],
                        'seed': image_data.get('seed'),
                        'prompt': prompt
                    }
        
        raise ValueError("No image generated")
        
    except requests.exceptions.RequestException as e:
        raise ValueError(f"ImageFX API error: {str(e)}")

def save_image_from_base64(image_data, filename):
    """Save base64 image data to file"""
    try:
        image_bytes = base64.b64decode(image_data)
        with open(filename, 'wb') as f:
            f.write(image_bytes)
        return True
    except Exception as e:
        print(f"Error saving image: {e}")
        return False