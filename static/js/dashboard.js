// ===== DASHBOARD FUNCTIONALITY =====
class DashboardManager {
    constructor() {
        // Popular models data
        this.POPULAR_EMBEDDING_MODELS = [
            {
                name: "nomic-embed-text:latest",
                description: "Best all-around balance of accuracy and speed",
                category: "recommended",
                size: "~330MB",
                dimensions: 768,
                accuracy: "High",
                speed: "Fast",
                useCase: "Most documents, general purpose",
                ramRequired: "2GB+",
                pullCommand: "ollama pull nomic-embed-text"
            },
            {
                name: "mxbai-embed-large:latest",
                description: "Most accurate, best for complex documents",
                category: "accurate",
                size: "~1.4GB",
                dimensions: 1024,
                accuracy: "Very High",
                speed: "Medium",
                useCase: "Academic papers, technical docs",
                ramRequired: "4GB+",
                pullCommand: "ollama pull mxbai-embed-large"
            },
            {
                name: "all-minilm:latest",
                description: "Very fast, good for many simple documents",
                category: "fast",
                size: "~80MB",
                dimensions: 384,
                accuracy: "Good",
                speed: "Very Fast",
                useCase: "Many simple documents, fast search",
                ramRequired: "1GB+",
                pullCommand: "ollama pull all-minilm"
            },
            {
                name: "bge-small-en:latest",
                description: "Optimized for English text, efficient",
                category: "efficient",
                size: "~130MB",
                dimensions: 384,
                accuracy: "Good",
                speed: "Fast",
                useCase: "English documents, general purpose",
                ramRequired: "1.5GB+",
                pullCommand: "ollama pull bge-small-en"
            },
            {
                name: "e5-mistral:latest",
                description: "Based on Mistral, good for instruction following",
                category: "advanced",
                size: "~5GB",
                dimensions: 4096,
                accuracy: "Excellent",
                speed: "Slow",
                useCase: "Complex queries, instruction-based search",
                ramRequired: "8GB+",
                pullCommand: "ollama pull e5-mistral"
            },
            {
                name: "multilingual-e5:latest",
                description: "Supports multiple languages",
                category: "multilingual",
                size: "~2.3GB",
                dimensions: 1024,
                accuracy: "High",
                speed: "Medium",
                useCase: "Multilingual documents",
                ramRequired: "4GB+",
                pullCommand: "ollama pull multilingual-e5"
            }
        ];

        this.POPULAR_CHAT_MODELS = [
            {
                name: "qwen:0.5b",
                description: "Small, fast, efficient for basic tasks",
                size: "~300MB",
                ramRequired: "1GB+"
            },
            {
                name: "llama2:7b",
                description: "Good balance of capability and speed",
                size: "~4GB",
                ramRequired: "8GB+"
            },
            {
                name: "mistral:7b",
                description: "Excellent for reasoning tasks",
                size: "~4GB",
                ramRequired: "8GB+"
            },
            {
                name: "phi:latest",
                description: "Very fast, good for constrained environments",
                size: "~1.5GB",
                ramRequired: "4GB+"
            },
            {
                name: "gemma:2b",
                description: "Google's efficient model",
                size: "~1.5GB",
                ramRequired: "4GB+"
            },
            {
                name: "mixtral:8x7b",
                description: "Powerful mixture of experts model",
                size: "~25GB",
                ramRequired: "32GB+"
            }
        ];

        // State variables
        this.currentConfig = null;
        this.availableModels = null;
        this.currentTaskMonitor = null;
        this.taskPollingInterval = null;

        // DOM elements
        this.elements = {
            chatModelSelect: document.getElementById('chatModelSelect'),
            embeddingModelSelect: document.getElementById('embeddingModelSelect'),
            applyBtn: document.getElementById('applyBtn'),
            statusMessage: document.getElementById('statusMessage'),
            currentModelTag: document.getElementById('currentModelTag'),
            currentChatModel: document.getElementById('currentChatModel'),
            currentEmbeddingModel: document.getElementById('currentEmbeddingModel'),
            vectorStoreStatus: document.getElementById('vectorStoreStatus'),
            ollamaStatus: document.getElementById('ollamaStatus'),
            memoryText: document.getElementById('memoryText'),
            cpuText: document.getElementById('cpuText'),
            diskText: document.getElementById('diskText'),
            tasksText: document.getElementById('tasksText'),
            memoryBar: document.getElementById('memoryBar'),
            memoryLabel: document.getElementById('memoryLabel'),
            refreshModelsBtn: document.getElementById('refreshModelsBtn'),
            loadingOverlay: document.getElementById('loadingOverlay'),
            loadingText: document.getElementById('loadingText'),
            popularModelsGrid: document.getElementById('popularModelsGrid'),
            installMissingBtn: document.getElementById('installMissingBtn'),
            refreshModelsListBtn: document.getElementById('refreshModelsListBtn'),
            showGuideBtn: document.getElementById('showGuideBtn'),
            refreshResourcesBtn: document.getElementById('refreshResourcesBtn'),
            reindexBtn: document.getElementById('reindexBtn'),
            progressOverlay: document.getElementById('progressOverlay'),
            progressTitle: document.getElementById('progressTitle'),
            progressMessage: document.getElementById('progressMessage'),
            progressBar: document.getElementById('progressBar'),
            progressPercent: document.getElementById('progressPercent'),
            taskLogs: document.getElementById('taskLogs'),
            cancelTaskBtn: document.getElementById('cancelTaskBtn'),
            cpuPercent: document.getElementById('cpuPercent'),
            memoryPercent: document.getElementById('memoryPercent'),
            diskPercent: document.getElementById('diskPercent'),
            activeTasksCount: document.getElementById('activeTasksCount')
        };

        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        this.loadDashboard();
        
        // Setup periodic updates
        this.setupPeriodicUpdates();
    }

