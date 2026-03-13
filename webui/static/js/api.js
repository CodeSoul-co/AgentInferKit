/**
 * API Client for Benchmark Platform
 * 
 * Wraps all backend endpoints with automatic ResponseEnvelope handling
 * and SSE event stream support.
 */

const API_BASE = '/api/v1';

/**
 * Custom API Error class
 */
class APIError extends Error {
    constructor(code, message, data = null) {
        super(message);
        this.name = 'APIError';
        this.code = code;
        this.data = data;
    }
}

/**
 * Handle ResponseEnvelope and extract data or throw error
 */
async function handleResponse(response) {
    if (!response.ok) {
        const text = await response.text();
        try {
            const json = JSON.parse(text);
            throw new APIError(json.code || response.status, json.message || json.detail || 'Request failed');
        } catch (e) {
            if (e instanceof APIError) throw e;
            throw new APIError(response.status, text || 'Request failed');
        }
    }
    
    const json = await response.json();
    
    if (json.code !== 0) {
        throw new APIError(json.code, json.message, json.data);
    }
    
    return json.data;
}

/**
 * Make a GET request
 */
async function get(endpoint, params = {}) {
    const url = new URL(API_BASE + endpoint, window.location.origin);
    Object.entries(params).forEach(([key, value]) => {
        if (value !== null && value !== undefined) {
            url.searchParams.append(key, value);
        }
    });
    
    const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
        },
    });
    
    return handleResponse(response);
}

/**
 * Make a POST request with JSON body
 */
async function post(endpoint, data = {}) {
    const response = await fetch(API_BASE + endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        },
        body: JSON.stringify(data),
    });
    
    return handleResponse(response);
}

/**
 * Make a POST request with FormData (for file uploads)
 */
async function postForm(endpoint, formData) {
    const response = await fetch(API_BASE + endpoint, {
        method: 'POST',
        body: formData,
    });
    
    return handleResponse(response);
}

/**
 * Make a DELETE request
 */
async function del(endpoint) {
    const response = await fetch(API_BASE + endpoint, {
        method: 'DELETE',
        headers: {
            'Accept': 'application/json',
        },
    });
    
    return handleResponse(response);
}

/**
 * Subscribe to SSE event stream
 * @param {string} endpoint - SSE endpoint
 * @param {Object} handlers - Event handlers { onProgress, onDone, onError, onToken }
 * @returns {EventSource} - EventSource instance for manual close
 */
function subscribeSSE(endpoint, handlers = {}) {
    const url = API_BASE + endpoint;
    const eventSource = new EventSource(url);
    
    eventSource.addEventListener('progress', (event) => {
        const data = JSON.parse(event.data);
        if (handlers.onProgress) handlers.onProgress(data);
    });
    
    eventSource.addEventListener('done', (event) => {
        const data = JSON.parse(event.data);
        if (handlers.onDone) handlers.onDone(data);
        eventSource.close();
    });
    
    eventSource.addEventListener('error', (event) => {
        if (event.data) {
            const data = JSON.parse(event.data);
            if (handlers.onError) handlers.onError(data);
        } else {
            if (handlers.onError) handlers.onError({ message: 'Connection error' });
        }
        eventSource.close();
    });
    
    eventSource.addEventListener('token', (event) => {
        const data = JSON.parse(event.data);
        if (handlers.onToken) handlers.onToken(data);
    });
    
    eventSource.onerror = () => {
        if (handlers.onError) handlers.onError({ message: 'SSE connection failed' });
        eventSource.close();
    };
    
    return eventSource;
}

/**
 * POST request with SSE response (for streaming chat)
 */
async function postSSE(endpoint, data, handlers = {}) {
    const response = await fetch(API_BASE + endpoint, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream',
        },
        body: JSON.stringify(data),
    });
    
    if (!response.ok) {
        const text = await response.text();
        if (handlers.onError) handlers.onError({ message: text });
        return;
    }
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    
    while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
            if (line.startsWith('event: ')) {
                const eventType = line.slice(7).trim();
                continue;
            }
            if (line.startsWith('data: ')) {
                const dataStr = line.slice(6);
                try {
                    const data = JSON.parse(dataStr);
                    
                    if (data.token !== undefined && handlers.onToken) {
                        handlers.onToken(data);
                    } else if (data.usage !== undefined && handlers.onDone) {
                        handlers.onDone(data);
                    } else if (data.message !== undefined && handlers.onError) {
                        handlers.onError(data);
                    } else if (data.completed !== undefined && handlers.onProgress) {
                        handlers.onProgress(data);
                    }
                } catch (e) {
                    console.warn('Failed to parse SSE data:', dataStr);
                }
            }
        }
    }
}

