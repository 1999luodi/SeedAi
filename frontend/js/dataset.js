const DM_MAX_FILES = 1000;

class DatasetFlowManager {
    constructor() {
        this.datasets = [];
        this.currentDataset = null;
        this.currentImages = [];
        this.pendingFiles = [];
        this.selectedImageId = null;

        this.el = {
            loginLink: document.getElementById('loginLink'),
            createBtn: document.getElementById('dmCreateBtn'),
            listView: document.getElementById('dmListView'),
            detailView: document.getElementById('dmDetailView'),
            cards: document.getElementById('dmDatasetCards'),
            datasetTitle: document.getElementById('dmDatasetTitle'),
            datasetMeta: document.getElementById('dmDatasetMeta'),
            fileList: document.getElementById('dmFileList'),
            annoSummary: document.getElementById('dmAnnoSummary'),
            backBtn: document.getElementById('dmBackBtn'),
            uploadBtn: document.getElementById('dmUploadBtn'),
            goAnnotateBtn: document.getElementById('dmGoAnnotateBtn'),
            createModal: document.getElementById('dmCreateModal'),
            createForm: document.getElementById('dmCreateForm'),
            nameInput: document.getElementById('dmName'),
            descInput: document.getElementById('dmDesc'),
            typeInput: document.getElementById('dmType'),
            closeCreate: document.getElementById('dmCloseCreate'),
            cancelCreate: document.getElementById('dmCancelCreate'),
            uploadModal: document.getElementById('dmUploadModal'),
            closeUpload: document.getElementById('dmCloseUpload'),
            dropZone: document.getElementById('dmDropZone'),
            pickFilesBtn: document.getElementById('dmPickFilesBtn'),
            pickFolderBtn: document.getElementById('dmPickFolderBtn'),
            startUploadBtn: document.getElementById('dmStartUploadBtn'),
            fileInput: document.getElementById('dmFileInput'),
            folderInput: document.getElementById('dmFolderInput'),
            uploadList: document.getElementById('dmUploadList')
        };

        this.setupAuth();
        this.bindEvents();
        this.loadDatasets();
    }

    setupAuth() {
        if (!SeedAI.auth.requireLogin('login.html')) {
            return;
        }

        SeedAI.auth.applyUserNav({
            loginLinkId: 'loginLink',
            loginText: '登录/注册',
            logoutText: '登出',
            logoutHref: 'login.html'
        });
    }

    bindEvents() {
        this.el.createBtn.addEventListener('click', () => this.toggleCreateModal(true));
        this.el.closeCreate.addEventListener('click', () => this.toggleCreateModal(false));
        this.el.cancelCreate.addEventListener('click', () => this.toggleCreateModal(false));
        this.el.createForm.addEventListener('submit', (event) => this.createDataset(event));

        this.el.backBtn.addEventListener('click', () => this.showListView());
        this.el.uploadBtn.addEventListener('click', () => this.toggleUploadModal(true));
        this.el.goAnnotateBtn.addEventListener('click', () => this.gotoAnnotate());

        this.el.closeUpload.addEventListener('click', () => this.toggleUploadModal(false));
        this.el.pickFilesBtn.addEventListener('click', () => this.el.fileInput.click());
        this.el.pickFolderBtn.addEventListener('click', () => this.el.folderInput.click());
        this.el.fileInput.addEventListener('change', (event) => this.handlePickedFiles(event.target.files));
        this.el.folderInput.addEventListener('change', (event) => this.handlePickedFiles(event.target.files));
        this.el.startUploadBtn.addEventListener('click', () => this.uploadPendingFiles());

        this.el.dropZone.addEventListener('dragover', (event) => {
            event.preventDefault();
            this.el.dropZone.classList.add('dragover');
        });

        this.el.dropZone.addEventListener('dragleave', () => {
            this.el.dropZone.classList.remove('dragover');
        });

        this.el.dropZone.addEventListener('drop', (event) => {
            event.preventDefault();
            this.el.dropZone.classList.remove('dragover');
            this.handlePickedFiles(event.dataTransfer.files);
        });

        [this.el.createModal, this.el.uploadModal].forEach((modal) => {
            modal.addEventListener('click', (event) => {
                if (event.target === modal) {
                    modal.style.display = 'none';
                }
            });
        });
    }

