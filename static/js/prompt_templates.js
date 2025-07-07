// Prompt Templates JavaScript
class PromptTemplates {
    constructor() {
        this.initializeElements();
        this.setupEventListeners();
        this.loadTemplates();
    }
    
    initializeElements() {
        this.createForm = document.getElementById('createTemplateForm');
        this.editForm = document.getElementById('editTemplateForm');
        this.templatesList = document.getElementById('templatesList');
        this.editModal = new bootstrap.Modal(document.getElementById('editTemplateModal'));
        
        // Create form elements
        this.templateName = document.getElementById('templateName');
        this.templateContent = document.getElementById('templateContent');
        this.templateDescription = document.getElementById('templateDescription');
        
        // Edit form elements
        this.editTemplateId = document.getElementById('editTemplateId');
        this.editTemplateName = document.getElementById('editTemplateName');
        this.editTemplateContent = document.getElementById('editTemplateContent');
        this.editTemplateDescription = document.getElementById('editTemplateDescription');
        this.saveTemplateBtn = document.getElementById('saveTemplateBtn');
    }
    
    setupEventListeners() {
        this.createForm.addEventListener('submit', (e) => this.createTemplate(e));
        this.saveTemplateBtn.addEventListener('click', () => this.updateTemplate());
    }
    
    async loadTemplates() {
        try {
            this.showLoading();
            const data = await Utils.makeRequest('/api/prompt-templates');
            this.renderTemplates(data.templates);
        } catch (error) {
            Utils.showToast('Error loading templates: ' + error.message, 'error');
            this.templatesList.innerHTML = '<div class="alert alert-danger">Error loading templates</div>';
        }
    }
    
    showLoading() {
        this.templatesList.innerHTML = `
            <div class="text-center py-4">
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <p class="mt-2">Loading templates...</p>
            </div>
        `;
    }
    
    renderTemplates(templates) {
        if (templates.length === 0) {
            this.templatesList.innerHTML = `
                <div class="alert alert-info text-center">
                    <i class="fas fa-magic fa-3x mb-3"></i>
                    <h5>No templates found</h5>
                    <p>Create your first prompt template to get started.</p>
                </div>
            `;
            return;
        }
        
        this.templatesList.innerHTML = templates.map(template => this.renderTemplate(template)).join('');
    }
    
    renderTemplate(template) {
        return `
            <div class="card mb-3 template-card" data-template-id="${template.id}">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <h6 class="card-title">
                                <i class="fas fa-magic me-2 text-primary"></i>${template.name}
                            </h6>
                            <p class="card-text">
                                <code>${template.template}</code>
                            </p>
                            <p class="text-muted small mb-0">${template.description || 'No description'}</p>
                        </div>
                        <div class="btn-group">
                            <button class="btn btn-sm btn-outline-primary" onclick="promptTemplates.editTemplate(${template.id})">
                                <i class="fas fa-edit"></i>
                            </button>
                            <button class="btn btn-sm btn-outline-danger" onclick="promptTemplates.deleteTemplate(${template.id})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    async createTemplate(e) {
        e.preventDefault();
        
        try {
            const templateData = {
                name: this.templateName.value,
                template: this.templateContent.value,
                description: this.templateDescription.value
            };
            
            await Utils.makeRequest('/api/prompt-templates', {
                method: 'POST',
                body: JSON.stringify(templateData)
            });
            
            Utils.showToast('Template created successfully!');
            this.createForm.reset();
            
            // Collapse the create form
            const collapse = bootstrap.Collapse.getInstance(document.getElementById('createTemplate'));
            if (collapse) {
                collapse.hide();
            }
            
            this.loadTemplates();
            
        } catch (error) {
            Utils.showToast('Error creating template: ' + error.message, 'error');
        }
    }
    
    async editTemplate(templateId) {
        try {
            const data = await Utils.makeRequest('/api/prompt-templates');
            const template = data.templates.find(t => t.id === templateId);
            
            if (!template) {
                Utils.showToast('Template not found', 'error');
                return;
            }
            
            this.editTemplateId.value = template.id;
            this.editTemplateName.value = template.name;
            this.editTemplateContent.value = template.template;
            this.editTemplateDescription.value = template.description || '';
            
            this.editModal.show();
            
        } catch (error) {
            Utils.showToast('Error loading template: ' + error.message, 'error');
        }
    }
    
    async updateTemplate() {
        try {
            const templateId = parseInt(this.editTemplateId.value);
            const templateData = {
                name: this.editTemplateName.value,
                template: this.editTemplateContent.value,
                description: this.editTemplateDescription.value
            };
            
            await Utils.makeRequest(`/api/prompt-templates/${templateId}`, {
                method: 'PUT',
                body: JSON.stringify(templateData)
            });
            
            Utils.showToast('Template updated successfully!');
            this.editModal.hide();
            this.loadTemplates();
            
        } catch (error) {
            Utils.showToast('Error updating template: ' + error.message, 'error');
        }
    }
    
    async deleteTemplate(templateId) {
        if (!confirm('Are you sure you want to delete this template?')) {
            return;
        }
        
        try {
            await Utils.makeRequest(`/api/prompt-templates/${templateId}`, {
                method: 'DELETE'
            });
            
            Utils.showToast('Template deleted successfully!');
            this.loadTemplates();
            
        } catch (error) {
            Utils.showToast('Error deleting template: ' + error.message, 'error');
        }
    }
}

// Initialize when DOM is loaded
let promptTemplates;
document.addEventListener('DOMContentLoaded', function() {
    promptTemplates = new PromptTemplates();
});