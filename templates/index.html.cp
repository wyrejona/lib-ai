{% extends "base.html" %}

{% block title %}Dashboard - Library Support AI{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="/static/css/index.css">
{% endblock %}

{% block content %}
<div class="container">
    <header>
        <div class="logo">
            <i class="fas fa-brain"></i>
            <h1>Library Support AI</h1>
        </div>
        
        <div class="nav-links">
            <a href="/" class="nav-link {% if request.url.path == '/' %}active{% endif %}">
                <i class="fas fa-home"></i> Home
            </a>
            <a href="/files" class="nav-link {% if request.url.path == '/files' %}active{% endif %}">
                <i class="fas fa-folder"></i> Manage Files
            </a>
            <a href="/chat" class="nav-link {% if request.url.path == '/chat' %}active{% endif %}">
                <i class="fas fa-comments"></i> Chat
            </a>
        </div>
    </header>

    <section class="welcome-section">
        <h2>Welcome!</h2>
        <p>System Reliability Dashboard for Library Research AI</p>
        <p><small>Manage your AI models and system resources from this dashboard.</small></p>
    </section>

    <div class="grid-menu">
        <a href="/chat" class="menu-card">
            <i class="fas fa-comments"></i>
            <h3>AI Chat Interface</h3>
            <p>Query your uploaded research papers using natural language.</p>
            <span style="color: var(--primary); font-weight: bold;">Open Chat →</span>
        </a>

        <a href="/files" class="menu-card">
            <i class="fas fa-folder"></i>
            <h3>Manage Documents</h3>
            <p>Upload, view, and manage your PDF documents.</p>
            <span style="color: var(--primary); font-weight: bold;">Manage Files →</span>
        </a>
    </div>

    <!-- System Status Section -->
    <section class="status-section">
        <h2>System Status</h2>
        <div class="status-grid">
            <!-- AI Engine Status -->
            <div class="status-card">
                <h3><i class="fas fa-microchip"></i> AI Engine Status</h3>
                <div class="status-item">
                    <span class="status-label">Chat Model:</span>
                    <span id="currentChatModel" class="status-value">Loading...</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Embedding Model:</span>
                    <span id="currentEmbeddingModel" class="status-value">Loading...</span>
                </div>
                <div class="status-item">
                    <span class="status-label">Vector Store:</span>
                    <span id="vectorStoreStatus" class="status-value">Loading...</span>
                    <small id="vectorStoreTime" class="timestamp"></small>
                </div>
                <div class="status-item">
                    <span class="status-label">Ollama Connection:</span>
                    <span id="ollamaStatus" class="status-value">Loading...</span>
                    <small id="ollamaTime" class="timestamp"></small>
                </div>
            </div>

            <!-- System Resources -->
            <div class="status-card">
                <h3><i class="fas fa-server"></i> System Resources</h3>
                <div class="status-item">
                    <span class="status-label">Memory Usage:</span>
                    <div class="progress-bar">
                        <div id="memoryProgress" class="progress-fill" style="width: 0%"></div>
                    </div>
                    <span id="memoryPercent" class="status-value">0%</span>
                </div>
                <div class="status-item">
                    <span>Used: <span id="memoryUsed">0 GB</span> | Total: <span id="memoryTotal">0 GB</span></span>
                </div>
                
                <div class="status-item">
                    <span class="status-label">CPU Usage:</span>
                    <div class="progress-bar">
                        <div id="cpuProgress" class="progress-fill" style="width: 0%"></div>
                    </div>
                    <span id="cpuPercent" class="status-value">0%</span>
                </div>
                <div class="status-item">
                    <span id="cpuCores">Cores: 0</span> | <span id="cpuLoad">Load: 0.00</span>
                </div>
                
                <div class="status-item">
                    <span class="status-label">Disk Usage:</span>
                    <div class="progress-bar">
                        <div id="diskProgress" class="progress-fill" style="width: 0%"></div>
                    </div>
                    <span id="diskPercent" class="status-value">0%</span>
                </div>
                <div class="status-item">
                    <span>Used: <span id="diskUsed">0 GB</span> | Total: <span id="diskTotal">0 GB</span></span>
                </div>
            </div>
        </div>
    </section>

    <!-- Model Configuration Section -->
    <section class="config-section">
        <h2><i class="fas fa-cog"></i> Model Configuration</h2>
        <div class="config-grid">
            <!-- Chat Model Update -->
            <div class="config-card">
                <h3>Chat Model Settings</h3>
                <div class="form-group">
                    <label for="chatModelSelect">Select Chat Model:</label>
                    <select id="chatModelSelect" class="form-select">
                        <option value="">Loading models...</option>
                    </select>
                </div>
                <div class="form-group">
                    <button id="updateChatBtn" class="btn btn-primary" onclick="Dashboard.updateChatModel()">
                        <i class="fas fa-sync-alt"></i> Update Chat Model
                    </button>
                    <small class="form-text">Current model will be marked as "(Current)"</small>
                </div>
            </div>

            <!-- Embedding Model Update -->
            <div class="config-card">
                <h3>Embedding Model Settings</h3>
                <div class="form-group">
                    <label for="embeddingModelSelect">Select Embedding Model:</label>
                    <select id="embeddingModelSelect" class="form-select">
                        <option value="">Loading models...</option>
                    </select>
                </div>
                <div class="form-group">
                    <button id="updateEmbeddingBtn" class="btn btn-primary" onclick="Dashboard.updateEmbeddingModel()">
                        <i class="fas fa-sync-alt"></i> Update Embedding Model
                    </button>
                    <small class="form-text">Changing embedding model requires re-indexing</small>
                </div>
            </div>

            <!-- Quick Actions -->
            <div class="config-card">
                <h3>Quick Actions</h3>
                <div class="action-buttons">
                    <button onclick="Dashboard.refresh()" class="btn btn-secondary">
                        <i class="fas fa-redo"></i> Refresh Dashboard
                    </button>
                    <button onclick="location.reload()" class="btn btn-secondary">
                        <i class="fas fa-sync"></i> Reload Page
                    </button>
                    <button onclick="Dashboard.showNotification('Checking system...', 'info')" class="btn btn-secondary">
                        <i class="fas fa-heartbeat"></i> Check Health
                    </button>
                </div>
                <div class="action-info">
                    <p><small>Last updated: <span id="lastUpdateTime" class="timestamp">Never</span></small></p>
                </div>
            </div>
        </div>
    </section>
</div>

<!-- Include the dashboard JavaScript -->
<script src="/static/js/index.js"></script>

<!-- Notification Container (will be created by JavaScript) -->
<div id="notification-container"></div>
{% endblock %}