    async api(path, options = {}) {
        return SeedAI.api.request(path, options);
    }

    async loadDatasets() {
        try {
            const payload = await this.api(SeedAI.api.route('GET_API_DATASETS'));
            this.datasets = (payload && payload.data) || [];
            this.renderDatasetCards();
        } catch (error) {
            this.el.cards.innerHTML = `<div class="empty-state"><p>${error.message}</p></div>`;
        }
    }

    renderDatasetCards() {
        if (!this.datasets.length) {
            this.el.cards.innerHTML = '<div class="empty-state"><p>暂无数据集，先创建一个数据集。</p></div>';
            return;
        }

        this.el.cards.innerHTML = this.datasets.map((dataset) => {
            const typeText = dataset.category === 'classification' ? '分类' : '检测';
            const imageCount = Number.isFinite(Number(dataset.image_count))
                ? Number(dataset.image_count)
                : (Number.isFinite(Number(dataset.item_count)) ? Number(dataset.item_count) : 0);
            const isPublic = Boolean(dataset.is_public);
            const starClass = isPublic ? 'dm-visibility-star dm-visibility-star--public' : 'dm-visibility-star dm-visibility-star--private';
            const starTitle = isPublic ? '公开数据集' : '私密数据集';
            return `
                <article class="dm-card">
                    <span class="${starClass}" title="${starTitle}" aria-label="${starTitle}">&#9733;</span>
                    <h4>${this.escapeHtml(dataset.name)}</h4>
                    <p>${this.escapeHtml(dataset.description || '暂无描述')}</p>
                    <div class="dm-card-meta">
                        <span>类型: ${typeText}</span>
                        <span>数量: ${imageCount}</span>
                    </div>
                    <div class="dm-card-actions">
                        <button class="btn btn-secondary" data-open-id="${dataset.id}">打开</button>
                        <button class="btn btn-danger" data-del-id="${dataset.id}">删除</button>
                    </div>
                </article>
            `;
        }).join('');

        this.el.cards.querySelectorAll('[data-open-id]').forEach((button) => {
            button.addEventListener('click', () => this.openDataset(Number(button.dataset.openId)));
        });

        this.el.cards.querySelectorAll('[data-del-id]').forEach((button) => {
            button.addEventListener('click', () => this.deleteDataset(Number(button.dataset.delId)));
        });
    }

    toggleCreateModal(visible) {
        this.el.createModal.style.display = visible ? 'flex' : 'none';
        if (!visible) {
            this.el.createForm.reset();
        }
    }

    async createDataset(event) {
        event.preventDefault();

        const name = this.el.nameInput.value.trim();
        if (!name) {
            alert('请填写数据集名');
            return;
        }

        try {
            await this.api(SeedAI.api.route('POST_API_DATASETS'), {
                method: 'POST',
                body: JSON.stringify({
                    name,
                    description: this.el.descInput.value.trim(),
                    category: this.el.typeInput.value
                })
            });

            this.toggleCreateModal(false);
            await this.loadDatasets();
        } catch (error) {
            alert(error.message);
        }
    }

    async deleteDataset(datasetId) {
        if (!window.confirm('确定删除这个数据集吗？')) {
            return;
        }

        try {
            await this.api(SeedAI.api.route('DELETE_API_DATASETS_BY_DATASET_ID', { dataset_id: datasetId }), { method: 'DELETE' });
            await this.loadDatasets();
        } catch (error) {
            alert(error.message);
        }
    }

    async openDataset(datasetId) {
        this.gotoWorkspace(datasetId);
    }

    gotoWorkspace(datasetId) {
        const query = new URLSearchParams();
        query.set('dataset', String(datasetId));
        window.location.href = `dataset-workspace.html?${query.toString()}`;
    }

    showListView() {
        this.currentDataset = null;
        this.currentImages = [];
        this.selectedImageId = null;
        this.el.detailView.style.display = 'none';
        this.el.listView.style.display = 'block';
    }

    showDetailView() {
        this.el.listView.style.display = 'none';
        this.el.detailView.style.display = 'block';
    }

