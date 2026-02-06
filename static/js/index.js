// Dashboard JavaScript - Main functionality

// Dashboard module
const Dashboard = {
    // Initialize the dashboard
    init: function() {
        console.log('Dashboard initialized');
        
        // Fetch initial data
        this.fetchAllData();
        
        // Set up auto-refresh
        this.autoRefreshInterval = setInterval(() => this.fetchAllData(), 30000);
        
        // Add notification styles
        this.addNotificationStyles();
        
        // Set up manual refresh button if exists
        this.setupManualRefresh();
    },
    
    // Fetch all dashboard data
    fetchAllData: async function() {
        try {
            console.log('Fetching all dashboard data...');
            
            // Fetch engine status
            await this.fetchAIEngineStatus();
            
            // Fetch system resources
            await this.fetchSystemResources();
            
            // Load available models (only on first load and every minute)
            if (!this.modelsLoaded) {
                await this.loadAvailableModels();
                this.modelsLoaded = true;
            }
            
            // Update timestamp
            this.updateTimestamp();
            
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
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            // Update status values with styling
            this.updateStatusElement('currentChatModel', data.chatModel);
            this.updateStatusElement('currentEmbeddingModel', data.embeddingModel);
            
            // Special handling for connection status
            this.updateConnectionStatus('vectorStoreStatus', data.vectorStore, 'vectorStoreTime');
            this.updateConnectionStatus('ollamaStatus', data.ollamaStatus, 'ollamaTime');
            
        } catch (error) {
            console.error('Failed to fetch AI engine status:', error);
            this.showNotification('Error fetching engine status', 'error');
            
            // Set error states
            this.setErrorState('currentChatModel', 'Error');
            this.setErrorState('currentEmbeddingModel', 'Error');
            this.setErrorState('vectorStoreStatus', 'Error');
            this.setErrorState('ollamaStatus', 'Error');
        }
    },
    
    // Fetch system resources
    fetchSystemResources: async function() {
        try {
            const response = await fetch('/api/system/status');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            // Update memory
            this.updateMemoryUsage(data.memory);
            
            // Update CPU
            this.updateCpuUsage(data.cpu);
            
            // Update disk
            this.updateDiskUsage(data.disk);
            
        } catch (error) {
            console.error('Failed to fetch system resources:', error);
            // Don't show notification for system resources - they're less critical
        }
    },
    
    // Update memory usage display
    updateMemoryUsage: function(memory) {
        const percent = memory.percent;
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
        
        this.setTextContent('memoryUsed', `${memory.used_gb?.toFixed(1) || '0.0'} GB`);
        this.setTextContent('memoryPercent', `${percent?.toFixed(1) || '0.0'}%`);
        this.setTextContent('memoryTotal', `${memory.total_gb?.toFixed(1) || '0.0'} GB`);
    },
    
    // Update CPU usage display
    updateCpuUsage: function(cpu) {
        const percent = cpu.percent;
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
        this.setTextContent('cpuPercent', `${percent?.toFixed(1) || '0.0'}%`);
        
        // Load average if available
        if (cpu.load_average && cpu.load_average.length > 0) {
            this.setTextContent('cpuLoad', `Load: ${cpu.load_average[0]?.toFixed(2) || '0.00'}`);
        }
    },
    
    // Update disk usage display
    updateDiskUsage: function(disk) {
        const percent = disk.percent;
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
        
        this.setTextContent('diskUsed', `${disk.used_gb?.toFixed(1) || '0.0'} GB`);
        this.setTextContent('diskPercent', `${percent?.toFixed(1) || '0.0'}%`);
        this.setTextContent('diskTotal', `${disk.total_gb?.toFixed(1) || '0.0'} GB`);
    },
    
    // Load available models
    loadAvailableModels: async function() {
        try {
            const response = await fetch('/api/config');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            
            const data = await response.json();
            
            // Populate chat models
            this.populateModelSelect('chatModelSelect', data.current.chat_model, data.available_models.chat_models);
            
            // Populate embedding models
            this.populateModelSelect('embeddingModelSelect', data.current.embedding_model, data.available_models.embedding_models);
            
        } catch (error) {
            console.error('Failed to load available models:', error);
            this.showNotification('Error loading available models', 'error');
        }
    },
    
    // Populate model select dropdown
    populateModelSelect: function(selectId, currentModel, availableModels) {
        const select = document.getElementById(selectId);
        if (!select) return;
        
        select.innerHTML = '';
        
        // Add current model as first option
        const currentOption = document.createElement('option');
        currentOption.value = currentModel;
        currentOption.textContent = `${currentModel} (Current)`;
        currentOption.selected = true;
        select.appendChild(currentOption);
        
        // Add separator
        const separator = document.createElement('option');
        separator.disabled = true;
        separator.textContent = '────────────';
        select.appendChild(separator);
        
        // Add other available models (excluding current)
        const otherModels = (availableModels || []).filter(model => model !== currentModel);
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
    },
    
    // Update chat model
    updateChatModel: async function() {
        const select = document.getElementById('chatModelSelect');
        const newModel = select?.value;
        const btn = document.getElementById('updateChatBtn');
        
        if (!newModel || newModel.includes('(Current)')) {
            this.showNotification('Please select a different model', 'warning');
            return;
        }
        
        if (!btn) return;
        
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
        btn.disabled = true;
        
        try {
            const response = await fetch('/api/config/model', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    chat_model: newModel
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Chat model updated successfully!', 'success');
                // Refresh all data
                await this.fetchAllData();
                // Reset models loaded flag to refresh dropdown
                this.modelsLoaded = false;
            } else {
                this.showNotification(result.error || 'Failed to update model', 'error');
            }
            
        } catch (error) {
            console.error('Error updating chat model:', error);
            this.showNotification('Error updating chat model', 'error');
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    },
    
    // Update embedding model
    updateEmbeddingModel: async function() {
        const select = document.getElementById('embeddingModelSelect');
        const newModel = select?.value;
        const btn = document.getElementById('updateEmbeddingBtn');
        
        if (!newModel || newModel.includes('(Current)')) {
            this.showNotification('Please select a different model', 'warning');
            return;
        }
        
        if (!btn) return;
        
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Updating...';
        btn.disabled = true;
        
        try {
            const response = await fetch('/api/config/model', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    embedding_model: newModel
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Embedding model updated successfully!', 'success');
                // Refresh all data
                await this.fetchAllData();
                // Reset models loaded flag to refresh dropdown
                this.modelsLoaded = false;
            } else {
                this.showNotification(result.error || 'Failed to update model', 'error');
            }
            
        } catch (error) {
            console.error('Error updating embedding model:', error);
            this.showNotification('Error updating embedding model', 'error');
        } finally {
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    },
    
    // Helper: Update status element
    updateStatusElement: function(elementId, value) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        element.textContent = value || 'Unknown';
        element.className = 'status-value';
    },
    
    // Helper: Update connection status with color coding
    updateConnectionStatus: function(elementId, value, timeElementId) {
        const element = document.getElementById(elementId);
        const timeElement = document.getElementById(timeElementId);
        
        if (!element) return;
        
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
            timeElement.textContent = `Last updated: ${new Date().toLocaleTimeString()}`;
        }
    },
    
    // Helper: Set text content safely
    setTextContent: function(elementId, text) {
        const element = document.getElementById(elementId);
        if (element) {
            element.textContent = text;
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
        
        // Update any timestamp elements without specific IDs
        const timestampElements = document.querySelectorAll('.timestamp:not([id*="Time"])');
        timestampElements.forEach(el => {
            el.textContent = `Last updated: ${timeString}`;
        });
    },
    
    // Show notification
    showNotification: function(message, type = 'info') {
        // Remove any existing notifications
        const existingNotifications = document.querySelectorAll('.notification');
        existingNotifications.forEach(n => n.remove());
        
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
    
    // Add notification styles if not present
    addNotificationStyles: function() {
        if (document.getElementById('notification-styles')) return;
        
        // Styles are already in index.css, so we don't need to add them here
        // This function is kept for compatibility
    },
    
    // Setup manual refresh button
    setupManualRefresh: function() {
        // You can add a manual refresh button to your HTML and wire it up here
        // Example: <button onclick="Dashboard.refresh()" class="refresh-btn">Refresh</button>
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
    
    // Models loaded flag
    modelsLoaded: false,
    
    // Auto refresh interval reference
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
