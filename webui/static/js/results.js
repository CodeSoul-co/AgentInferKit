/**
 * Results Visualization Module
 * 
 * Integrates Chart.js to visualize evaluation metrics.
 */

class ResultsVisualizer {
    constructor(options = {}) {
        this.container = options.container || document.getElementById('results-container');
        this.chartsContainer = options.chartsContainer || document.getElementById('charts-container');
        this.metricsContainer = options.metricsContainer || document.getElementById('metrics-container');
        
        this.charts = {};
        this.currentExperimentId = null;
        
        this.init();
    }
    
    init() {
        // Check if Chart.js is loaded
        if (typeof Chart === 'undefined') {
            console.warn('Chart.js not loaded. Loading from CDN...');
            this.loadChartJS();
        }
    }
    
    loadChartJS() {
        const script = document.createElement('script');
        script.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js';
        script.onload = () => console.log('Chart.js loaded');
        document.head.appendChild(script);
    }
    
    async loadMetrics(experimentId) {
        this.currentExperimentId = experimentId;
        
        try {
            const metrics = await API.getMetrics(experimentId);
            this.renderMetrics(metrics);
            this.renderCharts(metrics);
            return metrics;
        } catch (error) {
            this.showError(`加载指标失败: ${error.message}`);
            throw error;
        }
    }
    
    renderMetrics(metrics) {
        if (!this.metricsContainer) return;
        
        const overall = metrics.overall || {};
        
        // Build metrics cards
        const metricsHtml = Object.entries(overall).map(([key, value]) => {
            const displayName = this.getMetricDisplayName(key);
            const displayValue = this.formatMetricValue(key, value);
            const icon = this.getMetricIcon(key);
            
            return `
                <div class="stat-card">
                    <div class="stat-label">${icon} ${displayName}</div>
                    <div class="stat-value">${displayValue}</div>
                </div>
            `;
        }).join('');
        
        this.metricsContainer.innerHTML = `
            <div class="stats-grid">
                ${metricsHtml}
            </div>
        `;
    }
    