    renderFileList() {
        if (!this.currentImages.length) {
            this.el.fileList.innerHTML = '<p>该数据集暂无文件。</p>';
            return;
        }

        this.el.fileList.innerHTML = this.currentImages.map((image) => {
            const activeClass = image.id === this.selectedImageId ? ' active' : '';
            const hasAnnotation = Boolean(
                (image.annotations_path && String(image.annotations_path).trim()) ||
                (image.annotations && String(image.annotations).trim() && String(image.annotations).trim() !== '[]')
            );
            const statusText = hasAnnotation ? '是否标注: 已标注' : '是否标注: 未标注';
            return `
                <div class="dm-file-item${activeClass}">
                    <button class="dm-file-left" data-image-id="${image.id}" type="button">
                        <span class="dm-file-name" title="${this.escapeHtml(image.original_filename || image.filename || '')}">${this.escapeHtml(image.original_filename || image.filename)}</span>
                        <small class="dm-file-status">${this.escapeHtml(statusText)}</small>
                    </button>
                    <button class="btn btn-danger" data-delete-image-id="${image.id}" type="button">删除</button>
                </div>
            `;
        }).join('');

        this.el.fileList.querySelectorAll('[data-image-id]').forEach((item) => {
            item.addEventListener('click', async () => {
                this.selectedImageId = Number(item.dataset.imageId);
                this.renderFileList();
                await this.renderAnnotationSummary();
            });
        });

        this.el.fileList.querySelectorAll('[data-delete-image-id]').forEach((button) => {
            button.addEventListener('click', async (event) => {
                event.preventDefault();
                event.stopPropagation();
                const imageId = Number(button.dataset.deleteImageId);
                if (!imageId) {
                    return;
                }

                const targetImage = this.currentImages.find((item) => Number(item.id) === imageId);
                const displayName = targetImage ? (targetImage.original_filename || targetImage.filename || `ID ${imageId}`) : `ID ${imageId}`;
                await this.deleteImage(imageId, displayName);
            });
        });
    }

    async deleteImage(imageId, displayName) {
        if (!window.confirm(`确认删除「${displayName}」吗？`)) {
            return;
        }

        try {
            await this.api(`/images/${imageId}`, { method: 'DELETE' });

            if (this.selectedImageId === imageId) {
                this.selectedImageId = null;
            }

            await this.openDataset(this.currentDataset.id);
        } catch (error) {
            alert(error.message || '删除失败');
        }
    }

    async renderAnnotationSummary() {
        if (!this.currentImages.length) {
            this.el.annoSummary.innerHTML = '<p>上传文件后会自动生成同名标注JSON入口。</p>';
            return;
        }

        const targetImage = this.currentImages.find((image) => image.id === this.selectedImageId) || this.currentImages[0];
        if (!targetImage) {
            this.el.annoSummary.innerHTML = '<p>未找到文件。</p>';
            return;
        }

        const fileBaseName = (targetImage.original_filename || targetImage.filename || '').replace(/\.[^.]+$/, '');
        const localClassKey = this.getImageClassKey(targetImage.id);
        const localClasses = this.readJson(localClassKey, []);

        try {
            const annotationPayload = await this.api(`/images/${targetImage.id}/annotations`);
            const boxes = annotationPayload.data || [];

            this.ensureAnnotationPlaceholder(targetImage);

            const boxItems = boxes.length
                ? boxes.map((box) => `<li>${this.escapeHtml(box.label)} [${box.x_min.toFixed(3)}, ${box.y_min.toFixed(3)}, ${box.x_max.toFixed(3)}, ${box.y_max.toFixed(3)}]</li>`).join('')
                : '<li>暂无目标框</li>';
            const classItems = localClasses.length
                ? localClasses.map((name) => `<li>${this.escapeHtml(name)}</li>`).join('')
                : '<li>暂无分类标签</li>';

            this.el.annoSummary.innerHTML = `
                <div class="dm-summary-card">
                    <h5>文件: ${this.escapeHtml(targetImage.original_filename || targetImage.filename)}</h5>
                    <p>标注JSON: ${this.escapeHtml(fileBaseName)}.json</p>
                    <div class="dm-summary-grid">
                        <div>
                            <strong>目标框</strong>
                            <ul>${boxItems}</ul>
                        </div>
                        <div>
                            <strong>分类</strong>
                            <ul>${classItems}</ul>
                        </div>
                    </div>
                </div>
            `;
        } catch (error) {
            this.el.annoSummary.innerHTML = `<p>${this.escapeHtml(error.message)}</p>`;
        }
    }

