/**
 * Dataset Upload Module
 * 
 * Implements drag-and-drop file upload with real-time validation feedback.
 */

class DatasetUploader {
    constructor(options = {}) {
        this.dropZone = options.dropZone || document.getElementById('drop-zone');
        this.fileInput = options.fileInput || document.getElementById('file-input');
        this.statusContainer = options.statusContainer || document.getElementById('upload-status');
        this.taskTypeSelect = options.taskTypeSelect || document.getElementById('task-type');
        this.datasetNameInput = options.datasetNameInput || document.getElementById('dataset-name');
        
        this.currentFile = null;
        this.isUploading = false;
        
        this.init();
    }
    
    init() {
        if (this.dropZone) {
            this.setupDropZone();
        }
        if (this.fileInput) {
            this.setupFileInput();
        }
    }
    
    setupDropZone() {
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            });
        });
        
        // Highlight drop zone when dragging over
        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => {
                this.dropZone.classList.add('drag-over');
            });
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => {
                this.dropZone.classList.remove('drag-over');
            });
        });
        
        // Handle dropped files
        this.dropZone.addEventListener('drop', (e) => {
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFile(files[0]);
            }
        });
        
        // Click to open file dialog
        this.dropZone.addEventListener('click', () => {
            if (this.fileInput) {
                this.fileInput.click();
            }
        });
    }
    
    setupFileInput() {
        this.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFile(e.target.files[0]);
            }
        });
    }
    
    async handleFile(file) {
        // Validate file type
        if (!file.name.endsWith('.jsonl') && !file.name.endsWith('.json')) {
            this.showStatus('error', '请上传 JSONL 或 JSON 格式的文件');
            return;
        }
        
        this.currentFile = file;
        
        // Auto-fill dataset name if empty
        if (this.datasetNameInput && !this.datasetNameInput.value) {
            this.datasetNameInput.value = file.name.replace(/\.jsonl?$/, '');
        }
        
        // Prevalidate JSONL format
        const validation = await this.prevalidateJsonl(file);
        this.showFileInfo(file, validation);
    }
    
    async prevalidateJsonl(file) {
        try {
            const text = await file.slice(0, 50000).text();
            const lines = text.split('\n').filter(l => l.trim());
            let errors = 0;
            let firstError = null;
            
            lines.forEach((line, i) => {
                try {
                    JSON.parse(line);
                } catch {
                    errors++;
                    if (!firstError) firstError = i + 1;
                }
            });
            
            return { total: lines.length, errors, firstError };
        } catch (error) {
            return { total: 0, errors: 1, firstError: 1 };
        }
    }
    
    showFileInfo(file, validation = null) {
        const sizeKB = (file.size / 1024).toFixed(2);
        const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
        const sizeStr = file.size > 1024 * 1024 ? `${sizeMB} MB` : `${sizeKB} KB`;
        
        const validationHtml = validation ? `
            <div class="file-validation" style="color:${validation.errors === 0 ? 'var(--success-color)' : 'var(--warning-color)'}">
                <i data-lucide="${validation.errors === 0 ? 'check-circle' : 'alert-triangle'}" style="width:14px;height:14px;"></i>
                ${validation.errors === 0 ? `JSONL 格式正确 · 预检 ${validation.total} 条` : `发现 ${validation.errors} 个错误 · 第 ${validation.firstError} 行`}
            </div>
        ` : '';
        
        this.showStatus('info', `
            <div class="file-info-card ${validation && validation.errors === 0 ? 'success' : ''}">
                <div class="file-info">
                    <div class="file-name"><i data-lucide="file-text" style="width:16px;height:16px;display:inline;vertical-align:middle;margin-right:4px;"></i>${file.name}</div>
                    <div class="file-size">${sizeStr}</div>
                    ${validationHtml}
                </div>
            </div>
            </div>
        `);
        if (window.lucide) lucide.createIcons();
    }
    
    showStatus(type, message) {
        if (!this.statusContainer) return;
        
        const typeClass = {
            'info': 'alert-info',
            'success': 'alert-success',
            'error': 'alert-error',
            'warning': 'alert-warning',
        }[type] || 'alert-info';
        
        this.statusContainer.innerHTML = `
            <div class="alert ${typeClass}">
                ${message}
            </div>
        `;
        this.statusContainer.classList.remove('hidden');
    }
    
    updateProgress(percent, loaded, total) {
        const processedText = total > 0 ? ` · 已处理 ${Math.round(loaded / total * 100)}%` : '';
        this.statusContainer.innerHTML = `
            <div class="upload-progress">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                    <span class="progress-label" style="margin-bottom:0;">${I18N ? I18N.t('common.upload_progress') : '上传中...'}${processedText}</span>
                    <span style="font-size:0.8rem;font-weight:700;color:var(--primary-color);">${percent}%</span>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill running" style="width: ${percent}%"></div>
                </div>
            </div>
        `;
        this.statusContainer.classList.remove('hidden');
    }
    
    showUploadResult(result) {
        const validatedIcon = result.validated ? '<i data-lucide="check-circle" style="width:20px;height:20px;color:var(--success-color);"></i>' : '<i data-lucide="alert-triangle" style="width:20px;height:20px;color:var(--warning-color);"></i>';
        const validatedText = result.validated ? (I18N ? I18N.t('common.validated') : '验证通过') : (I18N ? I18N.t('common.validated_warn') : '验证有警告');
        
        let warningsHtml = '';
        if (result.warnings && result.warnings.length > 0) {
            warningsHtml = `
                <div class="warnings mt-sm">
                    <strong>警告:</strong>
                    <ul>
                        ${result.warnings.map(w => `<li>${w}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        this.showStatus('success', `
            <div class="file-info-card success">
                <div style="display:flex;align-items:flex-start;gap:12px;">
                    ${validatedIcon}
                    <div style="flex:1;">
                        <div style="font-weight:600;margin-bottom:4px;">${validatedText}</div>
                        <div style="font-size:0.9rem;color:var(--text-secondary);margin-bottom:8px;">
                            ${result.dataset_id} · ${result.total_samples} 条 · task_type: ${this.taskTypeSelect?.value || 'unknown'}
                        </div>
                        ${warningsHtml}
                    </div>
                </div>
            </div>
        `);
        
        // Refresh datasets list if available
        setTimeout(() => {
            console.log('Attempting to refresh datasets list...');
            if (typeof refreshDatasetsList === 'function') {
                console.log('Calling refreshDatasetsList()');
                refreshDatasetsList();
            } else {
                console.warn('refreshDatasetsList function not found');
            }
            // Also refresh dashboard stats
            if (typeof refreshDashboard === 'function') {
                refreshDashboard();
            }
        }, 500);
    }
    
    async upload() {
        if (!this.currentFile) {
            this.showStatus('error', '请先选择文件');
            return null;
        }
        
        if (this.isUploading) {
            return null;
        }
        
        const taskType = this.taskTypeSelect?.value || 'qa';
        const datasetName = this.datasetNameInput?.value || this.currentFile.name.replace(/\.jsonl?$/, '');
        
        this.isUploading = true;
        this.showUploadProgress(0);
        
        try {
            // Simulate progress (actual progress would need XHR)
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress = Math.min(progress + 10, 90);
                this.showUploadProgress(progress);
            }, 200);
            
            const result = await API.uploadDataset(this.currentFile, taskType, {
                dataset_name: datasetName,
            });
            
            clearInterval(progressInterval);
            this.showUploadProgress(100);
            
            // Show result after a brief delay
            setTimeout(() => {
                this.showUploadResult(result);
            }, 300);
            
            this.currentFile = null;
            this.isUploading = false;
            if (window.lucide) lucide.createIcons();
            
            return result;
            
        } catch (error) {
            this.isUploading = false;
            this.showStatus('error', `上传失败: ${error.message}`);
            return null;
        }
    }
    
    reset() {
        this.currentFile = null;
        this.isUploading = false;
        if (this.fileInput) {
            this.fileInput.value = '';
        }
        if (this.datasetNameInput) {
            this.datasetNameInput.value = '';
        }
        if (this.statusContainer) {
            this.statusContainer.innerHTML = '';
            this.statusContainer.classList.add('hidden');
        }
    }
}

// Initialize uploader when DOM is ready
let datasetUploader = null;

function initUploader() {
    datasetUploader = new DatasetUploader();
}

// Auto-init if elements exist
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('drop-zone')) {
        initUploader();
    }
});

// Export for global access
window.DatasetUploader = DatasetUploader;
window.initUploader = initUploader;
