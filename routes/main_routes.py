from flask import Blueprint, render_template
from config import ASPECT_RATIOS, GEMINI_MODELS, IMAGEFX_MODELS, POLLINATIONS_MODELS, POLLINATIONS_TEXT_MODELS, IMAGE_PROVIDERS, TEXT_PROVIDERS

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html',
                         aspect_ratios=ASPECT_RATIOS,
                         gemini_models=GEMINI_MODELS,
                         imagefx_models=IMAGEFX_MODELS,
                         pollinations_models=POLLINATIONS_MODELS,
                         pollinations_text_models=POLLINATIONS_TEXT_MODELS,
                         image_providers=IMAGE_PROVIDERS,
                         text_providers=TEXT_PROVIDERS)

@main_bp.route('/settings')
def settings():
    return render_template('settings.html',
                         image_providers=IMAGE_PROVIDERS,
                         text_providers=TEXT_PROVIDERS,
                         pollinations_models=POLLINATIONS_MODELS,
                         pollinations_text_models=POLLINATIONS_TEXT_MODELS)

@main_bp.route('/file-manager')
def file_manager():
    return render_template('file_manager.html')

@main_bp.route('/video-generator')
def video_generator():
    return render_template('video_generator.html',
                         aspect_ratios=ASPECT_RATIOS,
                         gemini_models=GEMINI_MODELS,
                         imagefx_models=IMAGEFX_MODELS,
                         pollinations_models=POLLINATIONS_MODELS,
                         pollinations_text_models=POLLINATIONS_TEXT_MODELS,
                         image_providers=IMAGE_PROVIDERS,
                         text_providers=TEXT_PROVIDERS)

@main_bp.route('/prompt-templates')
def prompt_templates():
    return render_template('prompt_templates.html')

@main_bp.route('/tts-video-generator')
def tts_video_generator():
    return render_template('tts_video_generator.html',
                         aspect_ratios=ASPECT_RATIOS,
                         gemini_models=GEMINI_MODELS,
                         imagefx_models=IMAGEFX_MODELS,
                         pollinations_models=POLLINATIONS_MODELS,
                         pollinations_text_models=POLLINATIONS_TEXT_MODELS,
                         image_providers=IMAGE_PROVIDERS,
                         text_providers=TEXT_PROVIDERS)

@main_bp.route('/pollinations-test')
def pollinations_test():
    return render_template('pollinations_test.html',
                         pollinations_models=POLLINATIONS_MODELS,
                         pollinations_text_models=POLLINATIONS_TEXT_MODELS,
                         aspect_ratios=ASPECT_RATIOS)