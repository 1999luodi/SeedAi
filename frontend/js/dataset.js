// 数据集管理页面逻辑
class DatasetManager {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 12;
        this.totalPages = 1;
        this.searchQuery = '';
        this.sortBy = 'newest';
        this.selectedFiles = [];
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkAuth();
        this.loadDatasets();
    }

    bindEvents() {
        // 创建数据集
        document.getElementById('createDatasetBtn').addEventListener('click', () => this.showCreateModal());
        document.getElementById('createFirstDatasetBtn').addEventListener('click', () => this.showCreateModal());
        document.getElementById('closeCreateModal').addEventListener('click', () => this.hideCreateModal());
        document.getElementById('cancelCreate').addEventListener('click', () => this.hideCreateModal());
        document.getElementById('createDatasetForm').addEventListener('submit', (e) => this.handleCreateDataset(e));

        // 导入数据集
        document.getElementById('importDatasetBtn').addEventListener('click', () => this.showImportModal());
        document.getElementById('closeImportModal').addEventListener('click', () => this.hideImportModal());
        document.getElementById('cancelImport').addEventListener('click', () => this.hideImportModal());

        // 导入选项
        document.querySelectorAll('.import-option').forEach(option => {
            option.addEventListener('click', () => this.selectImportType(option.dataset.type));
        });

        // 文件输入
        document.getElementById('zipFileInput').addEventListener('change', (e) => this.handleFileSelect(e));
        document.getElementById('folderInput').addEventListener('change', (e) => this.handleFolderSelect(e));
        document.getElementById('startImport').addEventListener('click', () => this.startImport());

        // 搜索和排序
        document.getElementById('searchInput').addEventListener('input', (e) => {
            this.searchQuery = e.target.value;
            this.currentPage = 1;
            this.loadDatasets();
        });
        document.getElementById('sortSelect').addEventListener('change', (e) => {
            this.sortBy = e.target.value;
            this.currentPage = 1;
            this.loadDatasets();
        });

        // 分页
        document.getElementById('prevPage').addEventListener('click', () => this.prevPage());
        document.getElementById('nextPage').addEventListener('click', () => this.nextPage());

        // 关闭详情模态框
        document.getElementById('closeDetailModal').addEventListener('click', () => this.hideDetailModal());

        // 点击模态框背景关闭
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    modal.style.display = 'none';
                }
            });
        });
    }

    checkAuth() {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = 'login.html';
            return;
        }

        // 更新导航链接
        const loginLink = document.getElementById('loginLink');
        if (loginLink) {
            loginLink.textContent = '登出';
            loginLink.href = '#';
            loginLink.addEventListener('click', (e) => {
                e.preventDefault();
                this.logout();
            });
        }
    }

    logout() {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = 'login.html';
    }

    async loadDatasets() {
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                limit: this.pageSize,
                search: this.searchQuery,
                sort: this.sortBy
            });

            const response = await API.get(`/datasets?${params}`);
            const data = await response.json();

            if (response.ok) {
                this.renderDatasets(data.datasets || []);
                this.updatePagination(data.total || 0, data.pages || 1);
            } else {
                this.showError('加载数据集失败: ' + (data.message || '未知错误'));
            }
        } catch (error) {
            console.error('加载数据集失败:', error);
            this.showError('网络错误，请重试');
        }
    }

    renderDatasets(datasets) {
        const grid = document.getElementById('datasetsGrid');

        if (datasets.length === 0) {
            grid.innerHTML = `
                <div class="empty-state">
                    <div class="empty-icon">📂</div>
                    <p>暂无数据集</p>
                    <p>${this.searchQuery ? '没有找到匹配的数据集' : '创建您的第一个数据集开始标注之旅吧！'}</p>
                    <button class="btn btn-primary" onclick="datasetManager.showCreateModal()">
                        <span class="btn-icon">🚀</span>
                        创建数据集
                    </button>
                </div>
            `;
            return;
        }

        grid.innerHTML = datasets.map(dataset => this.createDatasetCard(dataset)).join('');
    }

    createDatasetCard(dataset) {
        const createdDate = new Date(dataset.created_at).toLocaleDateString('zh-CN');
        const isPublic = dataset.is_public ? '公开' : '私有';

        return `
            <div class="dataset-card" data-id="${dataset.id}">
                <div class="dataset-header">
                    <h4 class="dataset-title">${escapeHtml(dataset.name)}</h4>
                    <span class="dataset-badge ${dataset.is_public ? 'badge-public' : 'badge-private'}">${isPublic}</span>
                </div>
                <div class="dataset-meta">
                    <span class="meta-item">
                        <span class="meta-icon">🖼️</span>
                        ${dataset.image_count || 0} 张图片
                    </span>
                    <span class="meta-item">
                        <span class="meta-icon">📅</span>
                        ${createdDate}
                    </span>
                </div>
                ${dataset.description ? `<p class="dataset-description">${escapeHtml(dataset.description)}</p>` : ''}
                <div class="dataset-actions">
                    <button class="btn btn-sm btn-outline" onclick="datasetManager.viewDataset('${dataset.id}')">
                        <span class="btn-icon">👁️</span>
                        查看
                    </button>
                    <button class="btn btn-sm btn-primary" onclick="datasetManager.annotateDataset('${dataset.id}')">
                        <span class="btn-icon">✏️</span>
                        标注
                    </button>
                    <button class="btn btn-sm btn-danger" onclick="datasetManager.deleteDataset('${dataset.id}')">
                        <span class="btn-icon">🗑️</span>
                        删除
                    </button>
                </div>
            </div>
        `;
    }

    updatePagination(total, pages) {
        this.totalPages = pages;
        const pagination = document.getElementById('pagination');
        const pageInfo = document.getElementById('pageInfo');
        const prevBtn = document.getElementById('prevPage');
        const nextBtn = document.getElementById('nextPage');

        if (pages <= 1) {
            pagination.style.display = 'none';
            return;
        }

        pagination.style.display = 'flex';
        pageInfo.textContent = `第 ${this.currentPage} 页，共 ${pages} 页`;
        prevBtn.disabled = this.currentPage <= 1;
        nextBtn.disabled = this.currentPage >= pages;
    }

    prevPage() {
        if (this.currentPage > 1) {
            this.currentPage--;
            this.loadDatasets();
        }
    }

    nextPage() {
        if (this.currentPage < this.totalPages) {
            this.currentPage++;
            this.loadDatasets();
        }
    }

    showCreateModal() {
        document.getElementById('createDatasetModal').style.display = 'block';
        document.getElementById('datasetName').focus();
    }

    hideCreateModal() {
        document.getElementById('createDatasetModal').style.display = 'none';
        document.getElementById('createDatasetForm').reset();
    }

    async handleCreateDataset(e) {
        e.preventDefault();

        const name = document.getElementById('datasetName').value.trim();
        const description = document.getElementById('datasetDescription').value.trim();
        const isPublic = document.getElementById('isPublic').checked;

        if (!name) {
            this.showError('请输入数据集名称');
            return;
        }

        try {
            const response = await API.post('/datasets', {
                name,
                description,
                is_public: isPublic
            });

            const data = await response.json();

            if (response.ok) {
                this.showSuccess('数据集创建成功！');
                this.hideCreateModal();
                this.loadDatasets();
            } else {
                this.showError(data.message || '创建失败');
            }
        } catch (error) {
            console.error('创建数据集失败:', error);
            this.showError('网络错误，请重试');
        }
    }

    showImportModal() {
        document.getElementById('importDatasetModal').style.display = 'block';
    }

    hideImportModal() {
        document.getElementById('importDatasetModal').style.display = 'none';
        document.getElementById('importForm').style.display = 'none';
        document.getElementById('importProgress').style.display = 'none';
        this.selectedFiles = [];
        this.updateImportButton();
    }

    selectImportType(type) {
        const form = document.getElementById('importForm');
        form.style.display = 'block';

        // 触发文件选择
        if (type === 'zip') {
            document.getElementById('zipFileInput').click();
        } else if (type === 'folder') {
            document.getElementById('folderInput').click();
        } else if (type === 'url') {
            // URL导入逻辑可以后续实现
            this.showError('URL导入功能暂未实现');
        }
    }

    handleFileSelect(e) {
        const files = Array.from(e.target.files);
        this.selectedFiles = files;
        this.updateImportButton();
    }

    handleFolderSelect(e) {
        const files = Array.from(e.target.files).filter(file =>
            file.type.startsWith('image/') ||
            file.name.match(/\.(jpg|jpeg|png|gif|bmp|webp)$/i)
        );
        this.selectedFiles = files;
        this.updateImportButton();
    }

    updateImportButton() {
        const btn = document.getElementById('startImport');
        const nameInput = document.getElementById('importDatasetName');

        btn.disabled = this.selectedFiles.length === 0 || !nameInput.value.trim();
    }

    async startImport() {
        const name = document.getElementById('importDatasetName').value.trim();
        const description = document.getElementById('importDescription').value.trim();

        if (!name || this.selectedFiles.length === 0) {
            this.showError('请填写数据集名称并选择文件');
            return;
        }

        // 显示进度条
        document.getElementById('importProgress').style.display = 'block';
        const progressFill = document.getElementById('importProgressFill');
        const progressText = document.getElementById('importProgressText');

        try {
            // 首先创建数据集
            const createResponse = await API.post('/datasets', {
                name,
                description,
                is_public: false
            });

            if (!createResponse.ok) {
                throw new Error('创建数据集失败');
            }

            const dataset = await createResponse.json();

            // 上传文件
            let uploaded = 0;
            const total = this.selectedFiles.length;

            for (const file of this.selectedFiles) {
                const formData = new FormData();
                formData.append('file', file);
                formData.append('dataset_id', dataset.id);

                const uploadResponse = await API.post('/images/upload', formData, false);

                if (uploadResponse.ok) {
                    uploaded++;
                    const progress = (uploaded / total) * 100;
                    progressFill.style.width = `${progress}%`;
                    progressText.textContent = `上传中... ${uploaded}/${total}`;
                }
            }

            this.showSuccess(`数据集导入完成！成功上传 ${uploaded}/${total} 张图片`);
            this.hideImportModal();
            this.loadDatasets();

        } catch (error) {
            console.error('导入失败:', error);
            this.showError('导入失败，请重试');
        } finally {
            document.getElementById('importProgress').style.display = 'none';
        }
    }

    async viewDataset(datasetId) {
        try {
            const response = await API.get(`/datasets/${datasetId}`);
            const data = await response.json();

            if (response.ok) {
                this.showDatasetDetail(data);
            } else {
                this.showError(data.message || '加载数据集详情失败');
            }
        } catch (error) {
            console.error('加载数据集详情失败:', error);
            this.showError('网络错误，请重试');
        }
    }

    showDatasetDetail(dataset) {
        const modal = document.getElementById('datasetDetailModal');
        const title = document.getElementById('datasetDetailTitle');
        const detail = document.getElementById('datasetDetail');

        title.textContent = `数据集详情 - ${dataset.name}`;

        detail.innerHTML = `
            <div class="dataset-info">
                <div class="info-section">
                    <h4>基本信息</h4>
                    <div class="info-grid">
                        <div class="info-item">
                            <label>名称:</label>
                            <span>${escapeHtml(dataset.name)}</span>
                        </div>
                        <div class="info-item">
                            <label>状态:</label>
                            <span class="badge ${dataset.is_public ? 'badge-public' : 'badge-private'}">
                                ${dataset.is_public ? '公开' : '私有'}
                            </span>
                        </div>
                        <div class="info-item">
                            <label>图片数量:</label>
                            <span>${dataset.image_count || 0}</span>
                        </div>
                        <div class="info-item">
                            <label>创建时间:</label>
                            <span>${new Date(dataset.created_at).toLocaleString('zh-CN')}</span>
                        </div>
                    </div>
                    ${dataset.description ? `
                        <div class="info-item">
                            <label>描述:</label>
                            <p>${escapeHtml(dataset.description)}</p>
                        </div>
                    ` : ''}
                </div>

                <div class="info-section">
                    <h4>图片预览</h4>
                    <div class="image-gallery" id="imageGallery">
                        <div class="loading">加载中...</div>
                    </div>
                </div>
            </div>
        `;

        modal.style.display = 'block';
        this.loadDatasetImages(dataset.id);
    }

    async loadDatasetImages(datasetId) {
        try {
            const response = await API.get(`/datasets/${datasetId}/images?limit=20`);
            const data = await response.json();

            const gallery = document.getElementById('imageGallery');

            if (response.ok && data.images && data.images.length > 0) {
                gallery.innerHTML = data.images.map(image => `
                    <div class="gallery-item">
                        <img src="/api/images/${image.id}/file" alt="${image.filename}" loading="lazy">
                        <div class="image-info">
                            <span class="filename">${escapeHtml(image.filename)}</span>
                            <span class="file-size">${formatFileSize(image.file_size)}</span>
                        </div>
                    </div>
                `).join('');
            } else {
                gallery.innerHTML = '<p class="no-images">暂无图片</p>';
            }
        } catch (error) {
            console.error('加载图片失败:', error);
            document.getElementById('imageGallery').innerHTML = '<p class="error">加载图片失败</p>';
        }
    }

    hideDetailModal() {
        document.getElementById('datasetDetailModal').style.display = 'none';
    }

    async deleteDataset(datasetId) {
        if (!confirm('确定要删除这个数据集吗？此操作不可撤销。')) {
            return;
        }

        try {
            const response = await API.delete(`/datasets/${datasetId}`);

            if (response.ok) {
                this.showSuccess('数据集删除成功');
                this.loadDatasets();
            } else {
                const data = await response.json();
                this.showError(data.message || '删除失败');
            }
        } catch (error) {
            console.error('删除数据集失败:', error);
            this.showError('网络错误，请重试');
        }
    }

    annotateDataset(datasetId) {
        window.location.href = `annotate.html?dataset=${datasetId}`;
    }

    showSuccess(message) {
        this.showMessage(message, 'success');
    }

    showError(message) {
        this.showMessage(message, 'error');
    }

    showMessage(message, type) {
        // 使用全局消息显示函数，如果存在的话
        if (window.showMessage) {
            window.showMessage(message, type);
        } else {
            alert(message);
        }
    }
}

// 工具函数
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

// 初始化
const datasetManager = new DatasetManager();
