/**
 * AgentInferKit - Internationalization (i18n) module
 * Supports: zh-CN (Chinese), en (English)
 */

const I18N = {
    currentLang: localStorage.getItem('aik-lang') || 'zh',

    translations: {
        zh: {
            // Sidebar
            'nav.dashboard': 'Dashboard',
            'nav.datasets': '数据集管理',
            'nav.experiments': '实验配置',
            'nav.results': '结果分析',
            'nav.rag': '知识库管理',
            'nav.chat': '对话调试',
            'sidebar.status.checking': '检查系统状态...',
            'sidebar.status.failed': '连接失败',

            // Dashboard
            'dashboard.title': 'Dashboard',
            'dashboard.refresh': '刷新',
            'dashboard.updated_at': '更新于',
            'dashboard.stat.datasets': '数据集数量',
            'dashboard.stat.experiments': '实验数量',
            'dashboard.stat.kbs': '知识库数量',
            'dashboard.stat.models': '可用模型',
            'dashboard.quick.upload': '上传数据集',
            'dashboard.quick.new_exp': '新建实验',
            'dashboard.quick.results': '查看结果',
            'dashboard.quick.chat': '对话调试',
            'dashboard.recent': '最近实验',
            'dashboard.no_exp': '暂无实验',
            'dashboard.no_exp_desc': '上传数据集并创建您的第一个评测实验',
            'dashboard.create_exp': '创建实验',
            'dashboard.table.name': '名称',
            'dashboard.table.status': '状态',
            'dashboard.table.progress': '进度',
            'dashboard.table.created': '创建时间',

            // Datasets
            'datasets.title': '数据集管理',
            'datasets.subtitle': '上传 JSONL 数据集文件并管理评测数据',
            'datasets.upload': '上传数据集',
            'datasets.task_type': '任务类型',
            'datasets.task_type.qa': '问答 (QA)',
            'datasets.task_type.text_exam': '文本选择题',
            'datasets.task_type.image_mcq': '图片选择题',
            'datasets.task_type.api_calling': 'API 调用',
            'datasets.name': '数据集名称',
            'datasets.name_placeholder': '留空则使用文件名',
            'datasets.upload_file': '上传文件',
            'datasets.drop_text': '拖拽 JSONL 文件到此处，或',
            'datasets.drop_click': '点击选择文件',
            'datasets.upload_btn': '上传',
            'datasets.list': '数据集列表',
            'datasets.no_data': '暂无数据集',
            'datasets.no_data_desc': '上传您的第一个 JSONL 数据集',

            // Experiments
            'experiments.title': '实验配置',
            'experiments.subtitle': '创建和管理模型评测实验',
            'experiments.new': '新建实验',
            'experiments.create': '创建新实验',
            'experiments.step1': '基本信息',
            'experiments.step2': '模型与策略',
            'experiments.step3': '运行参数',
            'experiments.exp_name': '实验名称 *',
            'experiments.exp_name_placeholder': '例如: GPT-4 MMLU 测试',
            'experiments.description': '描述',
            'experiments.desc_placeholder': '实验描述（可选）',
            'experiments.dataset': '数据集 *',
            'experiments.select_dataset': '选择数据集...',
            'experiments.split': '数据分割',
            'experiments.max_samples': '最大样本数',
            'experiments.max_samples_placeholder': '全部',
            'experiments.model': '模型 *',
            'experiments.select_model': '选择模型...',
            'experiments.strategy': '推理策略',
            'experiments.strategy.direct': 'Direct',
            'experiments.strategy.direct_desc': '直接推理，速度最快',
            'experiments.strategy.cot': 'CoT',
            'experiments.strategy.cot_desc': '链式思维，逐步推理',
            'experiments.strategy.long_cot': 'Long CoT',
            'experiments.strategy.long_cot_desc': '深度思考，复杂问题',
            'experiments.strategy.tot': 'ToT',
            'experiments.strategy.tot_desc': '思维树，多路径探索',
            'experiments.concurrency': '并发数',
            'experiments.retry': '重试次数',
            'experiments.metrics': '评估指标',
            'experiments.cancel': '取消',
            'experiments.create_btn': '创建实验',
            'experiments.list': '实验列表',
            'experiments.no_exp': '暂无实验',
            'experiments.no_exp_desc': '点击上方按钮创建第一个实验',

            // Results
            'results.title': '结果分析',
            'results.subtitle': '查看实验评测指标与可视化图表',
            'results.select_exp': '选择实验查看结果...',
            'results.chart.accuracy': '准确率分布',
            'results.chart.latency': '延迟分布',

            // RAG
            'rag.title': '知识库管理',
            'rag.subtitle': '构建和管理 RAG 检索知识库',
            'rag.build': '构建知识库',
            'rag.kb_name': '知识库名称',
            'rag.kb_name_placeholder': '例如: medical_kb',
            'rag.chunk_strategy': '分块策略',
            'rag.chunk_strategy.topic': '按主题',
            'rag.chunk_strategy.sentence': '按句子',
            'rag.chunk_strategy.token': '按 Token',
            'rag.chunk_size': '分块大小',
            'rag.upload_doc': '上传文档 (JSONL)',
            'rag.build_btn': '构建',
            'rag.list': '知识库列表',
            'rag.no_kb': '暂无知识库',
            'rag.no_kb_desc': '上传文档并构建您的第一个知识库',

            // Chat
            'chat.title': '对话调试',
            'chat.subtitle': '与模型实时对话测试推理效果',
            'chat.model': '模型',
            'chat.strategy': '策略',
            'chat.start': '开始对话',
            'chat.start_desc': '在下方输入消息开始调试模型',
            'chat.input_placeholder': '输入消息... (Ctrl+Enter 发送)',
            'chat.thinking': '思考中',

            // Common
            'common.upload_progress': '上传中...',
            'common.validated': '验证通过',
            'common.validated_warn': '验证有警告',
            'common.upload_fail': '上传失败',
        },

        en: {
            // Sidebar
            'nav.dashboard': 'Dashboard',
            'nav.datasets': 'Datasets',
            'nav.experiments': 'Experiments',
            'nav.results': 'Results',
            'nav.rag': 'Knowledge Base',
            'nav.chat': 'Chat Debug',
            'sidebar.status.checking': 'Checking status...',
            'sidebar.status.failed': 'Connection failed',

            // Dashboard
            'dashboard.title': 'Dashboard',
            'dashboard.refresh': 'Refresh',
            'dashboard.updated_at': 'Updated at',
            'dashboard.stat.datasets': 'Datasets',
            'dashboard.stat.experiments': 'Experiments',
            'dashboard.stat.kbs': 'Knowledge Bases',
            'dashboard.stat.models': 'Models',
            'dashboard.quick.upload': 'Upload Dataset',
            'dashboard.quick.new_exp': 'New Experiment',
            'dashboard.quick.results': 'View Results',
            'dashboard.quick.chat': 'Chat Debug',
            'dashboard.recent': 'Recent Experiments',
            'dashboard.no_exp': 'No Experiments',
            'dashboard.no_exp_desc': 'Upload a dataset and create your first experiment',
            'dashboard.create_exp': 'Create Experiment',
            'dashboard.table.name': 'Name',
            'dashboard.table.status': 'Status',
            'dashboard.table.progress': 'Progress',
            'dashboard.table.created': 'Created',

            // Datasets
            'datasets.title': 'Dataset Management',
            'datasets.subtitle': 'Upload JSONL dataset files and manage evaluation data',
            'datasets.upload': 'Upload Dataset',
            'datasets.task_type': 'Task Type',
            'datasets.task_type.qa': 'QA',
            'datasets.task_type.text_exam': 'Text Exam',
            'datasets.task_type.image_mcq': 'Image MCQ',
            'datasets.task_type.api_calling': 'API Calling',
            'datasets.name': 'Dataset Name',
            'datasets.name_placeholder': 'Leave empty to use filename',
            'datasets.upload_file': 'Upload File',
            'datasets.drop_text': 'Drag & drop a JSONL file here, or',
            'datasets.drop_click': 'click to select',
            'datasets.upload_btn': 'Upload',
            'datasets.list': 'Dataset List',
            'datasets.no_data': 'No Datasets',
            'datasets.no_data_desc': 'Upload your first JSONL dataset',

            // Experiments
            'experiments.title': 'Experiment Configuration',
            'experiments.subtitle': 'Create and manage model evaluation experiments',
            'experiments.new': 'New Experiment',
            'experiments.create': 'Create Experiment',
            'experiments.step1': 'Basic Info',
            'experiments.step2': 'Model & Strategy',
            'experiments.step3': 'Run Parameters',
            'experiments.exp_name': 'Experiment Name *',
            'experiments.exp_name_placeholder': 'e.g. GPT-4 MMLU Test',
            'experiments.description': 'Description',
            'experiments.desc_placeholder': 'Description (optional)',
            'experiments.dataset': 'Dataset *',
            'experiments.select_dataset': 'Select dataset...',
            'experiments.split': 'Split',
            'experiments.max_samples': 'Max Samples',
            'experiments.max_samples_placeholder': 'All',
            'experiments.model': 'Model *',
            'experiments.select_model': 'Select model...',
            'experiments.strategy': 'Inference Strategy',
            'experiments.strategy.direct': 'Direct',
            'experiments.strategy.direct_desc': 'Direct inference, fastest',
            'experiments.strategy.cot': 'CoT',
            'experiments.strategy.cot_desc': 'Chain-of-thought reasoning',
            'experiments.strategy.long_cot': 'Long CoT',
            'experiments.strategy.long_cot_desc': 'Deep thinking, complex tasks',
            'experiments.strategy.tot': 'ToT',
            'experiments.strategy.tot_desc': 'Tree-of-thought, multi-path',
            'experiments.concurrency': 'Concurrency',
            'experiments.retry': 'Retries',
            'experiments.metrics': 'Eval Metrics',
            'experiments.cancel': 'Cancel',
            'experiments.create_btn': 'Create Experiment',
            'experiments.list': 'Experiment List',
            'experiments.no_exp': 'No Experiments',
            'experiments.no_exp_desc': 'Click the button above to create one',

            // Results
            'results.title': 'Results Analysis',
            'results.subtitle': 'View evaluation metrics and visualizations',
            'results.select_exp': 'Select experiment to view results...',
            'results.chart.accuracy': 'Accuracy Distribution',
            'results.chart.latency': 'Latency Distribution',

            // RAG
            'rag.title': 'Knowledge Base',
            'rag.subtitle': 'Build and manage RAG retrieval knowledge bases',
            'rag.build': 'Build Knowledge Base',
            'rag.kb_name': 'KB Name',
            'rag.kb_name_placeholder': 'e.g. medical_kb',
            'rag.chunk_strategy': 'Chunk Strategy',
            'rag.chunk_strategy.topic': 'By Topic',
            'rag.chunk_strategy.sentence': 'By Sentence',
            'rag.chunk_strategy.token': 'By Token',
            'rag.chunk_size': 'Chunk Size',
            'rag.upload_doc': 'Upload Document (JSONL)',
            'rag.build_btn': 'Build',
            'rag.list': 'Knowledge Base List',
            'rag.no_kb': 'No Knowledge Bases',
            'rag.no_kb_desc': 'Upload documents and build your first KB',

            // Chat
            'chat.title': 'Chat Debug',
            'chat.subtitle': 'Test model inference with real-time conversation',
            'chat.model': 'Model',
            'chat.strategy': 'Strategy',
            'chat.start': 'Start Conversation',
            'chat.start_desc': 'Type a message below to begin',
            'chat.input_placeholder': 'Type a message... (Ctrl+Enter to send)',
            'chat.thinking': 'Thinking',

            // Common
            'common.upload_progress': 'Uploading...',
            'common.validated': 'Validated',
            'common.validated_warn': 'Validated with warnings',
            'common.upload_fail': 'Upload failed',
        }
    },

    t(key) {
        const lang = this.translations[this.currentLang] || this.translations['zh'];
        return lang[key] || key;
    },

    setLang(lang) {
        this.currentLang = lang;
        localStorage.setItem('aik-lang', lang);
        this.applyAll();
    },

    toggle() {
        this.setLang(this.currentLang === 'zh' ? 'en' : 'zh');
    },

    applyAll() {
        // Apply translations to all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            const text = this.t(key);
            if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
                el.placeholder = text;
            } else if (el.tagName === 'OPTION') {
                el.textContent = text;
            } else {
                el.textContent = text;
            }
        });
        // Apply to data-i18n-placeholder
        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            el.placeholder = this.t(el.getAttribute('data-i18n-placeholder'));
        });
        // Update lang toggle button label
        const btn = document.getElementById('lang-toggle');
        if (btn) {
            btn.textContent = this.currentLang === 'zh' ? 'EN' : '中';
        }
    }
};
