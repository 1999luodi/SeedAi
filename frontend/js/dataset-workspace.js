const WS_MAX_FILES = 1000;
const WS_MAX_TOTAL_BYTES = 5 * 1024 * 1024 * 1024; // 5GB

class DatasetWorkspacePage {
    constructor() {
        this.query = new URLSearchParams(window.location.search);
        this.datasetId = this.query.get('dataset');
        this.dataset = null;
        this.images = [];
        this.pendingFiles = [];

        this.el = {
            loginLink: document.getElementById('loginLink'),
            datasetTitle: document.getElementById('wsDatasetTitle'),
            datasetMeta: document.getElementById('wsDatasetMeta'),
            visibilitySelect: document.getElementById('wsVisibilitySelect'),
            toAnnotateBtn: document.getElementById('wsToAnnotateBtn'),
            backBtn: document.getElementById('wsBackBtn'),
            dropZone: document.getElementById('wsDropZone'),
            pickFilesBtn: document.getElementById('wsPickFilesBtn'),
            pickFolderBtn: document.getElementById('wsPickFolderBtn'),
            clearBtn: document.getElementById('wsClearBtn'),
            startUploadBtn: document.getElementById('wsStartUploadBtn'),
            fileInput: document.getElementById('wsFileInput'),
            folderInput: document.getElementById('wsFolderInput'),
            uploadSummary: document.getElementById('wsUploadSummary'),
            uploadList: document.getElementById('wsUploadList'),
            fileList: document.getElementById('wsFileList')
        };

        this.setupAuth();
        this.bindEvents();
        this.bootstrap();
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
        // Prevent browser default file-open behavior outside the drop zone.
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach((eventName) => {
            window.addEventListener(eventName, (event) => {
                event.preventDefault();
            });
        });

        this.el.backBtn.addEventListener('click', () => {
            window.location.href = 'dataset.html';
        });

        this.el.visibilitySelect.addEventListener('change', () => this.updateVisibility());

        this.el.toAnnotateBtn.addEventListener('click', () => {
            if (!this.datasetId) {
                return;
            }
            window.location.href = `annotate.html?dataset=${encodeURIComponent(String(this.datasetId))}`;
        });

        this.el.pickFilesBtn.addEventListener('click', () => this.el.fileInput.click());
        this.el.pickFolderBtn.addEventListener('click', () => this.el.folderInput.click());
        this.el.clearBtn.addEventListener('click', () => this.clearPendingFiles());
        this.el.startUploadBtn.addEventListener('click', () => this.uploadPendingFiles());

        this.el.fileInput.addEventListener('change', (event) => this.handlePickedFiles(event.target.files));
        this.el.folderInput.addEventListener('change', (event) => this.handlePickedFiles(event.target.files));

        this.el.dropZone.addEventListener('dragover', (event) => {
            event.preventDefault();
            event.stopPropagation();
            this.el.dropZone.classList.add('dragover');
        });

        this.el.dropZone.addEventListener('dragleave', (event) => {
            event.preventDefault();
            event.stopPropagation();
            this.el.dropZone.classList.remove('dragover');
        });

        this.el.dropZone.addEventListener('drop', async (event) => {
            event.preventDefault();
            event.stopPropagation();
            this.el.dropZone.classList.remove('dragover');

            const droppedFiles = await this.extractDroppedFiles(event);
            this.handlePickedFiles(droppedFiles);
        });
    }

    async extractDroppedFiles(event) {
        const transfer = event && event.dataTransfer ? event.dataTransfer : null;
        if (!transfer) {
            return [];
        }

        const items = transfer.items ? Array.from(transfer.items) : [];
        if (!items.length) {
            return transfer.files ? Array.from(transfer.files) : [];
        }

        const files = [];
        for (const item of items) {
            if (!item || item.kind !== 'file') {
                continue;
            }

            if (typeof item.webkitGetAsEntry === 'function') {
                const entry = item.webkitGetAsEntry();
                if (entry) {
                    const nestedFiles = await this.readEntryFiles(entry);
                    files.push(...nestedFiles);
                    continue;
                }
            }

            const file = item.getAsFile();
            if (file) {
                files.push(file);
            }
        }

        return files;
    }

