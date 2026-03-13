/**
 * Experiment Management Module - v3.0
 * 
 * Inference and Evaluation are separated into two sub-tabs.
 * Inference: 7-section single-page scroll form with task_type awareness.
 * Evaluation: independent entry to run evaluation on existing predictions.
 */

// =========================================================================
// Default metrics by task type (aligned with registry.py _METRIC_MAP keys)
// =========================================================================
const DEFAULT_METRICS_BY_TASK = {
    qa: {
        performance: ['exact_match', 'f1_score', 'rouge_l'],
        efficiency: ['latency_stats', 'token_stats', 'cost_estimate'],
        optional: ['bleu', 'win_rate', 'avg_reasoning_steps', 'avg_trace_tokens', 'llm_judge'],
        rag: ['retrieval_hit_rate', 'context_relevance', 'retrieval_recall_at_k', 'answer_evidence_consistency', 'hallucination_rate'],
    },
    text_exam: {
        performance: ['choice_accuracy', 'option_bias'],
        efficiency: ['latency_stats', 'token_stats', 'cost_estimate'],
        optional: ['win_rate', 'avg_reasoning_steps', 'avg_trace_tokens', 'llm_judge'],
        rag: ['retrieval_hit_rate', 'context_relevance', 'retrieval_recall_at_k', 'answer_evidence_consistency', 'hallucination_rate'],
    },
    image_mcq: {
        performance: ['choice_accuracy', 'option_bias'],
        efficiency: ['latency_stats', 'token_stats', 'cost_estimate'],
        optional: ['win_rate', 'avg_reasoning_steps', 'avg_trace_tokens', 'llm_judge'],
    },
    api_calling: {
        performance: ['tool_selection_accuracy', 'parameter_accuracy', 'end_to_end_success_rate', 'invalid_call_rate', 'avg_tool_calls'],
        efficiency: ['latency_stats', 'token_stats', 'cost_estimate'],
        optional: ['avg_reasoning_steps', 'avg_trace_tokens'],
    },
};

