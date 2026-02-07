// Model Manager - Handles model discovery, installation, and management

const ModelManager = {
    // Model database with requirements
    modelDatabase: {
        chat: [
            {
                name: "qwen:0.5b",
                displayName: "Qwen 0.5B",
                description: "Lightweight Chinese model, good for basic tasks",
                size: "0.5B",
                ram: "1 GB",
                disk: "0.3 GB",
                speed: "⚡⚡⚡⚡",
                quality: "⭐⭐",
                category: "lightweight",
                tags: ["fast", "multilingual", "beginner"]
            },
            {
                name: "phi:2.7b",
                displayName: "Phi-2.7B",
                description: "Microsoft's small but capable model",
                size: "2.7B",
                ram: "3 GB",
                disk: "1.6 GB",
                speed: "⚡⚡⚡",
                quality: "⭐⭐⭐",
                category: "balanced",
                tags: ["fast", "efficient", "general"]
            },
            {
                name: "mistral:7b",
                displayName: "Mistral 7B",
                description: "Fast, efficient, great for coding and general tasks",
                size: "7B",
                ram: "8 GB",
                disk: "4.2 GB",
                speed: "⚡⚡",
                quality: "⭐⭐⭐⭐",
                category: "recommended",
                tags: ["coding", "efficient", "popular"]
            },
            {
                name: "llama3:8b",
                displayName: "Llama 3 8B",
                description: "Meta's latest, excellent all-around performance",
                size: "8B",
                ram: "10 GB",
                disk: "4.7 GB",
                speed: "⚡⚡",
                quality: "⭐⭐⭐⭐",
                category: "recommended",
                tags: ["latest", "general", "english"]
            },
            {
                name: "llama3:70b",
                displayName: "Llama 3 70B",
                description: "High-quality model for demanding tasks",
                size: "70B",
                ram: "80 GB",
                disk: "40 GB",
                speed: "⚡",
                quality: "⭐⭐⭐⭐⭐",
                category: "powerful",
                tags: ["high-quality", "memory-hungry", "professional"]
            },
            {
                name: "mixtral:8x7b",
                displayName: "Mixtral 8x7B",
                description: "Mixture of Experts, very capable",
                size: "47B",
                ram: "50 GB",
                disk: "26 GB",
                speed: "⚡",
                quality: "⭐⭐⭐⭐⭐",
                category: "powerful",
                tags: ["expert", "high-quality", "large"]
            },
            {
                name: "gemma:7b",
                displayName: "Gemma 7B",
                description: "Google's lightweight model",
                size: "7B",
                ram: "8 GB",
                disk: "4.5 GB",
                speed: "⚡⚡",
                quality: "⭐⭐⭐",
                category: "balanced",
                tags: ["google", "lightweight", "general"]
            },
            {
                name: "tinyllama:1.1b",
                displayName: "TinyLlama 1.1B",
                description: "Very fast, good for testing and prototyping",
                size: "1.1B",
                ram: "1.5 GB",
                disk: "0.7 GB",
                speed: "⚡⚡⚡⚡⚡",
                quality: "⭐",
                category: "lightweight",
                tags: ["fastest", "testing", "prototype"]
            }
        ],
        embedding: [
            {
                name: "all-minilm:latest",
                displayName: "All-MiniLM",
                description: "Lightweight, fast, good accuracy",
                size: "Small",
                ram: "1 GB",
                disk: "0.2 GB",
                speed: "⚡⚡⚡⚡",
                quality: "⭐⭐⭐",
                category: "recommended",
                tags: ["fast", "lightweight", "general"]
            },
            {
                name: "nomic-embed-text:latest",
                displayName: "Nomic Embed Text",
                description: "Best overall, 8192 context length",
                size: "Medium",
                ram: "2 GB",
                disk: "0.4 GB",
                speed: "⚡⚡⚡",
                quality: "⭐⭐⭐⭐⭐",
                category: "best",
                tags: ["best", "long-context", "general"]
            },
            {
                name: "mxbai-embed-large:latest",
                displayName: "MXBAI Embed Large",
                description: "High quality embeddings",
                size: "Large",
                ram: "3 GB",
                disk: "0.8 GB",
                speed: "⚡⚡",
                quality: "⭐⭐⭐⭐",
                category: "powerful",
                tags: ["high-quality", "accurate", "english"]
            },
            {
                name: "bge-large-en:latest",
                displayName: "BGE Large English",
                description: "Popular for English tasks",
                size: "Large",
                ram: "3 GB",
                disk: "1.2 GB",
                speed: "⚡⚡",
                quality: "⭐⭐⭐⭐",
                category: "powerful",
                tags: ["english", "popular", "accurate"]
            },
            {
                name: "multilingual-e5-large:latest",
                displayName: "Multilingual E5 Large",
                description: "For multilingual support",
                size: "Large",
                ram: "4 GB",
                disk: "1.5 GB",
                speed: "⚡⚡",
                quality: "⭐⭐⭐⭐",
                category: "specialized",
                tags: ["multilingual", "multiple-languages"]
            }
        ]
    },

    // Current state
    currentState: {
        installedModels: [],
        currentChatModel: "",
        currentEmbeddingModel: "",
        systemResources: null,
        activeTab: "chat"
    },

    // Initialize
    init: async function() {
        console.log("Model Manager initialized");
        
        // Load initial data
        await this.loadInstalledModels();
        await this.loadCurrentModels();
        
        // Load chat models tab by default
        this.showTab('chat');
        
        // Update recommendations
        this.updateRecommendations();
    },

    // Load installed models from Ollama
    loadInstalledModels: async function() {
        try {
            const response = await fetch('/api/models/installed');
            if (response.ok) {
                const data = await response.json();
                this.currentState.installedModels = data.models || [];
                console.log("Installed models loaded:", this.currentState.installedModels);
            } else {
                // Fallback: Try direct Ollama API
                await this.loadInstalledModelsFallback();
            }
        } catch (error) {
            console.error("Failed to load installed models:", error);
            await this.loadInstalledModelsFallback();
        }
    },

    // Fallback method to load installed models
    loadInstalledModelsFallback: async function() {
        try {
            const response = await fetch('/api/config');
            if (response.ok) {
                const data = await response.json();
                // Extract from config
                this.currentState.installedModels = [
                    data.current.chat_model,
                    data.current.embedding_model
                ].filter(Boolean);
            }
        } catch (error) {
            console.error("Fallback also failed:", error);
            this.currentState.installedModels = [];
        }
    },

    // Load current active models
    loadCurrentModels: async function() {
        try {
            const response = await fetch('/api/config');
            if (response.ok) {
                const data = await response.json();
                this.currentState.currentChatModel = data.current.chat_model;
                this.currentState.currentEmbeddingModel = data.current.embedding_model;
                
                // Update UI
                this.updateCurrentModelsUI();
            }
        } catch (error) {
            console.error("Failed to load current models:", error);
        }
    },

    // Update current models in UI
    updateCurrentModelsUI: function() {
        const chatModel = this.findModelInfo(this.currentState.currentChatModel, 'chat');
        const embeddingModel = this.findModelInfo(this.currentState.currentEmbeddingModel, 'embedding');
        
        if (chatModel) {
            document.getElementById('activeChatModelName').textContent = chatModel.displayName;
            document.getElementById('activeChatModelSize').textContent = `Size: ${chatModel.size}`;
            document.getElementById('activeChatModelRAM').textContent = `RAM: ${chatModel.ram}`;
        }
        
        if (embeddingModel) {
            document.getElementById('activeEmbeddingModelName').textContent = embeddingModel.displayName;
            document.getElementById('activeEmbeddingModelSize').textContent = `Size: ${embeddingModel.size}`;
            document.getElementById('activeEmbeddingModelRAM').textContent = `RAM: ${embeddingModel.ram}`;
        }
    },

    // Find model information
    findModelInfo: function(modelName, type) {
        const models = this.modelDatabase[type] || [];
        return models.find(m => m.name === modelName);
    },

    // Show specific tab
    showTab: function(tabName) {
        // Update tabs
        document.querySelectorAll('.tab-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.textContent.toLowerCase().includes(tabName)) {
                btn.classList.add('active');
            }
        });
        
        // Update content
        document.querySelectorAll('.model-tab').forEach(tab => {
            tab.classList.remove('active');
        });
        
        const tabId = tabName + 'ModelsTab';
        const tabElement = document.getElementById(tabId);
        if (tabElement) {
            tabElement.classList.add('active');
        }
        
        this.currentState.activeTab = tabName;
        this.loadTabContent(tabName);
    },

    // Load content for tab
    loadTabContent: function(tabName) {
        switch(tabName) {
            case 'chat':
                this.renderModelList('chat');
                break;
            case 'embedding':
                this.renderModelList('embedding');
                break;
            case 'installed':
                this.renderInstalledModels();
                break;
        }
    },

    // Render model list
    renderModelList: function(type) {
        const container = document.getElementById(`${type}ModelsTab`).querySelector('.model-list');
        const models = this.modelDatabase[type];
        
        if (!models || models.length === 0) {
            container.innerHTML = '<p>No models found</p>';
            return;
        }
        
        let html = '';
        models.forEach(model => {
            const isInstalled = this.currentState.installedModels.includes(model.name);
            const isCurrent = type === 'chat' 
                ? model.name === this.currentState.currentChatModel
                : model.name === this.currentState.currentEmbeddingModel;
            
            html += `
                <div class="model-card ${isInstalled ? 'installed' : ''} ${isCurrent ? 'current' : ''}">
                    <div class="model-header">
                        <span class="model-title">${model.displayName}</span>
                        <span class="model-status ${isCurrent ? 'status-current' : isInstalled ? 'status-installed' : 'status-available'}">
                            ${isCurrent ? 'Active' : isInstalled ? 'Installed' : 'Available'}
                        </span>
                    </div>
                    <p class="model-description">${model.description}</p>
                    <div class="model-stats">
                        <span class="model-stat">${model.size}</span>
                        <span class="model-stat">${model.ram} RAM</span>
                        <span class="model-stat">${model.speed}</span>
                        <span class="model-stat">${model.quality}</span>
                    </div>
                    <div class="model-actions">
                        ${isCurrent ? `
                            <button class="btn btn-secondary" disabled>Current</button>
                        ` : isInstalled ? `
                            <button class="btn btn-primary" onclick="ModelManager.applyModel('${model.name}', '${type}')">
                                Apply
                            </button>
                        ` : `
                            <button class="btn btn-primary" onclick="ModelManager.showInstallModal('${model.name}', '${type}')">
                                Install
                            </button>
                        `}
                        <button class="btn btn-secondary" onclick="ModelManager.showModelDetails('${model.name}', '${type}')">
                            Details
                        </button>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    },

    // Render installed models
    renderInstalledModels: function() {
        const container = document.getElementById('installedModelsTab').querySelector('.model-list');
        
        if (this.currentState.installedModels.length === 0) {
            container.innerHTML = '<p>No models installed yet.</p>';
            return;
        }
        
        let html = '';
        this.currentState.installedModels.forEach(modelName => {
            // Try to find model info
            let modelInfo = this.findModelInfo(modelName, 'chat') || 
                           this.findModelInfo(modelName, 'embedding');
            
            if (!modelInfo) {
                modelInfo = {
                    displayName: modelName,
                    description: "Installed model",
                    size: "Unknown",
                    ram: "Unknown"
                };
            }
            
            const isChat = modelName.includes(this.currentState.currentChatModel);
            const isEmbedding = modelName.includes(this.currentState.currentEmbeddingModel);
            const isCurrent = isChat || isEmbedding;
            const type = isChat ? 'chat' : 'embedding';
            
            html += `
                <div class="model-card installed ${isCurrent ? 'current' : ''}">
                    <div class="model-header">
                        <span class="model-title">${modelInfo.displayName}</span>
                        <span class="model-status ${isCurrent ? 'status-current' : 'status-installed'}">
                            ${isCurrent ? 'Active' : 'Installed'}
                        </span>
                    </div>
                    <p class="model-description">${modelInfo.description}</p>
                    <div class="model-stats">
                        <span class="model-stat">${modelInfo.size}</span>
                        <span class="model-stat">${modelInfo.ram} RAM</span>
                    </div>
                    <div class="model-actions">
                        ${isCurrent ? `
                            <button class="btn btn-secondary" disabled>Current</button>
                        ` : `
                            <button class="btn btn-primary" onclick="ModelManager.applyModel('${modelName}', '${type}')">
                                Apply
                            </button>
                        `}
                        <button class="btn btn-danger" onclick="ModelManager.showUninstallModal('${modelName}')">
                            Remove
                        </button>
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    },

    // Show chat models
    showChatModels: function() {
        this.showTab('chat');
    },

    // Show embedding models
    showEmbeddingModels: function() {
        this.showTab('embedding');
    },

    // Show install modal
    showInstallModal: function(modelName, modelType) {
        const model = this.findModelInfo(modelName, modelType);
        if (!model) return;
        
        this.currentState.selectedModel = model;
        this.currentState.selectedModelType = modelType;
        
        // Update modal content
        document.getElementById('installModelName').textContent = model.displayName;
        document.getElementById('installModelType').textContent = modelType === 'chat' ? 'Chat Model' : 'Embedding Model';
        document.getElementById('installModelSize').textContent = model.size;
        document.getElementById('installModelRAM').textContent = model.ram;
        document.getElementById('installModelDisk').textContent = model.disk || '0.5 GB';
        
        // Load system resources
        this.updateSystemResourcesInModal();
        
        // Show modal
        document.getElementById('installModal').classList.add('active');
        
        // Reset progress
        document.getElementById('installProgress').style.display = 'none';
        document.getElementById('installModelInfo').style.display = 'block';
        document.getElementById('installConfirmBtn').style.display = 'block';
        document.getElementById('installCancelBtn').textContent = 'Cancel';
    },

    // Update system resources in modal
    updateSystemResourcesInModal: function() {
        // Get system resources from dashboard
        const memoryAvailable = document.getElementById('memoryAvailable')?.textContent || '0 GB';
        const diskFree = document.getElementById('diskFree')?.textContent || '0 GB';
        
        document.getElementById('installAvailableRAM').textContent = memoryAvailable;
        document.getElementById('installAvailableDisk').textContent = diskFree;
        
        // Check compatibility
        this.checkCompatibility();
    },

    // Check compatibility
    checkCompatibility: function() {
        const model = this.currentState.selectedModel;
        const compatibilityDiv = document.getElementById('installCompatibility');
        
        if (!model) return;
        
        // Parse available RAM (simplified)
        const availableRAM = this.parseSize(document.getElementById('installAvailableRAM').textContent);
        const requiredRAM = this.parseSize(model.ram);
        
        if (availableRAM >= requiredRAM * 0.8) { // 80% of required
            compatibilityDiv.className = 'compatibility-check compatibility-ok';
            compatibilityDiv.innerHTML = `
                <p><i class="fas fa-check-circle"></i> Your system meets the requirements</p>
                <p>Required: ${model.ram} | Available: ${document.getElementById('installAvailableRAM').textContent}</p>
            `;
        } else if (availableRAM >= requiredRAM * 0.5) { // 50% of required
            compatibilityDiv.className = 'compatibility-check compatibility-warning';
            compatibilityDiv.innerHTML = `
                <p><i class="fas fa-exclamation-triangle"></i> Your system may struggle with this model</p>
                <p>Required: ${model.ram} | Available: ${document.getElementById('installAvailableRAM').textContent}</p>
                <p><small>Performance may be degraded</small></p>
            `;
        } else {
            compatibilityDiv.className = 'compatibility-check compatibility-error';
            compatibilityDiv.innerHTML = `
                <p><i class="fas fa-times-circle"></i> Your system may not have enough RAM</p>
                <p>Required: ${model.ram} | Available: ${document.getElementById('installAvailableRAM').textContent}</p>
                <p><small>Consider a smaller model</small></p>
            `;
        }
    },

    // Parse size string (e.g., "8 GB" to number in GB)
    parseSize: function(sizeString) {
        const match = sizeString.match(/(\d+(?:\.\d+)?)\s*(GB|MB)/i);
        if (!match) return 0;
        
        const value = parseFloat(match[1]);
        const unit = match[2].toLowerCase();
        
        if (unit === 'gb') return value;
        if (unit === 'mb') return value / 1024;
        return 0;
    },

    // Confirm installation
    confirmInstall: async function() {
        const model = this.currentState.selectedModel;
        if (!model) return;
        
        // Show progress
        document.getElementById('installModelInfo').style.display = 'none';
        document.getElementById('installProgress').style.display = 'block';
        document.getElementById('installConfirmBtn').style.display = 'none';
        document.getElementById('installCancelBtn').textContent = 'Close';
        
        // Start installation
        await this.installModel(model.name);
    },

    // Install model via API
    installModel: async function(modelName) {
        try {
            const response = await fetch('/api/models/install', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model: modelName
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            const logContainer = document.getElementById('installLog');
            
            while (true) {
                const { done, value } = await reader.read();
                if (done) break;
                
                const text = decoder.decode(value);
                const lines = text.split('\n');
                
                lines.forEach(line => {
                    if (line.trim()) {
                        try {
                            const data = JSON.parse(line);
                            this.updateInstallProgress(data);
                            
                            // Add to log
                            const logEntry = document.createElement('div');
                            logEntry.className = 'install-log-entry';
                            logEntry.textContent = data.message || data.status || JSON.stringify(data);
                            logContainer.appendChild(logEntry);
                            logContainer.scrollTop = logContainer.scrollHeight;
                        } catch (e) {
                            // Not JSON, log as text
                            if (line.trim()) {
                                const logEntry = document.createElement('div');
                                logEntry.className = 'install-log-entry';
                                logEntry.textContent = line;
                                logContainer.appendChild(logEntry);
                                logContainer.scrollTop = logContainer.scrollHeight;
                            }
                        }
                    }
                });
            }
            
            // Installation complete
            this.showNotification(`Model ${modelName} installed successfully!`, 'success');
            
            // Reload installed models
            await this.loadInstalledModels();
            await this.renderModelList(this.currentState.activeTab);
            
        } catch (error) {
            console.error('Installation failed:', error);
            this.showNotification(`Installation failed: ${error.message}`, 'error');
        }
    },

    // Update installation progress
    updateInstallProgress: function(data) {
        if (data.progress) {
            const progress = data.progress * 100;
            document.getElementById('installProgressBar').style.width = `${progress}%`;
            document.getElementById('installProgressText').textContent = `${Math.round(progress)}%`;
        }
        
        if (data.status) {
            document.getElementById('installStatus').textContent = data.status;
        }
    },

    // Apply model
    applyModel: async function(modelName, modelType) {
        try {
            const field = modelType === 'chat' ? 'chat_model' : 'embedding_model';
            const response = await fetch('/api/config/model', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    [field]: modelName
                })
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification(`Model switched to ${modelName}`, 'success');
                
                // Update current models
                await this.loadCurrentModels();
                
                // Reload current tab
                this.loadTabContent(this.currentState.activeTab);
                
                // Also refresh dashboard
                if (window.Dashboard) {
                    window.Dashboard.fetchAllData();
                }
            } else {
                throw new Error(result.error || 'Failed to apply model');
            }
        } catch (error) {
            console.error('Failed to apply model:', error);
            this.showNotification(`Failed to apply model: ${error.message}`, 'error');
        }
    },

    // Show model details
    showModelDetails: function(modelName, modelType) {
        const model = this.findModelInfo(modelName, modelType);
        if (!model) return;
        
        let details = `
            <h4>${model.displayName}</h4>
            <p><strong>Description:</strong> ${model.description}</p>
            <p><strong>Model ID:</strong> ${model.name}</p>
            <p><strong>Size:</strong> ${model.size}</p>
            <p><strong>Required RAM:</strong> ${model.ram}</p>
            <p><strong>Speed:</strong> ${model.speed}</p>
            <p><strong>Quality:</strong> ${model.quality}</p>
            <p><strong>Category:</strong> ${model.category}</p>
        `;
        
        if (model.tags && model.tags.length > 0) {
            details += `<p><strong>Tags:</strong> ${model.tags.join(', ')}</p>`;
        }
        
        this.showNotification(details, 'info');
    },

    // Show uninstall modal
    showUninstallModal: function(modelName) {
        if (confirm(`Are you sure you want to remove ${modelName}? This will free up disk space.`)) {
            this.uninstallModel(modelName);
        }
    },

    // Uninstall model
    uninstallModel: async function(modelName) {
        try {
            const response = await fetch('/api/models/uninstall', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    model: modelName
                })
            });
            
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification(`Model ${modelName} removed successfully`, 'success');
                
                // Reload installed models
                await this.loadInstalledModels();
                this.renderInstalledModels();
            } else {
                throw new Error(result.error || 'Failed to remove model');
            }
        } catch (error) {
            console.error('Failed to remove model:', error);
            this.showNotification(`Failed to remove model: ${error.message}`, 'error');
        }
    },

    // Close modal
    closeModal: function() {
        document.getElementById('installModal').classList.remove('active');
        this.currentState.selectedModel = null;
    },

    // Update recommendations based on system resources
    updateRecommendations: function() {
        const container = document.getElementById('recommendationsList');
        
        // Get system resources from dashboard
        const memoryElement = document.getElementById('memoryAvailable');
        const memoryText = memoryElement?.textContent || '0 GB';
        const availableRAM = this.parseSize(memoryText);
        
        let recommendations = '';
        
        // Recommend based on available RAM
        if (availableRAM > 50) {
            recommendations = `
                <div class="recommendation-item">
                    <div class="recommendation-title">
                        <span>Llama 3 70B</span>
                        <span class="recommendation-badge">Powerful</span>
                    </div>
                    <p class="recommendation-reason">Your system has plenty of RAM for high-quality models</p>
                    <div class="recommendation-stats">
                        <span>80GB RAM</span>
                        <span>⭐⭐⭐⭐⭐ Quality</span>
                        <span>Professional</span>
                    </div>
                </div>
            `;
        } else if (availableRAM > 8) {
            recommendations = `
                <div class="recommendation-item">
                    <div class="recommendation-title">
                        <span>Llama 3 8B</span>
                        <span class="recommendation-badge">Recommended</span>
                    </div>
                    <p class="recommendation-reason">Balanced performance for your available resources</p>
                    <div class="recommendation-stats">
                        <span>10GB RAM</span>
                        <span>⭐⭐⭐⭐ Quality</span>
                        <span>All-purpose</span>
                    </div>
                </div>
                <div class="recommendation-item">
                    <div class="recommendation-title">
                        <span>Mistral 7B</span>
                        <span class="recommendation-badge">Efficient</span>
                    </div>
                    <p class="recommendation-reason">Fast and efficient, great for coding tasks</p>
                    <div class="recommendation-stats">
                        <span>8GB RAM</span>
                        <span>⭐⭐⭐⭐ Quality</span>
                        <span>Coding</span>
                    </div>
                </div>
            `;
        } else if (availableRAM > 2) {
            recommendations = `
                <div class="recommendation-item">
                    <div class="recommendation-title">
                        <span>Phi-2.7B</span>
                        <span class="recommendation-badge">Balanced</span>
                    </div>
                    <p class="recommendation-reason">Good performance for limited RAM systems</p>
                    <div class="recommendation-stats">
                        <span>3GB RAM</span>
                        <span>⭐⭐⭐ Quality</span>
                        <span>General use</span>
                    </div>
                </div>
                <div class="recommendation-item">
                    <div class="recommendation-title">
                        <span>Qwen 0.5B</span>
                        <span class="recommendation-badge">Lightweight</span>
                    </div>
                    <p class="recommendation-reason">Very fast, good for testing and basic tasks</p>
                    <div class="recommendation-stats">
                        <span>1GB RAM</span>
                        <span>⭐⭐ Quality</span>
                        <span>Fast testing</span>
                    </div>
                </div>
            `;
        } else {
            recommendations = `
                <div class="recommendation-item">
                    <div class="recommendation-title">
                        <span>TinyLlama 1.1B</span>
                        <span class="recommendation-badge">Minimal</span>
                    </div>
                    <p class="recommendation-reason">Smallest model for systems with very limited RAM</p>
                    <div class="recommendation-stats">
                        <span>1.5GB RAM</span>
                        <span>⭐ Quality</span>
                        <span>Testing only</span>
                    </div>
                </div>
            `;
        }
        
        // Embedding recommendation (always the same)
        recommendations += `
            <div class="recommendation-item">
                <div class="recommendation-title">
                    <span>Nomic Embed Text</span>
                    <span class="recommendation-badge">Best Embedding</span>
                </div>
                <p class="recommendation-reason">Best overall embedding model with long context support</p>
                <div class="recommendation-stats">
                    <span>2GB RAM</span>
                    <span>8192 tokens</span>
                    <span>Top quality</span>
                </div>
            </div>
        `;
        
        container.innerHTML = recommendations;
    },

    // Show notification
    showNotification: function(message, type = 'info') {
        // Check if it's HTML content
        if (message.includes('<')) {
            // Create a modal for detailed info
            const modal = document.createElement('div');
            modal.className = 'modal active';
            modal.innerHTML = `
                <div class="modal-content" style="max-width: 500px;">
                    <div class="modal-header">
                        <h3><i class="fas fa-info-circle"></i> Model Details</h3>
                        <button class="modal-close" onclick="this.parentElement.parentElement.remove()">&times;</button>
                    </div>
                    <div class="modal-body">
                        ${message}
                    </div>
                    <div class="modal-footer">
                        <button class="btn btn-primary" onclick="this.parentElement.parentElement.parentElement.remove()">Close</button>
                    </div>
                </div>
            `;
            document.body.appendChild(modal);
        } else {
            // Use existing dashboard notification
            if (window.Dashboard && window.Dashboard.showNotification) {
                window.Dashboard.showNotification(message, type);
            } else {
                alert(message);
            }
        }
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    ModelManager.init();
});

// Make available globally
window.ModelManager = ModelManager;