    setupEventListeners() {
        // Apply model changes
        this.elements.applyBtn.addEventListener('click', () => this.applyModelChanges());
        
        // Refresh buttons
        this.elements.refreshModelsBtn.addEventListener('click', () => this.refreshModels());
        this.elements.refreshModelsListBtn.addEventListener('click', () => this.refreshModels());
        
        // Install missing models
        this.elements.installMissingBtn.addEventListener('click', () => this.installMissingModels());
        
        // Refresh resources
        this.elements.refreshResourcesBtn.addEventListener('click', () => this.updateSystemResources());
        
        // Reindex documents
        this.elements.reindexBtn.addEventListener('click', () => this.startReindexing());
        
        // Cancel task
        this.elements.cancelTaskBtn.addEventListener('click', () => this.cancelCurrentTask());
        
        // Model select change listeners
        this.elements.chatModelSelect.addEventListener('change', () => {
            if (this.currentConfig && this.elements.chatModelSelect.value !== this.currentConfig.current.chat_model) {
                this.elements.applyBtn.disabled = false;
            }
        });

        this.elements.embeddingModelSelect.addEventListener('change', () => {
            if (this.currentConfig && this.elements.embeddingModelSelect.value !== this.currentConfig.current.embedding_model) {
                this.elements.applyBtn.disabled = false;
            }
        });

        // Global event handlers
        document.addEventListener('DOMContentLoaded', () => this.handlePageLoad());
        
        // Expose methods to window for onclick handlers
        window.useModel = (modelName) => this.useModel(modelName);
        window.installModel = (modelName, pullCommand) => this.installModelPrompt(modelName, pullCommand);
        window.showDetailedMetrics = () => this.showDetailedMetrics();
        window.showActiveTasks = () => this.showActiveTasks();
    }

    setupPeriodicUpdates() {
        // Auto-refresh system resources every 10 seconds
        setInterval(() => this.updateSystemResources(), 10000);
        
        // Auto-refresh active tasks every 5 seconds
        setInterval(() => this.checkActiveTasks(), 5000);
        
        // Auto-refresh status every 30 seconds
        setInterval(() => this.checkSystemStatus(), 30000);
    }

    async handlePageLoad() {
        // Show initial loading
        this.showLoading('Connecting to server...');
        
        // Check if server is responding with retry logic
        let serverReady = false;
        let retries = 3;
        
        while (retries > 0 && !serverReady) {
            try {
                const response = await fetch('/health', { 
                    method: 'GET',
                    headers: { 'Accept': 'application/json' },
                    signal: AbortSignal.timeout(5000)
                });
                
                if (response.ok) {
                    serverReady = true;
                    this.hideLoading();
                    await this.loadDashboard();
                    break;
                }
            } catch (error) {
                console.log(`Server check attempt ${4-retries} failed:`, error.message);
                retries--;
                
                if (retries > 0) {
                    this.elements.loadingText.textContent = `Waiting for server... Retrying in ${5 - retries} seconds`;
                    await new Promise(resolve => setTimeout(resolve, 1000));
                }
            }
        }
        
        if (!serverReady) {
            this.hideLoading();
            this.showStatus(
                'Server is not responding. Please ensure:<br>' +
                '1. FastAPI is running (python app/main.py)<br>' +
                '2. Port 8000 is not in use<br>' +
                '3. Check server logs for errors<br>' +
                '4. Try refreshing the page in a few seconds',
                'error'
            );
            return;
        }
        
        // Load initial configuration
        await this.loadDashboard();
        
        // Check for URL parameters
        const urlParams = new URLSearchParams(window.location.search);
        const updateStatus = urlParams.get('update');
        if (updateStatus === 'success') {
            this.showStatus('Models updated successfully!', 'success');
            window.history.replaceState({}, document.title, window.location.pathname);
        }
    }

