/**
 * Results Visualization Module - v2.0
 * 
 * Task-type aware metrics rendering with dimension-separated charts.
 * Supports: qa, text_exam, image_mcq, api_calling
 * 
 * Regions:
 * A - Experiment meta info
 * B - Performance metric cards (task-type specific)
 * C - Efficiency metric cards (universal)
 * D - Charts (dimension-separated, task-type specific)
 * E - Group statistics tabs
 * F - Sample browser (collapsible, paginated)
 */

class ResultsVisualizer {
    constructor(options = {}) {
        this.metaContainer = document.getElementById('results-meta');
        this.perfContainer = document.getElementById('results-perf-cards');
        this.effContainer = document.getElementById('results-eff-cards');
        this.chartsContainer = document.getElementById('results-charts');
        this.groupContainer = document.getElementById('results-groups');
        this.sampleContainer = document.getElementById('results-samples');
        this.compareContainer = document.getElementById('results-compare');
        
        this.charts = {};
        this.currentExperimentId = null;
        this.currentMetrics = null;
        this.currentTaskType = null;
        this.compareMode = false;
        this.compareList = [];
        
        // Sample browser state
        this.sampleOffset = 0;
        this.sampleLimit = 20;
        this.sampleFilters = {};
        
        this.init();
    }
    
    init() {
        if (typeof Chart === 'undefined') {
            this.loadChartJS();
        }
    }
    
    loadChartJS() {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js';
        script.onload = () => console.log('Chart.js loaded');
        document.head.appendChild(script);
    }
    
    // =========================================================================
    // Meta fields that should NOT appear as metric cards
    // =========================================================================
    static META_FIELDS = new Set([
        'experiment_id', 'model', 'strategy', 'dataset',
        'total_samples', 'valid_samples', 'evaluated_at',
        'model_id', 'dataset_id', 'task_type', 'name',
        'status', 'created_at', 'updated_at', 'config',
        'by_difficulty', 'by_topic', 'by_category',
        'by_call_type', 'by_question_type',
        'latency_stats', 'token_stats', 'cost_estimate',
        'option_bias', 'exact_match', 'f1_score', 'bleu', 'rouge_l',
    ]);
    
    // =========================================================================
    // Performance metric card configs per task type
    // =========================================================================
    static METRIC_CARDS_BY_TASK = {
        qa: [
            { key: 'exact_match',  altKeys: ['accuracy'], label: '精确匹配',  icon: 'target',     color: '#22C55E', fmt: 'pct' },
            { key: 'f1_score',     altKeys: ['avg_f1'],   label: 'F1 分数',   icon: 'activity',   color: '#3B82F6', fmt: 'pct' },
            { key: 'rouge_l',      altKeys: ['avg_rouge_l_f1'], label: 'ROUGE-L', icon: 'align-left', color: '#8B5CF6', fmt: 'pct' },
            { key: 'bleu',         altKeys: ['avg_bleu'], label: 'BLEU',      icon: 'hash',       color: '#F59E0B', fmt: 'pct' },
        ],
        text_exam: [
            { key: 'choice_accuracy', altKeys: ['accuracy'], label: '选择题准确率', icon: 'check-circle', color: '#22C55E', fmt: 'pct' },
            { key: 'win_rate',        altKeys: [],           label: 'Win Rate',    icon: 'trophy',       color: '#F59E0B', fmt: 'pct' },
        ],
        image_mcq: [
            { key: 'choice_accuracy',      altKeys: ['accuracy'], label: '选择题准确率',    icon: 'check-circle', color: '#22C55E', fmt: 'pct' },
            { key: 'grounding_error_rate', altKeys: [],           label: 'Grounding错误率', icon: 'eye-off',      color: '#EF4444', fmt: 'pct' },
            { key: 'win_rate',             altKeys: [],           label: 'Win Rate',       icon: 'trophy',       color: '#F59E0B', fmt: 'pct' },
        ],
        api_calling: [
            { key: 'tool_selection_accuracy',  altKeys: ['accuracy'], label: '工具选择准确率', icon: 'wrench',       color: '#3B82F6', fmt: 'pct' },
            { key: 'parameter_accuracy',       altKeys: ['accuracy'], label: '参数准确率',     icon: 'sliders',      color: '#22C55E', fmt: 'pct' },
            { key: 'end_to_end_success_rate',  altKeys: ['rate'],     label: '端到端成功率',   icon: 'check-circle', color: '#8B5CF6', fmt: 'pct' },
            { key: 'invalid_call_rate',        altKeys: ['rate'],     label: '无效调用率',     icon: 'x-circle',     color: '#EF4444', fmt: 'pct' },
        ],
    };
    
