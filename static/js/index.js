// Dashboard JavaScript - Main functionality

// Dashboard module
const Dashboard = {
    // Initialize the dashboard
    init: function() {
        console.log('Dashboard initialized');
        
        // Set up event listeners
        this.setupEventListeners();
        
        // Fetch initial data
        this.fetchAllData();
        
        // Set up auto-refresh every 30 seconds
        this.autoRefreshInterval = setInterval(() => this.fetchAllData(), 30000);
        
        console.log('Dashboard setup complete');
    },
    
    // Setup event listeners
    setupEventListeners: function() {
        // Manual refresh button
        const refreshBtn = document.getElementById('refreshBtn');
        if (refreshBtn) {
            refreshBtn.addEventListener('click', () => this.refresh());
        }
        
        // Health check button
        const healthBtn = document.getElementById('healthBtn');
        if (healthBtn) {
            healthBtn.addEventListener('click', () => this.checkHealth());
        }
        
        // Model update buttons are handled via onclick in HTML
        console.log('Event listeners setup complete');
    },
    
    // Fetch all dashboard data
    fetchAllData: async function() {
        try {
            console.log('Fetching all dashboard data...');
            
            // Update timestamp immediately
            this.updateTimestamp();
            
            // Fetch engine status
            await this.fetchAIEngineStatus();
            
            // Fetch system resources
            await this.fetchSystemResources();
            
            // Load available models (only on first load and every minute)
            if (!this.modelsLoaded || Date.now() - this.lastModelLoad > 60000) {
                await this.loadAvailableModels();
                this.modelsLoaded = true;
                this.lastModelLoad = Date.now();
            }
            
            console.log('Dashboard data updated successfully');
            
        } catch (error) {
            console.error('Error fetching dashboard data:', error);
            this.showNotification('Error loading dashboard data', 'error');
        }
    },
    
    // Fetch AI Engine status
    fetchAIEngineStatus: async function() {
        try {
            const response = await fetch('/api/engine-status');
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            
            const data = await response.json();
            console.log('Engine status:', data);
            
            // Update status values with styling
            this.updateStatusElement('currentChatModel', data.chatModel);
            this.updateStatusElement('currentEmbeddingModel', data.embeddingModel);
            
            // Special handling for connection status
            this.updateConnectionStatus('vectorStoreStatus', data.vectorStore, 'vectorStoreTime');
            this.updateConnectionStatus('ollamaStatus', data.ollamaStatus, 'ollamaTime');
            
        } catch (error) {
            console.error('Failed to fetch AI engine status:', error);
            this.setErrorState('currentChatModel', 'Error');
            this.setErrorState('currentEmbeddingModel', 'Error');
            this.setErrorState('vectorStoreStatus', 'Connection Error');
            this.setErrorState('ollamaStatus', 'Connection Error');
        }
    },
    
    // Fetch system resources
    fetchSystemResources: async function() {
        try {
            const response = await fetch('/api/system/status');
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            
            const data = await response.json();
            console.log('System resources:', data);
            
            // Update memory
            this.updateMemoryUsage(data.memory);
            
            // Update CPU
            this.updateCpuUsage(data.cpu);
            
            // Update disk
            this.updateDiskUsage(data.disk);
            
        } catch (error) {
            console.error('Failed to fetch system resources:', error);
            this.setErrorState('memoryPercent', 'Error');
            this.setErrorState('cpuPercent', 'Error');
            this.setErrorState('diskPercent', 'Error');
        }
    },
    
    // Update memory usage display
    updateMemoryUsage: function(memory) {
        const percent = memory.percent || 0;
        const progressBar = document.getElementById('memoryProgress');
        if (!progressBar) return;
        
        progressBar.style.width = `${percent}%`;
        
        // Change color based on usage
        progressBar.className = 'progress-fill';
        if (percent > 80) {
            progressBar.classList.add('danger');
        } else if (percent > 60) {
            progressBar.classList.add('warning');
        }
        
        this.setTextContent('memoryUsed', `${(memory.used_gb || 0).toFixed(1)} GB`);
        this.setTextContent('memoryPercent', `${percent.toFixed(1)}%`);
        this.setTextContent('memoryTotal', `${(memory.total_gb || 0).toFixed(1)} GB`);
    },
    
    // Update CPU usage display
    updateCpuUsage: function(cpu) {
        const percent = cpu.percent || 0;
        const progressBar = document.getElementById('cpuProgress');
        if (!progressBar) return;
        
        progressBar.style.width = `${percent}%`;
        
        // Change color based on usage
        progressBar.className = 'progress-fill';
        if (percent > 80) {
            progressBar.classList.add('danger');
        } else if (percent > 60) {
            progressBar.classList.add('warning');
        }
        
        this.setTextContent('cpuCores', `Cores: ${cpu.cores || 'N/A'}`);
        this.setTextContent('cpuPercent', `${percent.toFixed(1)}%`);
        
        // Load average if available
        if (cpu.load_average && cpu.load_average.length > 0) {
            this.setTextContent('cpuLoad', `Load: ${cpu.load_average[0].toFixed(2)}`);
        }
    },
    
    // Update disk usage display
    updateDiskUsage: function(disk) {
        const percent = disk.percent || 0;
        const progressBar = document.getElementById('diskProgress');
        if (!progressBar) return;
        
        progressBar.style.width = `${percent}%`;
        
        // Change color based on usage
        progressBar.className = 'progress-fill';
        if (percent > 90) {
            progressBar.classList.add('danger');
        } else if (percent > 80) {
            progressBar.classList.add('warning');
        }
        
        this.setTextContent('diskUsed', `${(disk.used_gb || 0).toFixed(1)} GB`);
        this.setTextContent('diskPercent', `${percent.toFixed(1)}%`);
        this.setTextContent('diskTotal', `${(disk.total_gb || 0).toFixed(1)} GB`);
    },
    
    // Load available models
    loadAvailableModels: async function() {
        try {
            console.log('Loading available models...');
            const response = await fetch('/api/config');
            if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            
            const data = await response.json();
            console.log('Available models data:', data);
            
            // Populate chat models
            this.populateModelSelect('chatModelSelect', data.current.chat_model, data.available_models?.chat_models || []);
            
            // Populate embedding models
            this.populateModelSelect('embeddingModelSelect', data.current.embedding_model, data.available_models?.embedding_models || []);
            
        } catch (error) {
            console.error('Failed to load available models:', error);
            this.showNotification('Error loading available models', 'error');
        }
    },
    
    // Populate model select dropdown
    populateModelSelect: function(selectId, currentModel, availableModels) {
        const select = document.getElementById(selectId);
        if (!select) {
            console.error(`Select element ${selectId} not found`);
            return;
        }
        
        select.innerHTML = '';
        
        if (!availableModels || availableModels.length === 0) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No models available';
            option.disabled = true;
            select.appendChild(option);
            return;
        }
        
        // Add current model as first option
        const currentOption = document.createElement('option');
        currentOption.value = currentModel;
        currentOption.textContent = `${currentModel} (Current)`;
        currentOption.selected = true;
        select.appendChild(currentOption);
        
        // Add separator
        const separator = document.createElement('option');
        separator.disabled = true;
        separator.textContent = '──────────';
        select.appendChild(separator);
        
        // Add other available models (excluding current)
        const otherModels = availableModels.filter(model => model !== currentModel);
        otherModels.forEach(model => {
            const option = document.createElement('option');
            option.value = model;
            option.textContent = model;
            select.appendChild(option);
        });
        
        // Enable update button
        const btnId = selectId === 'chatModelSelect' ? 'updateChatBtn' : 'updateEmbeddingBtn';
        const button = document.getElementById(btnId);
        if (button) {
            button.disabled = false;
        }
        
        console.log(`Populated ${selectId} with ${otherModels.length + 1} models`);
    },
    
    // Update chat model
    updateChatModel: async function() {
        console.log('updateChatModel called');
        const select = document.getElementById('chatModelSelect');
        const btn = document.getElementById('updateChatBtn');
        
        if (!select || !btn) {
            console.error('Chat model select or button not found');
            return;
        }
        
        const newModel = select.value;
        console.log('Selected model:', newModel);
        
        if (!newModel || newModel.includes('(Current)')) {
            this.showNotification('Please select a different model', 'warning');
            return;
        }
        
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
        btn.disabled = true;
        
        try {
            console.log('Sending update request for chat model:', newModel);
            const response = await fetch('/api/config/model', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    chat_model: newModel
                })
            });
            
            console.log('Update response status:', response.status);
            const result = await response.json();
            console.log('Update response data:', result);
            
            if (!response.ok) {
                throw new Error(result.error || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            if (result.success) {
                this.showNotification('Chat model updated successfully! Changes take effect immediately.', 'success');
                // Refresh all data
                await this.fetchAllData();
                // Reset models loaded flag to refresh dropdown
                this.modelsLoaded = false;
            } else {
                this.showNotification(result.error || 'Failed to update model', 'error');
            }
            
        } catch (error) {
            console.error('Error updating chat model:', error);
            this.showNotification('Error updating chat model: ' + error.message, 'error');
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    },
    
    // Update embedding model
    updateEmbeddingModel: async function() {
        console.log('updateEmbeddingModel called');
        const select = document.getElementById('embeddingModelSelect');
        const btn = document.getElementById('updateEmbeddingBtn');
        
        if (!select || !btn) {
            console.error('Embedding model select or button not found');
            return;
        }
        
        const newModel = select.value;
        console.log('Selected model:', newModel);
        
        if (!newModel || newModel.includes('(Current)')) {
            this.showNotification('Please select a different model', 'warning');
            return;
        }
        
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
        btn.disabled = true;
        
        try {
            console.log('Sending update request for embedding model:', newModel);
            const response = await fetch('/api/config/model', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                },
                body: JSON.stringify({
                    embedding_model: newModel
                })
            });
            
            console.log('Update response status:', response.status);
            const result = await response.json();
            console.log('Update response data:', result);
            
            if (!response.ok) {
                throw new Error(result.error || `HTTP ${response.status}: ${response.statusText}`);
            }
            
            if (result.success) {
                this.showNotification('Embedding model updated successfully! Note: You may need to re-index documents.', 'success');
                // Refresh all data
                await this.fetchAllData();
                // Reset models loaded flag to refresh dropdown
                this.modelsLoaded = false;
            } else {
                this.showNotification(result.error || 'Failed to update model', 'error');
            }
            
        } catch (error) {
            console.error('Error updating embedding model:', error);
            this.showNotification('Error updating embedding model: ' + error.message, 'error');
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    },
    
    // Check system health
    checkHealth: async function() {
        try {
            const response = await fetch('/api/health');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            this.showNotification(`System status: ${data.status}`, 'info');
        } catch (error) {
            this.showNotification('Health check failed', 'error');
        }
    },
    
    // Helper: Update status element
    updateStatusElement: function(elementId, value) {
        const element = document.getElementById(elementId);
        if (!element) {
            console.warn(`Element ${elementId} not found`);
            return;
        }
        
        element.textContent = value || 'Unknown';
        element.className = 'status-value';
    },
    
    // Helper: Update connection status with color coding
    updateConnectionStatus: function(elementId, value, timeElementId) {
        const element = document.getElementById(elementId);
        const timeElement = timeElementId ? document.getElementById(timeElementId) : null;
        
        if (!element) {
            console.warn(`Element ${elementId} not found`);
            return;
        }
        
        element.textContent = value || 'Unknown';
        element.className = 'status-value';
        
        // Add appropriate class based on status
        if (value && (value.includes('Ready') || value.includes('Connected'))) {
            element.classList.add('connected');
        } else if (value && (value.includes('Not ready') || value.includes('Disconnected'))) {
            element.classList.add('disconnected');
        }
        
        // Update timestamp
        if (timeElement) {
            const now = new Date();
            timeElement.textContent = `Last updated: ${now.toLocaleTimeString()}`;
        }
    },
    
    // Helper: Set text content safely
    setTextContent: function(elementId, text) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text;
        } else {
            console.warn(`Element ${elementId} not found for text: ${text}`);
        }
    },
    
    // Helper: Set error state
    setErrorState: function(elementId, text) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text;
            element.className = 'status-value';
            element.classList.add('disconnected');
        }
    },
    
    // Update timestamp
    updateTimestamp: function() {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        const dateString = now.toLocaleDateString();
        
        // Update last update time
        this.setTextContent('lastUpdateTime', `${dateString} ${timeString}`);
        
        // Update any timestamp elements
        const timestampElements = document.querySelectorAll('.timestamp:not(#lastUpdateTime)');
        timestampElements.forEach(el => {
            if (!el.id || !el.id.includes('Time')) {
                el.textContent = `Last updated: ${timeString}`;
            }
        });
    },
    
    // Show notification
    showNotification: function(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <i class="fas ${this.getNotificationIcon(type)}"></i>
                <span>${message}</span>
            </div>
            <button class="notification-close" onclick="this.parentElement.remove()">
                <i class="fas fa-times"></i>
            </button>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    },
    
    // Get notification icon based on type
    getNotificationIcon: function(type) {
        switch(type) {
            case 'success': return 'fa-check-circle';
            case 'error': return 'fa-exclamation-circle';
            case 'warning': return 'fa-exclamation-triangle';
            default: return 'fa-info-circle';
        }
    },
    
    // Manual refresh function
    refresh: function() {
        console.log('Manual refresh triggered');
        this.fetchAllData();
        this.showNotification('Dashboard refreshed', 'info');
    },
    
    // Clean up (for single page applications)
    destroy: function() {
        if (this.autoRefreshInterval) {
            clearInterval(this.autoRefreshInterval);
        }
    },
    
    // State
    modelsLoaded: false,
    lastModelLoad: 0,
    autoRefreshInterval: null
};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    Dashboard.init();
});

// Make Dashboard available globally
window.Dashboard = Dashboard;

// Add refresh function to window for console access
window.refreshDashboard = function() {
    Dashboard.refresh();
};
