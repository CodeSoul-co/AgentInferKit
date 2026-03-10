/**
 * Experiment Management Module - v2.0
 * 
 * Inference and Evaluation are separated into two sub-tabs.
 * Inference: 3-step stepper with task_type aware dynamic fields.
 * Evaluation: independent entry to run evaluation on existing predictions.
 */

// =========================================================================
// Default metrics by task type
// =========================================================================
const DEFAULT_METRICS_BY_TASK = {
    qa: {
        performance: ['exact_match', 'f1_score', 'rouge_l'],
        efficiency: ['latency_stats', 'token_stats', 'cost_estimate'],
        optional: ['bleu', 'win_rate'],
    },
    text_exam: {
        performance: ['choice_accuracy', 'option_bias'],
        efficiency: ['latency_stats', 'token_stats', 'cost_estimate'],
        optional: ['win_rate'],
    },
    image_mcq: {
        performance: ['choice_accuracy', 'option_bias'],
        efficiency: ['latency_stats', 'token_stats', 'cost_estimate'],
        optional: ['win_rate'],
    },
    api_calling: {
        performance: ['tool_selection_accuracy', 'parameter_accuracy', 'end_to_end_success_rate', 'invalid_call_rate'],
        efficiency: ['latency_stats', 'token_stats', 'cost_estimate'],
        optional: ['avg_tool_calls'],
    },
};

const METRIC_LABELS = {
    exact_match: '精确匹配', f1_score: 'F1 分数', rouge_l: 'ROUGE-L', bleu: 'BLEU',
    choice_accuracy: '选择题准确率', option_bias: '选项偏好', win_rate: '胜率',
    tool_selection_accuracy: '工具选择准确率', parameter_accuracy: '参数准确率',
    end_to_end_success_rate: '端到端成功率', invalid_call_rate: '无效调用率',
    avg_tool_calls: '平均工具调用', latency_stats: '延迟统计', token_stats: 'Token统计',
    cost_estimate: '成本估算',
};

const GROUP_OPTIONS = {
    qa: ['difficulty', 'topic'],
    text_exam: ['difficulty', 'topic', 'question_type'],
    image_mcq: ['difficulty', 'question_type'],
    api_calling: ['difficulty', 'call_type', 'category'],
};

const GROUP_LABELS = {
    difficulty: '按难度', topic: '按主题', question_type: '按题型',
    call_type: '按调用类型', category: '按类别',
};

// =========================================================================
// ExperimentManager
// =========================================================================
class ExperimentManager {
    constructor(options = {}) {
        this.formContainer = options.formContainer || document.getElementById('experiment-form');
        this.progressContainer = options.progressContainer || document.getElementById('experiment-progress');
        this.listContainer = options.listContainer || document.getElementById('experiment-list');
        
        this.currentExperiment = null;
        this.eventSource = null;
        this.currentStep = 1;
        this.currentTaskType = null;
        this.currentDatasetId = null;
        this.datasetsCache = [];
        this.modelsCache = [];
        
        this.init();
    }
    
    init() {
        this.loadExperiments();
    }
    
    // =====================================================================
    // Experiment List
    // =====================================================================
    async loadExperiments() {
        if (!this.listContainer) return;
        
        try {
            const experiments = await API.fetchExperiments();
            this.renderExperimentList(experiments);
        } catch (error) {
            console.error('Failed to load experiments:', error);
            this.listContainer.innerHTML = `<div class="alert alert-error">加载实验列表失败: ${error.message}</div>`;
        }
    }
    