    // ===== UI UTILITIES =====
    showLoading(text = 'Loading...') {
        this.elements.loadingText.textContent = text;
        this.elements.loadingOverlay.style.display = 'flex';
    }

    hideLoading() {
        this.elements.loadingOverlay.style.display = 'none';
        this.elements.loadingText.textContent = 'Loading...';
    }

    showProgress(title = 'Processing...') {
        this.elements.progressTitle.textContent = title;
        this.elements.progressOverlay.style.display = 'flex';
        this.elements.taskLogs.innerHTML = '';
    }

    hideProgress() {
        this.elements.progressOverlay.style.display = 'none';
        if (this.taskPollingInterval) {
            clearInterval(this.taskPollingInterval);
            this.taskPollingInterval = null;
        }
        this.currentTaskMonitor = null;
    }

    showStatus(message, type = 'info', duration = 5000) {
        this.elements.statusMessage.textContent = message;
        this.elements.statusMessage.className = `status-message status-${type}`;
        this.elements.statusMessage.style.display = 'block';
        
        // Auto-hide success messages after duration
        if (type === 'success') {
            setTimeout(() => {
                this.elements.statusMessage.style.display = 'none';
            }, duration);
        }
    }

    updateProgress(progress, message, logs = []) {
        this.elements.progressBar.style.width = `${progress}%`;
        this.elements.progressPercent.textContent = `${progress}%`;
        this.elements.progressMessage.textContent = message;
        
        // Update logs
        if (logs.length > 0) {
            this.elements.taskLogs.innerHTML = logs.map(log => 
                `<div class="log-entry">${log}</div>`
            ).join('');
            this.elements.taskLogs.scrollTop = this.elements.taskLogs.scrollHeight;
        }
    }

    // ===== DASHBOARD LOADING =====
    async loadDashboard() {
        try {
            this.showLoading('Loading configuration...');
            
            // Load current configuration
            const configResponse = await fetch('/api/system/config', {
                headers: { 'Accept': 'application/json' }
            });
            
            if (!configResponse.ok) {
                throw new Error(`Failed to load configuration: ${configResponse.status}`);
            }
            
            this.currentConfig = await configResponse.json();
            
            // Update UI with current configuration
            this.elements.currentModelTag.textContent = `Ollama: ${this.currentConfig.current.chat_model}`;
            this.elements.currentChatModel.textContent = this.currentConfig.current.chat_model;
            this.elements.currentEmbeddingModel.textContent = this.currentConfig.current.embedding_model;
            
            // Update selects with current values
            this.updateModelSelects();
            
            // Populate popular models grid
            this.populatePopularModels();
            
            // Check system status
            await this.checkSystemStatus();
            
            // Update system resources
            await this.updateSystemResources();
            
            // Check active tasks
            await this.checkActiveTasks();
            
            this.showStatus('Dashboard loaded successfully!', 'success', 3000);
            
        } catch (error) {
            console.error('Error loading configuration:', error);
            this.showStatus('Failed to load configuration: ' + error.message, 'error');
            this.elements.currentModelTag.textContent = 'Ollama: Error';
            this.elements.currentChatModel.textContent = 'Error loading model';
            this.elements.currentEmbeddingModel.textContent = 'Error loading model';
        } finally {
            this.hideLoading();
        }
    }