    readEntryFiles(entry) {
        return new Promise((resolve) => {
            if (!entry) {
                resolve([]);
                return;
            }

            if (entry.isFile) {
                entry.file((file) => resolve(file ? [file] : []), () => resolve([]));
                return;
            }

            if (entry.isDirectory) {
                const reader = entry.createReader();
                const allEntries = [];

                const readBatch = () => {
                    reader.readEntries(async (batch) => {
                        if (!batch || !batch.length) {
                            const nested = await Promise.all(allEntries.map((child) => this.readEntryFiles(child)));
                            resolve(nested.flat());
                            return;
                        }

                        allEntries.push(...batch);
                        readBatch();
                    }, () => resolve([]));
                };

                readBatch();
                return;
            }

            resolve([]);
        });
    }

    async bootstrap() {
        if (!this.datasetId) {
            alert('缺少数据集ID，已返回数据集列表');
            window.location.href = 'dataset.html';
            return;
        }

        await this.loadDataset();
    }

    async api(path, options = {}) {
        return SeedAI.api.request(path, options);
    }

    async loadDataset() {
        try {
            const datasetPayload = await this.api(SeedAI.api.route('GET_API_DATASETS_BY_DATASET_ID', { dataset_id: this.datasetId }));
            const imagesPayload = await this.api(SeedAI.api.route('GET_API_DATASETS_BY_DATASET_ID_IMAGES', { dataset_id: this.datasetId }));

            this.dataset = datasetPayload.data;
            this.images = imagesPayload.data || [];

            const typeText = this.dataset.category === 'classification' ? '分类' : '检测';
            const visibilityText = this.dataset.is_public ? '公开' : '私密';
            this.el.datasetTitle.textContent = this.dataset.name || '数据集操作';
            this.el.datasetMeta.textContent = `类型: ${typeText} | 可见性: ${visibilityText} | 文件数: ${this.images.length}`;
            this.el.visibilitySelect.value = this.dataset.is_public ? 'public' : 'private';

            this.renderFileList();
            this.renderPendingSummary();
        } catch (error) {
            alert(error.message || '加载数据集失败');
            window.location.href = 'dataset.html';
        }
    }

    handlePickedFiles(fileList) {
        if (!fileList || !fileList.length) {
            return;
        }

        const incoming = Array.from(fileList);
        const merged = [...this.pendingFiles, ...incoming];

        if (merged.length > WS_MAX_FILES) {
            alert(`文件数量不能超过 ${WS_MAX_FILES} 个`);
            return;
        }

        const totalBytes = merged.reduce((acc, file) => acc + (file.size || 0), 0);
        if (totalBytes >= WS_MAX_TOTAL_BYTES) {
            alert('单次上传总大小必须小于 5GB');
            return;
        }

        this.pendingFiles = merged;
        this.renderPendingSummary();
        this.renderPendingList();
    }

    clearPendingFiles() {
        this.pendingFiles = [];
        this.el.fileInput.value = '';
        this.el.folderInput.value = '';
        this.renderPendingSummary();
        this.renderPendingList();
    }

    renderPendingSummary() {
        const totalBytes = this.pendingFiles.reduce((acc, file) => acc + (file.size || 0), 0);
        const totalText = this.formatBytes(totalBytes);
        this.el.uploadSummary.textContent = `已选择 ${this.pendingFiles.length} / ${WS_MAX_FILES} 个文件，当前总大小 ${totalText} / < 5GB`;
    }

    renderPendingList() {
        if (!this.pendingFiles.length) {
            this.el.uploadList.innerHTML = '<p>尚未选择文件</p>';
            return;
        }

        this.el.uploadList.innerHTML = `
            <p>待上传文件（显示前20个）</p>
            <div class="dm-upload-preview">
                ${this.pendingFiles.slice(0, 20).map((file) => `<span>${this.escapeHtml(file.name)}</span>`).join('')}
            </div>
        `;
    }