    renderExperimentList(experiments) {
        if (!this.listContainer) return;
        
        if (experiments.length === 0) {
            this.listContainer.innerHTML = `
                <div class="empty-state">
                    <div class="empty-state-icon"><i data-lucide="flask-conical"></i></div>
                    <div class="empty-state-title">暂无实验</div>
                    <div class="empty-state-description">创建您的第一个推理任务开始评测</div>
                </div>
            `;
            if (window.lucide) lucide.createIcons();
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
                        <th>策略</th>
                        <th>进度</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody>
                    ${experiments.map(exp => `
                        <tr data-id="${exp.experiment_id}">
                            <td style="font-weight:600;">${exp.name}</td>
                            <td>${statusBadge(exp.status)}</td>
                            <td><span class="badge badge-info">${exp.dataset_id}</span></td>
                            <td>${exp.model_id}</td>
                            <td><span class="badge badge-neutral">${exp.strategy || 'direct'}</span></td>
                            <td>
                                <div class="progress-bar" style="width:100px;">
                                    <div class="progress-fill${exp.status === 'running' ? ' running' : ''}" style="width:${exp.total_samples > 0 ? (exp.completed / exp.total_samples * 100) : 0}%"></div>
                                </div>
                                <span class="text-muted" style="font-size:0.75rem;">${exp.completed}/${exp.total_samples}</span>
                            </td>
                            <td>
                                ${exp.status === 'created' || exp.status === 'failed' ? `
                                    <button class="btn btn-primary btn-sm" onclick="experimentManager.runExperiment('${exp.experiment_id}')">
                                        <i data-lucide="play" style="width:14px;height:14px;"></i> 运行
                                    </button>
                                ` : ''}
                                ${exp.status === 'running' ? `
                                    <button class="btn btn-warning btn-sm" onclick="experimentManager.stopExperiment('${exp.experiment_id}')">
                                        <i data-lucide="square" style="width:14px;height:14px;"></i> 停止
                                    </button>
                                ` : ''}
                                ${exp.status === 'finished' ? `
                                    <button class="btn btn-primary btn-sm" onclick="experimentManager.openEvaluate('${exp.experiment_id}')">
                                        <i data-lucide="bar-chart-2" style="width:14px;height:14px;"></i> 评估
                                    </button>
                                    <button class="btn btn-secondary btn-sm" onclick="viewResults('${exp.experiment_id}')">
                                        <i data-lucide="eye" style="width:14px;height:14px;"></i> 结果
                                    </button>
                                ` : ''}
                                <button class="btn btn-danger btn-sm" onclick="experimentManager.deleteExperiment('${exp.experiment_id}')">
                                    <i data-lucide="trash-2" style="width:14px;height:14px;"></i>
                                </button>
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
        if (window.lucide) lucide.createIcons();
    }
    
    // =====================================================================
    // 3-Step Stepper for Inference
    // =====================================================================
    async showCreateForm() {
        const formCard = document.getElementById('create-experiment-form');
        if (formCard) formCard.classList.remove('hidden');
        
        this.currentStep = 1;
        this.currentTaskType = null;
        this.currentDatasetId = null;
        
        await this.loadFormOptions();
        this.renderStep(1);
    }
    
    hideCreateForm() {
        const formCard = document.getElementById('create-experiment-form');
        if (formCard) formCard.classList.add('hidden');
    }
    
    async loadFormOptions() {
        try {
            const [datasetsResp, modelsResp] = await Promise.all([
                API.Datasets.list(),
                API.Models.list(),
            ]);
            this.datasetsCache = datasetsResp.datasets || [];
            this.modelsCache = modelsResp.models || [];
            
            // Populate model select dropdown
            const modelSelect = document.getElementById('exp-model-select');
            if (modelSelect) {
                modelSelect.innerHTML = '<option value="">选择模型...</option>' +
                    this.modelsCache.map(m => `<option value="${m.model_id}">${m.model_id} (${m.provider})</option>`).join('');
            }
        } catch (error) {
            console.error('Failed to load form options:', error);
        }
    }
    
    renderStep(step) {
        this.currentStep = step;
        
        // Update step indicators
        document.querySelectorAll('.step-item').forEach(item => {
            const s = parseInt(item.dataset.step);
            item.classList.remove('active', 'completed');
            if (s === step) item.classList.add('active');
            if (s < step) item.classList.add('completed');
        });
        
        // Update step panels
        document.querySelectorAll('.step-panel').forEach(p => p.classList.remove('active'));
        const panel = document.getElementById(`step-panel-${step}`);
        if (panel) panel.classList.add('active');
        
        // Update nav buttons
        const prevBtn = document.getElementById('step-prev-btn');
        const nextBtn = document.getElementById('step-next-btn');
        const submitBtn = document.getElementById('step-submit-btn');
        
        if (prevBtn) prevBtn.style.display = step > 1 ? '' : 'none';
        if (nextBtn) nextBtn.style.display = step < 3 ? '' : 'none';
        if (submitBtn) submitBtn.style.display = step === 3 ? '' : 'none';
        
        // Render step-specific content
        if (step === 1) this.renderStep1();
        if (step === 2) this.renderStep2();
        if (step === 3) this.renderStep3();
        
        if (window.lucide) lucide.createIcons();
    }
    
    nextStep() {
        if (this.currentStep === 1) {
            // Validate step 1
            const name = document.querySelector('#step-panel-1 [name="name"]')?.value;
            if (!name) { this.showNotification('error', '请输入实验名称'); return; }
            if (!this.currentDatasetId) { this.showNotification('error', '请选择数据集'); return; }
        }
        if (this.currentStep === 2) {
            const model = document.querySelector('#step-panel-2 [name="model_id"]')?.value;
            if (!model) { this.showNotification('error', '请选择模型'); return; }
        }
        if (this.currentStep < 3) {
            this.renderStep(this.currentStep + 1);
        }
    }
    
    prevStep() {
        if (this.currentStep > 1) {
            this.renderStep(this.currentStep - 1);
        }
    }
    
    // ----- Step 1: Data Selection -----
    renderStep1() {
        const container = document.getElementById('step1-datasets');
        if (!container) return;
        
        if (this.datasetsCache.length === 0) {
            container.innerHTML = `
                <div class="empty-state" style="padding:20px;">
                    <div class="empty-state-icon"><i data-lucide="database"></i></div>
                    <div class="empty-state-title">暂无数据集</div>
                    <div class="empty-state-description">请先在数据集管理页面上传数据集</div>
                </div>
            `;
            return;
        }
        
        container.innerHTML = `<div class="dataset-card-grid">
            ${this.datasetsCache.map(ds => `
                <div class="dataset-select-card${this.currentDatasetId === ds.dataset_id ? ' selected' : ''}" 
                     onclick="experimentManager.selectDataset('${ds.dataset_id}', '${ds.task_type || 'qa'}')">
                    <div class="dataset-select-name">${ds.dataset_id}</div>
                    <div class="dataset-select-meta">
                        <span class="badge badge-info">${ds.task_type || 'qa'}</span>
                        <span>${ds.total_samples} 样本</span>
                    </div>
                </div>
            `).join('')}
        </div>`;
    }
    
    selectDataset(datasetId, taskType) {
        this.currentDatasetId = datasetId;
        this.currentTaskType = taskType;
        
        // Update visual selection
        document.querySelectorAll('.dataset-select-card').forEach(c => c.classList.remove('selected'));
        // Find the clicked card by dataset_id and mark it selected
        document.querySelectorAll('.dataset-select-card').forEach(c => {
            if (c.querySelector('.dataset-select-name')?.textContent === datasetId) {
                c.classList.add('selected');
            }
        });
        
        // Update hidden select
        const hiddenSelect = document.querySelector('#step-panel-1 [name="dataset_id"]');
        if (hiddenSelect) hiddenSelect.value = datasetId;
        
        // Auto-fill experiment name
        const nameInput = document.querySelector('#step-panel-1 [name="name"]');
        if (nameInput && !nameInput.value) {
            nameInput.value = `${datasetId}_test`;
        }
    }
    
    // ----- Step 2: Inference Config (task_type aware) -----
    renderStep2() {
        const container = document.getElementById('step2-dynamic');
        if (!container) return;
        
        let dynamicHtml = '';
        
        // RAG config for text_exam / qa
        if (this.currentTaskType === 'text_exam' || this.currentTaskType === 'qa') {
            dynamicHtml += this.renderRAGConfig();
        }
        
        // Tool config for api_calling
        if (this.currentTaskType === 'api_calling') {
            dynamicHtml += this.renderToolConfig();
        }
        
        // VLM warning for image_mcq
        if (this.currentTaskType === 'image_mcq') {
            dynamicHtml += `
                <div class="alert alert-info" id="vlm-warning" style="margin-top:12px;">
                    <i data-lucide="info" style="width:16px;height:16px;"></i>
                    图像任务需要支持多模态的模型（VLM）。请选择支持视觉输入的模型。
                </div>
            `;
        }
        
        container.innerHTML = dynamicHtml;
    }
    
    renderRAGConfig() {
        return `
            <div class="form-section" style="margin-top:16px;">
                <div class="form-section-title"><i data-lucide="book-open" style="width:16px;height:16px;"></i> RAG 配置</div>
                <div class="rag-mode-grid">
                    <label class="rag-mode-card selected" onclick="experimentManager.selectRAGMode('closed', this)">
                        <input type="radio" name="rag_mode" value="closed" checked>
                        <div class="rag-mode-title">Closed-book</div>
                        <div class="rag-mode-desc">不使用外部知识，直接作答</div>
                    </label>
                    <label class="rag-mode-card" onclick="experimentManager.selectRAGMode('oracle', this)">
                        <input type="radio" name="rag_mode" value="oracle">
                        <div class="rag-mode-title">Oracle RAG</div>
                        <div class="rag-mode-desc">使用标注好的正确知识块</div>
                    </label>
                    <label class="rag-mode-card" onclick="experimentManager.selectRAGMode('retrieved', this)">
                        <input type="radio" name="rag_mode" value="retrieved">
                        <div class="rag-mode-title">Retrieved RAG</div>
                        <div class="rag-mode-desc">从知识库自动检索</div>
                    </label>
                </div>
                <div id="rag-retrieved-options" style="display:none;margin-top:12px;">
                    <div class="flex gap-md">
                        <div class="form-group flex-1">
                            <label class="form-label">知识库</label>
                            <select name="kb_name" class="form-select" id="rag-kb-select">
                                <option value="">选择知识库...</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label class="form-label">Top-K 召回数</label>
                            <input type="number" name="top_k" class="form-input" value="3" min="1" max="20" style="width:80px;">
                        </div>
                    </div>
                </div>
            </div>
        `;
    }
    
    selectRAGMode(mode, el) {
        document.querySelectorAll('.rag-mode-card').forEach(c => c.classList.remove('selected'));
        el.classList.add('selected');
        
        const retrievedOptions = document.getElementById('rag-retrieved-options');
        if (retrievedOptions) {
            retrievedOptions.style.display = mode === 'retrieved' ? 'block' : 'none';
            if (mode === 'retrieved') this.loadKnowledgeBases();
        }
    }
    
    async loadKnowledgeBases() {
        try {
            const kbs = await API.RAG.list();
            const select = document.getElementById('rag-kb-select');
            if (select && kbs) {
                const kbList = kbs.knowledge_bases || kbs || [];
                select.innerHTML = '<option value="">选择知识库...</option>' +
                    (Array.isArray(kbList) ? kbList : []).map(kb => {
                        const name = typeof kb === 'string' ? kb : kb.kb_name || kb.name;
                        return `<option value="${name}">${name}</option>`;
                    }).join('');
            }
        } catch (e) {
            console.warn('Failed to load knowledge bases:', e);
        }
    }
    
    renderToolConfig() {
        return `
            <div class="form-section" style="margin-top:16px;">
                <div class="form-section-title"><i data-lucide="wrench" style="width:16px;height:16px;"></i> 工具配置</div>
                <div class="tool-checkboxes" id="tool-checkboxes">
                    <label class="tool-checkbox">
                        <input type="checkbox" name="tools" value="search_api" checked> search_api
                    </label>
                </div>
                <div class="form-group" style="margin-top:8px;">
                    <label class="form-label" style="font-size:12px;">
                        <input type="checkbox" name="mock_mode" checked style="margin-right:6px;"> 使用 Mock responses
                    </label>
                </div>
            </div>
        `;
    }
    
    // ----- Step 3: Run Parameters -----
    renderStep3() {
        // Step 3 is static HTML, no dynamic rendering needed
    }
    
    // =====================================================================
    // Form Submission
    // =====================================================================
    getFormData() {
        const name = document.querySelector('#step-panel-1 [name="name"]')?.value || '';
        const description = document.querySelector('#step-panel-1 [name="description"]')?.value || '';
        const dataset_id = this.currentDatasetId || '';
        const split = document.querySelector('#step-panel-1 [name="split"]')?.value || 'test';
        const max_samples = parseInt(document.querySelector('#step-panel-1 [name="max_samples"]')?.value) || null;
        
        const model_id = document.querySelector('#step-panel-2 [name="model_id"]')?.value || '';
        const strategyCard = document.querySelector('.strategy-card.selected');
        const strategy = strategyCard?.dataset.strategy || 'direct';
        
        const concurrency = parseInt(document.querySelector('#step-panel-3 [name="concurrency"]')?.value) || 5;
        const retry_times = parseInt(document.querySelector('#step-panel-3 [name="retry_times"]')?.value) || 3;
        
        // RAG config
        const ragMode = document.querySelector('input[name="rag_mode"]:checked')?.value || 'closed';
        const rag = {
            enabled: ragMode !== 'closed',
            mode: ragMode,
            kb_name: document.querySelector('[name="kb_name"]')?.value || null,
            top_k: parseInt(document.querySelector('[name="top_k"]')?.value) || 3,
        };
        
        return {
            name, description, dataset_id, split, max_samples,
            model_id, strategy,
            rag,
            runner: { concurrency, retry_times, resume: true },
            eval: { metrics: [], group_by: [] },
        };
    }
    
    async submitForm() {
        const config = this.getFormData();
        if (!config.name) { this.showNotification('error', '请输入实验名称'); return; }
        if (!config.dataset_id) { this.showNotification('error', '请选择数据集'); return; }
        if (!config.model_id) { this.showNotification('error', '请选择模型'); return; }
        
        await this.createExperiment(config);
    }
    
    async submitAndRun() {
        const config = this.getFormData();
        if (!config.name) { this.showNotification('error', '请输入实验名称'); return; }
        if (!config.dataset_id) { this.showNotification('error', '请选择数据集'); return; }
        if (!config.model_id) { this.showNotification('error', '请选择模型'); return; }
        
        try {
            const result = await this.createExperiment(config);
            if (result && result.experiment_id) {
                this.hideCreateForm();
                await this.runExperiment(result.experiment_id);
            }
        } catch (e) {
            // Error already shown by createExperiment
        }
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
    
    // =====================================================================
    // Experiment Execution (SSE)
    // =====================================================================
    async runExperiment(experimentId) {
        this.currentExperiment = experimentId;
        this.showProgress(experimentId, { status: 'starting', completed: 0, total: 0 });
        
        try {
            const result = await API.Experiments.run(experimentId);
            const streamUrl = result.stream_url || `/${experimentId}/progress`;
            this.subscribeToProgress(streamUrl, experimentId);
            this.showNotification('info', '实验已启动');
        } catch (error) {
            this.showNotification('error', `启动失败: ${error.message}`);
            this.hideProgress();
        }
    }
    
    subscribeToProgress(streamUrl, experimentId) {
        if (this.eventSource) this.eventSource.close();
        
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
            console.log('Sample completed:', JSON.parse(event.data));
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
                try { errorMsg = JSON.parse(event.data).message || errorMsg; } catch (e) {}
            }
            this.handleExperimentError(experimentId, errorMsg);
            this.eventSource.close();
            this.eventSource = null;
        });
        
        this.eventSource.onerror = () => {
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
        });
        
        const row = document.querySelector(`tr[data-id="${experimentId}"]`);
        if (row) {
            const progressFill = row.querySelector('.progress-fill');
            const progressText = row.querySelector('.text-muted');
            if (progressFill && data.total > 0) {
                progressFill.style.width = `${(data.completed / data.total) * 100}%`;
            }
            if (progressText) progressText.textContent = `${data.completed}/${data.total}`;
        }
    }
    
    handleExperimentDone(experimentId, data) {
        this.showNotification('success', '推理完成！可在实验列表中点击「评估」运行评估。');
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
        
        this.progressContainer.innerHTML = `
            <div class="card">
                <div class="card-header"><i data-lucide="loader" style="width:16px;height:16px;"></i> 推理进度 - ${experimentId}</div>
                <div class="card-body">
                    <div class="progress-info flex justify-between mb-sm">
                        <span>状态: <strong>${data.status}</strong></span>
                        <span>${data.completed} / ${data.total} 样本</span>
                    </div>
                    <div class="progress-bar" style="height:20px;">
                        <div class="progress-fill running" style="width:${percent}%;transition:width 0.3s ease;"></div>
                    </div>
                    <div class="progress-footer flex justify-between mt-sm">
                        <span>${percent}%</span>
                    </div>
                </div>
            </div>
        `;
        this.progressContainer.classList.remove('hidden');
        if (window.lucide) lucide.createIcons();
    }
    
    hideProgress() {
        if (this.progressContainer) this.progressContainer.classList.add('hidden');
    }
    
    async stopExperiment(experimentId) {
        try {
            await API.Experiments.stop(experimentId);
            this.showNotification('warning', '实验已停止');
            if (this.eventSource) { this.eventSource.close(); this.eventSource = null; }
            this.hideProgress();
            await this.loadExperiments();
        } catch (error) {
            this.showNotification('error', `停止失败: ${error.message}`);
        }
    }
    
    async deleteExperiment(experimentId) {
        if (!confirm('确定要删除这个实验吗？')) return;
        try {
            await API.Experiments.delete(experimentId);
            this.showNotification('success', '实验已删除');
            await this.loadExperiments();
        } catch (error) {
            this.showNotification('error', `删除失败: ${error.message}`);
        }
    }
    
    // =====================================================================
    // Evaluation Sub-Tab
    // =====================================================================
    openEvaluate(experimentId) {
        // Switch to evaluation sub-tab
        document.querySelectorAll('.exp-sub-tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.exp-sub-tab-panel').forEach(p => p.classList.remove('active'));
        
        const evalBtn = document.querySelector('.exp-sub-tab-btn[data-panel="exp-eval-panel"]');
        const evalPanel = document.getElementById('exp-eval-panel');
        if (evalBtn) evalBtn.classList.add('active');
        if (evalPanel) evalPanel.classList.add('active');
        
        // Pre-fill the experiment select
        const select = document.getElementById('eval-experiment-select');
        if (select) {
            select.value = experimentId;
            this.onEvalExperimentChange(experimentId);
        }
    }
    
    async loadEvalExperiments() {
        const select = document.getElementById('eval-experiment-select');
        if (!select) return;
        
        try {
            const experiments = await API.fetchExperiments({ status: 'finished' });
            select.innerHTML = '<option value="">选择已完成的推理任务...</option>' +
                experiments.map(e => `<option value="${e.experiment_id}">${e.name} (${e.dataset_id})</option>`).join('');
        } catch (e) {
            console.warn('Failed to load eval experiments:', e);
        }
    }
    
    async onEvalExperimentChange(experimentId) {
        if (!experimentId) return;
        
        // Infer task type from experiment
        try {
            const exp = await API.Experiments.get(experimentId);
            const taskType = this.inferTaskTypeFromDatasetId(exp.dataset_id);
            this.renderEvalMetrics(taskType);
            this.renderEvalGroups(taskType);
        } catch (e) {
            console.warn('Failed to load experiment info:', e);
            this.renderEvalMetrics('qa');
            this.renderEvalGroups('qa');
        }
    }
    
    inferTaskTypeFromDatasetId(datasetId) {
        if (!datasetId) return 'qa';
        const id = datasetId.toLowerCase();
        if (id.includes('exam') || id.includes('choice')) return 'text_exam';
        if (id.includes('mcq') || id.includes('image')) return 'image_mcq';
        if (id.includes('agent') || id.includes('api') || id.includes('calling') || id.includes('tool')) return 'api_calling';
        return 'qa';
    }
    
    renderEvalMetrics(taskType) {
        const container = document.getElementById('eval-metrics-checkboxes');
        if (!container) return;
        
        const config = DEFAULT_METRICS_BY_TASK[taskType] || DEFAULT_METRICS_BY_TASK.qa;
        const allMetrics = [...config.performance, ...config.efficiency, ...(config.optional || [])];
        const defaultChecked = new Set([...config.performance, ...config.efficiency]);
        
        container.innerHTML = allMetrics.map(m => `
            <label class="eval-checkbox">
                <input type="checkbox" name="eval_metrics" value="${m}" ${defaultChecked.has(m) ? 'checked' : ''}>
                <span>${METRIC_LABELS[m] || m}</span>
            </label>
        `).join('');
    }
    
    renderEvalGroups(taskType) {
        const container = document.getElementById('eval-groups-checkboxes');
        if (!container) return;
        
        const groups = GROUP_OPTIONS[taskType] || GROUP_OPTIONS.qa;
        
        container.innerHTML = groups.map((g, i) => `
            <label class="eval-checkbox">
                <input type="checkbox" name="eval_groups" value="${g}" ${i < 2 ? 'checked' : ''}>
                <span>${GROUP_LABELS[g] || g}</span>
            </label>
        `).join('');
    }
    
    async submitEvaluation() {
        const experimentId = document.getElementById('eval-experiment-select')?.value;
        if (!experimentId) {
            this.showNotification('error', '请选择推理任务');
            return;
        }
        
        const metrics = Array.from(document.querySelectorAll('input[name="eval_metrics"]:checked'))
            .map(cb => cb.value);
        const groupBy = Array.from(document.querySelectorAll('input[name="eval_groups"]:checked'))
            .map(cb => cb.value);
        
        if (metrics.length === 0) {
            this.showNotification('error', '请至少选择一个评估指标');
            return;
        }
        
        this.showNotification('info', '正在运行评估...');
        
        try {
            await API.Experiments.evaluate(experimentId, { metrics, group_by: groupBy });
            this.showNotification('success', '评估完成！正在跳转到结果分析...');
            
            // Jump to results
            setTimeout(() => {
                if (typeof viewResults === 'function') {
                    viewResults(experimentId);
                }
            }, 500);
        } catch (error) {
            this.showNotification('error', `评估失败: ${error.message}`);
        }
    }
    
    // =====================================================================
    // Notifications
    // =====================================================================
    showNotification(type, message) {
        const container = document.getElementById('notifications') || document.body;
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'error' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'info'}`;
        notification.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;min-width:300px;max-width:500px;animation:slideIn 0.3s ease;';
        notification.innerHTML = message;
        container.appendChild(notification);
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// =========================================================================
// Strategy card selection helper
// =========================================================================
function selectStrategy(el) {
    document.querySelectorAll('.strategy-card').forEach(c => c.classList.remove('selected'));
    el.classList.add('selected');
    
    const hiddenSelect = document.getElementById('strategy-hidden-select');
    if (hiddenSelect) hiddenSelect.value = el.dataset.strategy;
}

// =========================================================================
// Global instance
// =========================================================================
var experimentManager = null;

function initExperimentManager() {
    experimentManager = new ExperimentManager();
    window.experimentManager = experimentManager;
}

// Auto-init (only once)
document.addEventListener('DOMContentLoaded', () => {
    if (!window.experimentManager && (document.getElementById('experiment-list') || document.getElementById('experiment-form'))) {
        initExperimentManager();
    }
});

// Export
window.ExperimentManager = ExperimentManager;
window.initExperimentManager = initExperimentManager;
window.selectStrategy = selectStrategy;
