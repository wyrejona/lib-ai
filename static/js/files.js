// Files page JavaScript
document.addEventListener('DOMContentLoaded', function() {
    loadFileData();
    initDragAndDrop();
    
    // Close modal on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') closeModal();
    });
    
    // Close modal on outside click
    const modal = document.getElementById('pdfModal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target.id === 'pdfModal') closeModal();
        });
    }
    
    // File input change listener
    document.getElementById('fileInput').addEventListener('change', function() {
        uploadFiles(this.files);
    });
});

// Load file data from API
async function loadFileData() {
    try {
        const response = await fetch('/api/files/status');
        if (!response.ok) throw new Error('Failed to load file data');
        
        const data = await response.json();
        
        // Update status indicator
        const statusDot = document.getElementById('statusDot');
        const statusText = document.getElementById('statusText');
        if (statusDot && statusText) {
            if (data.vector_store_status === 'ready') {
                statusDot.className = 'status-dot ready';
                statusText.textContent = 'Vector Store: Ready';
            } else {
                statusDot.className = 'status-dot not-ready';
                statusText.textContent = 'Vector Store: Not ready';
            }
        }
        
        // Update dashboard cards
        updateDashboardCards(data);
        
        // Update file table
        updateFileTable(data.files);
        
        // Update buttons
        updateButtons(data.files.length > 0);
        
    } catch (error) {
        console.error('Error loading file data:', error);
        showNotification('Error loading file data', 'error');
    }
}

// Update dashboard cards
function updateDashboardCards(data) {
    // File count
    const fileCountElement = document.getElementById('totalFiles');
    if (fileCountElement) {
        fileCountElement.textContent = data.file_count;
    }
    
    // Total size
    const totalSizeElement = document.getElementById('totalSize');
    if (totalSizeElement) {
        if (data.files.length > 0) {
            const totalSize = data.files.reduce((sum, file) => sum + file.size, 0);
            totalSizeElement.textContent = formatFileSize(totalSize);
        } else {
            totalSizeElement.textContent = '0 B';
        }
    }
    
    // Processing status
    const processStatusElement = document.getElementById('processStatus');
    if (processStatusElement) {
        processStatusElement.textContent = data.vector_store_status === 'ready' ? 'Ready' : 'Not processed';
    }
    
    // Last updated
    const lastUpdatedElement = document.getElementById('lastUpdated');
    if (lastUpdatedElement) {
        if (data.files.length > 0) {
            const latestFile = data.files.reduce((latest, file) => {
                return new Date(file.modified) > new Date(latest.modified) ? file : latest;
            }, data.files[0]);
            
            const date = new Date(latestFile.modified);
            lastUpdatedElement.textContent = date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        } else {
            lastUpdatedElement.textContent = 'N/A';
        }
    }
}

// Update file table
function updateFileTable(files) {
    const emptyState = document.getElementById('emptyState');
    const fileTableContainer = document.getElementById('fileTableContainer');
    const fileTableBody = document.getElementById('fileTableBody');
    
    if (files.length === 0) {
        // Show empty state, hide table
        if (emptyState) emptyState.style.display = 'block';
        if (fileTableContainer) fileTableContainer.style.display = 'none';
        if (fileTableBody) fileTableBody.innerHTML = '';
    } else {
        // Hide empty state, show table
        if (emptyState) emptyState.style.display = 'none';
        if (fileTableContainer) fileTableContainer.style.display = 'block';
        
        // Populate table with files
        if (fileTableBody) {
            fileTableBody.innerHTML = files.map(file => `
                <tr>
                    <td>
                        <div class="file-info">
                            <div class="file-icon">
                                <i class="fas fa-file-pdf"></i>
                            </div>
                            <div class="file-details">
                                <div class="file-name" title="${file.name}">${file.name}</div>
                                <div class="file-meta">PDF Document</div>
                            </div>
                        </div>
                    </td>
                    <td>${file.formatted_size}</td>
                    <td>${formatDate(file.modified)}</td>
                    <td>
                        <div class="file-actions">
                            <button class="btn-icon-small btn-download" onclick="downloadFile('${file.name}')" title="Download">
                                <i class="fas fa-download"></i>
                            </button>
                            <button class="btn-icon-small btn-preview" onclick="previewPDF('${file.name}')" title="Preview">
                                <i class="fas fa-eye"></i>
                            </button>
                            <button class="btn-icon-small btn-delete" onclick="deleteFile('${file.name}')" title="Delete">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `).join('');
        }
    }
}

// Helper: Format date nicely
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
}

// Update buttons state
function updateButtons(hasFiles) {
    const processBtn = document.getElementById('processBtn');
    const clearBtn = document.getElementById('clearBtn');
    
    if (processBtn) {
        processBtn.disabled = !hasFiles;
        if (hasFiles) {
            processBtn.style.display = 'inline-block';
        } else {
            processBtn.style.display = 'inline-block'; // Keep visible but disabled
        }
    }
    
    if (clearBtn) {
        clearBtn.style.display = hasFiles ? 'inline-block' : 'none';
    }
}

// Format file size helper
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Initialize drag and drop
function initDragAndDrop() {
    const uploadArea = document.getElementById('uploadArea');
    if (!uploadArea) return;
    
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        uploadArea.style.borderColor = 'var(--primary)';
        uploadArea.style.background = 'rgba(26, 115, 232, 0.1)';
    }
    
    function unhighlight() {
        uploadArea.style.borderColor = 'var(--gray)';
        uploadArea.style.background = 'var(--gray-light)';
    }
    
    uploadArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const files = e.dataTransfer.files;
        uploadFiles(files);
    }
}