    async uploadPendingFiles() {
        if (!this.pendingFiles.length) {
            alert('请先选择文件');
            return;
        }

        const validation = this.validateUploadPairs(this.pendingFiles);
        if (validation.blockedMessages.length) {
            const preview = validation.blockedMessages.slice(0, 12).join('\n');
            alert(`以下文件不满足一一唯一对应规则，已阻止上传:\n${preview}${validation.blockedMessages.length > 12 ? '\n...（其余略）' : ''}`);
        }

        if (!validation.validPairs.length) {
            this.el.uploadList.innerHTML = '<p>没有符合规则的文件可上传</p>';
            return;
        }

        const totalBytes = this.pendingFiles.reduce((acc, file) => acc + (file.size || 0), 0);
        if (this.pendingFiles.length > WS_MAX_FILES) {
            alert(`文件数量不能超过 ${WS_MAX_FILES} 个`);
            return;
        }
        if (totalBytes >= WS_MAX_TOTAL_BYTES) {
            alert('单次上传总大小必须小于 5GB');
            return;
        }

        const uploaded = [];
        const failed = [];

        for (let index = 0; index < validation.validPairs.length; index += 1) {
            const pair = validation.validPairs[index];
            const formData = new FormData();
            formData.append('file', pair.imageFile);
            if (pair.annotationFile) {
                formData.append('annotation', pair.annotationFile);
            }

            try {
                await SeedAI.api.upload(SeedAI.api.route('POST_API_DATASETS_BY_DATASET_ID_UPLOAD', { dataset_id: this.datasetId }), formData);
                uploaded.push(pair.imageFile.name + (pair.annotationFile ? ` + ${pair.annotationFile.name}` : ''));
            } catch (error) {
                failed.push(`${pair.imageFile.name}: ${error.message}`);
            }

            this.el.uploadList.innerHTML = `<p>上传进度 ${index + 1}/${validation.validPairs.length}</p>`;
        }

        if (uploaded.length) {
            alert(`上传完成，成功 ${uploaded.length} 个${failed.length ? `，失败 ${failed.length} 个` : ''}`);
        } else {
            alert('上传失败，请重试');
        }

        if (failed.length) {
            this.el.uploadList.innerHTML = `<p>${failed.join('<br>')}</p>`;
        } else {
            this.clearPendingFiles();
        }

        await this.loadDataset();
    }

    validateUploadPairs(files) {
        const imageExt = new Set(['png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp']);
        const grouped = new Map();
        const blockedMessages = [];
        const validPairs = [];

        const getStem = (name) => {
            const n = String(name || '');
            const dot = n.lastIndexOf('.');
            return (dot > 0 ? n.slice(0, dot) : n).toLowerCase();
        };
        const getExt = (name) => {
            const n = String(name || '');
            const dot = n.lastIndexOf('.');
            return dot > -1 ? n.slice(dot + 1).toLowerCase() : '';
        };

        (files || []).forEach((file) => {
            const stem = getStem(file.name);
            if (!grouped.has(stem)) {
                grouped.set(stem, []);
            }
            grouped.get(stem).push(file);
        });

        grouped.forEach((rows, stem) => {
            if (rows.length >= 3) {
                blockedMessages.push(`文件名 ${stem} 出现 ${rows.length} 次（>=3），该组全部禁止上传`);
                return;
            }

            const images = rows.filter((f) => imageExt.has(getExt(f.name)));
            const jsons = rows.filter((f) => getExt(f.name) === 'json');
            const others = rows.filter((f) => !imageExt.has(getExt(f.name)) && getExt(f.name) !== 'json');

            if (others.length > 0) {
                blockedMessages.push(`文件名 ${stem} 包含不支持的文件类型，已禁止上传`);
                return;
            }
            if (images.length > 1 || jsons.length > 1) {
                blockedMessages.push(`文件名 ${stem} 不是一一唯一对应（图片:${images.length}, JSON:${jsons.length}），已禁止上传`);
                return;
            }
            if (jsons.length === 1 && images.length === 0) {
                blockedMessages.push(`文件名 ${stem} 只有JSON没有对应图片，已禁止上传`);
                return;
            }
            if (images.length === 0) {
                return;
            }

            validPairs.push({
                stem,
                imageFile: images[0],
                annotationFile: jsons[0] || null
            });
        });

        return { validPairs, blockedMessages };
    }

