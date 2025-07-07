// Video Generator JavaScript with Pollinations support and Text Provider Selection
class VideoGenerator {
    constructor() {
        this.sessionId = null;
        this.textFile = null;
        this.audioFile = null;
        this.textContent = '';
        this.audioDuration = 0;
        this.imageProviders = {};
        this.textProviders = {};
        
        this.initializeElements();
        this.setupEventListeners();
        this.loadProviders();
        this.loadPromptTemplates();
        this.loadVideoEffectsSettings();
    }
    
    initializeElements() {
        this.textUploadArea = document.getElementById('textUploadArea');
        this.audioUploadArea = document.getElementById('audioUploadArea');
        this.textFileInput = document.getElementById('textFile');
        this.audioFileInput = document.getElementById('audioFile');
        this.textFileInfo = document.getElementById('textFileInfo');
        this.audioFileInfo = document.getElementById('audioFileInfo');
        this.generateBtn = document.getElementById('generateVideoBtn');
        this.progressSection = document.getElementById('generationProgress');
        this.progressBar = document.querySelector('.progress-bar');
        this.progressText = document.getElementById('progressText');
        this.resultsSection = document.getElementById('resultsSection');
        this.resultsContent = document.getElementById('resultsContent');
        this.promptTemplate = document.getElementById('promptTemplate');
        
        // Text provider elements
        this.textProvider = document.getElementById('textProvider');
        this.textModel = document.getElementById('textModel');
        this.textProviderInfo = document.getElementById('textProviderInfo');
        this.textProviderInfoText = document.getElementById('textProviderInfoText');
        
        // Image provider elements
        this.imageProvider = document.getElementById('imageProvider');
        this.imageModel = document.getElementById('imageModel');
        this.imageProviderInfo = document.getElementById('imageProviderInfo');
        this.imageProviderInfoText = document.getElementById('imageProviderInfoText');
        
        // Video effects elements
        this.initializeVideoEffectsElements();
    }
    
    initializeVideoEffectsElements() {
        // Master toggle
        this.effectsEnabled = document.getElementById('effectsEnabled');
        this.motionEffectsEnabled = document.getElementById('motionEffectsEnabled');
        this.transitionEffectsEnabled = document.getElementById('transitionEffectsEnabled');
        
        this.zoomInProbability = document.getElementById('zoomInProbability');
        this.zoomOutProbability = document.getElementById('zoomOutProbability');
        this.panRightProbability = document.getElementById('panRightProbability');
        this.panLeftProbability = document.getElementById('panLeftProbability');
        this.panUpProbability = document.getElementById('panUpProbability');
        this.panDownProbability = document.getElementById('panDownProbability');
        this.noEffectProbability = document.getElementById('noEffectProbability');
        this.fadeProbability = document.getElementById('fadeProbability');
        this.fadeDuration = document.getElementById('fadeDuration');
        this.kenBurnsIntensity = document.getElementById('kenBurnsIntensity');
        
        // Value displays
        this.zoomInValue = document.getElementById('zoomInValue');
        this.zoomOutValue = document.getElementById('zoomOutValue');
        this.panRightValue = document.getElementById('panRightValue');
        this.panLeftValue = document.getElementById('panLeftValue');
        this.panUpValue = document.getElementById('panUpValue');
        this.panDownValue = document.getElementById('panDownValue');
        this.noEffectValue = document.getElementById('noEffectValue');
        this.fadeValue = document.getElementById('fadeValue');
        this.fadeDurationValue = document.getElementById('fadeDurationValue');
        this.kenBurnsValue = document.getElementById('kenBurnsValue');
        this.totalMotionProbability = document.getElementById('totalMotionProbability');
        this.totalFadeProbability = document.getElementById('totalFadeProbability');
        
        // Effect sections
        this.motionEffectsSection = document.getElementById('motionEffectsSection');
        this.transitionEffectsSection = document.getElementById('transitionEffectsSection');
    }
    