    updateModelSelects() {
        this.availableModels = this.currentConfig.available_models;
        
        // Update chat model select
        this.elements.chatModelSelect.innerHTML = '';
        if (this.availableModels.chat_models && this.availableModels.chat_models.length > 0) {
            // Add popular models first
            const popularSection = document.createElement('optgroup');
            popularSection.label = 'Popular Models';
            this.POPULAR_CHAT_MODELS.forEach(model => {
                if (this.availableModels.chat_models.includes(model.name)) {
                    const option = document.createElement('option');
                    option.value = model.name;
                    option.textContent = `${model.name} (${model.description})`;
                    if (model.name === this.currentConfig.current.chat_model) {
                        option.selected = true;
                    }
                    popularSection.appendChild(option);
                }
            });
            this.elements.chatModelSelect.appendChild(popularSection);
            
            // Add all other models
            const otherSection = document.createElement('optgroup');
            otherSection.label = 'All Available Models';
            this.availableModels.chat_models.forEach(model => {
                if (!this.POPULAR_CHAT_MODELS.some(m => m.name === model)) {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model;
                    if (model === this.currentConfig.current.chat_model) {
                        option.selected = true;
                    }
                    otherSection.appendChild(option);
                }
            });
            this.elements.chatModelSelect.appendChild(otherSection);
        } else {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No chat models available';
            this.elements.chatModelSelect.appendChild(option);
            this.elements.chatModelSelect.disabled = true;
        }
        
        // Update embedding model select
        this.elements.embeddingModelSelect.innerHTML = '';
        if (this.availableModels.embedding_models && this.availableModels.embedding_models.length > 0) {
            // Add popular embedding models first
            const popularSection = document.createElement('optgroup');
            popularSection.label = 'Recommended Embedding Models';
            this.POPULAR_EMBEDDING_MODELS.forEach(model => {
                if (this.availableModels.embedding_models.includes(model.name)) {
                    const option = document.createElement('option');
                    option.value = model.name;
                    option.textContent = `${model.name} (${model.description})`;
                    if (model.name === this.currentConfig.current.embedding_model) {
                        option.selected = true;
                    }
                    popularSection.appendChild(option);
                }
            });
            this.elements.embeddingModelSelect.appendChild(popularSection);
            
            // Add all other embedding models
            const otherSection = document.createElement('optgroup');
            otherSection.label = 'All Embedding Models';
            this.availableModels.embedding_models.forEach(model => {
                if (!this.POPULAR_EMBEDDING_MODELS.some(m => m.name === model)) {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model;
                    if (model === this.currentConfig.current.embedding_model) {
                        option.selected = true;
                    }
                    otherSection.appendChild(option);
                }
            });
            this.elements.embeddingModelSelect.appendChild(otherSection);
        } else {
            // If no embedding models found, show all models
            if (this.availableModels.chat_models && this.availableModels.chat_models.length > 0) {
                const allSection = document.createElement('optgroup');
                allSection.label = 'All Available Models (Can be used for embedding)';
                this.availableModels.chat_models.forEach(model => {
                    const option = document.createElement('option');
                    option.value = model;
                    option.textContent = model;
                    if (model === this.currentConfig.current.embedding_model) {
                        option.selected = true;
                    }
                    allSection.appendChild(option);
                });
                this.elements.embeddingModelSelect.appendChild(allSection);
            } else {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No models available';
                this.elements.embeddingModelSelect.appendChild(option);
                this.elements.embeddingModelSelect.disabled = true;
            }
        }
        
        // Enable apply button if we have models
        this.elements.applyBtn.disabled = !this.availableModels || 
            (!this.availableModels.chat_models && !this.availableModels.embedding_models);
    }

