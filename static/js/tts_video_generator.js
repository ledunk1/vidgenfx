// TTS Video Generator JavaScript with Pollinations Text support - Fixed video player and download bug
class TTSVideoGenerator {
    constructor() {
        this.sessionId = null;
        this.textContent = '';
        this.textFile = null;
        this.imageProviders = {};
        this.textProviders = {};
        
        this.initializeElements();
        this.setupEventListeners();
        this.loadProviders();
        this.loadPromptTemplates();
        this.loadVideoEffectsSettings();
        this.loadTTSSettings();
    }
    
    initializeElements() {
        // Text file upload
        this.textUploadArea = document.getElementById('textUploadArea');
        this.textFileInput = document.getElementById('textFile');
        this.textFileInfo = document.getElementById('textFileInfo');
        this.textPreview = document.getElementById('textPreview');
        this.wordCount = document.getElementById('wordCount');
        this.charCount = document.getElementById('charCount');
        
        // TTS Settings
        this.ttsVoice = document.getElementById('ttsVoice');
        this.ttsVoiceStyle = document.getElementById('ttsVoiceStyle');
        this.ttsLanguage = document.getElementById('ttsLanguage');
        
        // Configuration
        this.textMode = document.getElementById('textMode');
        this.promptTemplate = document.getElementById('promptTemplate');
        this.aspectRatio = document.getElementById('aspectRatio');
        
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
        
        // Random images setting
        this.randomImagesPerParagraph = document.getElementById('randomImagesPerParagraph');
        
        // Video Effects
        this.initializeVideoEffectsElements();
        
        // Generation
        this.generateBtn = document.getElementById('generateTTSVideoBtn');
        this.progressSection = document.getElementById('generationProgress');
        this.progressBar = document.querySelector('.progress-bar');
        this.progressText = document.getElementById('progressText');
        this.resultsSection = document.getElementById('resultsSection');
        this.resultsContent = document.getElementById('resultsContent');
    }
    
