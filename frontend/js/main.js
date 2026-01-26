// API基础配置
const API_BASE = '/api';

// 工具函数
class Utils {
    static getToken() {
        return localStorage.getItem('token');
    }

    static setToken(token) {
        localStorage.setItem('token', token);
    }

    static isLoggedIn() {
        return !!this.getToken();
    }

    static logout() {
        localStorage.removeItem('token');
        window.location.href = 'login.html';
    }

    static showMessage(message, type = 'info', duration = 5000) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type} fade-in`;
        messageDiv.innerHTML = `
            <span class="message-icon">${this.getMessageIcon(type)}</span>
            <span class="message-text">${message}</span>
            <button class="message-close" onclick="this.parentElement.remove()">&times;</button>
        `;

        const container = document.querySelector('.container') || document.body;
        container.insertBefore(messageDiv, container.firstChild);

        if (duration > 0) {
            setTimeout(() => {
                if (messageDiv.parentElement) {
                    messageDiv.remove();
                }
            }, duration);
        }

        return messageDiv;
    }

    static getMessageIcon(type) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };
        return icons[type] || icons.info;
    }

    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    static formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    }
}

// API请求类
class API {
    static async request(endpoint, options = {}) {
        const token = Utils.getToken();
        const defaultOptions = {
            headers: {
                'Authorization': token ? `Bearer ${token}` : '',
                'Content-Type': 'application/json'
            }
        };

        // 如果是FormData，不要设置Content-Type，让浏览器自动设置
        if (options.body instanceof FormData) {
            delete defaultOptions.headers['Content-Type'];
        }

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(`${API_BASE}${endpoint}`, config);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || `HTTP ${response.status}`);
            }

            return data;
        } catch (error) {
            console.error('API请求错误:', error);
            throw error;
        }
    }

    static async get(endpoint) {
        return this.request(endpoint);
    }

    static async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    static async put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
    }

    static async delete(endpoint) {
        return this.request(endpoint, { method: 'DELETE' });
    }

    static async upload(endpoint, formData, onProgress) {
        const token = Utils.getToken();
        const xhr = new XMLHttpRequest();

        return new Promise((resolve, reject) => {
            xhr.open('POST', `${API_BASE}${endpoint}`);

            if (token) {
                xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            }

            xhr.upload.addEventListener('progress', (e) => {
                if (e.lengthComputable && onProgress) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    onProgress(percentComplete);
                }
            });

            xhr.onload = () => {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const data = JSON.parse(xhr.responseText);
                        resolve(data);
                    } catch (e) {
                        resolve({ success: true });
                    }
                } else {
                    try {
                        const error = JSON.parse(xhr.responseText);
                        reject(new Error(error.message || `HTTP ${xhr.status}`));
                    } catch (e) {
                        reject(new Error(`HTTP ${xhr.status}`));
                    }
                }
            };

            xhr.onerror = () => {
                reject(new Error('网络错误'));
            };

            xhr.send(formData);
        });
    }
}

// 应用主类
class SeedAIApp {
    constructor() {
        this.selectedFiles = [];
        this.currentDataset = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateAuthStatus();
        this.loadStats();
        this.loadRecentUploads();
    }

    bindEvents() {
        // 文件上传区域
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('imageInput');
        const fileSelect = document.getElementById('fileSelect');
        const uploadBtn = document.getElementById('uploadBtn');

        // 文件选择
        fileSelect.addEventListener('click', () => fileInput.click());
        fileInput.addEventListener('change', (e) => this.handleFileSelect(e.target.files));

        // 拖拽上传
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            this.handleFileSelect(e.dataTransfer.files);
        });

        // 上传按钮
        uploadBtn.addEventListener('click', () => this.uploadFiles());

        // 创建数据集
        document.getElementById('createDatasetBtn').addEventListener('click', () => this.showCreateDatasetModal());
        document.getElementById('closeModal').addEventListener('click', () => this.hideCreateDatasetModal());
        document.getElementById('cancelCreate').addEventListener('click', () => this.hideCreateDatasetModal());

        document.getElementById('createDatasetForm').addEventListener('submit', (e) => this.handleCreateDataset(e));
    }

    updateAuthStatus() {
        const loginLink = document.getElementById('loginLink');
        if (Utils.isLoggedIn()) {
            loginLink.textContent = '登出';
            loginLink.href = '#';
            loginLink.addEventListener('click', (e) => {
                e.preventDefault();
                Utils.logout();
            });
        } else {
            loginLink.textContent = '登录';
            loginLink.href = 'login.html';
        }
    }

    async loadStats() {
        try {
            // 这里可以调用后端API获取统计数据
            // 暂时使用模拟数据
            document.getElementById('totalImages').textContent = '1,234';
            document.getElementById('totalDatasets').textContent = '56';
            document.getElementById('activeUsers').textContent = '89';
        } catch (error) {
            console.error('加载统计数据失败:', error);
        }
    }

    async loadRecentUploads() {
        try {
            if (!Utils.isLoggedIn()) return;

            const response = await API.get('/datasets');
            if (response.success && response.data.length > 0) {
                this.renderRecentUploads(response.data);
            }
        } catch (error) {
            console.error('加载最近上传失败:', error);
        }
    }

    renderRecentUploads(datasets) {
        const container = document.getElementById('recentUploads');
        container.innerHTML = '';

        datasets.slice(0, 6).forEach(dataset => {
            const item = document.createElement('div');
            item.className = 'upload-item';
            item.innerHTML = `
                <div class="upload-item-info">
                    <div class="upload-item-title">${dataset.name}</div>
                    <div class="upload-item-meta">${dataset.image_count} 张图片 • ${Utils.formatDate(dataset.created_at)}</div>
                </div>
            `;
            item.addEventListener('click', () => {
                window.location.href = `dataset.html?id=${dataset.id}`;
            });
            container.appendChild(item);
        });
    }

    handleFileSelect(files) {
        this.selectedFiles = Array.from(files).filter(file => {
            if (!file.type.startsWith('image/')) {
                Utils.showMessage(`${file.name} 不是图片文件`, 'warning');
                return false;
            }
            if (file.size > 10 * 1024 * 1024) { // 10MB
                Utils.showMessage(`${file.name} 文件过大（最大10MB）`, 'error');
                return false;
            }
            return true;
        });

        this.updateUploadUI();
    }

    updateUploadUI() {
        const uploadArea = document.getElementById('uploadArea');
        const uploadBtn = document.getElementById('uploadBtn');

        if (this.selectedFiles.length > 0) {
            uploadArea.querySelector('.upload-text p').textContent = `已选择 ${this.selectedFiles.length} 个文件`;
            uploadBtn.disabled = false;
        } else {
            uploadArea.querySelector('.upload-text p').innerHTML = '拖拽图片到此处，或 <span class="upload-link" id="fileSelect">点击选择</span>';
            uploadBtn.disabled = true;
        }
    }

    async uploadFiles() {
        if (!Utils.isLoggedIn()) {
            Utils.showMessage('请先登录', 'warning');
            window.location.href = 'login.html';
            return;
        }

        if (this.selectedFiles.length === 0) return;

        // 如果没有选择数据集，先让用户选择或创建
        if (!this.currentDataset) {
            const shouldCreate = confirm('您还没有选择数据集，是否要创建新数据集？');
            if (shouldCreate) {
                this.showCreateDatasetModal();
                return;
            } else {
                Utils.showMessage('请先选择数据集', 'info');
                return;
            }
        }

        const progressDiv = document.getElementById('uploadProgress');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');

        progressDiv.style.display = 'block';
        let uploadedCount = 0;

        for (const file of this.selectedFiles) {
            try {
                const formData = new FormData();
                formData.append('file', file);

                await API.upload(`/datasets/${this.currentDataset}/upload`, formData, (progress) => {
                    const overallProgress = ((uploadedCount + progress / 100) / this.selectedFiles.length) * 100;
                    progressFill.style.width = `${overallProgress}%`;
                    progressText.textContent = `上传中... ${Math.round(overallProgress)}%`;
                });

                uploadedCount++;
                Utils.showMessage(`"${file.name}" 上传成功`, 'success');
            } catch (error) {
                Utils.showMessage(`"${file.name}" 上传失败: ${error.message}`, 'error');
            }
        }

        progressDiv.style.display = 'none';
        this.selectedFiles = [];
        this.updateUploadUI();
        this.loadRecentUploads();

        Utils.showMessage(`上传完成！成功 ${uploadedCount}/${this.selectedFiles.length} 个文件`, 'success');
    }

    showCreateDatasetModal() {
        document.getElementById('createDatasetModal').style.display = 'flex';
    }

    hideCreateDatasetModal() {
        document.getElementById('createDatasetModal').style.display = 'none';
        document.getElementById('createDatasetForm').reset();
    }

    async handleCreateDataset(e) {
        e.preventDefault();

        const name = document.getElementById('datasetName').value.trim();
        const description = document.getElementById('datasetDescription').value.trim();

        if (!name) {
            Utils.showMessage('请输入数据集名称', 'warning');
            return;
        }

        try {
            const response = await API.post('/datasets', { name, description });
            if (response.success) {
                this.currentDataset = response.data.id;
                this.hideCreateDatasetModal();
                Utils.showMessage('数据集创建成功！', 'success');
                this.loadRecentUploads();
            }
        } catch (error) {
            Utils.showMessage(`创建数据集失败: ${error.message}`, 'error');
        }
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new SeedAIApp();
});