    setupEventListeners() {
        // Setup drag and drop for text file
        Utils.setupDragAndDrop(
            this.textUploadArea,
            this.textFileInput,
            ['txt'],
            (file) => this.handleTextFile(file)
        );
        
        // Setup drag and drop for audio file
        Utils.setupDragAndDrop(
            this.audioUploadArea,
            this.audioFileInput,
            ['mp3', 'wav', 'ogg', 'm4a', 'aac'],
            (file) => this.handleAudioFile(file)
        );
        
        // Provider changes
        this.textProvider.addEventListener('change', () => this.updateTextModels());
        this.imageProvider.addEventListener('change', () => this.updateImageModels());
        
        // Generate button
        this.generateBtn.addEventListener('click', () => this.generateVideo());
        
        // Video effects range inputs
        this.setupVideoEffectsListeners();
        
        // Reset effects button
        document.getElementById('resetEffects').addEventListener('click', () => this.resetVideoEffects());
    }
    
    async loadProviders() {
        try {
            // Load text providers
            const textData = await Utils.makeRequest('/api/text-providers');
            this.textProviders = textData.providers;
            this.updateTextModels();
            
            // Load image providers
            const imageData = await Utils.makeRequest('/api/image-providers');
            this.imageProviders = imageData.providers;
            this.updateImageModels();
        } catch (error) {
            console.error('Error loading providers:', error);
        }
    }
    
    updateTextModels() {
        const selectedProvider = this.textProvider.value;
        const provider = this.textProviders[selectedProvider];
        
        if (!provider) return;
        
        // Clear existing options
        this.textModel.innerHTML = '';
        
        // Add models for selected provider
        Object.entries(provider.models).forEach(([key, value]) => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = value;
            this.textModel.appendChild(option);
        });
        