    populatePopularModels() {
        this.elements.popularModelsGrid.innerHTML = '';
        
        this.POPULAR_EMBEDDING_MODELS.forEach(model => {
            const isAvailable = this.availableModels && 
                (this.availableModels.embedding_models || []).includes(model.name);
            const isCurrent = this.currentConfig.current.embedding_model === model.name;
            
            const modelCard = document.createElement('div');
            modelCard.className = `model-card ${model.category} ${isCurrent ? 'current' : ''}`;
            
            // Determine badge based on category
            let badgeClass = '';
            let badgeText = '';
            switch(model.category) {
                case 'recommended':
                    badgeClass = 'badge-recommended';
                    badgeText = 'RECOMMENDED';
                    break;
                case 'accurate':
                    badgeClass = 'badge-accurate';
                    badgeText = 'ACCURATE';
                    break;
                case 'fast':
                    badgeClass = 'badge-fast';
                    badgeText = 'FAST';
                    break;
                case 'efficient':
                    badgeClass = 'badge-efficient';
                    badgeText = 'EFFICIENT';
                    break;
                case 'advanced':
                    badgeClass = 'badge-advanced';
                    badgeText = 'ADVANCED';
                    break;
                case 'multilingual':
                    badgeClass = 'badge-multilingual';
                    badgeText = 'MULTILINGUAL';
                    break;
                default:
                    badgeClass = 'badge-recommended';
                    badgeText = model.category.toUpperCase();
            }
            
            modelCard.innerHTML = `
                <div class="model-header">
                    <div class="model-name" title="${model.name}">${model.name}</div>
                    <div class="model-badge ${badgeClass}">${badgeText}</div>
                </div>
                <div class="model-desc">${model.description}</div>
                <div class="model-stats">
                    <span>Size: ${model.size}</span>
                    <span>Dim: ${model.dimensions}</span>
                    <span>RAM: ${model.ramRequired}</span>
                </div>
                <div class="model-stats">
                    <span>Accuracy: ${model.accuracy}</span>
                    <span>Speed: ${model.speed}</span>
                </div>
                <div class="model-action">
                    ${isAvailable ? 
                        `<button class="btn-use-model" data-model="${model.name}" ${isCurrent ? 'disabled' : ''}>
                            ${isCurrent ? '<i class="fas fa-check"></i> Current Model' : 'Use This Model'}
                        </button>` :
                        `<button class="btn-use-model" data-model="${model.name}" data-command="${model.pullCommand}" style="background: var(--warning);">
                            <i class="fas fa-download"></i> Install Model
                        </button>`
                    }
                </div>
            `;
            
            // Add event listeners
            const useButton = modelCard.querySelector('.btn-use-model');
            if (isAvailable && !isCurrent) {
                useButton.addEventListener('click', () => this.useModel(model.name));
            } else if (!isAvailable) {
                useButton.addEventListener('click', () => this.installModelPrompt(model.name, model.pullCommand));
            }
            
            this.elements.popularModelsGrid.appendChild(modelCard);
        });
    }

    // ===== MODEL MANAGEMENT =====
    useModel(modelName) {
        if (!modelName) return;
        
        // Set the embedding model select to this model
        this.elements.embeddingModelSelect.value = modelName;
        
        // Enable apply button
        this.elements.applyBtn.disabled = false;
        
        this.showStatus(`Selected model: ${modelName}. Click "Apply Model Changes" to use it.`, 'info');
        
        // Scroll to model selector
        document.querySelector('.model-selector').scrollIntoView({ behavior: 'smooth' });
    }

    installModelPrompt(modelName, pullCommand) {
        if (!confirm(`Install ${modelName}?\n\nThis will run: ${pullCommand}\n\nThis may take several minutes depending on your internet speed and model size.`)) {
            return;
        }
        
        this.installModel(modelName);
    }