// =============================================================================
// Datasets API
// =============================================================================

const Datasets = {
    /**
     * Upload a dataset file
     * @param {File} file - JSONL file
     * @param {Object} options - { dataset_name, task_type, version, split, description }
     */
    async upload(file, options) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('dataset_name', options.dataset_name);
        formData.append('task_type', options.task_type);
        if (options.version) formData.append('version', options.version);
        if (options.split) formData.append('split', options.split);
        if (options.description) formData.append('description', options.description);
        
        return postForm('/datasets/upload', formData);
    },
    
    /**
     * List all datasets
     * @param {string} taskType - Optional filter by task type
     */
    async list(taskType = null) {
        return get('/datasets', { task_type: taskType });
    },
    
    /**
     * Preview dataset samples
     * @param {string} datasetId - Dataset ID
     * @param {number} offset - Offset
     * @param {number} limit - Limit
     */
    async preview(datasetId, offset = 0, limit = 10) {
        return get(`/datasets/${datasetId}/preview`, { offset, limit });
    },
    
    /**
     * Get dataset statistics
     * @param {string} datasetId - Dataset ID
     */
    async stats(datasetId) {
        return get(`/datasets/${datasetId}/stats`);
    },
    
    /**
     * Delete a dataset
     * @param {string} datasetId - Dataset ID
     */
    async delete(datasetId) {
        return del(`/datasets/${datasetId}`);
    },
};

// =============================================================================
// Experiments API
// =============================================================================

const Experiments = {
    /**
     * Create a new experiment
     * @param {Object} config - Experiment configuration
     */
    async create(config) {
        return post('/experiments', config);
    },
    
    /**
     * List all experiments
     * @param {Object} filters - { status, dataset_id }
     */
    async list(filters = {}) {
        return get('/experiments', filters);
    },
    
    /**
     * Get experiment details
     * @param {string} experimentId - Experiment ID
     */
    async get(experimentId) {
        return get(`/experiments/${experimentId}`);
    },
    
    /**
     * Run an experiment
     * @param {string} experimentId - Experiment ID
     */
    async run(experimentId) {
        return post(`/experiments/${experimentId}/run`);
    },
    
    /**
     * Stop an experiment
     * @param {string} experimentId - Experiment ID
     */
    async stop(experimentId) {
        return post(`/experiments/${experimentId}/stop`);
    },
    
    /**
     * Subscribe to experiment progress
     * @param {string} experimentId - Experiment ID
     * @param {Object} handlers - { onProgress, onDone, onError }
     */
    subscribeProgress(experimentId, handlers) {
        return subscribeSSE(`/experiments/${experimentId}/stream`, handlers);
    },
    
    /**
     * Delete an experiment
     * @param {string} experimentId - Experiment ID
     */
    async delete(experimentId) {
        return del(`/experiments/${experimentId}`);
    },

    /**
     * Run evaluation on an existing experiment's predictions
     * @param {string} experimentId - Experiment ID
     * @param {Object} config - { metrics: [...], group_by: [...] }
     */
    async evaluate(experimentId, config = {}) {
        return post(`/experiments/${experimentId}/evaluate`, config);
    },
};

// =============================================================================
// Results API
// =============================================================================

const Results = {
    /**
     * Get experiment metrics
     * @param {string} experimentId - Experiment ID
     */
    async getMetrics(experimentId) {
        return get(`/results/${experimentId}/metrics`);
    },
    
    /**
     * Get predictions with pagination and filtering
     * @param {string} experimentId - Experiment ID
     * @param {Object} options - { offset, limit, correct, difficulty, has_error }
     */
    async getPredictions(experimentId, options = {}) {
        return get(`/results/${experimentId}/predictions`, options);
    },
    
    /**
     * Compare multiple experiments
     * @param {Array} experimentIds - List of experiment IDs
     * @param {Array} metrics - Metrics to compare
     * @param {string} groupBy - Optional grouping dimension
     */
    async compare(experimentIds, metrics = ['accuracy'], groupBy = null) {
        return post('/results/compare', {
            experiment_ids: experimentIds,
            metrics,
            group_by: groupBy,
        });
    },
    
    /**
     * Get export URL for results
     * @param {string} experimentId - Experiment ID
     * @param {string} format - Export format (csv, json, jsonl)
     * @param {string} include - What to include (predictions, metrics, all)
     */
    getExportUrl(experimentId, format = 'json', include = 'all') {
        return `${API_BASE}/results/${experimentId}/export?format=${format}&include=${include}`;
    },
};

// =============================================================================
// RAG API
// =============================================================================

