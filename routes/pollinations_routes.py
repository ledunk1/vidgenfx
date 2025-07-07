from flask import Blueprint, request, jsonify, send_file
import os
import uuid
import logging
from utils.pollinations_utils import (
    generate_pollinations_image, 
    save_pollinations_image, 
    get_pollinations_models,
    validate_pollinations_params,
    convert_aspect_ratio_to_dimensions,
    enhance_prompt_for_pollinations
)
from config import OUTPUT_FOLDER

pollinations_bp = Blueprint('pollinations', __name__)

@pollinations_bp.route('/models', methods=['GET'])
def get_available_models():
    """Get available Pollinations models"""
    try:
        models = get_pollinations_models()
        return jsonify({
            "success": True,
            "models": models
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pollinations_bp.route('/generate-image', methods=['POST'])
def generate_image():
    """Generate image using Pollinations API"""
    try:
        data = request.get_json()
        
        # Required parameters
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
        
        # Optional parameters with defaults
        model = data.get('model', 'flux')
        aspect_ratio = data.get('aspect_ratio', 'IMAGE_ASPECT_RATIO_LANDSCAPE')
        seed = data.get('seed')
        enhance = data.get('enhance', False)
        safe = data.get('safe', False)
        transparent = data.get('transparent', False)
        input_image_url = data.get('input_image_url')
        style_hint = data.get('style_hint')
        
        # Convert aspect ratio to dimensions
        width, height = convert_aspect_ratio_to_dimensions(aspect_ratio)
        
        # Allow custom dimensions if provided
        if 'width' in data:
            width = int(data['width'])
        if 'height' in data:
            height = int(data['height'])
        
        # Validate parameters
        validate_pollinations_params(width, height, model)
        
        # Enhance prompt if requested or style hint provided
        if enhance or style_hint:
            prompt = enhance_prompt_for_pollinations(prompt, style_hint)
        
        # Generate image
        result = generate_pollinations_image(
            prompt=prompt,
            model=model,
            width=width,
            height=height,
            seed=seed,
            enhance=enhance,
            safe=safe,
            transparent=transparent,
            input_image_url=input_image_url,
            private=True
        )
        
        # Generate unique session and filename
        session_id = str(uuid.uuid4())
        images_folder = os.path.join(OUTPUT_FOLDER, 'images', session_id)
        os.makedirs(images_folder, exist_ok=True)
        
        # Determine file extension from content type
        content_type = result.get('content_type', 'image/jpeg')
        extension = '.png' if 'png' in content_type else '.jpg'
        filename = f"pollinations_image_{model}{extension}"
        image_path = os.path.join(images_folder, filename)
        
        # Save image
        if save_pollinations_image(result['image_data'], image_path, content_type):
            return jsonify({
                "success": True,
                "session_id": session_id,
                "filename": filename,
                "image_path": image_path,
                "model": result['model'],
                "prompt": result['prompt'],
                "seed": result['seed'],
                "width": result['width'],
                "height": result['height'],
                "content_type": content_type,
                "file_size": len(result['image_data'])
            })
        else:
            return jsonify({"error": "Failed to save image"}), 500
            
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logging.error(f"Error in Pollinations image generation: {e}")
        return jsonify({"error": str(e)}), 500

@pollinations_bp.route('/generate-batch', methods=['POST'])
def generate_batch_images():
    """Generate multiple images with different models"""
    try:
        data = request.get_json()
        
        prompt = data.get('prompt', '').strip()
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400
        
        models = data.get('models', ['flux', 'turbo'])
        aspect_ratio = data.get('aspect_ratio', 'IMAGE_ASPECT_RATIO_LANDSCAPE')
        
        # Convert aspect ratio to dimensions
        width, height = convert_aspect_ratio_to_dimensions(aspect_ratio)
        
        results = []
        session_id = str(uuid.uuid4())
        images_folder = os.path.join(OUTPUT_FOLDER, 'images', session_id)
        os.makedirs(images_folder, exist_ok=True)
        
        for model in models:
            try:
                # Validate model
                validate_pollinations_params(width, height, model)
                
                # Generate image
                result = generate_pollinations_image(
                    prompt=prompt,
                    model=model,
                    width=width,
                    height=height,
                    private=True
                )
                
                # Save image
                content_type = result.get('content_type', 'image/jpeg')
                extension = '.png' if 'png' in content_type else '.jpg'
                filename = f"pollinations_{model}{extension}"
                image_path = os.path.join(images_folder, filename)
                
                if save_pollinations_image(result['image_data'], image_path, content_type):
                    results.append({
                        "model": model,
                        "filename": filename,
                        "success": True,
                        "file_size": len(result['image_data'])
                    })
                else:
                    results.append({
                        "model": model,
                        "success": False,
                        "error": "Failed to save image"
                    })
                    
            except Exception as e:
                logging.error(f"Error generating image with {model}: {e}")
                results.append({
                    "model": model,
                    "success": False,
                    "error": str(e)
                })
        
        successful_results = [r for r in results if r['success']]
        
        return jsonify({
            "success": len(successful_results) > 0,
            "session_id": session_id,
            "results": results,
            "successful_count": len(successful_results),
            "total_count": len(models),
            "prompt": prompt
        })
        
    except Exception as e:
        logging.error(f"Error in batch image generation: {e}")
        return jsonify({"error": str(e)}), 500

@pollinations_bp.route('/download-image/<session_id>/<filename>')
def download_image(session_id, filename):
    """Download generated image"""
    try:
        image_path = os.path.join(OUTPUT_FOLDER, 'images', session_id, filename)
        
        if os.path.exists(image_path):
            return send_file(image_path, as_attachment=True, download_name=filename)
        else:
            return jsonify({"error": "Image not found"}), 404
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@pollinations_bp.route('/test-models', methods=['POST'])
def test_models():
    """Test all available models with a simple prompt"""
    try:
        data = request.get_json()
        test_prompt = data.get('prompt', 'A beautiful sunset over the ocean')
        
        models = list(get_pollinations_models().keys())
        results = []
        
        for model in models:
            try:
                start_time = time.time()
                
                result = generate_pollinations_image(
                    prompt=test_prompt,
                    model=model,
                    width=512,  # Smaller size for testing
                    height=512,
                    private=True
                )
                
                end_time = time.time()
                generation_time = end_time - start_time
                
                results.append({
                    "model": model,
                    "success": True,
                    "generation_time": round(generation_time, 2),
                    "file_size": len(result['image_data']),
                    "content_type": result.get('content_type', 'unknown')
                })
                
            except Exception as e:
                results.append({
                    "model": model,
                    "success": False,
                    "error": str(e),
                    "generation_time": None
                })
        
        return jsonify({
            "success": True,
            "test_prompt": test_prompt,
            "results": results,
            "total_models": len(models),
            "successful_models": len([r for r in results if r['success']])
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500