    // =========================================================================
    // Efficiency metric card configs (universal)
    // =========================================================================
    static EFFICIENCY_CARDS = [
        { key: 'avg_latency_ms',       altKeys: ['avg_ms'], label: '平均延迟',     icon: 'clock',       fmt: 'ms',  source: 'latency_stats' },
        { key: 'tokens_per_sec',       altKeys: [],         label: 'Token/s',     icon: 'zap',         fmt: 'float', source: 'overall' },
        { key: 'avg_completion_tokens', altKeys: [],         label: '平均输出Token', icon: 'file-text',   fmt: 'int', source: 'overall' },
        { key: 'total_cost_usd',       altKeys: [],         label: '总成本',       icon: 'dollar-sign', fmt: 'usd', source: 'cost_estimate' },
    ];
    
    // =========================================================================
    // Group dimension configs
    // =========================================================================
    static GROUP_DIMS = {
        by_difficulty:    { label: '按难度',     tasks: ['qa','text_exam','image_mcq','api_calling'] },
        by_topic:         { label: '按主题',     tasks: ['qa','text_exam'] },
        by_question_type: { label: '按题型',     tasks: ['text_exam','image_mcq'] },
        by_category:      { label: '按设备类别', tasks: ['api_calling'] },
        by_call_type:     { label: '按调用类型', tasks: ['api_calling'] },
    };
    
    // =========================================================================
    // Main entry point
    // =========================================================================
    async loadMetrics(experimentId) {
        this.currentExperimentId = experimentId;
        this.showSkeleton();
        
        try {
            const [metricsResp, expInfo] = await Promise.all([
                API.getMetrics(experimentId),
                API.Experiments.get(experimentId).catch(() => null),
            ]);
            
            this.currentMetrics = metricsResp;
            
            // Infer task type
            const taskType = this.inferTaskType(metricsResp, expInfo);
            this.currentTaskType = taskType;
            
            this.renderExperimentMeta(metricsResp, expInfo, taskType);   // A
            this.renderPerformanceCards(metricsResp, taskType);           // B
            this.renderEfficiencyCards(metricsResp);                      // C
            this.renderTaskCharts(metricsResp, taskType);                 // D
            this.renderGroupTabs(metricsResp, taskType);                  // E
            this.initSampleBrowser(experimentId);                         // F
            
            if (window.lucide) lucide.createIcons();
            
            return metricsResp;
        } catch (error) {
            this.showError(`加载指标失败: ${error.message}`);
            throw error;
        }
    }
    
    inferTaskType(metrics, expInfo) {
        // Try from experiment info first
        if (expInfo) {
            const dsId = expInfo.dataset_id || '';
            if (dsId.includes('exam')) return 'text_exam';
            if (dsId.includes('mcq') || dsId.includes('image')) return 'image_mcq';
            if (dsId.includes('agent') || dsId.includes('api') || dsId.includes('calling')) return 'api_calling';
        }
        
        // Infer from metrics keys
        const overall = metrics.overall || {};
        if (overall.tool_selection_accuracy !== undefined || overall.end_to_end_success_rate !== undefined) return 'api_calling';
        if (overall.choice_accuracy !== undefined) {
            if (metrics.grounding_error_rate !== undefined) return 'image_mcq';
            return 'text_exam';
        }
        return 'qa';
    }
    
    // =========================================================================
    // Region A: Experiment Meta Info
    // =========================================================================
    renderExperimentMeta(metrics, expInfo, taskType) {
        if (!this.metaContainer) return;
        
        const taskLabels = { qa: '文本问答', text_exam: '选择题', image_mcq: '图像选择题', api_calling: 'API调用' };
        const strategyLabels = { direct: 'Direct', cot: 'CoT', long_cot: 'Long CoT', tot: 'ToT', react: 'ReAct', self_refine: 'Self Refine' };
        
        const model = metrics.model || expInfo?.model_id || '-';
        const strategy = metrics.strategy || expInfo?.strategy || '-';
        const dataset = metrics.dataset || expInfo?.dataset_id || '-';
        const datasetName = dataset.split('/').pop().replace('.jsonl', '');
        const total = metrics.total_samples || 0;
        const valid = metrics.valid_samples || metrics.overall?.valid_samples || 0;
        const evalAt = metrics.evaluated_at ? new Date(metrics.evaluated_at).toLocaleString('zh-CN') : '-';
        
        this.metaContainer.innerHTML = `
            <div class="results-meta-card">
                <div class="results-meta-header">
                    <div class="results-meta-title">${expInfo?.name || metrics.experiment_id}</div>
                    <div class="results-meta-badges">
                        <span class="badge badge-info">${taskLabels[taskType] || taskType}</span>
                        <span class="badge badge-primary">${strategyLabels[strategy] || strategy}</span>
                    </div>
                </div>
                <div class="results-meta-details">
                    <div class="results-meta-item"><span class="results-meta-label">数据集</span><span>${datasetName}</span></div>
                    <div class="results-meta-item"><span class="results-meta-label">模型</span><span>${model}</span></div>
                    <div class="results-meta-item"><span class="results-meta-label">样本</span><span>${valid} 有效 / ${total} 总计</span></div>
                    <div class="results-meta-item"><span class="results-meta-label">完成时间</span><span>${evalAt}</span></div>
                </div>
            </div>
        `;
    }
    