const RAG = {
    /**
     * Build RAG index (returns SSE stream)
     * @param {File} file - JSONL file
     * @param {Object} options - { kb_name, chunk_strategy, chunk_size, embedder }
     * @param {Object} handlers - { onProgress, onDone, onError }
     */
    async build(file, options, handlers) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('kb_name', options.kb_name);
        if (options.chunk_strategy) formData.append('chunk_strategy', options.chunk_strategy);
        if (options.chunk_size) formData.append('chunk_size', options.chunk_size);
        if (options.chunk_overlap !== undefined) formData.append('chunk_overlap', options.chunk_overlap);
        if (options.embedder) formData.append('embedder', options.embedder);
        
        const response = await fetch(API_BASE + '/rag/build', {
            method: 'POST',
            body: formData,
        });
        
        if (!response.ok) {
            const text = await response.text();
            try { const j = JSON.parse(text); throw new APIError(response.status, j.detail || j.message || 'Build failed'); }
            catch (e) { if (e instanceof APIError) throw e; throw new APIError(response.status, text || 'Build failed'); }
        }
        
        // Handle SSE response
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let currentEvent = 'message';
        
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop() || '';
            
            for (const line of lines) {
                if (line.startsWith('event: ')) {
                    currentEvent = line.slice(7).trim();
                } else if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));
                        if (currentEvent === 'error' && handlers.onError) {
                            handlers.onError(data);
                        } else if (currentEvent === 'done' && handlers.onDone) {
                            handlers.onDone(data);
                        } else if (currentEvent === 'progress' && handlers.onProgress) {
                            handlers.onProgress(data);
                        } else if (data.stage && handlers.onProgress) {
                            handlers.onProgress(data);
                        } else if (data.kb_name && handlers.onDone) {
                            handlers.onDone(data);
                        } else if (data.message && handlers.onError) {
                            handlers.onError(data);
                        }
                    } catch (e) { console.warn('SSE parse error:', e); }
                    currentEvent = 'message';
                } else if (line.trim() === '') {
                    currentEvent = 'message';
                }
            }
        }
    },
    
    /**
     * List all knowledge bases
     */
    async list() {
        return get('/rag');
    },
    
    /**
     * Search in a knowledge base
     * @param {string} kbName - Knowledge base name
     * @param {string} query - Search query
     * @param {number} topK - Number of results
     */
    async search(kbName, query, topK = 5) {
        return post('/rag/search', {
            kb_name: kbName,
            query,
            top_k: topK,
        });
    },
    
    /**
     * Delete a knowledge base
     * @param {string} kbName - Knowledge base name
     */
    async delete(kbName) {
        return del(`/rag/${kbName}`);
    },
};

// =============================================================================
// Chat API
// =============================================================================

const Chat = {
    /**
     * Complete a chat message
     * @param {Object} options - { model_id, strategy, messages, rag, sample_id }
     */
    async complete(options) {
        return post('/chat/complete', options);
    },
    
    /**
     * Stream chat completion
     * @param {Object} options - { model_id, strategy, messages, rag, sample_id }
     * @param {Object} handlers - { onToken, onDone, onError }
     */
    async stream(options, handlers) {
        return postSSE('/chat/stream', options, handlers);
    },
};

// =============================================================================
// Models API
// =============================================================================

const Models = {
    /**
     * List all available models
     */
    async list() {
        return get('/models');
    },
    
    /**
     * Test model connectivity
     * @param {string} modelId - Model ID
     */
    async ping(modelId) {
        return post(`/models/${modelId}/ping`);
    },
    
    /**
     * Set API key for a provider (session-only)
     * @param {string} provider - Provider name (e.g. 'openai')
     * @param {string} apiKey - API key value
     */
    async setApiKey(provider, apiKey) {
        return post('/models/api-key', { provider, api_key: apiKey });
    },
};

// =============================================================================
// System API
// =============================================================================

const System = {
    /**
     * Health check
     */
    async health() {
        return get('/system/health');
    },
    
    /**
     * Get system configuration overview
     */
    async config() {
        return get('/system/config');
    },
};

// =============================================================================
// Settings API
// =============================================================================