// Upload files
async function uploadFiles(files) {
    if (files.length === 0) return;
    
    const validFiles = Array.from(files).filter(file => {
        return file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
    });
    
    if (validFiles.length === 0) {
        showNotification('Please select PDF files only', 'error');
        return;
    }
    
    const formData = new FormData();
    for (let file of validFiles) {
        formData.append('files', file);
    }
    
    try {
        // Show progress
        const progress = document.getElementById('uploadProgress');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');
        
        if (progress && progressFill && progressText) {
            progress.style.display = 'block';
            progressFill.style.width = '0%';
            progressText.textContent = 'Uploading: 0%';
        }
        
        // Use fetch with progress tracking
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percentComplete = (e.loaded / e.total) * 100;
                if (progressFill) progressFill.style.width = percentComplete + '%';
                if (progressText) progressText.textContent = 'Uploading: ' + Math.round(percentComplete) + '%';
            }
        });
        
        xhr.addEventListener('load', () => {
            if (progressFill) progressFill.style.width = '100%';
            if (progressText) progressText.textContent = 'Uploading: 100%';
            
            if (xhr.status === 200) {
                const response = JSON.parse(xhr.responseText);
                if (response.success) {
                    showNotification(response.message || 'Files uploaded successfully!', 'success');
                    loadFileData(); // Refresh data
                } else {
                    showNotification(response.message || 'Upload failed', 'error');
                }
            } else {
                showNotification('Upload failed with status: ' + xhr.status, 'error');
            }
            
            setTimeout(() => {
                if (progress) progress.style.display = 'none';
            }, 2000);
        });
        
        xhr.addEventListener('error', () => {
            showNotification('Upload failed - network error', 'error');
            if (progress) progress.style.display = 'none';
        });
        
        xhr.open('POST', '/upload');
        xhr.send(formData);
        
    } catch (error) {
        console.error('Upload error:', error);
        showNotification('Error uploading files: ' + error.message, 'error');
        const progress = document.getElementById('uploadProgress');
        if (progress) progress.style.display = 'none';
    }
}

// Preview PDF in modal
function previewPDF(filename) {
    const modal = document.getElementById('pdfModal');
    const pdfViewer = document.getElementById('pdfViewer');
    const downloadBtn = document.getElementById('downloadBtn');
    const modalTitle = document.getElementById('modalTitle');
    
    if (!modal || !pdfViewer || !downloadBtn || !modalTitle) return;
    
    modalTitle.textContent = 'Preview: ' + filename;
    pdfViewer.src = '/download/' + encodeURIComponent(filename);
    downloadBtn.href = '/download/' + encodeURIComponent(filename);
    downloadBtn.download = filename;
    
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

// Close modal
function closeModal() {
    const modal = document.getElementById('pdfModal');
    const pdfViewer = document.getElementById('pdfViewer');
    
    if (modal && pdfViewer) {
        modal.classList.remove('active');
        pdfViewer.src = '';
        document.body.style.overflow = 'auto';
    }
}

// Download file
function downloadFile(filename) {
    const link = document.createElement('a');
    link.href = '/download/' + encodeURIComponent(filename);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showNotification('Download started: ' + filename, 'success');
}

// Delete file
async function deleteFile(filename) {
    if (!await confirmDialog(`Are you sure you want to delete "${filename}"?`)) return;
    
    try {
        const response = await fetch('/files/' + encodeURIComponent(filename), {
            method: 'DELETE'
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(result.message || 'File deleted successfully', 'success');
            loadFileData(); // Refresh data
        } else {
            throw new Error('Delete failed');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showNotification('Error deleting file: ' + error.message, 'error');
    }
}

// Clear all files
async function clearAllFiles() {
    if (!await confirmDialog('Are you sure you want to delete ALL files? This action cannot be undone.')) return;
    
    try {
        const response = await fetch('/clear-all-files', {
            method: 'DELETE'
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification(result.message || 'All files deleted', 'success');
            loadFileData(); // Refresh data
        } else {
            throw new Error('Clear all failed');
        }
    } catch (error) {
        console.error('Clear all error:', error);
        showNotification('Error clearing files: ' + error.message, 'error');
    }
}

// Process PDFs (Reindex)
async function processPDFs() {
    const btn = event.target.closest('button');
    const originalHTML = btn.innerHTML;
    
    try {
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        btn.disabled = true;
        
        const response = await fetch('/ingest', { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showNotification('PDFs processed successfully! AI is now ready to answer questions.', 'success');
            loadFileData(); // Refresh status
        } else {
            showNotification('Error processing PDFs: ' + (result.message || 'Unknown error'), 'error');
        }
    } catch (error) {
        console.error('Process error:', error);
        showNotification('Error processing PDFs: ' + error.message, 'error');
    } finally {
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    }
}

// Helper: Show notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
            <span>${message}</span>
        </div>
        <button class="notification-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) notification.remove();
    }, 5000);
}

// Helper: Confirm dialog
async function confirmDialog(message) {
    return new Promise((resolve) => {
        const dialog = document.createElement('div');
        dialog.className = 'confirm-dialog-overlay';
        dialog.innerHTML = `
            <div class="confirm-dialog">
                <div class="confirm-dialog-content">
                    <i class="fas fa-exclamation-triangle"></i>
                    <h4>Confirm Action</h4>
                    <p>${message}</p>
                </div>
                <div class="confirm-dialog-actions">
                    <button class="btn btn-secondary" onclick="this.closest('.confirm-dialog-overlay').remove(); resolve(false)">
                        Cancel
                    </button>
                    <button class="btn btn-danger" onclick="this.closest('.confirm-dialog-overlay').remove(); resolve(true)">
                        Confirm
                    </button>
                </div>
            </div>
        `;
        
        document.body.appendChild(dialog);
    });
}