    // =========================================================================
    // Metric value extractor - handles nested registry wrapper output
    // e.g. metrics.f1_score = {metric: "f1_score", avg_f1: 0.85, total: 100}
    //      metrics.overall.f1_score = 0.85 (if flattened)
    // =========================================================================
    extractMetricValue(metrics, cardKey, altKeys = []) {
        const overall = metrics.overall || {};
        
        // 1. Try overall[key] directly (flat numeric)
        if (overall[cardKey] !== undefined && typeof overall[cardKey] === 'number') {
            return overall[cardKey];
        }
        
        // 2. Try top-level metrics[key] as nested dict from registry wrapper
        const nested = metrics[cardKey];
        if (nested && typeof nested === 'object') {
            // Look for altKeys inside the nested dict
            for (const ak of altKeys) {
                if (nested[ak] !== undefined && typeof nested[ak] === 'number') return nested[ak];
            }
            // Common fallback keys inside wrapper dicts
            for (const fk of ['accuracy', 'rate', 'avg', 'value', 'score']) {
                if (nested[fk] !== undefined && typeof nested[fk] === 'number') return nested[fk];
            }
        }
        
        // 3. Try altKeys directly in overall
        for (const ak of altKeys) {
            if (overall[ak] !== undefined && typeof overall[ak] === 'number') return overall[ak];
        }
        
        return undefined;
    }
    
    // =========================================================================
    // Region B: Performance Metric Cards (task-type aware)
    // =========================================================================
    renderPerformanceCards(metrics, taskType) {
        if (!this.perfContainer) return;
        
        const cards = ResultsVisualizer.METRIC_CARDS_BY_TASK[taskType] || ResultsVisualizer.METRIC_CARDS_BY_TASK.qa;
        
        const html = cards.map(card => {
            const value = this.extractMetricValue(metrics, card.key, card.altKeys || []);
            const displayValue = value !== undefined ? this.formatValue(value, card.fmt) : '-';
            const rawDetail = this.getMetricDetail(metrics, card.key);
            
            return `
                <div class="perf-metric-card">
                    <div class="perf-metric-icon" style="background: ${card.color}15; color: ${card.color};">
                        <i data-lucide="${card.icon}" style="width:20px;height:20px;"></i>
                    </div>
                    <div class="perf-metric-body">
                        <div class="perf-metric-label">${card.label}</div>
                        <div class="perf-metric-value" style="color: ${card.color};">${displayValue}</div>
                        ${rawDetail ? `<div class="perf-metric-detail">${rawDetail}</div>` : ''}
                    </div>
                </div>
            `;
        }).join('');
        
        this.perfContainer.innerHTML = `<div class="perf-cards-grid">${html}</div>`;
    }
    
    getMetricDetail(metrics, key) {
        // Try to extract total from nested registry wrapper or overall
        const nested = metrics[key];
        const overall = metrics.overall || {};
        const total = (nested && nested.total) || overall.total_samples || metrics.total_samples || 0;
        const value = this.extractMetricValue(metrics, key, []);
        if (value === undefined || total === 0) return '';
        
        if (['exact_match', 'choice_accuracy', 'tool_selection_accuracy',
             'parameter_accuracy', 'end_to_end_success_rate'].includes(key)) {
            // Nested wrapper may have 'correct' field
            const correct = (nested && nested.correct !== undefined) ? nested.correct : Math.round(value * total);
            return `${correct}/${total} 样本`;
        }
        return '';
    }
    
    // =========================================================================
    // Region C: Efficiency Metric Cards (universal)
    // =========================================================================
    renderEfficiencyCards(metrics) {
        if (!this.effContainer) return;
        
        const overall = metrics.overall || {};
        const cards = ResultsVisualizer.EFFICIENCY_CARDS;
        
        const html = cards.map(card => {
            // Look up value from the appropriate source section
            let value;
            const src = card.source;
            if (src && src !== 'overall' && metrics[src] && typeof metrics[src] === 'object') {
                value = metrics[src][card.key];
                if (value === undefined) {
                    for (const ak of (card.altKeys || [])) {
                        if (metrics[src][ak] !== undefined) { value = metrics[src][ak]; break; }
                    }
                }
            }
            if (value === undefined) value = overall[card.key];
            if (value === undefined) {
                for (const ak of (card.altKeys || [])) {
                    if (overall[ak] !== undefined) { value = overall[ak]; break; }
                }
            }
            const displayValue = value !== undefined ? this.formatValue(value, card.fmt) : '-';
            
            return `
                <div class="eff-metric-card">
                    <div class="eff-metric-icon">
                        <i data-lucide="${card.icon}" style="width:16px;height:16px;"></i>
                    </div>
                    <div class="eff-metric-body">
                        <div class="eff-metric-value">${displayValue}</div>
                        <div class="eff-metric-label">${card.label}</div>
                    </div>
                </div>
            `;
        }).join('');
        
        this.effContainer.innerHTML = `<div class="eff-cards-grid">${html}</div>`;
    }
    
