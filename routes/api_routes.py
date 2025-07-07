from flask import Blueprint, request, jsonify
from config import load_settings, save_settings, load_prompt_templates, save_prompt_templates, IMAGE_PROVIDERS, TEXT_PROVIDERS
from utils.gemini_utils import generate_image_prompt, split_text_by_mode
from utils.imagefx_utils import generate_image
from utils.pollinations_utils import generate_pollinations_image, convert_aspect_ratio_to_dimensions
from utils.pollinations_text_utils import get_pollinations_text_models, test_pollinations_text_api

api_bp = Blueprint('api', __name__)

@api_bp.route('/settings', methods=['GET'])
def get_settings():
    settings = load_settings()
    # Return actual values for API keys (they are stored in JSON)
    return jsonify(settings)

@api_bp.route('/settings', methods=['POST'])
def update_settings():
    try:
        data = request.get_json()
        settings = load_settings()
        
        # Update settings with new values
        if 'gemini_api_key' in data and data['gemini_api_key']:
            settings['gemini_api_key'] = data['gemini_api_key']
        if 'imagefx_auth_token' in data and data['imagefx_auth_token']:
            settings['imagefx_auth_token'] = data['imagefx_auth_token']
        if 'default_gemini_model' in data:
            settings['default_gemini_model'] = data['default_gemini_model']
        if 'default_imagefx_model' in data:
            settings['default_imagefx_model'] = data['default_imagefx_model']
        if 'default_aspect_ratio' in data:
            settings['default_aspect_ratio'] = data['default_aspect_ratio']
        if 'default_image_provider' in data:
            settings['default_image_provider'] = data['default_image_provider']
        if 'default_text_provider' in data:
            settings['default_text_provider'] = data['default_text_provider']
        if 'video_effects' in data:
            settings['video_effects'] = data['video_effects']
            
        save_settings(settings)
        return jsonify({"message": "Settings saved successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/text-providers', methods=['GET'])
def get_text_providers():
    """Get available text generation providers"""
    try:
        return jsonify({
            "success": True,
            "providers": TEXT_PROVIDERS
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/image-providers', methods=['GET'])
def get_image_providers():
    """Get available image generation providers"""
    try:
        return jsonify({
            "success": True,
            "providers": IMAGE_PROVIDERS
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/generate-prompts', methods=['POST'])
def generate_prompts():
    try:
        data = request.get_json()
        text = data.get('text', '')
        mode = data.get('mode', 'paragraph')
        
        # Text generation settings
        text_provider = data.get('text_provider', 'gemini')
        text_model = data.get('text_model')
        
        # Legacy support for gemini_model parameter
        if not text_model and 'gemini_model' in data:
            text_model = data['gemini_model']
            if text_provider == 'gemini':
                text_model = data['gemini_model']
        
        # Set default models based on provider
        if not text_model:
            if text_provider == 'gemini':
                text_model = 'gemini-2.0-flash'
            elif text_provider == 'pollinations':
                text_model = 'openai'
        
        template_id = data.get('template_id')
        
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        # Split text by mode
        segments = split_text_by_mode(text, mode)
        
        # Load template if specified
        template = None
        if template_id:
            templates_data = load_prompt_templates()
            for t in templates_data['templates']:
                if t['id'] == template_id:
                    template = t['template']
                    break
        
        # Generate prompts for each segment
        prompts = []
        for i, segment in enumerate(segments):
            try:
                prompt = generate_image_prompt(
                    text_segment=segment,
                    provider=text_provider,
                    model=text_model,
                    template=template
                )
                prompts.append({
                    'index': i,
                    'text_segment': segment,
                    'image_prompt': prompt,
                    'provider_used': text_provider,
                    'model_used': text_model
                })
            except Exception as e:
                prompts.append({
                    'index': i,
                    'text_segment': segment,
                    'image_prompt': f"Error generating prompt: {str(e)}",
                    'provider_used': text_provider,
                    'model_used': text_model,
                    'error': True
                })
        
        return jsonify({
            "success": True,
            "prompts": prompts,
            "total_segments": len(segments),
            "text_provider_used": text_provider,
            "text_model_used": text_model
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/generate-image', methods=['POST'])
def generate_single_image():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        aspect_ratio = data.get('aspect_ratio', 'IMAGE_ASPECT_RATIO_LANDSCAPE')
        provider = data.get('provider', 'imagefx')
        model = data.get('model')
        
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
        
        # Generate image based on provider
        if provider == 'imagefx':
            # Use ImageFX
            imagefx_model = model or 'IMAGEN_3_5'
            result = generate_image(prompt, aspect_ratio, imagefx_model)
        elif provider == 'pollinations':
            # Use Pollinations
            pollinations_model = model or 'flux'
            width, height = convert_aspect_ratio_to_dimensions(aspect_ratio)
            result = generate_pollinations_image(
                prompt=prompt,
                model=pollinations_model,
                width=width,
                height=height
            )
            # Convert to ImageFX-like format
            result = {
                'image_data': result['image_data'],
                'model': result['model'],
                'prompt': result['prompt']
            }
        else:
            return jsonify({"error": f"Unknown provider: {provider}"}), 400
        
        return jsonify({
            "success": True,
            "image": result,
            "provider": provider
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/test-pollinations-text', methods=['POST'])
def test_pollinations_text():
    """Test Pollinations Text API with multiple models"""
    try:
        data = request.get_json()
        test_prompt = data.get('prompt', 'Write a short creative description of a sunset over the ocean')
        
        result = test_pollinations_text_api(test_prompt)
        
        return jsonify({
            "success": True,
            "test_results": result
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Prompt Templates CRUD
@api_bp.route('/prompt-templates', methods=['GET'])
def get_prompt_templates():
    try:
        templates = load_prompt_templates()
        return jsonify(templates)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/prompt-templates', methods=['POST'])
def create_prompt_template():
    try:
        data = request.get_json()
        name = data.get('name', '')
        template = data.get('template', '')
        description = data.get('description', '')
        
        if not name or not template:
            return jsonify({"error": "Name and template are required"}), 400
        
        templates_data = load_prompt_templates()
        
        # Generate new ID
        max_id = max([t['id'] for t in templates_data['templates']], default=0)
        new_id = max_id + 1
        
        new_template = {
            'id': new_id,
            'name': name,
            'template': template,
            'description': description
        }
        
        templates_data['templates'].append(new_template)
        save_prompt_templates(templates_data)
        
        return jsonify({
            "success": True,
            "template": new_template,
            "message": "Template created successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/prompt-templates/<int:template_id>', methods=['PUT'])
def update_prompt_template(template_id):
    try:
        data = request.get_json()
        templates_data = load_prompt_templates()
        
        # Find template
        template_found = False
        for i, template in enumerate(templates_data['templates']):
            if template['id'] == template_id:
                if 'name' in data:
                    template['name'] = data['name']
                if 'template' in data:
                    template['template'] = data['template']
                if 'description' in data:
                    template['description'] = data['description']
                template_found = True
                break
        
        if not template_found:
            return jsonify({"error": "Template not found"}), 404
        
        save_prompt_templates(templates_data)
        
        return jsonify({
            "success": True,
            "message": "Template updated successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@api_bp.route('/prompt-templates/<int:template_id>', methods=['DELETE'])
def delete_prompt_template(template_id):
    try:
        templates_data = load_prompt_templates()
        
        # Find and remove template
        original_length = len(templates_data['templates'])
        templates_data['templates'] = [t for t in templates_data['templates'] if t['id'] != template_id]
        
        if len(templates_data['templates']) == original_length:
            return jsonify({"error": "Template not found"}), 404
        
        save_prompt_templates(templates_data)
        
        return jsonify({
            "success": True,
            "message": "Template deleted successfully"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500