// ===== FILE MANAGER FUNCTIONALITY =====
class FileManager {
    constructor() {
        // DOM elements
        this.elements = {
            uploadArea: document.querySelector('.upload-area'),
            fileInput: document.getElementById('fileInput'),
            uploadProgress: document.getElementById('uploadProgress'),
            progressFill: document.getElementById('progressFill'),
            progressText: document.getElementById('progressText'),
            pdfModal: document.getElementById('pdfModal'),
            pdfViewer: document.getElementById('pdfViewer'),
            downloadBtn: document.getElementById('downloadBtn'),
            modalTitle: document.getElementById('modalTitle')
        };

        this.initialize();
    }

    initialize() {
        this.setupEventListeners();
        
        // Handle drag and drop
        this.setupDragAndDrop();
        
        // Close modal on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeModal();
            }
        });
        
        // Close modal on outside click
        this.elements.pdfModal.addEventListener('click', (e) => {
            if (e.target.id === 'pdfModal') {
                this.closeModal();
            }
        });
    }

    setupEventListeners() {
        // Upload area click
        this.elements.uploadArea.addEventListener('click', () => {
            this.elements.fileInput.click();
        });
        
        // File input change
        this.elements.fileInput.addEventListener('change', (e) => {
            this.uploadFiles(e.target.files);
        });
        
        // Expose methods to window for onclick handlers
        window.previewPDF = (filename) => this.previewPDF(filename);
        window.downloadFile = (filename) => this.downloadFile(filename);
        window.deleteFile = (filename) => this.deleteFile(filename);
        window.clearAllFiles = () => this.clearAllFiles();
        window.processPDFs = () => this.processPDFs();
        window.closeModal = () => this.closeModal();
    }

    setupDragAndDrop() {
        const uploadArea = this.elements.uploadArea;
        
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
        });
        
        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.highlight, false);
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.unhighlight, false);
        });
        
        uploadArea.addEventListener('drop', (e) => this.handleDrop(e), false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    highlight(e) {
        const uploadArea = document.querySelector('.upload-area');
        uploadArea.style.borderColor = 'var(--primary)';
        uploadArea.style.background = 'rgba(26, 115, 232, 0.1)';
    }

    unhighlight(e) {
        const uploadArea = document.querySelector('.upload-area');
        uploadArea.style.borderColor = 'var(--gray)';
        uploadArea.style.background = 'var(--gray-light)';
    }

    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        this.uploadFiles(files);
    }

    // ===== FILE OPERATIONS =====
    async uploadFiles(files) {
        if (files.length === 0) return;
        
        const formData = new FormData();
        for (let file of files) {
            formData.append('files', file);
        }
        
        try {
            // Show progress
            this.elements.uploadProgress.style.display = 'block';
            this.elements.progressFill.style.width = '0%';
            this.elements.progressText.textContent = 'Uploading: 0%';
            
            // Simulate progress (in real app, you'd use XMLHttpRequest with progress events)
            let progressPercent = 0;
            const progressInterval = setInterval(() => {
                progressPercent += 10;
                if (progressPercent > 90) {
                    clearInterval(progressInterval);
                }
                this.elements.progressFill.style.width = progressPercent + '%';
                this.elements.progressText.textContent = 'Uploading: ' + progressPercent + '%';
            }, 200);
            
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            clearInterval(progressInterval);
            this.elements.progressFill.style.width = '100%';
            this.elements.progressText.textContent = 'Uploading: 100%';
            
            if (response.ok) {
                this.showNotification('Files uploaded successfully!', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            } else {
                throw new Error('Upload failed');
            }
        } catch (error) {
            this.showNotification('Error uploading files: ' + error.message, 'error');
        } finally {
            setTimeout(() => {
                this.elements.uploadProgress.style.display = 'none';
            }, 2000);
        }
    }

    previewPDF(filename) {
        this.elements.modalTitle.textContent = 'Preview: ' + filename;
        this.elements.pdfViewer.src = '/download/' + encodeURIComponent(filename);
        this.elements.downloadBtn.href = '/download/' + encodeURIComponent(filename);
        this.elements.downloadBtn.download = filename;
        
        this.elements.pdfModal.classList.add('active');
        document.body.style.overflow = 'hidden';
    }

    closeModal() {
        this.elements.pdfModal.classList.remove('active');
        this.elements.pdfViewer.src = '';
        document.body.style.overflow = 'auto';
    }

    downloadFile(filename) {
        const link = document.createElement('a');
        link.href = '/download/' + encodeURIComponent(filename);
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }

    async deleteFile(filename) {
        if (!confirm('Are you sure you want to delete "' + filename + '"?')) return;
        
        try {
            const response = await fetch('/files/' + encodeURIComponent(filename), {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.showNotification('File deleted successfully', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } catch (error) {
            this.showNotification('Error deleting file: ' + error.message, 'error');
        }
    }

    async clearAllFiles() {
        if (!confirm('Are you sure you want to delete ALL files? This action cannot be undone.')) return;
        
        try {
            const response = await fetch('/clear-all-files', {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.showNotification('All files deleted', 'success');
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            }
        } catch (error) {
            this.showNotification('Error clearing files: ' + error.message, 'error');
        }
    }

    async processPDFs() {
        const btn = event.target;
        const originalHTML = btn.innerHTML;
        
        try {
            btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
            btn.disabled = true;
            
            const response = await fetch('/ingest', { method: 'POST' });
            const result = await response.json();
            
            if (result.success) {
                this.showNotification('PDFs processed successfully! AI is now ready to answer questions.', 'success');
            } else {
                this.showNotification('Error processing PDFs: ' + (result.error || 'Unknown error'), 'error');
            }
        } catch (error) {
            this.showNotification('Error processing PDFs: ' + error.message, 'error');
        } finally {
            btn.innerHTML = originalHTML;
            btn.disabled = false;
        }
    }

    // ===== UTILITIES =====
    showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = 'notification notification-' + type;
        notification.innerHTML = `
            <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            ${message}
        `;
        
        // Style notification
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? '#34a853' : '#d93025'};
            color: white;
            padding: 12px 24px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            display: flex;
            align-items: center;
            gap: 10px;
            animation: slideIn 0.3s ease;
        `;
        
        // Add animation
        const style = document.createElement('style');
        style.textContent = `
            @keyframes slideIn {
                from { transform: translateX(100%); opacity: 0; }
                to { transform: translateX(0); opacity: 1; }
            }
        `;
        document.head.appendChild(style);
        
        // Add to document
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideIn 0.3s ease reverse';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// ===== INITIALIZE FILE MANAGER =====
document.addEventListener('DOMContentLoaded', () => {
    window.fileManager = new FileManager();
});