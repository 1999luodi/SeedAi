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
        // 检查是否在首页，如果是则不执行初始化
        if (window.location.pathname.endsWith('index.html')) {
            return;
        }
        
        this.bindEvents();
        this.bindNavigation();
        this.updateAuthStatus();
        this.loadStats();
        this.loadRecentUploads();
    }

    bindNavigation() {
        // 导航检查 - 未登录用户点击受保护菜单项时跳转到登录页
        const navLinks = document.querySelectorAll('.nav-link[data-action="checkLogin"]');
        
        navLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                
                // 检查是否已登录
                if (!Utils.isLoggedIn()) {
                    // 跳转到登录页面
                    window.location.href = 'login.html';
                } else {
                    // 已登录，跳转到目标页面
                    const href = link.getAttribute('data-href');
                    if (href) {
                        window.location.href = href;
                    }
                }
            });
        });
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
            if (loginLink && loginLink.textContent !== '登出') {
                loginLink.textContent = '登出';
                loginLink.href = '#';
                // 移除旧事件监听器以避免重复绑定
                loginLink.replaceWith(loginLink.cloneNode(true)); // 克隆节点以移除所有事件监听器
                const newLoginLink = document.getElementById('loginLink');
                newLoginLink.addEventListener('click', (e) => {
                    e.preventDefault();
                    Utils.logout();
                });
            }
        } else {
            if (loginLink && loginLink.textContent !== '登录') {
                loginLink.textContent = '登录';
                loginLink.href = 'login.html';
            }
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

// 统一的导航栏初始化函数，可在所有页面使用
function initializeNavigation() {
    // 只在非首页运行完整的导航初始化
    if (!window.location.pathname.endsWith('index.html')) {
        updateNavDisplay();
        setupProtectedLinks();
        
        // 加载统计数据
        loadStats();
    }
}

// 更新导航栏显示 - 统一处理所有页面的导航栏
function updateNavDisplay() {
    const isLoggedIn = Utils.isLoggedIn();
    const loginLink = document.getElementById('loginLink');
    const profileLink = document.getElementById('profileLink');
    const logoutLink = document.getElementById('logoutLink');
    const usernameDisplay = document.getElementById('usernameDisplay');
    
    if (profileLink && logoutLink && usernameDisplay) {
        // 如果页面有profileLink（如首页），使用这个显示方式
        if (isLoggedIn) {
            // 用户已登录，显示用户名和退出链接
            if(loginLink) loginLink.style.display = 'none';
            profileLink.style.display = 'inline-flex';
            
            // 获取用户信息并显示用户名
            getUserInfo().then(userInfo => {
                if (userInfo && usernameDisplay) {
                    usernameDisplay.textContent = userInfo.username;
                }
            });
            
            // 为退出登录链接添加事件监听器
            if(logoutLink) {
                // 移除旧事件监听器以避免重复绑定
                logoutLink.replaceWith(logoutLink.cloneNode(true));
                const newLogoutLink = document.getElementById('logoutLink');
                newLogoutLink.addEventListener('click', function(e) {
                    e.preventDefault();
                    Utils.logout(); // 使用Utils类的登出方法
                });
            }
        } else {
            // 用户未登录，显示登录链接
            if(loginLink) loginLink.style.display = 'inline-flex';
            profileLink.style.display = 'none';
        }
    } else if (loginLink) {
        // 如果页面只有loginLink（如其他页面），使用updateAuthStatus逻辑
        const appInstance = new SeedAIApp();
        appInstance.updateAuthStatus();
    }
}

// 获取用户信息
async function getUserInfo() {
    const token = Utils.getToken();
    
    if (!token) {
        return null;
    }
    
    try {
        const response = await fetch('/api/users/profile', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            return data.data;
        } else {
            // 如果获取用户信息失败，可能是token无效，清除本地token
            Utils.logout(); // 使用Utils类的登出方法
            return null;
        }
    } catch (error) {
        console.error('获取用户信息失败:', error);
        Utils.logout(); // 使用Utils类的登出方法
        return null;
    }
}

// 退出登录
function logout() {
    localStorage.removeItem('token');
    updateNavDisplay();
    
    // 重定向到首页
    window.location.href = 'index.html';
}

// 检查登录并跳转
function checkLoginAndRedirect(href) {
    if (!Utils.isLoggedIn()) {
        // 未登录，跳转到登录页面
        window.location.href = 'login.html';
    } else {
        // 已登录，跳转到目标页面
        window.location.href = href;
    }
}

// 为受保护的链接添加点击事件监听器
function setupProtectedLinks() {
    const protectedLinks = document.querySelectorAll('.protected');
    
    protectedLinks.forEach(link => {
        // 移除旧事件监听器以避免重复绑定
        link.replaceWith(link.cloneNode(true)); // 克隆节点以移除所有事件监听器
        const newLink = document.querySelector(`[data-href="${link.getAttribute('data-href')}"]`);
        if (newLink) {
            newLink.addEventListener('click', function(e) {
                e.preventDefault();
                const href = this.getAttribute('data-href');
                checkLoginAndRedirect(href);
            });
        }
    });
}

// 页面加载完成后执行初始化
document.addEventListener('DOMContentLoaded', function() {
    // 只在非首页初始化SeedAIApp
    if (!window.location.pathname.endsWith('index.html')) {
        window.app = new SeedAIApp();
    }
    initializeNavigation();
});