    toggleUploadModal(visible) {
        this.el.uploadModal.style.display = visible ? 'flex' : 'none';
        if (!visible) {
            this.pendingFiles = [];
            this.el.uploadList.innerHTML = '';
            this.el.fileInput.value = '';
            this.el.folderInput.value = '';
        }
    }

    handlePickedFiles(fileList) {
        if (!fileList || !fileList.length) {
            return;
        }

        const incoming = Array.from(fileList);
        const merged = [...this.pendingFiles, ...incoming];

        if (merged.length > DM_MAX_FILES) {
            alert(`文件数量不能超过 ${DM_MAX_FILES}`);
            return;
        }

        this.pendingFiles = merged;
        this.el.uploadList.innerHTML = `
            <p>已选择 ${this.pendingFiles.length} 个文件</p>
            <div class="dm-upload-preview">
                ${this.pendingFiles.slice(0, 20).map((file) => `<span>${this.escapeHtml(file.name)}</span>`).join('')}
            </div>
        `;
    }

    async uploadPendingFiles() {
        if (!this.currentDataset) {
            alert('请先打开一个数据集');
            return;
        }

        if (!this.pendingFiles.length) {
            alert('请先选择文件');
            return;
        }

        const uploaded = [];
        const failed = [];

        for (let index = 0; index < this.pendingFiles.length; index += 1) {
            const file = this.pendingFiles[index];
            const formData = new FormData();
            formData.append('file', file);

            try {
                await SeedAI.api.upload(SeedAI.api.route('POST_API_DATASETS_BY_DATASET_ID_UPLOAD', { dataset_id: this.currentDataset.id }), formData);
                uploaded.push(file.name);
            } catch (error) {
                failed.push(`${file.name}: ${error.message}`);
            }

            this.el.uploadList.innerHTML = `<p>上传进度 ${index + 1}/${this.pendingFiles.length}</p>`;
        }

        if (uploaded.length) {
            alert(`上传完成，成功 ${uploaded.length} 个${failed.length ? `，失败 ${failed.length} 个` : ''}`);
        } else {
            alert('上传失败，请重试');
        }

        if (failed.length) {
            this.el.uploadList.innerHTML = `<p>${failed.join('<br>')}</p>`;
        }

        await this.openDataset(this.currentDataset.id);
        this.toggleUploadModal(false);
    }

    gotoAnnotate() {
        if (!this.currentDataset) {
            return;
        }

        const query = new URLSearchParams();
        query.set('dataset', String(this.currentDataset.id));
        if (this.selectedImageId) {
            query.set('image', String(this.selectedImageId));
        }
        window.location.href = `annotate.html?${query.toString()}`;
    }

    ensureAnnotationPlaceholder(image) {
        if (!this.currentDataset) {
            return;
        }

        const key = this.getDatasetAnnotationKey(this.currentDataset.id);
        const json = this.readJson(key, {});
        const filename = image.original_filename || image.filename;

        if (!json[filename]) {
            json[filename] = {
                jsonFile: `${filename.replace(/\.[^.]+$/, '')}.json`,
                createdAt: new Date().toISOString()
            };
            localStorage.setItem(key, JSON.stringify(json));
        }
    }

    getDatasetAnnotationKey(datasetId) {
        return `seedai.dataset.annotations.${datasetId}`;
    }

    getImageClassKey(imageId) {
        return `seedai.image.classes.${imageId}`;
    }

    readJson(key, fallback) {
        const raw = localStorage.getItem(key);
        if (!raw) {
            return fallback;
        }
        try {
            return JSON.parse(raw);
        } catch (error) {
            return fallback;
        }
    }

    escapeHtml(value) {
        const div = document.createElement('div');
        div.textContent = value || '';
        return div.innerHTML;
    }
}

window.addEventListener('DOMContentLoaded', () => {
    window.datasetFlowManager = new DatasetFlowManager();
});
