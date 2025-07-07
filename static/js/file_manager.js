// File Manager JavaScript - Enhanced version with upload cleanup and fixed video preview
class FileManager {
    constructor() {
        this.currentFileType = 'images';
        this.refreshInterval = null;
        this.initializeElements();
        this.setupEventListeners();
        this.loadFiles();
        this.loadStorageInfo();
        this.startAutoRefresh();
    }
    
    initializeElements() {
        this.imagesTab = document.getElementById('imagesTab');
        this.videosTab = document.getElementById('videosTab');
        this.uploadsTab = document.getElementById('uploadsTab');
        this.deleteAllBtn = document.getElementById('deleteAllBtn');
        this.cleanupAllBtn = document.getElementById('cleanupAllBtn');
        this.refreshBtn = document.getElementById('refreshBtn');
        this.filesList = document.getElementById('filesList');
        this.storageInfo = document.getElementById('storageInfo');
    }
    
    setupEventListeners() {
        // Tab switching
        if (this.imagesTab) {
            this.imagesTab.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab('images');
            });
        }
        
        if (this.videosTab) {
            this.videosTab.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab('videos');
            });
        }
        
        if (this.uploadsTab) {
            this.uploadsTab.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchTab('uploads');
            });
        }
        
        // Refresh button
        if (this.refreshBtn) {
            this.refreshBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.loadFiles();
                this.loadStorageInfo();
            });
        }
        
        // Delete all button
        if (this.deleteAllBtn) {
            this.deleteAllBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.deleteAll();
            });
        }
        
        // Cleanup all button
        if (this.cleanupAllBtn) {
            this.cleanupAllBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.cleanupAll();
            });
        }
        
        // Listen for generation completion events
        window.addEventListener('videoGenerated', () => {
            console.log('Video generation completed, refreshing file manager');
            setTimeout(() => {
                this.loadFiles();
                this.loadStorageInfo();
            }, 1000);
        });
        
        window.addEventListener('ttsVideoGenerated', () => {
            console.log('TTS video generation completed, refreshing file manager');
            setTimeout(() => {
                this.loadFiles();
                this.loadStorageInfo();
            }, 1000);
        });
    }
    
    startAutoRefresh() {
        // Auto refresh every 30 seconds
        this.refreshInterval = setInterval(() => {
            this.loadFiles();
            this.loadStorageInfo();
        }, 30000);
    }
    
    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }
    
    switchTab(fileType) {
        this.currentFileType = fileType;
        
        // Update tab appearance
        document.querySelectorAll('.btn-group .btn').forEach(btn => {
            btn.classList.remove('active');
        });
        
        if (fileType === 'images') {
            this.imagesTab.classList.add('active');
        } else if (fileType === 'videos') {
            this.videosTab.classList.add('active');
        } else if (fileType === 'uploads') {
            this.uploadsTab.classList.add('active');
        }
        
        this.loadFiles();
    }
    
    async loadFiles() {
        try {
            this.showLoading();
            
            const data = await Utils.makeRequest(`/files/list/${this.currentFileType}`);
            this.renderFiles(data.sessions);
            
        } catch (error) {
            console.error('Error loading files:', error);
            Utils.showToast(error.message, 'error');
            this.filesList.innerHTML = '<div class="alert alert-danger">Error loading files</div>';
        }
    }
    
    async loadStorageInfo() {
        try {
            const data = await Utils.makeRequest('/files/storage-info');
            this.renderStorageInfo(data.storage_info);
        } catch (error) {
            console.error('Error loading storage info:', error);
        }
    }
    
    renderStorageInfo(storageInfo) {
        if (!this.storageInfo) return;
        
        this.storageInfo.innerHTML = `
            <div class="row">
                <div class="col-md-2">
                    <div class="text-center">
                        <div class="h5 text-primary">${storageInfo.uploads.count}</div>
                        <div class="small text-muted">Uploads</div>
                        <div class="small">${storageInfo.uploads.size_formatted}</div>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="text-center">
                        <div class="h5 text-success">${storageInfo.images.count}</div>
                        <div class="small text-muted">Images</div>
                        <div class="small">${storageInfo.images.size_formatted}</div>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="text-center">
                        <div class="h5 text-info">${storageInfo.videos.count}</div>
                        <div class="small text-muted">Videos</div>
                        <div class="small">${storageInfo.videos.size_formatted}</div>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="text-center">
                        <div class="h5 text-warning">${storageInfo.audio.count}</div>
                        <div class="small text-muted">Audio</div>
                        <div class="small">${storageInfo.audio.size_formatted}</div>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="text-center">
                        <div class="h5 text-secondary">${storageInfo.temp.count}</div>
                        <div class="small text-muted">Temp</div>
                        <div class="small">${storageInfo.temp.size_formatted}</div>
                    </div>
                </div>
                <div class="col-md-2">
                    <div class="text-center">
                        <div class="h4 text-dark">${storageInfo.total.count}</div>
                        <div class="small text-muted"><strong>Total Files</strong></div>
                        <div class="small"><strong>${storageInfo.total.size_formatted}</strong></div>
                    </div>
                </div>
            </div>
        `;
    }
    
    showLoading() {
        this.filesList.innerHTML = `
            <div class="text-center py-5">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading files...</p>
            </div>
        `;
    }
    
    renderFiles(sessions) {
        if (sessions.length === 0) {
            this.filesList.innerHTML = `
                <div class="alert alert-info text-center">
                    <i class="fas fa-folder-open fa-3x mb-3"></i>
                    <h5>No ${this.currentFileType} found</h5>
                    <p>Generate some content to see files here.</p>
                </div>
            `;
            return;
        }
        
        this.filesList.innerHTML = sessions.map(session => this.renderSession(session)).join('');
        
        // Re-attach event listeners after rendering
        this.attachFileEventListeners();
    }
    
    attachFileEventListeners() {
        // Attach event listeners to dynamically created buttons
        document.querySelectorAll('[data-action="download-session"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const sessionId = btn.getAttribute('data-session-id');
                this.downloadSession(sessionId);
            });
        });
        
        document.querySelectorAll('[data-action="delete-session"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const sessionId = btn.getAttribute('data-session-id');
                this.deleteSession(sessionId);
            });
        });
        
        document.querySelectorAll('[data-action="download-file"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const sessionId = btn.getAttribute('data-session-id');
                const filename = btn.getAttribute('data-filename');
                this.downloadFile(sessionId, filename);
            });
        });
        
        document.querySelectorAll('[data-action="delete-file"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const sessionId = btn.getAttribute('data-session-id');
                const filename = btn.getAttribute('data-filename');
                this.deleteFile(sessionId, filename);
            });
        });
        
        document.querySelectorAll('[data-action="preview-video"]').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const sessionId = btn.getAttribute('data-session-id');
                const filename = btn.getAttribute('data-filename');
                this.previewVideo(sessionId, filename);
            });
        });
    }
    
    renderSession(session) {
        return `
            <div class="card session-card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h6 class="mb-0">
                        <i class="fas fa-folder me-2"></i>Session: ${session.session_id}
                    </h6>
                    <div>
                        <span class="badge bg-primary me-2">${session.file_count} files</span>
                        <span class="badge bg-secondary me-2">${session.total_size_formatted}</span>
                        <div class="btn-group btn-group-sm">
                            <button class="btn btn-outline-success" 
                                    data-action="download-session" 
                                    data-session-id="${session.session_id}"
                                    title="Download all files as ZIP">
                                <i class="fas fa-download"></i>
                            </button>
                            <button class="btn btn-outline-danger" 
                                    data-action="delete-session" 
                                    data-session-id="${session.session_id}"
                                    title="Delete entire session">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="card-body">
                    ${session.files.map(file => this.renderFile(file, session.session_id)).join('')}
                </div>
            </div>
        `;
    }
    
    renderFile(file, sessionId) {
        const isVideo = file.name.endsWith('.mp4');
        const isImage = file.name.match(/\.(jpg|jpeg|png|gif)$/i);
        const isAudio = file.name.match(/\.(mp3|wav|ogg|m4a|aac)$/i);
        const isText = file.name.endsWith('.txt');
        
        let icon = 'fas fa-file';
        if (isVideo) icon = 'fas fa-video';
        if (isImage) icon = 'fas fa-image';
        if (isAudio) icon = 'fas fa-music';
        if (isText) icon = 'fas fa-file-text';
        
        return `
            <div class="file-item">
                <div class="file-icon">
                    <i class="${icon} fa-2x text-primary"></i>
                </div>
                <div class="file-details">
                    <div class="file-name">${file.name}</div>
                    <div class="file-meta">
                        Size: ${Utils.formatFileSize(file.size)} | 
                        Modified: ${file.modified}
                    </div>
                </div>
                <div class="file-actions">
                    ${isVideo ? `
                        <button class="btn btn-sm btn-outline-primary" 
                                data-action="preview-video" 
                                data-session-id="${sessionId}" 
                                data-filename="${file.name}"
                                title="Preview video">
                            <i class="fas fa-play"></i>
                        </button>
                    ` : ''}
                    <button class="btn btn-sm btn-outline-success" 
                            data-action="download-file" 
                            data-session-id="${sessionId}" 
                            data-filename="${file.name}"
                            title="Download file">
                        <i class="fas fa-download"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" 
                            data-action="delete-file" 
                            data-session-id="${sessionId}" 
                            data-filename="${file.name}"
                            title="Delete file">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            </div>
        `;
    }
    
    async downloadSession(sessionId) {
        try {
            const url = `/files/download-zip/${this.currentFileType}/${sessionId}`;
            
            // Create a temporary link to trigger download
            const link = document.createElement('a');
            link.href = url;
            link.download = `${this.currentFileType}_${sessionId}.zip`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            Utils.showToast('Download started');
        } catch (error) {
            console.error('Error downloading session:', error);
            Utils.showToast(error.message, 'error');
        }
    }
    
    async downloadFile(sessionId, filename) {
        try {
            const url = `/files/download-file/${this.currentFileType}/${sessionId}/${encodeURIComponent(filename)}`;
            
            // Create a temporary link to trigger download
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            Utils.showToast('Download started');
        } catch (error) {
            console.error('Error downloading file:', error);
            Utils.showToast(error.message, 'error');
        }
    }
    
    async deleteFile(sessionId, filename) {
        if (!confirm(`Are you sure you want to delete ${filename}?`)) {
            return;
        }
        
        try {
            await Utils.makeRequest('/files/delete', {
                method: 'POST',
                body: JSON.stringify({
                    file_type: this.currentFileType,
                    session_id: sessionId,
                    filename: filename
                })
            });
            
            Utils.showToast('File deleted successfully');
            this.loadFiles(); // Refresh the list
            this.loadStorageInfo(); // Refresh storage info
        } catch (error) {
            console.error('Error deleting file:', error);
            Utils.showToast(error.message, 'error');
        }
    }
    
    async deleteSession(sessionId) {
        if (!confirm(`Are you sure you want to delete the entire session ${sessionId}?`)) {
            return;
        }
        
        try {
            await Utils.makeRequest('/files/delete', {
                method: 'POST',
                body: JSON.stringify({
                    file_type: this.currentFileType,
                    session_id: sessionId
                })
            });
            
            Utils.showToast('Session deleted successfully');
            this.loadFiles(); // Refresh the list
            this.loadStorageInfo(); // Refresh storage info
        } catch (error) {
            console.error('Error deleting session:', error);
            Utils.showToast(error.message, 'error');
        }
    }
    
    async deleteAll() {
        if (!confirm(`Are you sure you want to delete ALL ${this.currentFileType}? This action cannot be undone.`)) {
            return;
        }
        
        try {
            const response = await Utils.makeRequest(`/files/delete-all/${this.currentFileType}`, {
                method: 'POST'
            });
            
            Utils.showToast(`${response.message} (${response.files_deleted} files deleted)`);
            this.loadFiles(); // Refresh the list
            this.loadStorageInfo(); // Refresh storage info
        } catch (error) {
            console.error('Error deleting all files:', error);
            Utils.showToast(error.message, 'error');
        }
    }
    
    async cleanupAll() {
        if (!confirm('Are you sure you want to delete ALL files from uploads, images, videos, audio, and temp directories? This will completely clean your storage and cannot be undone.')) {
            return;
        }
        
        try {
            const response = await Utils.makeRequest('/files/cleanup-all', {
                method: 'POST'
            });
            
            Utils.showToast(response.message);
            
            // Show detailed cleanup results
            const details = response.details;
            let detailMessage = 'Cleanup Details:\n';
            if (details.uploads) detailMessage += `• Uploads: ${details.uploads} files\n`;
            if (details.images) detailMessage += `• Images: ${details.images} files\n`;
            if (details.videos) detailMessage += `• Videos: ${details.videos} files\n`;
            if (details.audio) detailMessage += `• Audio: ${details.audio} files\n`;
            if (details.temp) detailMessage += `• Temp: ${details.temp} items\n`;
            
            alert(detailMessage);
            
            this.loadFiles(); // Refresh the list
            this.loadStorageInfo(); // Refresh storage info
        } catch (error) {
            console.error('Error cleaning up all files:', error);
            Utils.showToast(error.message, 'error');
        }
    }
    
    previewVideo(sessionId, filename) {
        const videoUrl = `/files/download-file/${this.currentFileType}/${sessionId}/${encodeURIComponent(filename)}`;
        
        // Create modal for video preview with proper video element
        const modalHtml = `
            <div class="modal fade" id="videoPreviewModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">${filename}</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body text-center">
                            <video controls preload="metadata" style="max-width: 100%; max-height: 70vh;" id="previewVideo">
                                <source src="${videoUrl}" type="video/mp4">
                                Your browser does not support the video tag.
                            </video>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                            <a href="${videoUrl}" class="btn btn-primary" download="${filename}">
                                <i class="fas fa-download me-2"></i>Download
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Remove existing modal if any
        const existingModal = document.getElementById('videoPreviewModal');
        if (existingModal) {
            existingModal.remove();
        }
        
        // Add modal to body
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        // Show modal
        const modal = new bootstrap.Modal(document.getElementById('videoPreviewModal'));
        modal.show();
        
        // Clean up modal when hidden and pause video
        document.getElementById('videoPreviewModal').addEventListener('hidden.bs.modal', function() {
            const video = document.getElementById('previewVideo');
            if (video) {
                video.pause();
                video.currentTime = 0;
            }
            this.remove();
        });
        
        // Load video metadata when modal is shown
        document.getElementById('videoPreviewModal').addEventListener('shown.bs.modal', function() {
            const video = document.getElementById('previewVideo');
            if (video) {
                video.load(); // Force reload the video
            }
        });
    }
    
    // Method to be called when page is unloaded
    destroy() {
        this.stopAutoRefresh();
    }
}

// Initialize when DOM is loaded
let fileManager;
document.addEventListener('DOMContentLoaded', function() {
    fileManager = new FileManager();
});

// Clean up when page is unloaded
window.addEventListener('beforeunload', function() {
    if (fileManager) {
        fileManager.destroy();
    }
});