    // =========================================================================
    // Region D: Charts (dimension-separated, task-type specific)
    // =========================================================================
    renderTaskCharts(metrics, taskType) {
        if (!this.chartsContainer || typeof Chart === 'undefined') return;
        
        // Destroy existing charts
        Object.values(this.charts).forEach(c => c.destroy());
        this.charts = {};
        this.chartsContainer.innerHTML = '';
        
        const overall = metrics.overall || {};
        
        // Performance chart (0-100% axis)
        const perfData = this.getPerformanceChartData(metrics, taskType);
        if (perfData.labels.length > 0) {
            this.createHorizontalBar('perf-chart', '性能指标对比', perfData);
        }
        
        // Latency chart (ms axis, separate from performance)
        const latencyData = this.getLatencyChartData(metrics);
        if (latencyData.labels.length > 0) {
            this.createVerticalBar('latency-chart', '延迟分布 (ms)', latencyData, 'ms');
        }
        
        // Task-specific charts
        if ((taskType === 'text_exam' || taskType === 'image_mcq') && metrics.option_bias) {
            this.createOptionBiasChart('bias-chart', metrics.option_bias);
        }
        
        if (taskType === 'api_calling' && metrics.by_call_type) {
            this.createGroupBarChart('calltype-chart', '按调用类型成功率', metrics.by_call_type);
        }
    }
    
    getPerformanceChartData(metrics, taskType) {
        const cards = ResultsVisualizer.METRIC_CARDS_BY_TASK[taskType] || ResultsVisualizer.METRIC_CARDS_BY_TASK.qa;
        
        const labels = [];
        const values = [];
        const colors = [];
        
        for (const card of cards) {
            const v = this.extractMetricValue(metrics, card.key, card.altKeys || []);
            if (v !== undefined && typeof v === 'number') {
                labels.push(card.label);
                values.push(v * 100);
                colors.push(card.color);
            }
        }
        
        return { labels, values, colors };
    }
    
    getLatencyChartData(metrics) {
        // latency_stats can be top-level or nested inside overall
        const latency = metrics.latency_stats || metrics.overall?.latency_stats || {};
        // Also try flattened keys from EfficiencyEvaluator output
        const overall = metrics.overall || {};
        const labels = [];
        const values = [];
        
        const avgMs = latency.avg_ms || latency.avg_latency_ms || overall.avg_latency_ms;
        const p50Ms = latency.p50_ms || latency.p50_latency_ms || overall.p50_latency_ms;
        const p95Ms = latency.p95_ms || latency.p95_latency_ms || overall.p95_latency_ms;
        
        if (avgMs) { labels.push('平均延迟'); values.push(avgMs); }
        if (p50Ms) { labels.push('P50延迟'); values.push(p50Ms); }
        if (p95Ms) { labels.push('P95延迟'); values.push(p95Ms); }
        if (latency.min_ms) { labels.push('最小延迟'); values.push(latency.min_ms); }
        if (latency.max_ms) { labels.push('最大延迟'); values.push(latency.max_ms); }
        
        return { labels, values };
    }
    