const Settings = {
    /**
     * List all model configurations with full parameters
     */
    async listModelConfigs() {
        return get('/settings/models');
    },

    /**
     * Get model config for a provider
     * @param {string} provider - Provider name
     */
    async getModelConfig(provider) {
        return get(`/settings/models/${provider}`);
    },

    /**
     * Update model config for a provider
     * @param {string} provider - Provider name
     * @param {Object} config - Full config object
     */
    async updateModelConfig(provider, config) {
        const response = await fetch(API_BASE + `/settings/models/${provider}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
            body: JSON.stringify(config),
        });
        return handleResponse(response);
    },

    /**
     * Create a new model config
     * @param {string} provider - Provider name
     * @param {Object} config - Full config object
     */
    async createModelConfig(provider, config) {
        return post(`/settings/models/${provider}`, config);
    },

    /**
     * Delete model config
     * @param {string} provider - Provider name
     */
    async deleteModelConfig(provider) {
        return del(`/settings/models/${provider}`);
    },

    /**
     * List environment variables (API keys masked)
     */
    async listEnv() {
        return get('/settings/env');
    },

    /**
     * Update environment variables
     * @param {Object} variables - Key-value pairs
     */
    async updateEnv(variables) {
        const response = await fetch(API_BASE + '/settings/env', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
            body: JSON.stringify({ variables }),
        });
        return handleResponse(response);
    },
};

// =============================================================================
// Convenience Functions (用户要求的便捷函数)
// =============================================================================

/**
 * 获取实验列表
 * @param {Object} filters - 可选过滤条件 { status, dataset_id }
 * @returns {Promise<Array>} 实验列表
 */
async function fetchExperiments(filters = {}) {
    const result = await Experiments.list(filters);
    return result.experiments || [];
}

/**
 * 启动实验并处理 SSE 流
 * @param {string} id - 实验 ID
 * @param {Object} handlers - SSE 事件处理器 { onProgress, onSample, onDone, onError }
 * @returns {Promise<Object>} 包含 stream_url 和 EventSource 的对象
 */
async function runExperiment(id, handlers = {}) {
    // 先启动实验
    const result = await Experiments.run(id);
    
    // 然后订阅 SSE 进度流
    // stream_url from backend is relative like "/{id}/progress"
    const streamUrl = result.stream_url || `/${id}/progress`;
    const fullUrl = API_BASE + '/experiments' + streamUrl;
    
    return new Promise((resolve, reject) => {
        const eventSource = new EventSource(fullUrl);
        
        eventSource.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                if (data.content !== undefined && handlers.onContent) {
                    handlers.onContent(data);
                } else if (data.done && handlers.onDone) {
                    handlers.onDone(data);
                    eventSource.close();
                    resolve({ status: 'completed', data });
                } else if (data.error && handlers.onError) {
                    handlers.onError(data);
                    eventSource.close();
                    reject(new APIError(500, data.error));
                } else if (data.completed !== undefined && handlers.onProgress) {
                    handlers.onProgress(data);
                }
            } catch (e) {
                console.warn('Failed to parse SSE data:', event.data);
            }
        };
        
        eventSource.addEventListener('progress', (event) => {
            const data = JSON.parse(event.data);
            if (handlers.onProgress) handlers.onProgress(data);
        });
        
        eventSource.addEventListener('sample', (event) => {
            const data = JSON.parse(event.data);
            if (handlers.onSample) handlers.onSample(data);
        });
        
        eventSource.addEventListener('done', (event) => {
            const data = JSON.parse(event.data);
            if (handlers.onDone) handlers.onDone(data);
            eventSource.close();
            resolve({ status: 'completed', data });
        });
        
        eventSource.addEventListener('error', (event) => {
            let errorData = { message: 'SSE connection error' };
            if (event.data) {
                try {
                    errorData = JSON.parse(event.data);
                } catch (e) {}
            }
            if (handlers.onError) handlers.onError(errorData);
            eventSource.close();
            reject(new APIError(500, errorData.message));
        });
        
        eventSource.onerror = () => {
            if (handlers.onError) handlers.onError({ message: 'SSE connection failed' });
            eventSource.close();
        };
        
        // 返回 eventSource 以便外部可以手动关闭
        resolve({ status: 'running', eventSource, stream_url: streamUrl });
    });
}

/**
 * 上传数据集
 * @param {File} file - JSONL 文件
 * @param {string} taskType - 任务类型 (qa, text_exam, image_mcq, api_calling)
 * @param {Object} options - 可选参数 { dataset_name, version, split, description }
 * @returns {Promise<Object>} 上传结果
 */
async function uploadDataset(file, taskType, options = {}) {
    const uploadOptions = {
        dataset_name: options.dataset_name || file.name.replace(/\.jsonl?$/, ''),
        task_type: taskType,
        version: options.version,
        split: options.split,
        description: options.description,
    };
    return Datasets.upload(file, uploadOptions);
}

/**
 * 获取实验评估结果
 * @param {string} id - 实验 ID
 * @returns {Promise<Object>} 评估指标
 */
async function getMetrics(id) {
    return Results.getMetrics(id);
}

// =============================================================================
// Export
// =============================================================================

window.API = {
    APIError,
    Datasets,
    Experiments,
    Results,
    RAG,
    Chat,
    Models,
    System,
    Settings,
    // 便捷函数
    fetchExperiments,
    runExperiment,
    uploadDataset,
    getMetrics,
};
