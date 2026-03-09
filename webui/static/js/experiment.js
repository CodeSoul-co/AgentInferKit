/**
 * Experiment Management Module
 * 
 * Implements experiment creation form and SSE progress monitoring.
 */

class ExperimentManager {
    constructor(options = {}) {
        this.formContainer = options.formContainer || document.getElementById('experiment-form');
        this.progressContainer = options.progressContainer || document.getElementById('experiment-progress');
        this.listContainer = options.listContainer || document.getElementById('experiment-list');
        
        this.currentExperiment = null;
        this.eventSource = null;
        
        this.init();
    }
    
    init() {
        this.loadExperiments();
    }
    
    async loadExperiments() {
        if (!this.listContainer) return;
        
        try {
            const experiments = await API.fetchExperiments();
            this.renderExperimentList(experiments);
        } catch (error) {
            console.error('Failed to load experiments:', error);
            this.listContainer.innerHTML = `
                <div class="alert alert-error">
                    加载实验列表失败: ${error.message}
                </div>
            `;
        }
    }
    
    renderExperimentList(experiments) {
        if (!this.listContainer) return;
        
        if (experiments.length === 0) {
            this.listContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon">🧪</div>
                    <div class="empty-state-title">暂无实验</div>
                    <div class="empty-state-description">创建您的第一个实验开始评测</div>
                </div>
            `;
            return;
        }
        
        const statusBadge = (status) => {
            const badges = {
                'created': '<span class="badge badge-neutral">待运行</span>',
                'running': '<span class="badge badge-info">运行中</span>',
                'finished': '<span class="badge badge-success">已完成</span>',
                'failed': '<span class="badge badge-error">失败</span>',
                'stopped': '<span class="badge badge-warning">已停止</span>',
            };
            return badges[status] || `<span class="badge badge-neutral">${status}</span>`;
        };
        
        this.listContainer.innerHTML = `
            <table class="table">
                <thead>
                    <tr>
                        <th>实验名称</th>
                        <th>状态</th>
                        <th>数据集</th>
                        <th>模型</th>
                        <th>进度</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    ${experiments.map(exp => `
                        <tr data-id="${exp.experiment_id}">
                            <td>${exp.name}</td>
                            <td>${statusBadge(exp.status)}</td>
                            <td>${exp.dataset_id}</td>
                            <td>${exp.model_id}</td>
                            <td>
                                <div class="progress-bar" style="width: 100px;">
                                    <div class="progress-fill" style="width: ${exp.total_samples > 0 ? (exp.completed / exp.total_samples * 100) : 0}%"></div>
                                </div>
                                <span class="text-muted" style="font-size: 0.75rem;">${exp.completed}/${exp.total_samples}</span>
                            </td>
                            <td>
                                ${exp.status === 'created' ? `
                                    <button class="btn btn-primary btn-sm" onclick="experimentManager.runExperiment('${exp.experiment_id}')">
                                        ▶️ 运行
                                    </button>
                                ` : ''}
                                ${exp.status === 'running' ? `
                                    <button class="btn btn-warning btn-sm" onclick="experimentManager.stopExperiment('${exp.experiment_id}')">
                                        ⏹️ 停止
                                    </button>
                                ` : ''}
                                ${exp.status === 'finished' ? `
                                    <button class="btn btn-secondary btn-sm" onclick="viewResults('${exp.experiment_id}')">
                                        📊 查看结果
                                    </button>
                                ` : ''}
                                <button class="btn btn-danger btn-sm" onclick="experimentManager.deleteExperiment('${exp.experiment_id}')">
                                    🗑️
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }
    
    async createExperiment(config) {
        try {
            const result = await API.Experiments.create(config);
            this.showNotification('success', `实验 "${config.name}" 创建成功`);
            await this.loadExperiments();
            return result;
        } catch (error) {
            this.showNotification('error', `创建失败: ${error.message}`);
            throw error;
        }
    }
    
    async runExperiment(experimentId) {
        this.currentExperiment = experimentId;
        this.showProgress(experimentId, { status: 'starting', completed: 0, total: 0 });
        
        try {
            // Start the experiment
            const result = await API.Experiments.run(experimentId);
            
            // Subscribe to SSE progress stream
            const streamUrl = result.stream_url || `/experiments/${experimentId}/progress`;
            this.subscribeToProgress(streamUrl, experimentId);
            
            this.showNotification('info', '实验已启动');
            
        } catch (error) {
            this.showNotification('error', `启动失败: ${error.message}`);
            this.hideProgress();
        }
    }
    
    subscribeToProgress(streamUrl, experimentId) {
        // Close existing connection
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        // Build full URL: /api/v1/experiments + streamUrl
        // streamUrl is relative like "/{id}/progress"
        const fullUrl = '/api/v1/experiments' + streamUrl;
        this.eventSource = new EventSource(fullUrl);
        
        this.eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                this.handleProgressUpdate(experimentId, data);
            } catch (e) {
                console.warn('Failed to parse SSE data:', event.data);
            }
        };
        
        this.eventSource.addEventListener('progress', (event) => {
            const data = JSON.parse(event.data);
            this.handleProgressUpdate(experimentId, data);
        });
        
        this.eventSource.addEventListener('sample', (event) => {
            const data = JSON.parse(event.data);
            this.handleSampleUpdate(experimentId, data);
        });
        
        this.eventSource.addEventListener('done', (event) => {
            const data = JSON.parse(event.data);
            this.handleExperimentDone(experimentId, data);
            this.eventSource.close();
            this.eventSource = null;
        });
        
        this.eventSource.addEventListener('error', (event) => {
            let errorMsg = 'SSE 连接错误';
            if (event.data) {
                try {
                    const data = JSON.parse(event.data);
                    errorMsg = data.message || errorMsg;
                } catch (e) {}
            }
            this.handleExperimentError(experimentId, errorMsg);
            this.eventSource.close();
            this.eventSource = null;
        });
        
        this.eventSource.onerror = () => {
            // Connection might have closed normally
            if (this.eventSource && this.eventSource.readyState === EventSource.CLOSED) {
                this.loadExperiments();
            }
        };
    }
    
    handleProgressUpdate(experimentId, data) {
        this.showProgress(experimentId, {
            status: data.status || 'running',
            completed: data.completed || 0,
            total: data.total || 0,
            accuracy: data.accuracy,
        });
        
        // Update list row if visible
        const row = document.querySelector(`tr[data-id="${experimentId}"]`);
        if (row) {
            const progressFill = row.querySelector('.progress-fill');
            const progressText = row.querySelector('.text-muted');
            if (progressFill && data.total > 0) {
                progressFill.style.width = `${(data.completed / data.total) * 100}%`;
            }
            if (progressText) {
                progressText.textContent = `${data.completed}/${data.total}`;
            }
        }
    }
    
    handleSampleUpdate(experimentId, data) {
        // Could add real-time sample results display here
        console.log('Sample completed:', data);
    }
    
    handleExperimentDone(experimentId, data) {
        this.showNotification('success', '实验完成！');
        this.hideProgress();
        this.loadExperiments();
    }
    
    handleExperimentError(experimentId, message) {
        this.showNotification('error', `实验错误: ${message}`);
        this.hideProgress();
        this.loadExperiments();
    }
    
    showProgress(experimentId, data) {
        if (!this.progressContainer) return;
        
        const percent = data.total > 0 ? Math.round((data.completed / data.total) * 100) : 0;
        const accuracyText = data.accuracy !== undefined ? `准确率: ${(data.accuracy * 100).toFixed(1)}%` : '';
        
        this.progressContainer.innerHTML = `
            <div class="card">
                <div class="card-header">
                    实验进度 - ${experimentId}
                </div>
                <div class="card-body">
                    <div class="progress-info flex justify-between mb-sm">
                        <span>状态: <strong>${data.status}</strong></span>
                        <span>${data.completed} / ${data.total} 样本</span>
                    </div>
                    <div class="progress-bar" style="height: 20px;">
                        <div class="progress-fill" style="width: ${percent}%; transition: width 0.3s ease;"></div>
                    </div>
                    <div class="progress-footer flex justify-between mt-sm">
                        <span>${percent}%</span>
                        <span class="text-muted">${accuracyText}</span>
                    </div>
                </div>
            </div>
        `;
        this.progressContainer.classList.remove('hidden');
    }
    
    hideProgress() {
        if (this.progressContainer) {
            this.progressContainer.classList.add('hidden');
        }
    }
    
    async stopExperiment(experimentId) {
        try {
            await API.Experiments.stop(experimentId);
            this.showNotification('warning', '实验已停止');
            
            if (this.eventSource) {
                this.eventSource.close();
                this.eventSource = null;
            }
            
            this.hideProgress();
            await this.loadExperiments();
            
        } catch (error) {
            this.showNotification('error', `停止失败: ${error.message}`);
        }
    }
    
    async deleteExperiment(experimentId) {
        if (!confirm('确定要删除这个实验吗？')) {
            return;
        }
        
        try {
            await API.Experiments.delete(experimentId);
            this.showNotification('success', '实验已删除');
            await this.loadExperiments();
        } catch (error) {
            this.showNotification('error', `删除失败: ${error.message}`);
        }
    }
    
    showNotification(type, message) {
        // Use a simple notification system
        const container = document.getElementById('notifications') || document.body;
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'error' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'info'}`;
        notification.style.cssText = 'position: fixed; top: 20px; right: 20px; z-index: 9999; min-width: 300px; animation: slideIn 0.3s ease;';
        notification.innerHTML = message;
        
        container.appendChild(notification);
        
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
    
    getFormData() {
        const form = this.formContainer;
        if (!form) return null;
        
        return {
            name: form.querySelector('[name="name"]')?.value || '',
            description: form.querySelector('[name="description"]')?.value || '',
            dataset_id: form.querySelector('[name="dataset_id"]')?.value || '',
            split: form.querySelector('[name="split"]')?.value || 'test',
            max_samples: parseInt(form.querySelector('[name="max_samples"]')?.value) || null,
            model_id: form.querySelector('[name="model_id"]')?.value || '',
            strategy: form.querySelector('[name="strategy"]')?.value || 'direct',
            rag: {
                enabled: form.querySelector('[name="rag_enabled"]')?.checked || false,
                mode: form.querySelector('[name="rag_mode"]')?.value || 'retrieved',
                kb_name: form.querySelector('[name="kb_name"]')?.value || null,
                top_k: parseInt(form.querySelector('[name="top_k"]')?.value) || 3,
            },
            runner: {
                concurrency: parseInt(form.querySelector('[name="concurrency"]')?.value) || 5,
                retry_times: parseInt(form.querySelector('[name="retry_times"]')?.value) || 3,
                resume: form.querySelector('[name="resume"]')?.checked !== false,
            },
            eval: {
                metrics: (form.querySelector('[name="metrics"]')?.value || 'accuracy').split(',').map(s => s.trim()),
                group_by: (form.querySelector('[name="group_by"]')?.value || '').split(',').map(s => s.trim()).filter(Boolean),
            },
        };
    }
    
    async submitForm() {
        const config = this.getFormData();
        if (!config) return;
        
        if (!config.name) {
            this.showNotification('error', '请输入实验名称');
            return;
        }
        if (!config.dataset_id) {
            this.showNotification('error', '请选择数据集');
            return;
        }
        if (!config.model_id) {
            this.showNotification('error', '请选择模型');
            return;
        }
        
        await this.createExperiment(config);
    }
}

// Global instance
let experimentManager = null;

function initExperimentManager() {
    experimentManager = new ExperimentManager();
}

// Auto-init
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('experiment-list') || document.getElementById('experiment-form')) {
        initExperimentManager();
    }
});

// Export
window.ExperimentManager = ExperimentManager;
window.experimentManager = experimentManager;
window.initExperimentManager = initExperimentManager;