    createHorizontalBar(id, title, data) {
        const wrapper = this.createChartWrapper(id, title);
        const ctx = wrapper.querySelector('canvas').getContext('2d');
        
        this.charts[id] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: data.colors || data.labels.map(() => 'rgba(99,102,241,0.7)'),
                    borderColor: data.colors || data.labels.map(() => 'rgba(99,102,241,1)'),
                    borderWidth: 1,
                    borderRadius: 4,
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { beginAtZero: true, max: 100, ticks: { callback: v => v + '%' } },
                    y: { grid: { display: false } }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: ctx => `${ctx.raw.toFixed(1)}%` } }
                }
            }
        });
    }
    
    createVerticalBar(id, title, data, unit = '') {
        const wrapper = this.createChartWrapper(id, title);
        const ctx = wrapper.querySelector('canvas').getContext('2d');
        
        this.charts[id] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: 'rgba(249,115,22,0.7)',
                    borderColor: 'rgba(249,115,22,1)',
                    borderWidth: 1,
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, ticks: { callback: v => v + (unit ? ' ' + unit : '') } },
                    x: { grid: { display: false } }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: ctx => `${ctx.raw.toFixed(0)} ${unit}` } }
                }
            }
        });
    }
    
    createOptionBiasChart(id, optionBias) {
        if (!optionBias) return;
        
        // option_bias can be distribution directly or nested
        const dist = optionBias.distribution || optionBias;
        if (!dist || typeof dist !== 'object') return;
        
        const labels = Object.keys(dist);
        const values = Object.values(dist).map(v => typeof v === 'number' ? v * 100 : 0);
        const idealLine = 100 / labels.length;
        
        const wrapper = this.createChartWrapper(id, '选项偏置分布');
        const ctx = wrapper.querySelector('canvas').getContext('2d');
        
        const colors = ['#3B82F6', '#22C55E', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899'];
        
        this.charts[id] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: '选择比例',
                    data: values,
                    backgroundColor: labels.map((_, i) => colors[i % colors.length] + 'B3'),
                    borderColor: labels.map((_, i) => colors[i % colors.length]),
                    borderWidth: 1,
                    borderRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: { beginAtZero: true, max: 100, ticks: { callback: v => v + '%' } },
                    x: { grid: { display: false } }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: ctx => `${ctx.raw.toFixed(1)}%` } },
                    annotation: {
                        annotations: {
                            idealLine: {
                                type: 'line', yMin: idealLine, yMax: idealLine,
                                borderColor: '#94A3B8', borderDash: [5, 5], borderWidth: 1,
                                label: { content: '理想值', enabled: true }
                            }
                        }
                    }
                }
            }
        });
    }
    
    createGroupBarChart(id, title, groupData) {
        if (!groupData || typeof groupData !== 'object') return;
        
        // groupData can be { key: { accuracy, count, ... }, ... } or array
        let labels, values;
        if (Array.isArray(groupData)) {
            labels = groupData.map(g => g.group_name || g.key || '');
            values = groupData.map(g => (g.accuracy || 0) * 100);
        } else {
            labels = Object.keys(groupData);
            values = Object.values(groupData).map(v => {
                if (typeof v === 'object' && v.accuracy !== undefined) return v.accuracy * 100;
                if (typeof v === 'number') return v * 100;
                return 0;
            });
        }
        
        if (labels.length === 0) return;
        
        const wrapper = this.createChartWrapper(id, title);
        const ctx = wrapper.querySelector('canvas').getContext('2d');
        
        this.charts[id] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels,
                datasets: [{
                    data: values,
                    backgroundColor: 'rgba(99,102,241,0.7)',
                    borderColor: 'rgba(99,102,241,1)',
                    borderWidth: 1,
                    borderRadius: 4,
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: { beginAtZero: true, max: 100, ticks: { callback: v => v + '%' } },
                    y: { grid: { display: false } }
                },
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: ctx => `${ctx.raw.toFixed(1)}%` } }
                }
            }
        });
    }
    
    createChartWrapper(id, title) {
        const wrapper = document.createElement('div');
        wrapper.className = 'results-chart-card';
        wrapper.innerHTML = `
            <div class="results-chart-title">${title}</div>
            <div class="results-chart-body">
                <canvas id="${id}"></canvas>
            </div>
        `;
        this.chartsContainer.appendChild(wrapper);
        return wrapper;
    }
    
    // =========================================================================
    // Region E: Group Statistics Tabs
    // =========================================================================
    renderGroupTabs(metrics, taskType) {
        if (!this.groupContainer) return;
        
        const dims = ResultsVisualizer.GROUP_DIMS;
        const available = Object.entries(dims)
            .filter(([key, cfg]) => cfg.tasks.includes(taskType) && metrics[key] && this.hasGroupData(metrics[key]));
        
        if (available.length === 0) {
            this.groupContainer.innerHTML = '';
            return;
        }
        
        const tabsHtml = available.map(([key, cfg], i) => 
            `<button class="group-tab-btn${i === 0 ? ' active' : ''}" data-group="${key}">${cfg.label}</button>`
        ).join('');
        
        const panelsHtml = available.map(([key, cfg], i) =>
            `<div class="group-tab-panel${i === 0 ? ' active' : ''}" data-group="${key}">
                ${this.renderGroupTable(metrics[key])}
            </div>`
        ).join('');
        
        this.groupContainer.innerHTML = `
            <div class="results-section-title"><i data-lucide="layers" style="width:18px;height:18px;"></i> 分组统计</div>
            <div class="group-tabs">${tabsHtml}</div>
            <div class="group-panels">${panelsHtml}</div>
        `;
        
        // Tab switching
        this.groupContainer.querySelectorAll('.group-tab-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.groupContainer.querySelectorAll('.group-tab-btn').forEach(b => b.classList.remove('active'));
                this.groupContainer.querySelectorAll('.group-tab-panel').forEach(p => p.classList.remove('active'));
                btn.classList.add('active');
                this.groupContainer.querySelector(`.group-tab-panel[data-group="${btn.dataset.group}"]`)?.classList.add('active');
            });
        });
    }
    
    hasGroupData(data) {
        if (Array.isArray(data)) return data.length > 0;
        if (typeof data === 'object') return Object.keys(data).length > 0;
        return false;
    }
    
    renderGroupTable(groupData) {
        let rows;
        if (Array.isArray(groupData)) {
            rows = groupData;
        } else if (typeof groupData === 'object') {
            rows = Object.entries(groupData).map(([key, val]) => {
                if (typeof val === 'object') return { group_name: key, ...val };
                return { group_name: key, accuracy: val };
            });
        } else {
            return '<div style="color:var(--text-muted);padding:12px;">暂无数据</div>';
        }
        
        if (rows.length === 0) return '<div style="color:var(--text-muted);padding:12px;">暂无数据</div>';
        
        return `
            <table class="table">
                <thead>
                    <tr>
                        <th>分组</th>
                        <th>样本数</th>
                        <th>准确率</th>
                        <th>平均延迟</th>
                        <th>平均Token</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.map(r => `
                        <tr>
                            <td style="font-weight:600;">${r.group_name || r.key || '-'}</td>
                            <td>${r.count || r.total || '-'}</td>
                            <td>${r.accuracy !== undefined ? (r.accuracy * 100).toFixed(1) + '%' : '-'}</td>
                            <td>${r.avg_latency_ms !== undefined ? r.avg_latency_ms.toFixed(0) + ' ms' : '-'}</td>
                            <td>${r.avg_tokens !== undefined ? r.avg_tokens.toFixed(0) : '-'}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }
    
    // =========================================================================
    // Region F: Sample Browser (collapsible, paginated)
    // =========================================================================
    initSampleBrowser(experimentId) {
        if (!this.sampleContainer) return;
        
        this.sampleOffset = 0;
        this.sampleFilters = {};
        
        this.sampleContainer.innerHTML = `
            <div class="results-section-title sample-toggle" style="cursor:pointer;">
                <i data-lucide="chevron-down" style="width:18px;height:18px;"></i> 查看样本详情
            </div>
            <div class="sample-browser" style="display:none;">
                <div class="sample-filters">
                    <button class="sample-filter-btn active" data-filter="all">全部</button>
                    <button class="sample-filter-btn" data-filter="correct">正确 ✓</button>
                    <button class="sample-filter-btn" data-filter="wrong">错误 ✗</button>
                </div>
                <div class="sample-table-wrapper">
                    <div style="color:var(--text-muted);padding:20px;text-align:center;">点击上方按钮加载样本数据</div>
                </div>
                <div class="sample-pagination"></div>
            </div>
        `;
        
        // Toggle
        const toggle = this.sampleContainer.querySelector('.sample-toggle');
        const browser = this.sampleContainer.querySelector('.sample-browser');
        toggle.addEventListener('click', () => {
            const isOpen = browser.style.display !== 'none';
            browser.style.display = isOpen ? 'none' : 'block';
            toggle.querySelector('i')?.setAttribute('data-lucide', isOpen ? 'chevron-down' : 'chevron-up');
            if (window.lucide) lucide.createIcons();
            if (!isOpen) this.loadSamples(experimentId);
        });
        
        // Filter buttons
        this.sampleContainer.querySelectorAll('.sample-filter-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                this.sampleContainer.querySelectorAll('.sample-filter-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                
                const filter = btn.dataset.filter;
                this.sampleFilters = {};
                if (filter === 'correct') this.sampleFilters.correct = true;
                if (filter === 'wrong') this.sampleFilters.correct = false;
                this.sampleOffset = 0;
                this.loadSamples(experimentId);
            });
        });
    }
    
    async loadSamples(experimentId) {
        const wrapper = this.sampleContainer.querySelector('.sample-table-wrapper');
        if (!wrapper) return;
        
        wrapper.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">加载中...</div>';
        
        try {
            const params = {
                offset: this.sampleOffset,
                limit: this.sampleLimit,
                ...this.sampleFilters,
            };
            const result = await API.Results.getPredictions(experimentId, params);
            const predictions = result.items || result.predictions || [];
            const total = result.total || predictions.length;
            
            if (predictions.length === 0) {
                wrapper.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">暂无数据</div>';
                return;
            }
            
            wrapper.innerHTML = `
                <table class="table">
                    <thead>
                        <tr>
                            <th>Sample ID</th>
                            <th>预测答案</th>
                            <th>正确答案</th>
                            <th>结果</th>
                            <th>延迟</th>
                            <th>Token</th>
                            <th>思维链</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${predictions.map((p, idx) => {
                            const correct = p.correct;
                            const latency = p.usage?.latency_ms || p.latency_ms;
                            const tokens = p.usage?.total_tokens || p.total_tokens;
                            const hasTrace = p.reasoning_trace && (typeof p.reasoning_trace === 'string' ? p.reasoning_trace.trim() : true);
                            const traceText = hasTrace ? (typeof p.reasoning_trace === 'string' ? p.reasoning_trace : JSON.stringify(p.reasoning_trace, null, 2)) : '';
                            const traceId = `trace-row-${idx}`;
                            return `
                                <tr>
                                    <td style="font-family:monospace;font-size:12px;">${p.sample_id || '-'}</td>
                                    <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${this.escapeHtml(p.parsed_answer || '')}">${this.escapeHtml(p.parsed_answer || '-')}</td>
                                    <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" title="${this.escapeHtml(p.answer || p.reference_answer || '')}">${this.escapeHtml(p.answer || p.reference_answer || '-')}</td>
                                    <td>${correct === true ? '<span style="color:var(--success-color);">✓</span>' : correct === false ? '<span style="color:var(--error-color);">✗</span>' : '-'}</td>
                                    <td>${latency ? latency.toFixed(0) + 'ms' : '-'}</td>
                                    <td>${tokens || '-'}</td>
                                    <td>${hasTrace ? `<button class="btn btn-secondary btn-sm" style="padding:2px 8px;font-size:11px;" onclick="document.getElementById('${traceId}').style.display = document.getElementById('${traceId}').style.display === 'none' ? 'table-row' : 'none'">查看</button>` : '-'}</td>
                                </tr>
                                ${hasTrace ? `<tr id="${traceId}" style="display:none;"><td colspan="7" style="padding:12px;background:var(--bg-secondary);"><div style="font-size:12px;color:var(--text-muted);margin-bottom:4px;font-weight:600;">Reasoning Trace:</div><pre style="margin:0;white-space:pre-wrap;word-break:break-word;font-size:12px;line-height:1.5;max-height:300px;overflow-y:auto;color:var(--text-secondary);">${this.escapeHtml(traceText)}</pre></td></tr>` : ''}
                            `;
                        }).join('')}
                    </tbody>
                </table>
            `;
            
            // Pagination
            const pagination = this.sampleContainer.querySelector('.sample-pagination');
            if (pagination && total > this.sampleLimit) {
                const currentPage = Math.floor(this.sampleOffset / this.sampleLimit) + 1;
                const totalPages = Math.ceil(total / this.sampleLimit);
                pagination.innerHTML = `
                    <div class="pagination-controls">
                        <button class="btn btn-secondary btn-sm" ${this.sampleOffset === 0 ? 'disabled' : ''} onclick="resultsVisualizer.prevPage('${experimentId}')">上一页</button>
                        <span style="font-size:13px;color:var(--text-secondary);">${currentPage} / ${totalPages}</span>
                        <button class="btn btn-secondary btn-sm" ${this.sampleOffset + this.sampleLimit >= total ? 'disabled' : ''} onclick="resultsVisualizer.nextPage('${experimentId}')">下一页</button>
                    </div>
                `;
            }
        } catch (error) {
            wrapper.innerHTML = `<div style="padding:20px;text-align:center;color:var(--error-color);">加载失败: ${error.message}</div>`;
        }
    }
    
    prevPage(experimentId) {
        this.sampleOffset = Math.max(0, this.sampleOffset - this.sampleLimit);
        this.loadSamples(experimentId);
    }
    
    nextPage(experimentId) {
        this.sampleOffset += this.sampleLimit;
        this.loadSamples(experimentId);
    }
    
    // =========================================================================
    // Compare Mode
    // =========================================================================
    async enterCompareMode() {
        this.compareMode = true;
        if (!this.compareContainer) return;
        
        this.compareContainer.style.display = 'block';
        this.compareContainer.innerHTML = `
            <div class="results-section-title"><i data-lucide="git-compare" style="width:18px;height:18px;"></i> 实验对比</div>
            <div class="compare-experiment-select">
                <div class="compare-selected-list" id="compare-selected-list"></div>
                <button class="btn btn-secondary btn-sm" onclick="resultsVisualizer.addCompareExperiment()">+ 添加实验</button>
                <button class="btn btn-primary btn-sm" onclick="resultsVisualizer.runCompare()" style="margin-left:8px;">开始对比</button>
                <button class="btn btn-secondary btn-sm" onclick="resultsVisualizer.exitCompareMode()" style="margin-left:8px;">退出对比</button>
            </div>
            <div id="compare-results"></div>
        `;
        if (window.lucide) lucide.createIcons();
    }
    
    exitCompareMode() {
        this.compareMode = false;
        this.compareList = [];
        if (this.compareContainer) {
            this.compareContainer.style.display = 'none';
            this.compareContainer.innerHTML = '';
        }
    }
    
    async addCompareExperiment() {
        try {
            const experiments = await API.fetchExperiments({ status: 'finished' });
            const existing = new Set(this.compareList);
            const available = experiments.filter(e => !existing.has(e.experiment_id));
            
            if (available.length === 0) {
                alert('没有更多已完成的实验可添加');
                return;
            }
            
            const selected = prompt('输入实验ID:\n' + available.map(e => `${e.experiment_id} - ${e.name}`).join('\n'));
            if (selected && available.some(e => e.experiment_id === selected.trim())) {
                this.compareList.push(selected.trim());
                this.updateCompareList();
            }
        } catch (error) {
            alert('获取实验列表失败: ' + error.message);
        }
    }
    
    updateCompareList() {
        const list = document.getElementById('compare-selected-list');
        if (!list) return;
        list.innerHTML = this.compareList.map(id =>
            `<span class="badge badge-primary" style="margin-right:6px;">${id} <span style="cursor:pointer;margin-left:4px;" onclick="resultsVisualizer.removeCompare('${id}')">×</span></span>`
        ).join('');
    }
    
    removeCompare(id) {
        this.compareList = this.compareList.filter(x => x !== id);
        this.updateCompareList();
    }
    
    async runCompare() {
        if (this.compareList.length < 2) {
            alert('请至少选择 2 个实验进行对比');
            return;
        }
        
        const resultsDiv = document.getElementById('compare-results');
        if (!resultsDiv) return;
        
        resultsDiv.innerHTML = '<div style="padding:20px;text-align:center;color:var(--text-muted);">加载对比数据中...</div>';
        
        try {
            const result = await API.Results.compare(this.compareList, ['exact_match', 'f1_score']);
            
            if (result.columns && result.rows) {
                resultsDiv.innerHTML = `
                    <table class="table" style="margin-top:12px;">
                        <thead><tr>${result.columns.map(c => `<th>${c}</th>`).join('')}</tr></thead>
                        <tbody>${result.rows.map(row =>
                            `<tr>${row.map((cell, i) => `<td>${i === 0 ? cell : (typeof cell === 'number' ? (cell * 100).toFixed(1) + '%' : cell)}</td>`).join('')}</tr>`
                        ).join('')}</tbody>
                    </table>
                `;
            } else {
                resultsDiv.innerHTML = '<div style="padding:20px;color:var(--text-muted);">无对比数据</div>';
            }
        } catch (error) {
            resultsDiv.innerHTML = `<div style="padding:20px;color:var(--error-color);">对比失败: ${error.message}</div>`;
        }
    }
    
    // =========================================================================
    // Utilities
    // =========================================================================
    formatValue(value, fmt) {
        if (value === null || value === undefined) return '-';
        switch (fmt) {
            case 'pct': return (value * 100).toFixed(1) + '%';
            case 'ms': return value.toFixed(0) + ' ms';
            case 'usd': return '$' + value.toFixed(4);
            case 'int': return Math.round(value).toString();
            case 'float': return value.toFixed(1);
            default: return typeof value === 'number' ? value.toFixed(2) : String(value);
        }
    }
    
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    showSkeleton() {
        const skeletonHtml = `
            <div class="skeleton" style="height:80px;margin-bottom:16px;"></div>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:16px;">
                <div class="skeleton" style="height:100px;"></div>
                <div class="skeleton" style="height:100px;"></div>
                <div class="skeleton" style="height:100px;"></div>
                <div class="skeleton" style="height:100px;"></div>
            </div>
        `;
        if (this.metaContainer) this.metaContainer.innerHTML = skeletonHtml;
        if (this.perfContainer) this.perfContainer.innerHTML = '';
        if (this.effContainer) this.effContainer.innerHTML = '';
        if (this.chartsContainer) this.chartsContainer.innerHTML = '';
        if (this.groupContainer) this.groupContainer.innerHTML = '';
        if (this.sampleContainer) this.sampleContainer.innerHTML = '';
    }
    
    showError(message) {
        if (this.metaContainer) {
            this.metaContainer.innerHTML = `<div class="alert alert-error">${message}</div>`;
        }
    }
    
    destroy() {
        Object.values(this.charts).forEach(chart => chart.destroy());
        this.charts = {};
    }
}

// Global instance
var resultsVisualizer = null;

function initResultsVisualizer() {
    resultsVisualizer = new ResultsVisualizer();
    window.resultsVisualizer = resultsVisualizer;
}

async function viewResults(experimentId) {
    if (!resultsVisualizer) {
        initResultsVisualizer();
    }
    
    // Switch to results tab if exists
    if (typeof switchTab === 'function') {
        switchTab('results');
    }
    
    // Set dropdown value
    const select = document.getElementById('results-experiment-select');
    if (select) select.value = experimentId;
    
    await resultsVisualizer.loadMetrics(experimentId);
}

// Auto-init
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('results-meta') || document.getElementById('results-charts')) {
        initResultsVisualizer();
    }
});

// Export
window.ResultsVisualizer = ResultsVisualizer;
window.initResultsVisualizer = initResultsVisualizer;
window.viewResults = viewResults;