    getMetricDisplayName(key) {
        const names = {
            'accuracy': '准确率',
            'exact_match': '精确匹配',
            'f1_score': 'F1 分数',
            'rouge_l': 'ROUGE-L',
            'bleu': 'BLEU',
            'choice_accuracy': '选择题准确率',
            'hit_rate': '命中率',
            'mrr': 'MRR',
            'avg_latency_ms': '平均延迟',
            'tokens_per_sec': '吞吐量',
            'total_cost_usd': '总成本',
            'action_success_rate': '动作成功率',
            'parameter_accuracy': '参数准确率',
        };
        return names[key] || key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
    
    getMetricIcon(key) {
        const icons = {
            'accuracy': '🎯',
            'exact_match': '✅',
            'f1_score': '📊',
            'rouge_l': '📝',
            'choice_accuracy': '✓',
            'hit_rate': '🔍',
            'mrr': '📈',
            'avg_latency_ms': '⏱️',
            'tokens_per_sec': '⚡',
            'total_cost_usd': '💰',
        };
        return icons[key] || '📌';
    }
    
    formatMetricValue(key, value) {
        if (value === null || value === undefined) return '-';
        
        // Percentage metrics
        if (['accuracy', 'exact_match', 'f1_score', 'rouge_l', 'bleu', 'choice_accuracy', 
             'hit_rate', 'mrr', 'action_success_rate', 'parameter_accuracy'].includes(key)) {
            return `${(value * 100).toFixed(1)}%`;
        }
        
        // Latency
        if (key.includes('latency') || key.includes('_ms')) {
            return `${value.toFixed(0)} ms`;
        }
        
        // Cost
        if (key.includes('cost')) {
            return `$${value.toFixed(4)}`;
        }
        
        // Throughput
        if (key === 'tokens_per_sec') {
            return `${value.toFixed(1)} tok/s`;
        }
        
        // Default
        if (typeof value === 'number') {
            return value.toFixed(2);
        }
        
        return String(value);
    }
    
    renderCharts(metrics) {
        if (!this.chartsContainer || typeof Chart === 'undefined') return;
        
        // Clear existing charts
        Object.values(this.charts).forEach(chart => chart.destroy());
        this.charts = {};
        
        this.chartsContainer.innerHTML = '';
        
        const overall = metrics.overall || {};
        const byDifficulty = metrics.by_difficulty || [];
        const byTopic = metrics.by_topic || [];
        
        // Radar chart for overall metrics
        if (Object.keys(overall).length > 0) {
            this.createRadarChart('overall-radar', overall);
        }
        
        // Bar chart for difficulty breakdown
        if (byDifficulty.length > 0) {
            this.createBarChart('difficulty-bar', byDifficulty, '按难度分布');
        }
        
        // Bar chart for topic breakdown
        if (byTopic.length > 0) {
            this.createBarChart('topic-bar', byTopic, '按主题分布');
        }
    }
    
    createRadarChart(id, metrics) {
        // Filter metrics suitable for radar chart (0-1 range)
        const radarMetrics = {};
        const percentageKeys = ['accuracy', 'exact_match', 'f1_score', 'rouge_l', 'bleu', 
                                'choice_accuracy', 'hit_rate', 'mrr', 'action_success_rate', 'parameter_accuracy'];
        
        for (const [key, value] of Object.entries(metrics)) {
            if (percentageKeys.includes(key) && typeof value === 'number') {
                radarMetrics[key] = value;
            }
        }
        
        if (Object.keys(radarMetrics).length < 3) {
            // Not enough metrics for radar chart, create bar chart instead
            this.createMetricsBarChart(id, metrics);
            return;
        }
        
        const container = document.createElement('div');
        container.className = 'chart-container';
        container.innerHTML = `
            <div class="card">
                <div class="card-header">评估指标雷达图</div>
                <div class="card-body">
                    <canvas id="${id}" width="400" height="400"></canvas>
                </div>
            </div>
        `;
        this.chartsContainer.appendChild(container);
        
        const ctx = document.getElementById(id).getContext('2d');
        
        this.charts[id] = new Chart(ctx, {
            type: 'radar',
            data: {
                labels: Object.keys(radarMetrics).map(k => this.getMetricDisplayName(k)),
                datasets: [{
                    label: '评估结果',
                    data: Object.values(radarMetrics).map(v => v * 100),
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(59, 130, 246, 1)',
                    pointRadius: 4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            stepSize: 20,
                            callback: (value) => `${value}%`
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        callbacks: {
                            label: (context) => `${context.label}: ${context.raw.toFixed(1)}%`
                        }
                    }
                }
            }
        });
    }
    
    createMetricsBarChart(id, metrics) {
        const container = document.createElement('div');
        container.className = 'chart-container';
        container.innerHTML = `
            <div class="card">
                <div class="card-header">评估指标柱状图</div>
                <div class="card-body">
                    <canvas id="${id}" width="400" height="300"></canvas>
                </div>
            </div>
        `;
        this.chartsContainer.appendChild(container);
        
        const ctx = document.getElementById(id).getContext('2d');
        
        // Filter numeric metrics
        const numericMetrics = {};
        for (const [key, value] of Object.entries(metrics)) {
            if (typeof value === 'number') {
                numericMetrics[key] = value;
            }
        }
        
        this.charts[id] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(numericMetrics).map(k => this.getMetricDisplayName(k)),
                datasets: [{
                    label: '指标值',
                    data: Object.values(numericMetrics),
                    backgroundColor: 'rgba(59, 130, 246, 0.7)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 1,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    createBarChart(id, groupData, title) {
        const container = document.createElement('div');
        container.className = 'chart-container';
        container.innerHTML = `
            <div class="card">
                <div class="card-header">${title}</div>
                <div class="card-body">
                    <canvas id="${id}" width="400" height="300"></canvas>
                </div>
            </div>
        `;
        this.chartsContainer.appendChild(container);
        
        const ctx = document.getElementById(id).getContext('2d');
        
        const labels = groupData.map(g => g.group_name);
        const accuracies = groupData.map(g => g.accuracy * 100);
        const totals = groupData.map(g => g.total);
        
        this.charts[id] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [
                    {
                        label: '准确率 (%)',
                        data: accuracies,
                        backgroundColor: 'rgba(59, 130, 246, 0.7)',
                        borderColor: 'rgba(59, 130, 246, 1)',
                        borderWidth: 1,
                        yAxisID: 'y',
                    },
                    {
                        label: '样本数',
                        data: totals,
                        backgroundColor: 'rgba(34, 197, 94, 0.7)',
                        borderColor: 'rgba(34, 197, 94, 1)',
                        borderWidth: 1,
                        yAxisID: 'y1',
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        type: 'linear',
                        position: 'left',
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: '准确率 (%)'
                        }
                    },
                    y1: {
                        type: 'linear',
                        position: 'right',
                        beginAtZero: true,
                        grid: {
                            drawOnChartArea: false
                        },
                        title: {
                            display: true,
                            text: '样本数'
                        }
                    }
                },
                plugins: {
                    tooltip: {
                        callbacks: {
                            label: (context) => {
                                if (context.datasetIndex === 0) {
                                    return `准确率: ${context.raw.toFixed(1)}%`;
                                }
                                return `样本数: ${context.raw}`;
                            }
                        }
                    }
                }
            }
        });
    }
    
    async compareExperiments(experimentIds, metrics = ['accuracy']) {
        try {
            const result = await API.Results.compare(experimentIds, metrics);
            this.renderComparisonTable(result);
            this.renderComparisonChart(result, metrics);
            return result;
        } catch (error) {
            this.showError(`对比失败: ${error.message}`);
            throw error;
        }
    }
    
    renderComparisonTable(data) {
        if (!this.container) return;
        
        const tableHtml = `
            <div class="card mt-lg">
                <div class="card-header">实验对比</div>
                <div class="card-body">
                    <div class="table-container">
                        <table class="table">
                            <thead>
                                <tr>
                                    ${data.columns.map(col => `<th>${col}</th>`).join('')}
                                </tr>
                            </thead>
                            <tbody>
                                ${data.rows.map(row => `
                                    <tr>
                                        ${row.map((cell, i) => `
                                            <td>${i === 0 ? cell : this.formatMetricValue(data.columns[i], cell)}</td>
                                        `).join('')}
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        `;
        
        const tableContainer = document.createElement('div');
        tableContainer.innerHTML = tableHtml;
        this.container.appendChild(tableContainer);
    }
    
    renderComparisonChart(data, metrics) {
        if (!this.chartsContainer || typeof Chart === 'undefined') return;
        
        const id = 'comparison-chart';
        const container = document.createElement('div');
        container.className = 'chart-container';
        container.innerHTML = `
            <div class="card">
                <div class="card-header">实验对比图</div>
                <div class="card-body">
                    <canvas id="${id}" width="600" height="300"></canvas>
                </div>
            </div>
        `;
        this.chartsContainer.appendChild(container);
        
        const ctx = document.getElementById(id).getContext('2d');
        
        const experimentLabels = data.rows.map(row => row[0]);
        const datasets = metrics.map((metric, index) => {
            const metricIndex = data.columns.indexOf(metric);
            const values = data.rows.map(row => {
                const val = row[metricIndex];
                return typeof val === 'number' ? val * 100 : 0;
            });
            
            const colors = [
                'rgba(59, 130, 246, 0.7)',
                'rgba(34, 197, 94, 0.7)',
                'rgba(245, 158, 11, 0.7)',
                'rgba(239, 68, 68, 0.7)',
            ];
            
            return {
                label: this.getMetricDisplayName(metric),
                data: values,
                backgroundColor: colors[index % colors.length],
                borderWidth: 1,
            };
        });
        
        this.charts[id] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: experimentLabels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        title: {
                            display: true,
                            text: '百分比 (%)'
                        }
                    }
                }
            }
        });
    }
    
    showError(message) {
        if (!this.container) return;
        
        this.container.innerHTML = `
            <div class="alert alert-error">
                ${message}
            </div>
        `;
    }
    
    destroy() {
        Object.values(this.charts).forEach(chart => chart.destroy());
        this.charts = {};
    }
}

// Global instance
let resultsVisualizer = null;

function initResultsVisualizer() {
    resultsVisualizer = new ResultsVisualizer();
}

async function viewResults(experimentId) {
    if (!resultsVisualizer) {
        initResultsVisualizer();
    }
    
    // Switch to results tab if exists
    if (typeof switchTab === 'function') {
        switchTab('results');
    }
    
    await resultsVisualizer.loadMetrics(experimentId);
}

// Auto-init
document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('results-container') || document.getElementById('charts-container')) {
        initResultsVisualizer();
    }
});

// Export
window.ResultsVisualizer = ResultsVisualizer;
window.resultsVisualizer = resultsVisualizer;
window.initResultsVisualizer = initResultsVisualizer;
window.viewResults = viewResults;