const METRIC_LABELS = {
    exact_match: '精确匹配', f1_score: 'F1 分数', rouge_l: 'ROUGE-L', bleu: 'BLEU',
    choice_accuracy: '选择题准确率', option_bias: '选项偏置', win_rate: '胜率',
    tool_selection_accuracy: '工具选择准确率', parameter_accuracy: '参数准确率',
    end_to_end_success_rate: '端到端成功率', invalid_call_rate: '无效调用率',
    avg_tool_calls: '平均工具调用', avg_reasoning_steps: '平均推理步数',
    avg_trace_tokens: '平均 Trace Token', llm_judge: 'LLM 评委',
    retrieval_hit_rate: '检索命中率', context_relevance: '上下文相关性',
    retrieval_recall_at_k: '检索召回率@K', answer_evidence_consistency: '答案-证据一致性',
    hallucination_rate: '幻觉率',
    latency_stats: '延迟统计', token_stats: 'Token统计', cost_estimate: '成本估算',
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

// VLM-capable models (for image_mcq warning)
const VLM_MODELS = ['gpt-4o', 'gpt-4-vision', 'gpt-4o-mini', 'claude-3-5-sonnet', 'claude-3-opus', 'qwen-vl'];

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
                                    <button class="btn btn-secondary btn-sm" onclick="experimentManager.showPredictionDetail('${exp.experiment_id}')">
                                        <i data-lucide="file-search" style="width:14px;height:14px;"></i> 详情
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
    // Create Form (7-section single-page)
    // =====================================================================
    async showCreateForm() {
        const formCard = document.getElementById('create-experiment-form');
        if (formCard) formCard.classList.remove('hidden');
        
        this.currentTaskType = null;
        this.currentDatasetId = null;
        
        await this.loadFormOptions();
        this.renderDatasetCards();
        this.updateTaskTypeSections();
        this.renderInferMetrics('qa');
        
        if (window.lucide) lucide.createIcons();
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
        } catch (error) {
            console.error('Failed to load form options:', error);
        }
    }
    
    // ----- Section 1: Data Selection -----
    renderDatasetCards() {
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
                     onclick="experimentManager.selectDataset('${ds.dataset_id}', '${ds.task_type || 'qa'}', ${ds.total_samples || 0})">
                    <div class="dataset-select-name">${ds.dataset_id}</div>
                    <div class="dataset-select-meta">
                        <span class="badge badge-info">${ds.task_type || 'qa'}</span>
                        <span>${ds.total_samples || 0} 样本</span>
                    </div>
                </div>
            `).join('')}
        </div>`;
    }
    
    selectDataset(datasetId, taskType, totalSamples) {
        this.currentDatasetId = datasetId;
        this.currentTaskType = taskType;
        
        // Update visual selection
        document.querySelectorAll('.dataset-select-card').forEach(c => c.classList.remove('selected'));
        document.querySelectorAll('.dataset-select-card').forEach(c => {
            if (c.querySelector('.dataset-select-name')?.textContent === datasetId) {
                c.classList.add('selected');
            }
        });
        
        // Update hidden select
        const hiddenSelect = document.querySelector('[name="dataset_id"]');
        if (hiddenSelect) hiddenSelect.value = datasetId;
        
        // Show task type badge
        const badge = document.getElementById('task-type-badge');
        if (badge) {
            badge.style.display = 'block';
            badge.innerHTML = `<span class="badge badge-info" style="font-size:13px;">task_type: ${taskType}</span>` +
                (totalSamples ? ` <span class="text-muted" style="font-size:12px;">共 ${totalSamples} 条</span>` : '');
        }
        
        // Auto-fill experiment name
        const nameInput = document.getElementById('exp-name-input');
        if (nameInput && !nameInput.value) {
            nameInput.value = `${datasetId}_test`;
        }
        
        // Update max_samples placeholder
        const maxInput = document.querySelector('[name="max_samples"]');
        if (maxInput && totalSamples) maxInput.placeholder = `全部 (${totalSamples})`;
        
        // Update task-type-dependent sections
        this.updateTaskTypeSections();
        this.renderInferMetrics(taskType);
        
        if (window.lucide) lucide.createIcons();
    }
    
    updateTaskTypeSections() {
        const tt = this.currentTaskType;
        
        // Section 4: RAG (show for text_exam / qa)
        const ragSection = document.getElementById('section-rag');
        if (ragSection) ragSection.style.display = (tt === 'text_exam' || tt === 'qa') ? 'block' : 'none';
        
        // Section 5: Tools (show for api_calling)
        const toolsSection = document.getElementById('section-tools');
        if (toolsSection) {
            toolsSection.style.display = tt === 'api_calling' ? 'block' : 'none';
            if (tt === 'api_calling') this.loadToolSchemas();
        }
        
        // Strategy: show ReAct only for api_calling
        const reactCard = document.getElementById('strategy-react-card');
        if (reactCard) reactCard.style.display = tt === 'api_calling' ? '' : 'none';
        
        // VLM warning
        this.updateVlmWarning();
    }
    
    // ----- Section 2: Provider / Model linking -----
    onProviderChange(provider) {
        const modelSelect = document.getElementById('exp-model-select');
        if (!modelSelect) return;
        
        // Filter models by provider
        const filtered = this.modelsCache.filter(m => m.provider === provider);
        if (filtered.length > 0) {
            modelSelect.innerHTML = '<option value="">选择模型...</option>' +
                filtered.map(m => `<option value="${m.model_id}">${m.model_id}</option>`).join('');
        } else {
            modelSelect.innerHTML = '<option value="">该 Provider 暂无配置模型</option>';
        }
        
        // Hide API key field for Ollama
        const apiKeyGroup = document.getElementById('api-key-group');
        if (apiKeyGroup) apiKeyGroup.style.display = provider === 'ollama' ? 'none' : '';
        
        // Pre-fill base URL from model config
        if (filtered.length > 0 && filtered[0].config_file) {
            // Base URL will be loaded from config if available
        }
        
        this.updateVlmWarning();
    }
    
    updateVlmWarning() {
        const warning = document.getElementById('vlm-warning');
        if (!warning) return;
        
        if (this.currentTaskType === 'image_mcq') {
            const modelId = document.getElementById('exp-model-select')?.value || '';
            const isVlm = VLM_MODELS.some(v => modelId.toLowerCase().includes(v));
            warning.style.display = (modelId && !isVlm) ? 'block' : 'none';
        } else {
            warning.style.display = 'none';
        }
    }
    
    async testConnection() {
        const modelId = document.getElementById('exp-model-select')?.value;
        const apiKey = document.getElementById('exp-api-key')?.value;
        const baseUrl = document.getElementById('exp-base-url')?.value;
        const resultEl = document.getElementById('ping-result');
        
        if (!modelId) {
            this.showNotification('error', '请先选择模型');
            return;
        }
        
        if (resultEl) {
            resultEl.style.display = 'block';
            resultEl.innerHTML = '<span class="text-muted">正在测试连接...</span>';
        }
        
        // Set API key for this session if provided
        if (apiKey) {
            const provider = document.getElementById('exp-provider-select')?.value;
            try {
                await API.Models.setApiKey(provider, apiKey);
            } catch (e) {
                console.warn('Failed to set API key:', e);
            }
        }
        
        try {
            const start = Date.now();
            const resp = await API.Models.ping(modelId);
            const latency = Date.now() - start;
            if (resultEl) {
                resultEl.innerHTML = `<span style="color:var(--success-color);font-weight:600;">✓ 连接成功</span> <span class="text-muted">延迟 ${latency}ms</span>`;
            }
        } catch (error) {
            if (resultEl) {
                resultEl.innerHTML = `<span style="color:var(--error-color);font-weight:600;">✗ 连接失败</span> <span class="text-muted">${error.message}</span>`;
            }
        }
    }
    
    // ----- Section 4: RAG Config -----
    onRagToggle(checked) {
        const body = document.getElementById('rag-config-body');
        if (body) body.style.display = checked ? 'block' : 'none';
    }
    
    selectRAGMode(mode, el) {
        document.querySelectorAll('.rag-mode-card').forEach(c => c.classList.remove('selected'));
        el.classList.add('selected');
        
        const oracleOpts = document.getElementById('rag-oracle-options');
        const retrievedOpts = document.getElementById('rag-retrieved-options');
        
        if (oracleOpts) oracleOpts.style.display = mode === 'oracle' ? 'block' : 'none';
        if (retrievedOpts) retrievedOpts.style.display = mode === 'retrieved' ? 'block' : 'none';
        
        if (mode === 'oracle') this.loadOracleFiles();
        if (mode === 'retrieved') this.loadKnowledgeBases();
    }
    
    async loadOracleFiles() {
        // Load JSONL files that contain chunk data from the datasets
        const select = document.getElementById('rag-oracle-file-select');
        if (!select) return;
        
        try {
            const resp = await API.Datasets.list();
            const datasets = resp.datasets || [];
            select.innerHTML = '<option value="">选择含 chunk 的 JSONL 文件...</option>' +
                datasets.map(ds => `<option value="${ds.dataset_id}">${ds.dataset_id} (${ds.total_samples} 条)</option>`).join('');
        } catch (e) {
            console.warn('Failed to load oracle files:', e);
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
    
    // ----- Section 5: Tool Config -----
    async loadToolSchemas() {
        const container = document.getElementById('tool-checkboxes');
        if (!container) return;
        
        try {
            // Try to load tool schemas from backend
            const resp = await fetch('/api/v1/tools');
            if (resp.ok) {
                const data = await resp.json();
                const tools = data.data?.tools || data.tools || [];
                if (tools.length > 0) {
                    container.innerHTML = tools.map(t => `
                        <label><input type="checkbox" name="tools" value="${t.tool_id || t}" checked> <span>${t.tool_id || t}</span></label>
                    `).join('');
                    return;
                }
            }
        } catch (e) {
            // Fallback to defaults
        }
        
        // Fallback: show default tool list
        const defaultTools = ['search_api', 'tool_elec_0001', 'tool_elec_0002', 'tool_elec_0003'];
        container.innerHTML = defaultTools.map(t => `
            <label><input type="checkbox" name="tools" value="${t}" checked> <span>${t}</span></label>
        `).join('');
    }
    
    // ----- Section 7: Metrics auto-fill -----
    renderInferMetrics(taskType) {
        const config = DEFAULT_METRICS_BY_TASK[taskType] || DEFAULT_METRICS_BY_TASK.qa;
        
        // Performance metrics (auto-checked)
        const perfContainer = document.getElementById('infer-perf-metrics');
        if (perfContainer) {
            perfContainer.innerHTML = config.performance.map(m => `
                <label><input type="checkbox" name="infer_metrics" value="${m}" checked> <span>${METRIC_LABELS[m] || m}</span></label>
            `).join('');
        }
        
        // Efficiency metrics (auto-checked)
        const effContainer = document.getElementById('infer-eff-metrics');
        if (effContainer) {
            effContainer.innerHTML = config.efficiency.map(m => `
                <label><input type="checkbox" name="infer_metrics" value="${m}" checked> <span>${METRIC_LABELS[m] || m}</span></label>
            `).join('');
        }
        
        // Optional metrics (unchecked by default)
        const optContainer = document.getElementById('infer-opt-metrics');
        if (optContainer) {
            const optional = [...(config.optional || [])];
            // Add RAG metrics if RAG is enabled
            const ragToggle = document.getElementById('rag-toggle');
            const ragMode = document.querySelector('input[name="rag_mode"]:checked')?.value;
            if (ragToggle?.checked && ragMode === 'retrieved' && config.rag) {
                optional.push(...config.rag);
            }
            optContainer.innerHTML = optional.map(m => `
                <label><input type="checkbox" name="infer_metrics" value="${m}"> <span>${METRIC_LABELS[m] || m}</span></label>
            `).join('');
        }
        
        // Group dimensions
        const groupContainer = document.getElementById('infer-group-dims');
        if (groupContainer) {
            const groups = GROUP_OPTIONS[taskType] || GROUP_OPTIONS.qa;
            groupContainer.innerHTML = groups.map((g, i) => `
                <label><input type="checkbox" name="infer_groups" value="${g}" ${i === 0 ? 'checked' : ''}> <span>${GROUP_LABELS[g] || g}</span></label>
            `).join('');
        }
    }
    
    // =====================================================================
    // Form Submission
    // =====================================================================
    getFormData() {
        const form = document.getElementById('experiment-form');
        if (!form) return {};
        
        const val = (name) => {
            // For 'name' field, use direct getElementById to avoid ambiguity
            if (name === 'name') {
                return document.getElementById('exp-name-input')?.value?.trim() || '';
            }
            return form.querySelector(`[name="${name}"]`)?.value?.trim() || '';
        };
        const intVal = (name, def) => {
            const v = form.querySelector(`[name="${name}"]`)?.value;
            return v ? parseInt(v) : def;
        };
        const floatVal = (name, def) => {
            const v = form.querySelector(`[name="${name}"]`)?.value;
            return v !== '' && v !== undefined ? parseFloat(v) : def;
        };
        
        const strategyCard = document.querySelector('.strategy-card.selected');
        const strategy = strategyCard?.dataset.strategy || 'direct';
        
        // RAG config
        const ragToggle = document.getElementById('rag-toggle');
        const ragEnabled = ragToggle?.checked || false;
        const ragMode = ragEnabled ? (document.querySelector('input[name="rag_mode"]:checked')?.value || 'closed') : 'closed';
        const rag = {
            enabled: ragEnabled && ragMode !== 'closed',
            mode: ragMode,
            kb_name: val('kb_name') || null,
            top_k: intVal('top_k', 3),
            score_threshold: parseFloat(val('score_threshold') || '0') || 0.0,
            oracle_chunks_file: val('oracle_chunks_file') || null,
        };
        
        // Tool config
        const tools = Array.from(form.querySelectorAll('input[name="tools"]:checked')).map(cb => cb.value);
        const toolExecMode = document.querySelector('input[name="tool_exec_mode"]:checked')?.value || 'mock';
        const maxToolSteps = intVal('max_tool_steps', 10);
        
        // Eval metrics and groups
        const metrics = Array.from(form.querySelectorAll('input[name="infer_metrics"]:checked')).map(cb => cb.value);
        const groupBy = Array.from(form.querySelectorAll('input[name="infer_groups"]:checked')).map(cb => cb.value);
        
        // API key / base_url (session-only)
        const apiKey = val('api_key');
        const baseUrl = val('base_url');
        
        return {
            name: val('name'),
            description: val('description'),
            dataset_id: this.currentDatasetId || '',
            split: val('split') || 'test',
            max_samples: intVal('max_samples', null),
            model_id: val('model_id'),
            strategy,
            rag,
            tools: this.currentTaskType === 'api_calling' ? { available_tools: tools, exec_mode: toolExecMode, max_steps: maxToolSteps } : undefined,
            runner: {
                concurrency: intVal('concurrency', 5),
                retry_times: intVal('retry_times', 3),
                seed: intVal('seed', null),
                resume: form.querySelector('[name="resume"]')?.checked ?? true,
                request_timeout_s: intVal('request_timeout_s', 60),
                temperature: floatVal('temperature', 0.0),
                max_tokens: intVal('max_tokens', 2048),
                batch_size: intVal('batch_size', 10),
            },
            eval: { metrics, group_by: groupBy },
            _api_key: apiKey || undefined,
            _base_url: baseUrl || undefined,
        };
    }
    
    async submitForm() {
        const config = this.getFormData();
        if (!config.name) { this.showNotification('error', '请输入实验名称'); return; }
        if (!config.dataset_id) { this.showNotification('error', '请选择数据集'); return; }
        if (!config.model_id) { this.showNotification('error', '请选择模型'); return; }
        
        // Set API key if provided
        if (config._api_key) {
            const provider = document.getElementById('exp-provider-select')?.value;
            if (provider) {
                try {
                    await API.Models.setApiKey(provider, config._api_key);
                    this.showNotification('info', `已设置 ${provider} API Key（仅当前会话有效）`);
                } catch (e) {
                    this.showNotification('error', `设置 API Key 失败: ${e.message}`);
                    return;
                }
            }
        }
        
        await this.createExperiment(config);
    }
    
    async submitAndRun() {
        const config = this.getFormData();
        console.log('[submitAndRun] config:', JSON.stringify({name: config.name, dataset_id: config.dataset_id, model_id: config.model_id, strategy: config.strategy}));
        if (!config.name) { this.showNotification('error', '请输入实验名称'); return; }
        if (!config.dataset_id) { this.showNotification('error', '请选择数据集'); return; }
        if (!config.model_id) { this.showNotification('error', '请选择模型'); return; }
        
        // Set API key if provided
        if (config._api_key) {
            const provider = document.getElementById('exp-provider-select')?.value;
            if (provider) {
                try {
                    await API.Models.setApiKey(provider, config._api_key);
                    this.showNotification('info', `已设置 ${provider} API Key（仅当前会话有效）`);
                } catch (e) {
                    this.showNotification('error', `设置 API Key 失败: ${e.message}`);
                    return;
                }
            }
        }
        
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
    // Prediction Detail Panel (reasoning trace, params, RAG trace)
    // =====================================================================
    async showPredictionDetail(experimentId) {
        // Show detail panel below the experiment list
        let panel = document.getElementById('exp-detail-panel');
        if (!panel) {
            panel = document.createElement('div');
            panel.id = 'exp-detail-panel';
            panel.className = 'card mb-lg';
            if (this.listContainer) this.listContainer.parentNode.insertBefore(panel, this.listContainer.nextSibling);
        }
        panel.innerHTML = `
            <div class="card-header" style="display:flex;justify-content:space-between;align-items:center;">
                <span><i data-lucide="file-search" style="width:16px;height:16px;"></i> 推理详情 — ${experimentId}</span>
                <button class="btn btn-secondary btn-sm" onclick="document.getElementById('exp-detail-panel').remove()">关闭</button>
            </div>
            <div class="card-body" id="exp-detail-body">
                <div style="padding:20px;text-align:center;color:var(--text-muted);">加载中...</div>
            </div>`;
        if (window.lucide) lucide.createIcons();

        try {
            const result = await API.Results.getPredictions(experimentId, { offset: 0, limit: 50 });
            const predictions = result.items || result.predictions || [];
            const body = document.getElementById('exp-detail-body');
            if (!body) return;

            if (predictions.length === 0) {
                body.innerHTML = '<div style="padding:20px;color:var(--text-muted);">暂无推理结果</div>';
                return;
            }

            body.innerHTML = predictions.map((p, idx) => {
                const sid = p.sample_id || '-';
                const trace = p.reasoning_trace;
                const hasTrace = trace && (Array.isArray(trace) ? trace.length > 0 : (typeof trace === 'string' && trace.trim()));
                const rawOutput = p.raw_output || '';
                const hasRag = p.rag_context && p.rag_context.mode;
                const latency = p.usage?.latency_ms || 0;
                const tokens = p.usage?.total_tokens || 0;
                // Count reasoning steps from trace
                let stepCount = 0;
                if (hasTrace) {
                    if (Array.isArray(trace)) {
                        stepCount = trace.length;
                    } else if (typeof trace === 'string') {
                        stepCount = (trace.match(/^(Step|Thought|\d+[\.\)\:])/gm) || []).length || (trace.split('\n\n').filter(s => s.trim()).length);
                    }
                }
                const toolCallCount = Array.isArray(p.tool_trace) ? p.tool_trace.length : 0;

                let ragHtml = '';
                if (hasRag) {
                    const rc = p.rag_context;
                    const chunks = (rc.retrieved_chunks || []).map((c, ci) =>
                        `<div style="margin-bottom:8px;padding:8px;background:var(--bg-primary);border-radius:4px;border:1px solid var(--border-color);">
                            <div style="display:flex;justify-content:space-between;font-size:11px;color:var(--text-muted);margin-bottom:4px;">
                                <span><strong>${this._escHtml(c.chunk_id || 'chunk_' + ci)}</strong></span>
                                <span>score: ${c.score != null ? c.score.toFixed(4) : '-'}${c.topic ? ' | topic: ' + this._escHtml(c.topic) : ''}</span>
                            </div>
                            <div style="font-size:12px;line-height:1.5;color:var(--text-secondary);max-height:120px;overflow-y:auto;">${this._escHtml(c.text || '').substring(0, 500)}</div>
                        </div>`
                    ).join('');
                    ragHtml = `
                        <div style="margin-top:6px;">
                            <div style="cursor:pointer;font-size:12px;color:var(--primary-color);font-weight:600;"
                                 onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'; this.querySelector('.arrow').textContent = this.nextElementSibling.style.display === 'none' ? '▶' : '▼';">
                                <span class="arrow">▶</span> RAG 轨迹 (mode: ${this._escHtml(rc.mode)}${rc.retrieval_latency_ms ? ', ' + rc.retrieval_latency_ms.toFixed(0) + 'ms' : ''}, ${(rc.retrieved_chunks || []).length} chunks)
                            </div>
                            <div style="display:none;margin-top:6px;">
                                ${rc.query_text ? '<div style="font-size:12px;margin-bottom:6px;"><strong>Query:</strong> ' + this._escHtml(rc.query_text) + '</div>' : ''}
                                ${rc.source_qa_ids ? '<div style="font-size:12px;margin-bottom:6px;"><strong>Source QA IDs:</strong> ' + this._escHtml(JSON.stringify(rc.source_qa_ids)) + '</div>' : ''}
                                ${chunks}
                            </div>
                        </div>`;
                }

                return `
                    <div style="border:1px solid var(--border-color);border-radius:8px;padding:12px;margin-bottom:10px;">
                        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                            <span style="font-family:monospace;font-size:13px;font-weight:600;">${this._escHtml(sid)}</span>
                            <span style="font-size:12px;color:var(--text-muted);">
                                ${p.model ? 'Model: ' + this._escHtml(p.model) : ''} ${p.strategy ? '| Strategy: ' + this._escHtml(p.strategy) : ''}
                                | ${tokens} tokens | ${latency}ms
                                ${stepCount > 0 ? ' | <span style="color:var(--primary-color);">' + stepCount + ' steps</span>' : ''}
                                ${toolCallCount > 0 ? ' | <span style="color:#8B5CF6;">' + toolCallCount + ' tool calls</span>' : ''}
                                ${p.correct === true ? ' <span style="color:var(--success-color);">✓</span>' : p.correct === false ? ' <span style="color:var(--error-color);">✗</span>' : ''}
                            </span>
                        </div>
                        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:12px;margin-bottom:6px;">
                            <div><strong>预测:</strong> ${this._escHtml(p.parsed_answer || '-')}</div>
                            <div><strong>正确答案:</strong> ${this._escHtml(p.ground_truth || '-')}</div>
                        </div>
                        ${hasTrace ? `
                            <div style="cursor:pointer;font-size:12px;color:var(--primary-color);font-weight:600;"
                                 onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'; this.querySelector('.arrow').textContent = this.nextElementSibling.style.display === 'none' ? '▶' : '▼';">
                                <span class="arrow">▶</span> 思维链 / Reasoning Trace (${stepCount} steps)
                            </div>
                            <div style="display:none;margin-top:6px;max-height:400px;overflow-y:auto;">
                                ${Array.isArray(trace) ? trace.map(s => `
                                    <div style="margin-bottom:8px;padding:8px;background:var(--bg-secondary);border-radius:6px;border-left:3px solid var(--primary-color);">
                                        <div style="font-size:11px;color:var(--primary-color);font-weight:600;margin-bottom:4px;">
                                            Step ${s.step || '?'}${s.type ? ' <span style="color:var(--text-muted);font-weight:400;">(' + this._escHtml(s.type) + ')</span>' : ''}
                                        </div>
                                        <div style="font-size:12px;line-height:1.5;color:var(--text-secondary);white-space:pre-wrap;word-break:break-word;">${this._escHtml(s.content || s.thought || s.output || JSON.stringify(s))}</div>
                                    </div>
                                `).join('') : `<pre style="padding:8px;background:var(--bg-secondary);border-radius:6px;font-size:12px;line-height:1.5;white-space:pre-wrap;word-break:break-word;color:var(--text-secondary);">${this._escHtml(typeof trace === 'string' ? trace : JSON.stringify(trace, null, 2))}</pre>`}
                            </div>
                        ` : ''}
                        ${rawOutput ? `
                            <div style="cursor:pointer;font-size:12px;color:var(--text-muted);margin-top:4px;"
                                 onclick="this.nextElementSibling.style.display = this.nextElementSibling.style.display === 'none' ? 'block' : 'none'; this.querySelector('.arrow').textContent = this.nextElementSibling.style.display === 'none' ? '▶' : '▼';">
                                <span class="arrow">▶</span> 原始输出
                            </div>
                            <pre style="display:none;margin-top:6px;padding:8px;background:var(--bg-secondary);border-radius:6px;font-size:12px;line-height:1.5;white-space:pre-wrap;word-break:break-word;max-height:200px;overflow-y:auto;color:var(--text-secondary);">${this._escHtml(rawOutput)}</pre>
                        ` : ''}
                        ${ragHtml}
                    </div>`;
            }).join('');
        } catch (err) {
            const body = document.getElementById('exp-detail-body');
            if (body) body.innerHTML = `<div style="color:var(--error-color);padding:12px;">加载失败: ${err.message}</div>`;
        }
    }

    _escHtml(str) {
        if (!str) return '';
        return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
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
        
        this.loadEvalExperiments().then(() => {
            const select = document.getElementById('eval-experiment-select');
            if (select) {
                select.value = experimentId;
                this.onEvalExperimentChange(experimentId);
            }
        });
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
            <label><input type="checkbox" name="eval_metrics" value="${m}" ${defaultChecked.has(m) ? 'checked' : ''}> <span>${METRIC_LABELS[m] || m}</span></label>
        `).join('');
    }
    
    renderEvalGroups(taskType) {
        const container = document.getElementById('eval-groups-checkboxes');
        if (!container) return;
        
        const groups = GROUP_OPTIONS[taskType] || GROUP_OPTIONS.qa;
        
        container.innerHTML = groups.map((g, i) => `
            <label><input type="checkbox" name="eval_groups" value="${g}" ${i < 2 ? 'checked' : ''}> <span>${GROUP_LABELS[g] || g}</span></label>
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