        // Update provider info
        this.updateTextProviderInfo(provider, selectedProvider);
    }
    
    updateTextProviderInfo(provider, providerKey) {
        let infoText = '';
        let alertClass = 'alert-info';
        
        if (providerKey === 'gemini') {
            infoText = '🤖 Google Gemini: Advanced AI model, requires API key setup';
            alertClass = 'alert-warning';
        } else if (providerKey === 'pollinations') {
            infoText = '🌱 Pollinations Text: Multiple AI models, free to use, 3s rate limit';
            alertClass = 'alert-success';
        }
        
        this.textProviderInfo.className = `alert ${alertClass}`;
        this.textProviderInfoText.textContent = infoText;
    }
    
    updateImageModels() {
        const selectedProvider = this.imageProvider.value;
        const provider = this.imageProviders[selectedProvider];
        
        if (!provider) return;
        
        // Clear existing options
        this.imageModel.innerHTML = '';
        
        // Add models for selected provider
        Object.entries(provider.models).forEach(([key, value]) => {
            const option = document.createElement('option');
            option.value = key;
            option.textContent = value;
            this.imageModel.appendChild(option);
        });
        
        // Update provider info
        this.updateImageProviderInfo(provider, selectedProvider);
    }
    
    updateImageProviderInfo(provider, providerKey) {
        let infoText = '';
        let alertClass = 'alert-info';
        
        if (providerKey === 'imagefx') {
            infoText = '🔷 ImageFX: Excellent quality, requires auth token setup';
            alertClass = 'alert-warning';
        } else if (providerKey === 'pollinations') {
            infoText = '🌱 Pollinations: Very good quality, free to use, 5s delay for Turbo/Flux models';
            alertClass = 'alert-success';
        }
        
        this.imageProviderInfo.className = `alert ${alertClass}`;
        this.imageProviderInfoText.textContent = infoText;
    }
    
    setupVideoEffectsListeners() {
        // Master toggle listeners
        if (this.effectsEnabled) {
            this.effectsEnabled.addEventListener('change', () => this.toggleAllEffects());
        }
        if (this.motionEffectsEnabled) {
            this.motionEffectsEnabled.addEventListener('change', () => this.toggleMotionEffects());
        }
        if (this.transitionEffectsEnabled) {
            this.transitionEffectsEnabled.addEventListener('change', () => this.toggleTransitionEffects());
        }
        
        const effectInputs = [
            this.zoomInProbability, this.zoomOutProbability,
            this.panRightProbability, this.panLeftProbability,
            this.panUpProbability, this.panDownProbability,
            this.noEffectProbability, this.fadeProbability,
            this.fadeDuration, this.kenBurnsIntensity
        ];
        
        effectInputs.forEach(input => {
            if (input) {
                input.addEventListener('input', () => this.updateRangeValues());
            }
        });
    }
    
    toggleAllEffects() {
        const enabled = this.effectsEnabled.checked;
        
        // Enable/disable motion and transition toggles
        if (this.motionEffectsEnabled) {
            this.motionEffectsEnabled.disabled = !enabled;
            if (!enabled) this.motionEffectsEnabled.checked = false;
        }
        if (this.transitionEffectsEnabled) {
            this.transitionEffectsEnabled.disabled = !enabled;
            if (!enabled) this.transitionEffectsEnabled.checked = false;
        }
        
        // Toggle sections
        this.toggleMotionEffects();
        this.toggleTransitionEffects();
        
        // Update visual state
        const effectsContainer = document.querySelector('.video-effects-container');
        if (effectsContainer) {
            effectsContainer.style.opacity = enabled ? '1' : '0.5';
        }
    }
    
    toggleMotionEffects() {
        const enabled = this.effectsEnabled?.checked && this.motionEffectsEnabled?.checked;
        
        if (this.motionEffectsSection) {
            this.motionEffectsSection.style.opacity = enabled ? '1' : '0.5';
            
            // Disable/enable all motion effect inputs
            const motionInputs = this.motionEffectsSection.querySelectorAll('input[type="range"]');
            motionInputs.forEach(input => {
                input.disabled = !enabled;
            });
        }
    }
    
    toggleTransitionEffects() {
        const enabled = this.effectsEnabled?.checked && this.transitionEffectsEnabled?.checked;
        
        if (this.transitionEffectsSection) {
            this.transitionEffectsSection.style.opacity = enabled ? '1' : '0.5';
            
            // Disable/enable all transition effect inputs
            const transitionInputs = this.transitionEffectsSection.querySelectorAll('input[type="range"]');
            transitionInputs.forEach(input => {
                input.disabled = !enabled;
            });
        }
    }
    
    updateRangeValues() {
        this.zoomInValue.textContent = this.zoomInProbability.value + '%';
        this.zoomOutValue.textContent = this.zoomOutProbability.value + '%';
        this.panRightValue.textContent = this.panRightProbability.value + '%';
        this.panLeftValue.textContent = this.panLeftProbability.value + '%';
        this.panUpValue.textContent = this.panUpProbability.value + '%';
        this.panDownValue.textContent = this.panDownProbability.value + '%';
        this.noEffectValue.textContent = this.noEffectProbability.value + '%';
        this.fadeValue.textContent = this.fadeProbability.value + '%';
        this.fadeDurationValue.textContent = this.fadeDuration.value + 's';
        this.kenBurnsValue.textContent = this.kenBurnsIntensity.value;
        
        // Calculate total motion effects probability
        const totalMotion = parseInt(this.zoomInProbability.value) + 
                           parseInt(this.zoomOutProbability.value) + 
                           parseInt(this.panRightProbability.value) + 
                           parseInt(this.panLeftProbability.value) + 
                           parseInt(this.panUpProbability.value) + 
                           parseInt(this.panDownProbability.value) + 
                           parseInt(this.noEffectProbability.value);
        
        this.totalMotionProbability.textContent = totalMotion + '%';
        this.totalFadeProbability.textContent = this.fadeProbability.value + '%';
        
        // Update colors based on values
        this.totalMotionProbability.className = totalMotion === 100 ? 'text-success' : 'text-warning';
    }
    
    resetVideoEffects() {
        // Reset toggles
        if (this.effectsEnabled) this.effectsEnabled.checked = true;
        if (this.motionEffectsEnabled) this.motionEffectsEnabled.checked = true;
        if (this.transitionEffectsEnabled) this.transitionEffectsEnabled.checked = true;
        
        // Reset values
        this.zoomInProbability.value = 30;
        this.zoomOutProbability.value = 30;
        this.panRightProbability.value = 10;
        this.panLeftProbability.value = 10;
        this.panUpProbability.value = 10;
        this.panDownProbability.value = 10;
        this.noEffectProbability.value = 0;
        this.fadeProbability.value = 100;
        this.fadeDuration.value = 0.5;
        this.kenBurnsIntensity.value = 0.08;
        
        // Update toggles and values
        this.toggleAllEffects();
        this.updateRangeValues();
    }
    
    async loadPromptTemplates() {
        try {
            const data = await Utils.makeRequest('/api/prompt-templates');
            
            // Clear existing options except default
            this.promptTemplate.innerHTML = '<option value="">Default (No Template)</option>';
            
            // Add templates
            data.templates.forEach(template => {
                const option = document.createElement('option');
                option.value = template.id;
                option.textContent = template.name;
                option.title = template.description;
                this.promptTemplate.appendChild(option);
            });
            
        } catch (error) {
            console.error('Error loading templates:', error);
        }
    }
    
    async loadVideoEffectsSettings() {
        try {
            const data = await Utils.makeRequest('/api/settings');
            const effects = data.video_effects || {};
            
            // Load toggle states
            if (this.effectsEnabled) this.effectsEnabled.checked = effects.effects_enabled !== false;
            if (this.motionEffectsEnabled) this.motionEffectsEnabled.checked = effects.motion_effects_enabled !== false;
            if (this.transitionEffectsEnabled) this.transitionEffectsEnabled.checked = effects.transition_effects_enabled !== false;
            
            // Load effect values
            this.zoomInProbability.value = effects.zoom_in_probability || 30;
            this.zoomOutProbability.value = effects.zoom_out_probability || 30;
            this.panRightProbability.value = effects.pan_right_probability || 10;
            this.panLeftProbability.value = effects.pan_left_probability || 10;
            this.panUpProbability.value = effects.pan_up_probability || 10;
            this.panDownProbability.value = effects.pan_down_probability || 10;
            this.noEffectProbability.value = effects.no_effect_probability || 0;
            this.fadeProbability.value = effects.fade_probability || 100;
            this.fadeDuration.value = effects.fade_duration || 0.5;
            this.kenBurnsIntensity.value = effects.ken_burns_intensity || 0.08;
            
            // Apply toggles and update values
            this.toggleAllEffects();
            this.updateRangeValues();
            
        } catch (error) {
            console.error('Error loading video effects settings:', error);
        }
    }
    
    getVideoEffectsSettings() {
        return {
            effects_enabled: this.effectsEnabled?.checked !== false,
            motion_effects_enabled: this.motionEffectsEnabled?.checked !== false,
            transition_effects_enabled: this.transitionEffectsEnabled?.checked !== false,
            zoom_in_probability: parseInt(this.zoomInProbability.value),
            zoom_out_probability: parseInt(this.zoomOutProbability.value),
            pan_right_probability: parseInt(this.panRightProbability.value),
            pan_left_probability: parseInt(this.panLeftProbability.value),
            pan_up_probability: parseInt(this.panUpProbability.value),
            pan_down_probability: parseInt(this.panDownProbability.value),
            no_effect_probability: parseInt(this.noEffectProbability.value),
            fade_probability: parseInt(this.fadeProbability.value),
            fade_duration: parseFloat(this.fadeDuration.value),
            ken_burns_intensity: parseFloat(this.kenBurnsIntensity.value)
        };
    }
    
    handleTextFile(file) {
        this.textFile = file;
        this.textUploadArea.classList.add('has-file');
        
        // Read file content
        const reader = new FileReader();
        reader.onload = (e) => {
            this.textContent = e.target.result;
            this.updateTextFileInfo();
            this.checkReadyToGenerate();
        };
        reader.readAsText(file);
    }
    
    handleAudioFile(file) {
        this.audioFile = file;
        this.audioUploadArea.classList.add('has-file');
        
        // Create audio element to get duration
        const audio = new Audio();
        audio.onloadedmetadata = () => {
            this.audioDuration = audio.duration;
            this.updateAudioFileInfo();
            this.checkReadyToGenerate();
        };
        audio.src = URL.createObjectURL(file);
    }
    
    updateTextFileInfo() {
        const wordCount = this.textContent.split(/\s+/).length;
        const charCount = this.textContent.length;
        
        this.textFileInfo.innerHTML = `
            <div class="file-name">${this.textFile.name}</div>
            <div class="file-details">
                Size: ${Utils.formatFileSize(this.textFile.size)} | 
                Words: ${wordCount} | 
                Characters: ${charCount}
            </div>
        `;
        this.textFileInfo.style.display = 'block';
    }
    
    updateAudioFileInfo() {
        this.audioFileInfo.innerHTML = `
            <div class="file-name">${this.audioFile.name}</div>
            <div class="file-details">
                Size: ${Utils.formatFileSize(this.audioFile.size)} | 
                Duration: ${Utils.formatDuration(this.audioDuration)}
            </div>
        `;
        this.audioFileInfo.style.display = 'block';
    }
    
    checkReadyToGenerate() {
        if (this.textFile && this.audioFile && this.textContent && this.audioDuration > 0) {
            this.generateBtn.disabled = false;
        }
    }
    
    async generateVideo() {
        try {
            this.generateBtn.disabled = true;
            this.showProgress('Uploading files...', 10);
            
            // Upload files
            const formData = new FormData();
            formData.append('text_file', this.textFile);
            formData.append('audio_file', this.audioFile);
            
            const uploadResponse = await fetch('/video/upload-files', {
                method: 'POST',
                body: formData
            });
            
            const uploadData = await uploadResponse.json();
            
            if (!uploadData.success) {
                throw new Error(uploadData.error);
            }
            
            this.sessionId = uploadData.session_id;
            this.showProgress('Files uploaded successfully. Generating video...', 30);
            
            // Generate video with text and image providers
            const generateData = {
                session_id: this.sessionId,
                text_content: this.textContent,
                mode: document.getElementById('textMode').value,
                template_id: this.promptTemplate.value ? parseInt(this.promptTemplate.value) : null,
                
                // Text generation settings
                text_provider: this.textProvider.value,
                text_model: this.textModel.value,
                
                // Image generation settings
                image_provider: this.imageProvider.value,
                image_model: this.imageModel.value,
                
                aspect_ratio: document.getElementById('aspectRatio').value,
                video_effects: this.getVideoEffectsSettings()
            };
            
            this.showProgress('Processing text and generating images...', 50);
            
            const generateResponse = await Utils.makeRequest('/video/generate-video', {
                method: 'POST',
                body: JSON.stringify(generateData)
            });
            
            this.showProgress('Creating video with effects...', 80);
            
            // Show results
            this.showProgress('Video generation complete!', 100);
            this.showResults(generateResponse);
            
            // Trigger file manager refresh
            window.dispatchEvent(new CustomEvent('videoGenerated', { 
                detail: { sessionId: this.sessionId } 
            }));
            
        } catch (error) {
            Utils.showToast(error.message, 'error');
            this.hideProgress();
        } finally {
            this.generateBtn.disabled = false;
        }
    }
    
    showProgress(text, percentage) {
        this.progressSection.style.display = 'block';
        this.progressBar.style.width = percentage + '%';
        this.progressText.textContent = text;
    }
    
    hideProgress() {
        this.progressSection.style.display = 'none';
    }
    
    showResults(data) {
        this.hideProgress();
        
        // Create video URL with proper path - Fixed to use correct endpoint
        const videoUrl = `/video/download-video/${data.session_id}`;
        const effects = this.getVideoEffectsSettings();
        
        this.resultsContent.innerHTML = `
            <div class="row">
                <div class="col-md-8">
                    <div class="video-container">
                        <video controls preload="metadata" style="width: 100%; max-height: 70vh;" id="resultVideo">
                            <source src="${videoUrl}" type="video/mp4">
                            Your browser does not support the video tag.
                        </video>
                    </div>
                    <div class="mt-3 text-center">
                        <a href="${videoUrl}" class="btn btn-success btn-lg" download>
                            <i class="fas fa-download me-2"></i>Download Video
                        </a>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h6 class="mb-0">Generation Summary</h6>
                        </div>
                        <div class="card-body">
                            <p><strong>Images Generated:</strong> ${data.images_generated}</p>
                            <p><strong>Total Segments:</strong> ${data.total_segments}</p>
                            <p><strong>Text Provider:</strong> 
                                <span class="badge bg-primary">${this.textProvider.value}</span>
                            </p>
                            <p><strong>Text Model:</strong> 
                                <span class="badge bg-secondary">${this.textModel.value}</span>
                            </p>
                            <p><strong>Image Provider:</strong> 
                                <span class="badge bg-primary">${this.imageProvider.value}</span>
                            </p>
                            <p><strong>Image Model:</strong> 
                                <span class="badge bg-secondary">${this.imageModel.value}</span>
                            </p>
                            <p><strong>Session ID:</strong> ${data.session_id}</p>
                        </div>
                    </div>
                    
                    <div class="card mt-3">
                        <div class="card-header">
                            <h6 class="mb-0">Video Effects Used</h6>
                        </div>
                        <div class="card-body">
                            <p><strong>Effects Enabled:</strong> 
                                <span class="badge ${effects.effects_enabled ? 'bg-success' : 'bg-secondary'}">${effects.effects_enabled ? 'Yes' : 'No'}</span>
                            </p>
                            
                            ${effects.effects_enabled ? `
                                <h6 class="text-primary mt-3">Motion Effects:</h6>
                                <p><strong>Motion Enabled:</strong> 
                                    <span class="badge ${effects.motion_effects_enabled ? 'bg-success' : 'bg-secondary'}">${effects.motion_effects_enabled ? 'Yes' : 'No'}</span>
                                </p>
                                ${effects.motion_effects_enabled ? `
                                    <p><strong>Zoom In:</strong> ${effects.zoom_in_probability}%</p>
                                    <p><strong>Zoom Out:</strong> ${effects.zoom_out_probability}%</p>
                                    <p><strong>Pan Effects:</strong> ${effects.pan_right_probability + effects.pan_left_probability + effects.pan_up_probability + effects.pan_down_probability}%</p>
                                    <p><strong>No Effect:</strong> ${effects.no_effect_probability}%</p>
                                    <p><strong>Ken Burns Intensity:</strong> ${effects.ken_burns_intensity}</p>
                                ` : '<p class="text-muted">Motion effects disabled</p>'}
                                
                                <h6 class="text-warning mt-3">Transitions:</h6>
                                <p><strong>Transitions Enabled:</strong> 
                                    <span class="badge ${effects.transition_effects_enabled ? 'bg-success' : 'bg-secondary'}">${effects.transition_effects_enabled ? 'Yes' : 'No'}</span>
                                </p>
                                ${effects.transition_effects_enabled ? `
                                    <p><strong>Fade:</strong> ${effects.fade_probability}%</p>
                                    <p><strong>Duration:</strong> ${effects.fade_duration}s</p>
                                ` : '<p class="text-muted">Transition effects disabled</p>'}
                            ` : '<p class="text-muted">All video effects disabled</p>'}
                        </div>
                    </div>
                    
                    <div class="card mt-3">
                        <div class="card-header">
                            <h6 class="mb-0">Generation Log</h6>
                        </div>
                        <div class="card-body p-0">
                            <div class="generation-log">
                                ${this.renderGenerationLog(data.generation_log)}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        this.resultsSection.style.display = 'block';
        this.resultsSection.scrollIntoView({ behavior: 'smooth' });
        
        // Force video to load metadata after DOM is updated
        setTimeout(() => {
            const video = document.getElementById('resultVideo');
            if (video) {
                video.load();
                console.log('🎬 Video element configured with src:', video.src);
            }
        }, 100);
        
        Utils.showToast('Video generated successfully with multiple AI providers!');
    }
    
    renderGenerationLog(log) {
        return log.map(item => `
            <div class="log-item ${item.status}">
                <div class="log-index">Segment ${item.index}</div>
                <div class="log-text">${item.text_segment}</div>
                ${item.image_prompt ? `<div class="log-prompt">Prompt: ${item.image_prompt}</div>` : ''}
                ${item.provider_used ? `<div class="text-info">Provider: ${item.provider_used}</div>` : ''}
                ${item.error ? `<div class="text-danger">Error: ${item.error}</div>` : ''}
            </div>
        `).join('');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new VideoGenerator();
});