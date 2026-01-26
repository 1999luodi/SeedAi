// 图像标注页面逻辑
class ImageAnnotator {
    constructor() {
        this.urlParams = new URLSearchParams(window.location.search);
        this.datasetId = this.urlParams.get('dataset');
        this.currentImageIndex = 0;
        this.images = [];
        this.currentLabels = [];
        this.zoomLevel = 1.0;
        this.annotatedCount = 0;
        this.totalImages = 0;
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkAuth();
        this.loadDatasetInfo();

        if (this.datasetId) {
            this.loadImages();
        } else {
            this.showDatasetSelector();
        }
    }

    bindEvents() {
        // 标签管理
        document.getElementById('addLabelBtn').addEventListener('click', () => this.addLabel());
        document.getElementById('labelInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') this.addLabel();
        });

        // 常用标签
        document.getElementById('commonTags').addEventListener('click', (e) => {
            if (e.target.classList.contains('label-tag')) {
                this.addLabelFromTag(e.target.dataset.label);
            }
        });

        // 操作按钮
        document.getElementById('saveBtn').addEventListener('click', () => this.saveAnnotation());
        document.getElementById('skipBtn').addEventListener('click', () => this.nextImage());
        document.getElementById('clearLabelsBtn').addEventListener('click', () => this.clearLabels());

        // 导航
        document.getElementById('prevBtn').addEventListener('click', () => this.prevImage());
        document.getElementById('nextBtn').addEventListener('click', () => this.nextImage());

        // 缩放控制
        document.getElementById('zoomInBtn').addEventListener('click', () => this.zoomIn());
        document.getElementById('zoomOutBtn').addEventListener('click', () => this.zoomOut());
        document.getElementById('fitToScreenBtn').addEventListener('click', () => this.fitToScreen());

        // 数据集切换
        document.getElementById('changeDatasetBtn').addEventListener('click', () => this.showDatasetSelector());
        document.getElementById('closeDatasetModal').addEventListener('click', () => this.hideDatasetSelector());

        // AI 辅助标注
        document.getElementById('autoLabelBtn').addEventListener('click', () => this.requestAISuggestions());

        // 模态框背景点击关闭
        document.getElementById('datasetModal').addEventListener('click', (e) => {
            if (e.target === document.getElementById('datasetModal')) {
                this.hideDatasetSelector();
            }
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

    async loadDatasetInfo() {
        if (!this.datasetId) return;

        try {
            const response = await API.get(`/datasets/${this.datasetId}`);
            const dataset = await response.json();

            if (response.ok) {
                document.getElementById('datasetInfo').textContent = `数据集: ${dataset.name}`;
                document.title = `标注 - ${dataset.name} - SeedAI`;
            }
        } catch (error) {
            console.error('加载数据集信息失败:', error);
        }
    }

    async loadImages() {
        if (!this.datasetId) return;

        try {
            this.showLoading('加载图像中...');
            const response = await API.get(`/datasets/${this.datasetId}/images`);
            const data = await response.json();

            if (response.ok) {
                this.images = data.images || [];
                this.totalImages = this.images.length;
                this.annotatedCount = this.images.filter(img => img.labels && img.labels.length > 0).length;

                this.updateStats();
                this.hideLoading();

                if (this.images.length > 0) {
                    this.showImage(0);
                } else {
                    this.showPlaceholder('该数据集暂无图像');
                }
            } else {
                this.showError('加载图像失败: ' + (data.message || '未知错误'));
            }
        } catch (error) {
            console.error('加载图像失败:', error);
            this.showError('网络错误，请重试');
        }
    }

    showImage(index) {
        if (!this.images[index]) return;

        this.currentImageIndex = index;
        const image = this.images[index];
        const imgElement = document.getElementById('currentImage');
        const placeholder = document.getElementById('imagePlaceholder');

        // 显示图像
        imgElement.src = `/api/images/${image.id}/file`;
        imgElement.style.display = 'block';
        placeholder.style.display = 'none';

        // 加载当前标签
        this.currentLabels = image.labels || [];
        this.updateLabelsList();

        // 更新UI
        this.updateNavigation();
        this.updateImageInfo();
        this.fitToScreen();

        // 预加载下一张图片
        this.preloadNextImage();
    }

    showPlaceholder(message) {
        const imgElement = document.getElementById('currentImage');
        const placeholder = document.getElementById('imagePlaceholder');

        imgElement.style.display = 'none';
        placeholder.style.display = 'flex';
        placeholder.querySelector('p').textContent = message;
    }

    updateNavigation() {
        const prevBtn = document.getElementById('prevBtn');
        const nextBtn = document.getElementById('nextBtn');

        prevBtn.disabled = this.currentImageIndex <= 0;
        nextBtn.disabled = this.currentImageIndex >= this.images.length - 1;
    }

    updateImageInfo() {
        const counter = document.getElementById('imageCounter');
        const filename = document.getElementById('imageFilename');
        const progressFill = document.getElementById('progressFill');
        const progressText = document.getElementById('progressText');

        if (this.images.length > 0) {
            const image = this.images[this.currentImageIndex];
            counter.textContent = `${this.currentImageIndex + 1} / ${this.images.length}`;
            filename.textContent = image.filename;

            const progress = ((this.currentImageIndex + 1) / this.images.length) * 100;
            progressFill.style.width = `${progress}%`;
            progressText.textContent = `${Math.round(progress)}%`;
        } else {
            counter.textContent = '0 / 0';
            filename.textContent = '-';
            progressFill.style.width = '0%';
            progressText.textContent = '0%';
        }
    }

    updateStats() {
        document.getElementById('annotatedCount').textContent = this.annotatedCount;
        document.getElementById('totalImages').textContent = this.totalImages;
        const rate = this.totalImages > 0 ? Math.round((this.annotatedCount / this.totalImages) * 100) : 0;
        document.getElementById('completionRate').textContent = `${rate}%`;
    }

    addLabel() {
        const input = document.getElementById('labelInput');
        const label = input.value.trim().toLowerCase();

        if (label && !this.currentLabels.includes(label)) {
            this.currentLabels.push(label);
            input.value = '';
            this.updateLabelsList();
            this.updateSaveButton();
        }
    }

    addLabelFromTag(label) {
        if (!this.currentLabels.includes(label)) {
            this.currentLabels.push(label);
            this.updateLabelsList();
            this.updateSaveButton();
        }
    }

    updateLabelsList() {
        const container = document.getElementById('labelsList');

        if (this.currentLabels.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>暂无标签</p>
                    <p>点击上方添加或选择常用标签</p>
                </div>
            `;
            return;
        }

        container.innerHTML = this.currentLabels.map((label, index) => `
            <div class="label-item">
                <span class="label-text">${escapeHtml(label)}</span>
                <button class="label-remove" onclick="annotator.removeLabel(${index})" title="移除标签">
                    ×
                </button>
            </div>
        `).join('');
    }

    removeLabel(index) {
        this.currentLabels.splice(index, 1);
        this.updateLabelsList();
        this.updateSaveButton();
    }

    clearLabels() {
        if (this.currentLabels.length > 0 && confirm('确定要清空所有标签吗？')) {
            this.currentLabels = [];
            this.updateLabelsList();
            this.updateSaveButton();
        }
    }

    updateSaveButton() {
        const saveBtn = document.getElementById('saveBtn');
        const clearBtn = document.getElementById('clearLabelsBtn');

        saveBtn.disabled = this.currentLabels.length === 0;
        clearBtn.disabled = this.currentLabels.length === 0;
    }

    async saveAnnotation() {
        if (this.currentLabels.length === 0) return;

        const image = this.images[this.currentImageIndex];
        if (!image) return;

        try {
            this.showLoading('保存中...');
            const response = await API.put(`/images/${image.id}/labels`, {
                labels: this.currentLabels
            });

            if (response.ok) {
                // 更新标注统计
                if (!image.labels || image.labels.length === 0) {
                    this.annotatedCount++;
                    this.updateStats();
                }
                image.labels = [...this.currentLabels];

                this.showSuccess('标注保存成功！');
                setTimeout(() => this.nextImage(), 1000);
            } else {
                const data = await response.json();
                this.showError('保存失败: ' + (data.message || '未知错误'));
            }
        } catch (error) {
            console.error('保存标注失败:', error);
            this.showError('网络错误，请重试');
        } finally {
            this.hideLoading();
        }
    }

    prevImage() {
        if (this.currentImageIndex > 0) {
            this.showImage(this.currentImageIndex - 1);
        }
    }

    nextImage() {
        if (this.currentImageIndex < this.images.length - 1) {
            this.showImage(this.currentImageIndex + 1);
        }
    }

    zoomIn() {
        this.setZoom(this.zoomLevel * 1.2);
    }

    zoomOut() {
        this.setZoom(this.zoomLevel / 1.2);
    }

    fitToScreen() {
        const img = document.getElementById('currentImage');
        const container = img.parentElement;

        if (img.naturalWidth && img.naturalHeight) {
            const containerRatio = container.clientWidth / container.clientHeight;
            const imageRatio = img.naturalWidth / img.naturalHeight;

            let scale;
            if (imageRatio > containerRatio) {
                scale = container.clientWidth / img.naturalWidth;
            } else {
                scale = container.clientHeight / img.naturalHeight;
            }

            this.setZoom(Math.min(scale, 1));
        }
    }

    setZoom(level) {
        this.zoomLevel = Math.max(0.1, Math.min(3, level));
        const img = document.getElementById('currentImage');
        const zoomLevel = document.getElementById('zoomLevel');

        img.style.transform = `scale(${this.zoomLevel})`;
        zoomLevel.textContent = `${Math.round(this.zoomLevel * 100)}%`;
    }

    preloadNextImage() {
        const nextIndex = this.currentImageIndex + 1;
        if (nextIndex < this.images.length) {
            const nextImage = this.images[nextIndex];
            const img = new Image();
            img.src = `/api/images/${nextImage.id}/file`;
        }
    }

    showDatasetSelector() {
        const modal = document.getElementById('datasetModal');
        modal.style.display = 'block';
        this.loadAvailableDatasets();
    }

    hideDatasetSelector() {
        document.getElementById('datasetModal').style.display = 'none';
    }

    async loadAvailableDatasets() {
        try {
            const response = await API.get('/datasets');
            const data = await response.json();

            if (response.ok) {
                this.renderDatasetSelector(data.datasets || []);
            } else {
                this.showError('加载数据集失败');
            }
        } catch (error) {
            console.error('加载数据集失败:', error);
            this.showError('网络错误');
        }
    }

    renderDatasetSelector(datasets) {
        const container = document.getElementById('datasetSelector');

        if (datasets.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <p>暂无数据集</p>
                    <a href="dataset.html" class="btn btn-primary">创建数据集</a>
                </div>
            `;
            return;
        }

        container.innerHTML = datasets.map(dataset => `
            <div class="dataset-option ${dataset.id === this.datasetId ? 'active' : ''}"
                 onclick="annotator.selectDataset('${dataset.id}')">
                <h4>${escapeHtml(dataset.name)}</h4>
                <p>${dataset.image_count || 0} 张图片</p>
                <small>${dataset.is_public ? '公开' : '私有'}</small>
            </div>
        `).join('');
    }

    selectDataset(datasetId) {
        this.datasetId = datasetId;
        this.currentImageIndex = 0;
        this.currentLabels = [];
        this.zoomLevel = 1.0;

        // 更新URL
        const url = new URL(window.location);
        url.searchParams.set('dataset', datasetId);
        window.history.pushState({}, '', url);

        this.hideDatasetSelector();
        this.loadDatasetInfo();
        this.loadImages();
    }

    async requestAISuggestions() {
        const image = this.images[this.currentImageIndex];
        if (!image) return;

        const aiSection = document.getElementById('aiSuggestions');
        const aiTags = document.getElementById('aiTags');

        aiSection.style.display = 'block';
        aiTags.innerHTML = '<div class="loading">正在分析图像...</div>';

        try {
            // 这里可以调用AI API来获取建议标签
            // 暂时模拟一些建议
            setTimeout(() => {
                const suggestions = ['object', 'scene', 'person']; // 模拟AI建议
                aiTags.innerHTML = suggestions.map(tag => `
                    <span class="ai-tag" onclick="annotator.addLabelFromTag('${tag}')">
                        ${tag}
                        <small>(85%)</small>
                    </span>
                `).join('');
            }, 2000);
        } catch (error) {
            console.error('AI建议失败:', error);
            aiTags.innerHTML = '<p class="error">获取AI建议失败</p>';
        }
    }

    showLoading(message) {
        // 使用全局加载指示器，如果存在的话
        if (window.showLoading) {
            window.showLoading(message);
        }
    }

    hideLoading() {
        if (window.hideLoading) {
            window.hideLoading();
        }
    }

    showSuccess(message) {
        if (window.showMessage) {
            window.showMessage(message, 'success');
        } else {
            alert(message);
        }
    }

    showError(message) {
        if (window.showMessage) {
            window.showMessage(message, 'error');
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

// 初始化
const annotator = new ImageAnnotator();