    initializeVideoEffectsElements() {
        // Master toggle
        this.effectsEnabled = document.getElementById('effectsEnabled');
        this.motionEffectsEnabled = document.getElementById('motionEffectsEnabled');
        this.transitionEffectsEnabled = document.getElementById('transitionEffectsEnabled');
        
        // Motion effects
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
        
        // Provider changes
        if (this.textProvider) {
            this.textProvider.addEventListener('change', () => this.updateTextModels());
        }
        if (this.imageProvider) {
            this.imageProvider.addEventListener('change', () => this.updateImageModels());
        }
        
        // Video effects
        this.setupVideoEffectsListeners();
        
        // Generate button
        if (this.generateBtn) {
            this.generateBtn.addEventListener('click', () => this.generateTTSVideo());
        }
        
        // Reset effects
        const resetBtn = document.getElementById('resetEffects');
        if (resetBtn) {
            resetBtn.addEventListener('click', () => this.resetVideoEffects());
        }
        
        // Text mode change listener to show/hide random images option
        if (this.textMode) {
            this.textMode.addEventListener('change', () => this.updateRandomImagesVisibility());
        }
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
        if (!this.textProvider || !this.textModel) return;
        
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
        if (!this.textProviderInfo || !this.textProviderInfoText) return;
        
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
        if (!this.imageProvider || !this.imageModel) return;
        
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
        if (!this.imageProviderInfo || !this.imageProviderInfoText) return;
        
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
    
    updateRandomImagesVisibility() {
        if (!this.randomImagesPerParagraph || !this.textMode) return;
        
        const randomImagesContainer = this.randomImagesPerParagraph.closest('.col-md-3');
        if (randomImagesContainer) {
            if (this.textMode.value === 'paragraph') {
                randomImagesContainer.style.display = 'block';
            } else {
                randomImagesContainer.style.display = 'none';
                this.randomImagesPerParagraph.value = '1'; // Reset to default for sentence mode
            }
        }
    }
    
    handleTextFile(file) {
        this.textFile = file;
        this.textUploadArea.classList.add('has-file');
        
        // Upload file and get content
        this.uploadTextFile(file);
    }
    
    async uploadTextFile(file) {
        try {
            const formData = new FormData();
            formData.append('text_file', file);
            
            const response = await fetch('/tts-video/upload-text-file', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.sessionId = data.session_id;
                this.textContent = data.text_content;
                
                // Update file info
                this.updateTextFileInfo(data);
                
                // Update text stats and preview
                this.updateTextStats(data.word_count, data.char_count);
                
                // Enable generate button
                if (this.generateBtn) {
                    this.generateBtn.disabled = false;
                }
                
                // Update random images visibility
                this.updateRandomImagesVisibility();
                
                Utils.showToast('Text file uploaded successfully!');
            } else {
                throw new Error(data.error);
            }
            
        } catch (error) {
            Utils.showToast(error.message, 'error');
            this.textUploadArea.classList.remove('has-file');
            if (this.generateBtn) {
                this.generateBtn.disabled = true;
            }
        }
    }
    
    updateTextFileInfo(data) {
        if (!this.textFileInfo) return;
        
        this.textFileInfo.innerHTML = `
            <div class="file-name">${data.text_filename}</div>
            <div class="file-details">
                Words: ${data.word_count} | 
                Characters: ${data.char_count}
            </div>
        `;
        this.textFileInfo.style.display = 'block';
    }
    
    updateTextStats(wordCount, charCount) {
        if (this.wordCount) this.wordCount.textContent = wordCount;
        if (this.charCount) this.charCount.textContent = charCount;
        
        // Update preview
        if (this.textPreview) {
            if (this.textContent.trim()) {
                this.textPreview.textContent = this.textContent.substring(0, 200) + 
                    (this.textContent.length > 200 ? '...' : '');
            } else {
                this.textPreview.textContent = 'Upload text file to see preview...';
            }
        }
    }
    
    updateRangeValues() {
        // Update display values
        if (this.zoomInValue) this.zoomInValue.textContent = this.zoomInProbability.value + '%';
        if (this.zoomOutValue) this.zoomOutValue.textContent = this.zoomOutProbability.value + '%';
        if (this.panRightValue) this.panRightValue.textContent = this.panRightProbability.value + '%';
        if (this.panLeftValue) this.panLeftValue.textContent = this.panLeftProbability.value + '%';
        if (this.panUpValue) this.panUpValue.textContent = this.panUpProbability.value + '%';
        if (this.panDownValue) this.panDownValue.textContent = this.panDownProbability.value + '%';
        if (this.noEffectValue) this.noEffectValue.textContent = this.noEffectProbability.value + '%';
        if (this.fadeValue) this.fadeValue.textContent = this.fadeProbability.value + '%';
        if (this.fadeDurationValue) this.fadeDurationValue.textContent = this.fadeDuration.value + 's';
        if (this.kenBurnsValue) this.kenBurnsValue.textContent = this.kenBurnsIntensity.value;
        
        // Calculate total motion effects
        const totalMotion = parseInt(this.zoomInProbability.value) + 
                           parseInt(this.zoomOutProbability.value) + 
                           parseInt(this.panRightProbability.value) + 
                           parseInt(this.panLeftProbability.value) + 
                           parseInt(this.panUpProbability.value) + 
                           parseInt(this.panDownProbability.value) + 
                           parseInt(this.noEffectProbability.value);
        
        if (this.totalMotionProbability) {
            this.totalMotionProbability.textContent = totalMotion + '%';
            this.totalMotionProbability.className = totalMotion === 100 ? 'text-success' : 'text-warning';
        }
        
        if (this.totalFadeProbability) {
            this.totalFadeProbability.textContent = this.fadeProbability.value + '%';
        }
    }
    
    resetVideoEffects() {
        // Reset toggles
        if (this.effectsEnabled) this.effectsEnabled.checked = true;
        if (this.motionEffectsEnabled) this.motionEffectsEnabled.checked = true;
        if (this.transitionEffectsEnabled) this.transitionEffectsEnabled.checked = true;
        
        // Reset values
        if (this.zoomInProbability) this.zoomInProbability.value = 30;
        if (this.zoomOutProbability) this.zoomOutProbability.value = 30;
        if (this.panRightProbability) this.panRightProbability.value = 10;
        if (this.panLeftProbability) this.panLeftProbability.value = 10;
        if (this.panUpProbability) this.panUpProbability.value = 10;
        if (this.panDownProbability) this.panDownProbability.value = 10;
        if (this.noEffectProbability) this.noEffectProbability.value = 0;
        if (this.fadeProbability) this.fadeProbability.value = 100;
        if (this.fadeDuration) this.fadeDuration.value = 0.5;
        if (this.kenBurnsIntensity) this.kenBurnsIntensity.value = 0.08;
        
        // Update toggles and values
        this.toggleAllEffects();
        this.updateRangeValues();
    }
    
    async loadPromptTemplates() {
        try {
            const data = await Utils.makeRequest('/api/prompt-templates');
            
            if (this.promptTemplate) {
                this.promptTemplate.innerHTML = '<option value="">Default (No Template)</option>';
                
                data.templates.forEach(template => {
                    const option = document.createElement('option');
                    option.value = template.id;
                    option.textContent = template.name;
                    option.title = template.description;
                    this.promptTemplate.appendChild(option);
                });
            }
            
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
            if (this.zoomInProbability) this.zoomInProbability.value = effects.zoom_in_probability || 30;
            if (this.zoomOutProbability) this.zoomOutProbability.value = effects.zoom_out_probability || 30;
            if (this.panRightProbability) this.panRightProbability.value = effects.pan_right_probability || 10;
            if (this.panLeftProbability) this.panLeftProbability.value = effects.pan_left_probability || 10;
            if (this.panUpProbability) this.panUpProbability.value = effects.pan_up_probability || 10;
            if (this.panDownProbability) this.panDownProbability.value = effects.pan_down_probability || 10;
            if (this.noEffectProbability) this.noEffectProbability.value = effects.no_effect_probability || 0;
            if (this.fadeProbability) this.fadeProbability.value = effects.fade_probability || 100;
            if (this.fadeDuration) this.fadeDuration.value = effects.fade_duration || 0.5;
            if (this.kenBurnsIntensity) this.kenBurnsIntensity.value = effects.ken_burns_intensity || 0.08;
            
            // Apply toggles and update values
            this.toggleAllEffects();
            this.updateRangeValues();
            
        } catch (error) {
            console.error('Error loading video effects settings:', error);
        }
    }
    
    loadTTSSettings() {
        // Set default TTS settings
        if (this.ttsVoice) this.ttsVoice.value = 'nova';
        if (this.ttsVoiceStyle) this.ttsVoiceStyle.value = 'friendly';
        if (this.ttsLanguage) this.ttsLanguage.value = 'id-ID';
        
        // Initialize random images visibility
        this.updateRandomImagesVisibility();
    }
    
    getVideoEffectsSettings() {
        return {
            effects_enabled: this.effectsEnabled?.checked !== false,
            motion_effects_enabled: this.motionEffectsEnabled?.checked !== false,
            transition_effects_enabled: this.transitionEffectsEnabled?.checked !== false,
            zoom_in_probability: parseInt(this.zoomInProbability?.value || 30),
            zoom_out_probability: parseInt(this.zoomOutProbability?.value || 30),
            pan_right_probability: parseInt(this.panRightProbability?.value || 10),
            pan_left_probability: parseInt(this.panLeftProbability?.value || 10),
            pan_up_probability: parseInt(this.panUpProbability?.value || 10),
            pan_down_probability: parseInt(this.panDownProbability?.value || 10),
            no_effect_probability: parseInt(this.noEffectProbability?.value || 0),
            fade_probability: parseInt(this.fadeProbability?.value || 100),
            fade_duration: parseFloat(this.fadeDuration?.value || 0.5),
            ken_burns_intensity: parseFloat(this.kenBurnsIntensity?.value || 0.08)
        };
    }
    
    async generateTTSVideo() {
        try {
            if (!this.sessionId || !this.textContent.trim()) {
                Utils.showToast('Please upload a text file first', 'error');
                return;
            }
            
            if (this.generateBtn) {
                this.generateBtn.disabled = true;
            }
            this.showProgress('Initializing TTS video generation...', 5);
            
            const generateData = {
                session_id: this.sessionId,
                text_content: this.textContent,
                mode: this.textMode?.value || 'paragraph',
                template_id: this.promptTemplate?.value ? parseInt(this.promptTemplate.value) : null,
                
                // Text generation settings
                text_provider: this.textProvider?.value || 'gemini',
                text_model: this.textModel?.value || 'gemini-2.0-flash',
                
                // Image generation settings
                image_provider: this.imageProvider?.value || 'imagefx',
                image_model: this.imageModel?.value || 'IMAGEN_3_5',
                aspect_ratio: this.aspectRatio?.value || 'IMAGE_ASPECT_RATIO_LANDSCAPE',
                video_effects: this.getVideoEffectsSettings(),
                
                // TTS Settings
                tts_voice: this.ttsVoice?.value || 'nova',
                tts_voice_style: this.ttsVoiceStyle?.value || 'friendly',
                tts_language: this.ttsLanguage?.value || 'id-ID',
                random_images_per_paragraph: parseInt(this.randomImagesPerParagraph?.value || 1)
            };
            
            this.showProgress('Processing text and generating TTS audio...', 20);
            
            const response = await Utils.makeRequest('/tts-video/generate-tts-video', {
                method: 'POST',
                body: JSON.stringify(generateData)
            });
            
            this.showProgress('Generating multiple AI images per segment...', 50);
            
            // Simulate progress updates
            await this.simulateProgress(50, 80, 'Creating video with multiple images and effects...');
            
            this.showProgress('Finalizing TTS video...', 90);
            
            await new Promise(resolve => setTimeout(resolve, 1000));
            
            this.showProgress('TTS video generation complete!', 100);
            this.showResults(response);
            
            // Trigger file manager refresh
            window.dispatchEvent(new CustomEvent('ttsVideoGenerated', { 
                detail: { sessionId: this.sessionId } 
            }));
            
        } catch (error) {
            Utils.showToast(error.message, 'error');
            this.hideProgress();
        } finally {
            if (this.generateBtn) {
                this.generateBtn.disabled = false;
            }
        }
    }
    
    async simulateProgress(start, end, message) {
        const steps = 5;
        const increment = (end - start) / steps;
        
        for (let i = 0; i < steps; i++) {
            await new Promise(resolve => setTimeout(resolve, 500));
            const progress = start + (increment * (i + 1));
            this.showProgress(message, progress);
        }
    }
    
    showProgress(text, percentage) {
        if (this.progressSection) {
            this.progressSection.style.display = 'block';
        }
        if (this.progressBar) {
            this.progressBar.style.width = percentage + '%';
        }
        if (this.progressText) {
            this.progressText.textContent = text;
        }
    }
    
    hideProgress() {
        if (this.progressSection) {
            this.progressSection.style.display = 'none';
        }
    }
    
    showResults(data) {
        this.hideProgress();
        
        // Create video URL with timestamp to force reload and proper path - Fixed to use correct endpoint
        const timestamp = new Date().getTime();
        const videoUrl = `/tts-video/download-tts-video/${data.session_id}?t=${timestamp}&cache_bust=${Math.random()}`;
        const assetsUrl = `/tts-video/download-tts-assets/${data.session_id}`;
        const effects = this.getVideoEffectsSettings();
        
        if (this.resultsContent) {
            this.resultsContent.innerHTML = `
                <div class="row">
                    <div class="col-md-8">
                        <div class="video-container">
                            <video controls preload="metadata" style="width: 100%; max-height: 70vh;" id="resultVideo" crossorigin="anonymous">
                                <source src="${videoUrl}" type="video/mp4">
                                Your browser does not support the video tag.
                            </video>
                        </div>
                        <div class="mt-3 text-center">
                            <a href="${videoUrl}" class="btn btn-success btn-lg me-2" download>
                                <i class="fas fa-download me-2"></i>Download Video
                            </a>
                            <a href="${assetsUrl}" class="btn btn-info btn-lg" download>
                                <i class="fas fa-archive me-2"></i>Download Assets
                            </a>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <div class="card">
                            <div class="card-header">
                                <h6 class="mb-0">
                                    <i class="fas fa-chart-bar me-2"></i>Generation Summary
                                </h6>
                            </div>
                            <div class="card-body">
                                <p><strong>Segments Processed:</strong> ${data.segments_processed}</p>
                                <p><strong>Total Segments:</strong> ${data.total_segments}</p>
                                <p><strong>Total Images Generated:</strong> 
                                    <span class="badge bg-primary">${data.total_images_generated || 'N/A'}</span>
                                </p>
                                <p><strong>Total Images in Video:</strong> 
                                    <span class="badge bg-success">${data.total_images_in_video || 'N/A'}</span>
                                </p>
                                <p><strong>Segments with Fallback:</strong> 
                                    <span class="badge ${data.segments_with_fallback > 0 ? 'bg-warning' : 'bg-success'}">${data.segments_with_fallback || 0}</span>
                                </p>
                                <p><strong>Mode Used:</strong> 
                                    <span class="badge bg-info">${data.mode_used || 'paragraph'}</span>
                                </p>
                                <p><strong>Random Images per Paragraph:</strong> 
                                    <span class="badge bg-secondary">${data.random_images_per_paragraph}</span>
                                </p>
                                <p><strong>Text Provider:</strong> 
                                    <span class="badge bg-primary">${data.text_provider_used || 'gemini'}</span>
                                </p>
                                <p><strong>Text Model:</strong> 
                                    <span class="badge bg-secondary">${data.text_model_used || 'default'}</span>
                                </p>
                                <p><strong>Image Provider:</strong> 
                                    <span class="badge bg-primary">${data.image_provider_used || 'imagefx'}</span>
                                </p>
                                <p><strong>Image Model:</strong> 
                                    <span class="badge bg-secondary">${data.image_model_used || 'default'}</span>
                                </p>
                                <p><strong>Session ID:</strong> <small>${data.session_id}</small></p>
                            </div>
                        </div>
                        
                        <div class="card mt-3">
                            <div class="card-header">
                                <h6 class="mb-0">
                                    <i class="fas fa-microphone me-2"></i>TTS Settings Used
                                </h6>
                            </div>
                            <div class="card-body">
                                <p><strong>Voice:</strong> ${data.tts_settings?.voice || 'nova'}</p>
                                <p><strong>Style:</strong> ${data.tts_settings?.voice_style || 'friendly'}</p>
                                <p><strong>Language:</strong> ${data.tts_settings?.language || 'id-ID'}</p>
                            </div>
                        </div>
                        
                        <div class="card mt-3">
                            <div class="card-header">
                                <h6 class="mb-0">
                                    <i class="fas fa-magic me-2"></i>Video Effects Used
                                </h6>
                            </div>
                            <div class="card-body">
                                <p><strong>Effects Enabled:</strong> 
                                    <span class="badge ${effects.effects_enabled ? 'bg-success' : 'bg-secondary'}">${effects.effects_enabled ? 'Yes' : 'No'}</span>
                                </p>
                                
                                ${effects.effects_enabled ? `
                                    <h6 class="text-primary">Motion Effects:</h6>
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
                                <h6 class="mb-0">
                                    <i class="fas fa-list me-2"></i>Generation Log
                                </h6>
                            </div>
                            <div class="card-body p-0">
                                <div class="generation-log">
                                    ${this.renderGenerationLog(data.generation_log || [])}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        if (this.resultsSection) {
            this.resultsSection.style.display = 'block';
            this.resultsSection.scrollIntoView({ behavior: 'smooth' });
        }
        
        // Force video to load metadata after DOM is updated with enhanced error handling
        setTimeout(() => {
            const video = document.getElementById('resultVideo');
            if (video) {
                // Add comprehensive event listeners
                video.addEventListener('loadstart', function() {
                    console.log('Video load started');
                });
                
                video.addEventListener('loadeddata', function() {
                    console.log('Video data loaded');
                });
                
                video.addEventListener('loadedmetadata', function() {
                    console.log('Video metadata loaded, duration:', video.duration);
                    if (video.duration && video.duration > 0) {
                        console.log('✅ Video duration properly loaded:', video.duration, 'seconds');
                    }
                });
                
                video.addEventListener('canplay', function() {
                    console.log('Video can start playing');
                });
                
                video.addEventListener('canplaythrough', function() {
                    console.log('Video can play through without buffering');
                });
                
                video.addEventListener('error', function(e) {
                    console.error('Video error:', e);
                    console.error('Video error details:', video.error);
                    Utils.showToast('Error loading video. Please try downloading it directly.', 'error');
                });
                
                video.addEventListener('stalled', function() {
                    console.warn('Video loading stalled');
                });
                
                video.addEventListener('suspend', function() {
                    console.warn('Video loading suspended');
                });
                
                // Force reload the video with cache busting
                const originalSrc = video.src;
                video.src = '';
                video.load();
                video.src = originalSrc;
                video.load();
                
                console.log('🎬 Video element configured with src:', video.src);
            }
        }, 100);
        
        Utils.showToast('TTS video generated successfully with multiple AI providers!');
    }
    
    renderGenerationLog(log) {
        if (!log || log.length === 0) {
            return '<div class="text-muted p-3">No generation log available</div>';
        }
        
        return log.map(item => `
            <div class="log-item ${item.status}">
                <div class="log-index">Segment ${item.index}</div>
                <div class="log-text">${item.text_segment}</div>
                ${item.image_prompts && item.image_prompts.length > 0 ? `<div class="log-prompt">Prompts: ${item.image_prompts.slice(0, 2).join(', ')}${item.image_prompts.length > 2 ? '...' : ''}</div>` : ''}
                ${item.audio_generated ? `<div class="text-success">✅ TTS Audio Generated</div>` : ''}
                ${item.image_generated ? `<div class="text-success">✅ AI Images Generated</div>` : ''}
                ${item.images_count && item.images_count > 1 ? `<div class="text-info">🎲 ${item.images_count} images generated and used in video</div>` : ''}
                ${item.text_provider_used ? `<div class="text-info">🤖 Text: ${item.text_provider_used}/${item.text_model_used || 'default'}</div>` : ''}
                ${item.image_provider_used ? `<div class="text-info">🎨 Image: ${item.image_provider_used}/${item.image_model_used || 'default'}</div>` : ''}
                ${item.fallback_used ? `<div class="text-warning">🔄 Used fallback images from another segment</div>` : ''}
                ${item.fallback_attempted && !item.fallback_used ? `<div class="text-warning">⚠️ Fallback attempted but failed</div>` : ''}
                ${item.error ? `<div class="text-danger">❌ Error: ${item.error}</div>` : ''}
            </div>
        `).join('');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    new TTSVideoGenerator();
});