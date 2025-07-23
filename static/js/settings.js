// Settings JavaScript
class Settings {
    constructor() {
        this.initializeElements();
        this.setupEventListeners();
        this.loadSettings();
    }
    
    initializeElements() {
        this.form = document.getElementById('settingsForm');
        this.geminiApiKey = document.getElementById('geminiApiKey');
        this.imagefxAuthToken = document.getElementById('imagefxAuthToken');
        this.defaultGeminiModel = document.getElementById('defaultGeminiModel');
        this.defaultImagefxModel = document.getElementById('defaultImagefxModel');
        this.defaultAspectRatio = document.getElementById('defaultAspectRatio');
    }
    
    setupEventListeners() {
        this.form.addEventListener('submit', (e) => this.saveSettings(e));
    }
    
    async loadSettings() {
        try {
            const data = await Utils.makeRequest('/api/settings');
            
            // Don't overwrite password fields if they show masked values
            if (data.gemini_api_key && data.gemini_api_key !== '********') {
                this.geminiApiKey.value = data.gemini_api_key;
            }
            
            if (data.imagefx_auth_token && data.imagefx_auth_token !== '********') {
                this.imagefxAuthToken.value = data.imagefx_auth_token;
            }
            
            if (data.default_gemini_model) {
                this.defaultGeminiModel.value = data.default_gemini_model;
            }
            
            if (data.default_imagefx_model) {
                this.defaultImagefxModel.value = data.default_imagefx_model;
            }
            
            if (data.default_aspect_ratio) {
                this.defaultAspectRatio.value = data.default_aspect_ratio;
            }
            
        } catch (error) {
            Utils.showToast('Error loading settings: ' + error.message, 'error');
        }
    }
    
    async saveSettings(e) {
        e.preventDefault();
        
        try {
            const settings = {
                gemini_api_key: this.geminiApiKey.value,
                imagefx_auth_token: this.imagefxAuthToken.value,
                default_gemini_model: this.defaultGeminiModel.value,
                default_imagefx_model: this.defaultImagefxModel.value,
                default_aspect_ratio: this.defaultAspectRatio.value
            };
            
            await Utils.makeRequest('/api/settings', {
                method: 'POST',
                body: JSON.stringify(settings)
            });
            
            Utils.showToast('Settings saved successfully!');
            
        } catch (error) {
            Utils.showToast('Error saving settings: ' + error.message, 'error');
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new Settings();
});