    async updateVisibility() {
        if (!this.datasetId) {
            return;
        }

        const isPublic = this.el.visibilitySelect.value === 'public';

        try {
            this.el.visibilitySelect.disabled = true;
            await this.api(SeedAI.api.route('GET_API_DATASETS_BY_DATASET_ID', { dataset_id: this.datasetId }), {
                method: 'PUT',
                body: JSON.stringify({ is_public: isPublic })
            });
            await this.loadDataset();
        } catch (error) {
            alert(error.message || '可见性更新失败');
        } finally {
            this.el.visibilitySelect.disabled = false;
        }
    }

    renderFileList() {
        if (!this.images.length) {
            this.el.fileList.innerHTML = '<p>该数据集暂无文件。</p>';
            return;
        }

        this.el.fileList.innerHTML = this.images.map((image) => `
            <div class="dm-file-item ws-file-item">
                <div class="ws-file-left">
                    <span class="dm-file-name" title="${this.escapeHtml(image.original_filename || image.filename || '')}">${this.escapeHtml(image.original_filename || image.filename)}</span>
                    ${(() => {
                        const annotated = image.annotations_path && String(image.annotations_path).trim();
                        const statusClass = annotated ? 'ws-file-status-tag--done' : 'ws-file-status-tag--pending';
                        const statusText = annotated ? '已标注' : '未标注';
                        return `<small class="ws-file-status">是否标注: <span class="ws-file-status-tag ${statusClass}">${statusText}</span></small>`;
                    })()}
                </div>
                <button class="btn btn-danger" type="button" data-delete-image-id="${image.id}">删除</button>
            </div>
        `).join('');

        this.el.fileList.querySelectorAll('[data-delete-image-id]').forEach((button) => {
            button.addEventListener('click', async (event) => {
                event.preventDefault();
                event.stopPropagation();
                const imageId = Number(button.getAttribute('data-delete-image-id'));
                if (!imageId) {
                    return;
                }

                const image = this.images.find((item) => Number(item.id) === imageId);
                const displayName = image ? (image.original_filename || image.filename || `ID ${imageId}`) : `ID ${imageId}`;
                await this.deleteImageFromDataset(imageId, displayName);
            });
        });
    }

    async deleteImageFromDataset(imageId, displayName) {
        const confirmed = window.confirm(`确认删除图片「${displayName}」吗？\n将同时删除数据库记录、原始图片和标注文件。`);
        if (!confirmed) {
            return;
        }

        try {
            await this.api(`/images/${imageId}`, { method: 'DELETE' });
            await this.loadDataset();
            alert('图片删除成功');
        } catch (error) {
            alert(`删除失败: ${error.message || '未知错误'}`);
        }
    }

    formatBytes(bytes) {
        if (!bytes) {
            return '0 B';
        }

        const units = ['B', 'KB', 'MB', 'GB', 'TB'];
        let size = bytes;
        let index = 0;

        while (size >= 1024 && index < units.length - 1) {
            size /= 1024;
            index += 1;
        }

        return `${size.toFixed(index === 0 ? 0 : 2)} ${units[index]}`;
    }

    escapeHtml(value) {
        const div = document.createElement('div');
        div.textContent = value || '';
        return div.innerHTML;
    }
}

window.addEventListener('DOMContentLoaded', () => {
    window.datasetWorkspacePage = new DatasetWorkspacePage();
});