    async installModel(modelName) {
        try {
            this.showProgress(`Installing ${modelName}`);
            
            // Send request to install model
            const response = await fetch('/install-model', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model: modelName
                })
            });
            
            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.detail || 'Failed to start installation');
            }
            
            const result = await response.json();
            
            if (result.task_id) {
                // Start monitoring the task
                this.monitorTask(result.task_id, modelName);
            } else {
                throw new Error('No task ID returned');
            }
            
        } catch (error) {
            console.error('Error installing model:', error);
            this.hideProgress();
            this.showStatus('Failed to install model: ' + error.message, 'error');
        }
    }

    async installMissingModels() {
        if (!this.availableModels || !this.availableModels.embedding_models) return;
        
        const missingModels = this.POPULAR_EMBEDDING_MODELS.filter(model => 
            !this.availableModels.embedding_models.includes(model.name)
        );
        
        if (missingModels.length === 0) {
            this.showStatus('All popular models are already installed!', 'info');
            return;
        }
        
        const modelList = missingModels.map(m => m.name).join('\n');
        if (!confirm(`Install ${missingModels.length} missing models?\n\n${modelList}\n\nThis may take 10-20 minutes depending on your internet speed and model sizes.`)) {
            return;
        }
        
        try {
            this.showProgress(`Installing ${missingModels.length} models`);
            
            // Start with first model
            const firstModel = missingModels[0];
            const response = await fetch('/install-model', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model: firstModel.name
                })
            });
            
            if (!response.ok) {
                throw new Error('Failed to start installation');
            }
            
            const result = await response.json();
            
            if (result.task_id) {
                this.monitorTask(result.task_id, `Installing ${missingModels.length} models`);
            }
            
        } catch (error) {
            console.error('Error installing models:', error);
            this.hideProgress();
            this.showStatus('Failed to install models: ' + error.message, 'error');
        }
    }

    async applyModelChanges() {
        const selectedChatModel = this.elements.chatModelSelect.value;
        const selectedEmbeddingModel = this.elements.embeddingModelSelect.value;
        
        // Validate selections
        if (!selectedChatModel || !selectedEmbeddingModel) {
            this.showStatus('Please select both a chat model and an embedding model', 'error');
            return;
        }
        
        if (selectedChatModel === this.currentConfig.current.chat_model && 
            selectedEmbeddingModel === this.currentConfig.current.embedding_model) {
            this.showStatus('No changes detected', 'info');
            return;
        }
        
        try {
            this.showLoading('Applying model changes...');
            this.elements.applyBtn.disabled = true;
            this.elements.applyBtn.innerHTML = '<i class="fas fa-spinner loading"></i> Applying...';
            
            // Prepare update data
            const updateData = {};
            if (selectedChatModel !== this.currentConfig.current.chat_model) {
                updateData.chat_model = selectedChatModel;
            }
            if (selectedEmbeddingModel !== this.currentConfig.current.embedding_model) {
                updateData.embedding_model = selectedEmbeddingModel;
            }
            
            // Send update request
            const response = await fetch('/config/model', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(updateData)
            });
            
            const result = await response.json();
            
            if (response.ok && result.success) {
                this.showStatus(result.message || 'Models updated successfully!', 'success');
                
                // Update UI with new values
                this.elements.currentModelTag.textContent = `Ollama: ${selectedChatModel}`;
                this.elements.currentChatModel.textContent = selectedChatModel;
                this.elements.currentEmbeddingModel.textContent = selectedEmbeddingModel;
                
                // Update current config
                this.currentConfig.current.chat_model = selectedChatModel;
                this.currentConfig.current.embedding_model = selectedEmbeddingModel;
                
                // Update model selects to show current selection
                this.updateModelSelects();
                
            } else {
                throw new Error(result.error || 'Failed to update models');
            }
            
        } catch (error) {
            console.error('Error applying model changes:', error);
            this.showStatus('Failed to update models: ' + error.message, 'error');
        } finally {
            this.elements.applyBtn.disabled = false;
            this.elements.applyBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Apply Model Changes';
            this.hideLoading();
        }
    }

    // ===== TASK MANAGEMENT =====
    async monitorTask(taskId, taskName = 'Task') {
        if (!taskId) return;
        
        this.showProgress(taskName);
        this.currentTaskMonitor = taskId;
        
        // Set up polling for task progress
        this.taskPollingInterval = setInterval(async () => {
            try {
                const response = await fetch(`/tasks/progress/${taskId}`, {
                    headers: { 'Accept': 'application/json' }
                });
                
                if (!response.ok) {
                    if (response.status === 404) {
                        this.updateProgress(0, `Task ${taskId} not found`, [`Task ${taskId} was not found on the server`]);
                        clearInterval(this.taskPollingInterval);
                        setTimeout(() => {
                            this.hideProgress();
                            this.showStatus(`Task ${taskName} was not found on server`, 'error');
                        }, 2000);
                        return;
                    }
                    throw new Error(`Failed to get task progress: ${response.status}`);
                }
                
                const progress = await response.json();
                
                // Update progress display
                this.updateProgress(
                    progress.progress || 0,
                    progress.message || 'Processing...',
                    progress.logs || []
                );
                
                // Check if task is completed
                if (progress.status === 'completed') {
                    clearInterval(this.taskPollingInterval);
                    setTimeout(() => {
                        this.hideProgress();
                        this.showStatus(`${taskName} completed successfully!`, 'success');
                        // Refresh configuration to update available models
                        this.loadDashboard();
                    }, 2000);
                } else if (progress.status === 'failed') {
                    clearInterval(this.taskPollingInterval);
                    this.hideProgress();
                    this.showStatus(`${taskName} failed: ${progress.message}`, 'error');
                } else if (progress.status === 'cancelled') {
                    clearInterval(this.taskPollingInterval);
                    this.hideProgress();
                    this.showStatus(`${taskName} cancelled`, 'info');
                }
                
            } catch (error) {
                console.error('Error monitoring task:', error);
                this.updateProgress(0, 'Error monitoring task', [`Error: ${error.message}`]);
            }
        }, 1000);
    }

    async cancelCurrentTask() {
        if (!this.currentTaskMonitor) return;
        
        if (confirm('Are you sure you want to cancel this task?')) {
            try {
                const response = await fetch(`/tasks/${this.currentTaskMonitor}`, {
                    method: 'DELETE'
                });
                
                if (response.ok) {
                    this.showStatus('Task cancellation requested', 'info');
                }
            } catch (error) {
                console.error('Error cancelling task:', error);
                this.showStatus('Failed to cancel task: ' + error.message, 'error');
            }
        }
    }

    // ===== SYSTEM STATUS =====
    async checkSystemStatus() {
        try {
            // Check health
            const healthResponse = await fetch('/health', {
                headers: { 'Accept': 'application/json' }
            });
            
            if (healthResponse.ok) {
                const healthData = await healthResponse.json();
                
                // Update vector store status
                this.elements.vectorStoreStatus.textContent = healthData.vector_store_ready ? 
                    'Ready ✓' : 'Not ready (run ingest)';
                this.elements.vectorStoreStatus.className = healthData.vector_store_ready ? 
                    'status-value success' : 'status-value warning';
                
                // Update Ollama status
                this.elements.ollamaStatus.textContent = healthData.ollama_connected ? 
                    'Connected ✓' : 'Disconnected ✗';
                this.elements.ollamaStatus.className = healthData.ollama_connected ? 
                    'status-value success' : 'status-value error';
                
                // Update memory status
                if (healthData.memory_usage) {
                    this.elements.memoryText.textContent = healthData.memory_usage;
                }
            } else {
                throw new Error(`Health check failed: ${healthResponse.status}`);
            }
            
        } catch (error) {
            console.error('Error checking system status:', error);
            this.elements.vectorStoreStatus.textContent = 'Error checking';
            this.elements.vectorStoreStatus.className = 'status-value error';
            this.elements.ollamaStatus.textContent = 'Error checking';
            this.elements.ollamaStatus.className = 'status-value error';
        }
    }

    async updateSystemResources() {
        try {
            const response = await fetch('/api/system/status', {
                headers: { 'Accept': 'application/json' }
            });
            
            if (response.ok) {
                const data = await response.json();
                
                // Update memory visualization
                const memPercent = data.memory.percent;
                this.elements.memoryBar.style.width = `${memPercent}%`;
                this.elements.memoryBar.className = memPercent > 90 ? 'memory-used danger' : 
                                            memPercent > 70 ? 'memory-used warning' : 'memory-used';
                
                this.elements.memoryLabel.textContent = `${memPercent}% (${data.memory.available_gb}GB free)`;
                this.elements.memoryText.textContent = `${data.memory.percent}% - ${data.memory.available_gb}GB free of ${data.memory.total_gb}GB`;
                this.elements.memoryPercent.textContent = `${memPercent}%`;
                
                // Update CPU
                const cpuPercentValue = data.cpu.percent;
                this.elements.cpuText.textContent = `${cpuPercentValue}%`;
                this.elements.cpuPercent.textContent = `${cpuPercentValue}%`;
                
                // Update disk
                const diskPercentValue = data.disk.percent;
                this.elements.diskText.textContent = `${diskPercentValue}% - ${data.disk.free_gb}GB free of ${data.disk.total_gb}GB`;
                this.elements.diskPercent.textContent = `${diskPercentValue}%`;
                
                // Update tasks
                const activeTasks = data.system.active_tasks || 0;
                this.elements.tasksText.textContent = activeTasks;
                this.elements.activeTasksCount.textContent = activeTasks;
                
            } else {
                console.warn('Failed to fetch system status:', response.status);
            }
        } catch (error) {
            console.error('Error updating system resources:', error);
        }
    }

    async checkActiveTasks() {
        try {
            const response = await fetch('/api/tasks/active', {
                headers: { 'Accept': 'application/json' }
            });
            
            if (response.ok) {
                const data = await response.json();
                // Update task count
                this.elements.tasksText.textContent = data.active.length;
                this.elements.activeTasksCount.textContent = data.active.length;
            }
        } catch (error) {
            console.error('Error checking active tasks:', error);
        }
    }

    // ===== ACTIONS =====
    async refreshModels() {
        try {
            this.showLoading('Refreshing models list...');
            this.elements.refreshModelsBtn.innerHTML = '<i class="fas fa-spinner loading"></i> Refreshing...';
            this.elements.refreshModelsListBtn.innerHTML = '<i class="fas fa-spinner loading"></i> Refreshing...';
            
            // Reload configuration
            await this.loadDashboard();
            
            this.showStatus('Models refreshed successfully!', 'success');
        } catch (error) {
            console.error('Error refreshing models:', error);
            this.showStatus('Failed to refresh models: ' + error.message, 'error');
        } finally {
            this.elements.refreshModelsBtn.innerHTML = '<i class="fas fa-redo"></i> Refresh Models';
            this.elements.refreshModelsListBtn.innerHTML = '<i class="fas fa-redo"></i> Refresh Available Models';
            this.hideLoading();
        }
    }

    async startReindexing() {
        if (!confirm('Reindex all documents? This may take several minutes depending on the number of files.')) {
            return;
        }
        
        try {
            this.showLoading('Starting reindexing...');
            
            const response = await fetch('/tasks/start/reindex', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            
            if (response.ok) {
                const result = await response.json();
                this.hideLoading();
                this.monitorTask(result.task_id, 'Reindexing Documents');
            } else {
                throw new Error('Failed to start reindexing');
            }
        } catch (error) {
            this.hideLoading();
            this.showStatus('Failed to start reindexing: ' + error.message, 'error');
        }
    }

    async showDetailedMetrics() {
        try {
            this.showLoading('Loading detailed metrics...');
            
            const response = await fetch('/api/system/status', {
                headers: { 'Accept': 'application/json' }
            });
            
            if (response.ok) {
                const data = await response.json();
                
                let details = `
                    <strong>System Metrics:</strong><br><br>
                    <strong>CPU:</strong><br>
                    - Usage: ${data.cpu.percent}%<br>
                    - Cores: ${data.cpu.cores}<br>
                    - Load Average: ${data.cpu.load_average.join(', ')}<br><br>
                    
                    <strong>Memory:</strong><br>
                    - Total: ${data.memory.total_gb}GB<br>
                    - Used: ${data.memory.used_gb}GB<br>
                    - Available: ${data.memory.available_gb}GB<br>
                    - Usage: ${data.memory.percent}%<br>
                    - Swap Used: ${data.memory.swap_used_gb}GB of ${data.memory.swap_total_gb}GB<br><br>
                    
                    <strong>Disk:</strong><br>
                    - Total: ${data.disk.total_gb}GB<br>
                    - Used: ${data.disk.used_gb}GB<br>
                    - Free: ${data.disk.free_gb}GB<br>
                    - Usage: ${data.disk.percent}%<br><br>
                    
                    <strong>Process:</strong><br>
                    - Memory: ${data.process.memory_mb}MB<br>
                    - CPU: ${data.process.cpu_percent}%<br>
                    - Threads: ${data.process.threads}<br><br>
                    
                    <strong>System:</strong><br>
                    - Active Tasks: ${data.system.active_tasks}<br>
                    - Ollama Connected: ${data.system.ollama_connected ? 'Yes' : 'No'}<br>
                    - Ollama Models: ${data.system.ollama_models_count}<br>
                    - Vector Store Ready: ${data.system.vector_store_ready ? 'Yes' : 'No'}<br>
                `;
                
                this.hideLoading();
                alert(details);
            }
        } catch (error) {
            this.hideLoading();
            this.showStatus('Failed to load detailed metrics: ' + error.message, 'error');
        }
    }

    async showActiveTasks() {
        try {
            this.showLoading('Loading active tasks...');
            
            const response = await fetch('/api/tasks/active', {
                headers: { 'Accept': 'application/json' }
            });
            
            if (response.ok) {
                const data = await response.json();
                
                let tasksInfo = `<strong>Active Tasks (${data.active.length}):</strong><br><br>`;
                
                if (data.active.length === 0) {
                    tasksInfo += 'No active tasks<br><br>';
                } else {
                    data.active.forEach(task => {
                        tasksInfo += `
                            <strong>${task.type.toUpperCase()}:</strong><br>
                            - ID: ${task.task_id}<br>
                            - Progress: ${task.progress}%<br>
                            - Status: ${task.message}<br>
                            - Started: ${new Date(task.start_time).toLocaleTimeString()}<br><br>
                        `;
                    });
                }
                
                tasksInfo += `<strong>Recent Tasks (${data.recent.length}):</strong><br><br>`;
                
                if (data.recent.length === 0) {
                    tasksInfo += 'No recent tasks';
                } else {
                    data.recent.forEach(task => {
                        tasksInfo += `
                            <strong>${task.type.toUpperCase()}:</strong><br>
                            - Status: ${task.status}<br>
                            - Progress: ${task.progress}%<br>
                            - Duration: ${task.duration ? Math.round(task.duration) + 's' : 'N/A'}<br><br>
                        `;
                    });
                }
                
                this.hideLoading();
                alert(tasksInfo);
            }
        } catch (error) {
            this.hideLoading();
            this.showStatus('Failed to load tasks: ' + error.message, 'error');
        }
    }
}

// ===== INITIALIZE DASHBOARD =====
document.addEventListener('DOMContentLoaded', () => {
    window.dashboardManager = new DashboardManager();
});