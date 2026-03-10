class ManualAnnotationPage {
    constructor() {
        this.query = new URLSearchParams(window.location.search);
        this.datasetId = this.query.get('dataset');
        this.targetImageId = this.query.get('image');

        this.datasets = [];
        this.images = [];
        this.currentIndex = 0;
        this.mode = 'bbox';
        this.zoom = 1; 
        this.boxStrokeWidth = 8; // Base stroke width for boxes at zoom level 1.
        this.selectedBoxStrokeWidth = this.boxStrokeWidth * 2; // Selected box is 2x base stroke width.
        this.previewStrokeWidth = 10; // Stroke width for the preview box at zoom level 1.
        // Shared palette for label categories only; interaction hint colors are excluded.
        this.categoryColorPalette = [
            '#2563eb', '#ef4444', '#0d9488', '#d97706', '#7c3aed',
            '#0891b2', '#dc2626', '#65a30d', '#1d4ed8', '#be185d',
            '#0f766e', '#b45309'
        ];
        this.previewStrokeColor = '#22c55e';

        this.categories = [];
        this.boxes = [];
        this.classes = [];
        this.pendingBox = null;
        this.drawingStart = null;
        this.mousePoint = null;
        this.selectedBoxId = null;
        this.activeHandle = null;
        this.isDraggingHandle = false;
        this.handleHitSize = 10;
        this.dirty = false;
        this.isPanning = false;
        this.panMoved = false;
        this.panStartX = 0;
        this.panStartY = 0;
        this.panStartScrollLeft = 0;
        this.panStartScrollTop = 0;
        this.spacePressed = false;

        this.modalAction = null;
        this.currentObjectUrl = null;

        this.el = {
            loginLink: document.getElementById('loginLink'),
            datasetTitle: document.getElementById('annDatasetTitle'),
            statusText: document.getElementById('annStatusText'),
            tools: document.querySelectorAll('.ann-tool'),
            prevBtn: document.getElementById('annPrevBtn'),
            nextBtn: document.getElementById('annNextBtn'),
            saveBtn: document.getElementById('annSaveBtn'),
            exitBtn: document.getElementById('annExitBtn'),
            zoomOut: document.getElementById('annZoomOut'),
            zoomIn: document.getElementById('annZoomIn'),
            zoomReset: document.getElementById('annZoomReset'),
            zoomText: document.getElementById('annZoomText'),
            canvasWrap: document.getElementById('annCanvasWrap'),
            image: document.getElementById('annImage'),
            canvas: document.getElementById('annCanvas'),
            empty: document.getElementById('annEmpty'),
            addCategoryBtn: document.getElementById('annAddCategoryBtn'),
            categoryList: document.getElementById('annCategoryList'),
            labelFilter: document.getElementById('annLabelFilter'),
            labelList: document.getElementById('annLabelList'),
            fileList: document.getElementById('annFileList'),
            fileSearch: document.getElementById('annFileSearch'),
            datasetModal: document.getElementById('annDatasetModal'),
            datasetOptions: document.getElementById('annDatasetOptions'),
            categoryModal: document.getElementById('annCategoryModal'),
            categoryModalTitle: document.getElementById('annCategoryModalTitle'),
            categorySelect: document.getElementById('annCategorySelect'),
            categoryConfirm: document.getElementById('annCategoryConfirm'),
            categoryCancel: document.getElementById('annCategoryCancel'),
            addCategoryModal: document.getElementById('annAddCategoryModal'),
            addCategoryInput: document.getElementById('annAddCategoryInput'),
            addCategoryConfirm: document.getElementById('annAddCategoryConfirm'),
            addCategoryCancel: document.getElementById('annAddCategoryCancel'),
            contextMenu: document.getElementById('annContextMenu'),
            ctxDelete: document.getElementById('annCtxDelete'),
            ctxChangeCategory: document.getElementById('annCtxChangeCategory')
        };

        this.ctx = this.el.canvas.getContext('2d');

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
        this.handleCtrlWheelZoom = this.handleCtrlWheelZoom.bind(this);

        this.el.tools.forEach((tool) => {
            tool.addEventListener('click', () => this.setMode(tool.dataset.mode));
        });

        this.el.prevBtn.addEventListener('click', () => this.switchImage(this.currentIndex - 1));
        this.el.nextBtn.addEventListener('click', () => this.switchImage(this.currentIndex + 1));
        this.el.saveBtn.addEventListener('click', () => this.saveCurrentImage());
        this.el.exitBtn.addEventListener('click', async () => {
            await this.saveCurrentImage();
            window.location.href = 'dataset.html';
        });

        if (this.el.zoomOut) {
            this.el.zoomOut.addEventListener('click', () => this.changeZoom(this.zoom / 1.2));
        }
        if (this.el.zoomIn) {
            this.el.zoomIn.addEventListener('click', () => this.changeZoom(this.zoom * 1.2));
        }
        if (this.el.zoomReset) {
            this.el.zoomReset.addEventListener('click', () => this.fitZoom());
        }

        this.el.addCategoryBtn.addEventListener('click', () => this.openAddCategoryModal());

        this.el.canvas.addEventListener('mousedown', (event) => this.handleMouseDown(event));
        this.el.canvas.addEventListener('mousemove', (event) => this.handleMouseMove(event));
        this.el.canvas.addEventListener('mouseleave', () => this.handleMouseLeave());
        this.el.canvas.addEventListener('contextmenu', (event) => this.handleContextMenu(event));
        window.addEventListener('mouseup', (event) => this.handleMouseUp(event));
        window.addEventListener('keydown', (event) => this.handleKeyDown(event));
        window.addEventListener('keyup', (event) => this.handleKeyUp(event));
        window.addEventListener('resize', () => this.applyZoom());

        this.el.categoryConfirm.addEventListener('click', () => this.applyCategoryModal());
        this.el.categoryCancel.addEventListener('click', () => this.closeCategoryModal());
        this.el.addCategoryConfirm.addEventListener('click', () => this.addCategory());
        this.el.addCategoryCancel.addEventListener('click', () => this.closeAddCategoryModal());
        this.el.addCategoryInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter') {
                event.preventDefault();
                this.addCategory();
            }
        });

        this.el.ctxDelete.addEventListener('click', () => this.deleteSelectedBox());
        this.el.ctxChangeCategory.addEventListener('click', () => this.openChangeCategoryForSelectedBox());
        this.el.labelFilter.addEventListener('change', () => this.renderLabelList());
        this.el.fileSearch.addEventListener('input', () => this.renderFileList());

        // Intercept Ctrl+wheel on multiple targets/events to reliably suppress browser page zoom.
        window.addEventListener('wheel', this.handleCtrlWheelZoom, { passive: false, capture: true });
        document.addEventListener('wheel', this.handleCtrlWheelZoom, { passive: false, capture: true });
        this.el.canvasWrap.addEventListener('wheel', this.handleCtrlWheelZoom, { passive: false, capture: true });
        window.addEventListener('mousewheel', this.handleCtrlWheelZoom, { passive: false, capture: true });
        window.addEventListener('DOMMouseScroll', this.handleCtrlWheelZoom, { passive: false, capture: true });

        this.bindNavigationSaveGuard();

        document.addEventListener('click', (event) => {
            if (!this.el.contextMenu.contains(event.target)) {
                this.hideContextMenu();
            }
        });
    }

    handleCtrlWheelZoom(event) {
        if (!event || !event.ctrlKey) {
            return;
        }

        // Block browser-level zoom first.
        event.preventDefault();
        if (typeof event.stopPropagation === 'function') {
            event.stopPropagation();
        }

        if (!this.images[this.currentIndex]) {
            return;
        }

        const delta = Number(event.deltaY);
        const direction = Number.isFinite(delta)
            ? (delta < 0 ? -1 : 1)
            : ((Number(event.wheelDelta) > 0 || Number(event.detail) < 0) ? -1 : 1);

        const factor = direction < 0 ? 1.1 : 0.9;
        this.changeZoom(this.zoom * factor);
    }

    bindNavigationSaveGuard() {
        const navLinks = document.querySelectorAll('.nav a[href]');
        navLinks.forEach((link) => {
            link.addEventListener('click', async (event) => {
                const href = (link.getAttribute('href') || '').trim();
                if (!href || href.startsWith('javascript:') || href.startsWith('#')) {
                    return;
                }

                const currentPath = (window.location.pathname || '').split('/').pop();
                if (href === currentPath || href === 'annotate.html') {
                    return;
                }

                event.preventDefault();
                await this.saveCurrentImage();
                window.location.href = href;
            });
        });
    }

    async bootstrap() {
        if (!this.datasetId) {
            await this.openDatasetPicker();
            return;
        }

        await this.loadDataset(this.datasetId);
    }

    async api(path, options = {}) {
        return SeedAI.api.request(path, options);
    }

    async openDatasetPicker() {
        this.el.datasetModal.style.display = 'flex';
        try {
            const payload = await this.api(SeedAI.api.route('GET_API_DATASETS'));
            this.datasets = payload.data || [];

            if (!this.datasets.length) {
                this.renderNoDatasetPrompt('暂无数据集，请先在数据集管理页面创建。');
                return;
            }

            const datasetCountMap = await this.fetchDatasetImageCounts(this.datasets);

            this.el.datasetOptions.innerHTML = this.datasets.map((dataset) => `
                <button class="ann-dataset-option${String(this.datasetId || '') === String(dataset.id) ? ' active' : ''}" data-dataset-id="${dataset.id}" type="button">
                    <strong>${this.escapeHtml(dataset.name)}</strong>
                    <span>类型: ${dataset.category === 'classification' ? '分类' : '检测'} | 文件数: ${datasetCountMap[String(dataset.id)] ?? 0}</span>
                </button>
            `).join('');

            this.el.datasetOptions.querySelectorAll('[data-dataset-id]').forEach((button) => {
                button.addEventListener('click', async () => {
                    this.el.datasetOptions.querySelectorAll('.ann-dataset-option').forEach((item) => {
                        item.classList.remove('active');
                    });
                    button.classList.add('active');
                    this.datasetId = button.dataset.datasetId;

                    // Keep selection state visible before modal closes.
                    await new Promise((resolve) => {
                        window.setTimeout(resolve, 80);
                    });

                    this.el.datasetModal.style.display = 'none';
                    await this.loadDataset(this.datasetId);
                });
            });
        } catch (error) {
            this.renderNoDatasetPrompt(this.escapeHtml(error.message));
        }
    }

    async fetchDatasetImageCounts(datasets) {
        const entries = await Promise.all(datasets.map(async (dataset) => {
            try {
                const imagesPayload = await this.api(SeedAI.api.route('GET_API_DATASETS_BY_DATASET_ID_IMAGES', {
                    dataset_id: dataset.id
                }));
                const images = Array.isArray(imagesPayload.data) ? imagesPayload.data : [];
                return [String(dataset.id), images.length];
            } catch (error) {
                return [String(dataset.id), Number(dataset.item_count) || 0];
            }
        }));

        return Object.fromEntries(entries);
    }

    renderNoDatasetPrompt(message) {
        this.el.datasetOptions.innerHTML = `
            <p style="margin-bottom: 12px;">${message}</p>
            <div class="form-actions" style="margin-top: 12px; justify-content: center;">
                <button id="annNoDatasetConfirm" class="btn btn-primary" type="button" style="min-width: 120px;">确认</button>
            </div>
        `;

        const confirmBtn = document.getElementById('annNoDatasetConfirm');
        if (confirmBtn) {
            confirmBtn.addEventListener('click', () => {
                window.location.href = 'dataset.html';
            });
        }
    }

    async loadDataset(datasetId) {
        try {
            const datasetPayload = await this.api(SeedAI.api.route('GET_API_DATASETS_BY_DATASET_ID', { dataset_id: datasetId }));
            const imagesPayload = await this.api(SeedAI.api.route('GET_API_DATASETS_BY_DATASET_ID_IMAGES', { dataset_id: datasetId }));

            this.datasetId = String(datasetId);
            this.images = imagesPayload.data || [];
            this.categories = await this.loadCategoriesFromServer(datasetId);

            this.el.datasetTitle.textContent = `${datasetPayload.data.name} - 手工标注`;
            this.el.statusText.textContent = `模式: ${this.getModeLabel(this.mode)} | 数据 ${this.images.length} 张`;

            this.renderCategoryList();
            this.renderFileList();

            if (!this.images.length) {
                this.renderEmptyState('该数据集暂无图片');
                return;
            }

            this.currentIndex = 0;

            await this.loadCurrentImage();
        } catch (error) {
            this.renderEmptyState(error.message);
        }
    }

    renderEmptyState(text) {
        this.el.empty.style.display = 'flex';
        this.el.empty.textContent = text;
        this.el.image.style.display = 'none';
        this.ctx.clearRect(0, 0, this.el.canvas.width, this.el.canvas.height);
    }

    setMode(mode) {
        this.mode = mode;
        this.activeHandle = null;
        this.isDraggingHandle = false;
        if (this.mode !== 'bbox') {
            this.mousePoint = null;
            this.drawingStart = null;
            this.draw();
        }
        this.el.tools.forEach((tool) => tool.classList.toggle('active', tool.dataset.mode === mode));
        this.el.statusText.textContent = `模式: ${this.getModeLabel(this.mode)} | 第 ${this.currentIndex + 1}/${this.images.length} 张`;
        this.renderLabelList();
        this.hideContextMenu();
    }

    getModeLabel(mode) {
        if (mode === 'bbox') return '目标框';
        if (mode === 'classify') return '分类';
        return '修改';
    }

    async loadCurrentImage() {
        const image = this.images[this.currentIndex];
        if (!image) {
            this.renderEmptyState('无可用图片');
            return;
        }

        this.selectedBoxId = null;
        this.drawingStart = null;
        this.pendingBox = null;
        this.mousePoint = null;

        try {
            const annotationPayload = await this.api(`/images/${image.id}/annotations`);
            const rows = Array.isArray(annotationPayload.data)
                ? annotationPayload.data
                : (annotationPayload.data && Array.isArray(annotationPayload.data.annotations)
                    ? annotationPayload.data.annotations
                    : []);

            this.boxes = rows.map((box) => ({
                id: box.id,
                localId: `box-${box.id}`,
                label: box.label,
                x_min: box.x_min,
                y_min: box.y_min,
                x_max: box.x_max,
                y_max: box.y_max
            }));
        } catch (error) {
            this.boxes = [];
        }

        this.classes = this.readJson(this.getImageClassKey(image.id), []);
        this.dirty = false;
        this.renderLabelList();
        this.renderFileList();

        const src = await this.resolveImageSrc(image);
        this.el.image.onload = () => {
            this.el.empty.style.display = 'none';
            this.el.image.style.display = 'block';

            this.el.canvas.width = this.el.image.naturalWidth;
            this.el.canvas.height = this.el.image.naturalHeight;
            this.el.canvas.style.width = `${this.el.image.naturalWidth}px`;
            this.el.canvas.style.height = `${this.el.image.naturalHeight}px`;
            this.el.image.style.width = `${this.el.image.naturalWidth}px`;
            this.el.image.style.height = `${this.el.image.naturalHeight}px`;

            this.fitZoom();
            this.draw();
            this.updateStatusText();
        };
        this.el.image.src = src;
    }

    async resolveImageSrc(image) {
        if (this.currentObjectUrl) {
            URL.revokeObjectURL(this.currentObjectUrl);
            this.currentObjectUrl = null;
        }

        const token = SeedAI.token.get();
        const response = await fetch(`/api/images/${image.id}/content`, {
            headers: token ? { Authorization: `Bearer ${token}` } : {}
        });

        if (!response.ok) {
            throw new Error(`图片加载失败: HTTP ${response.status}`);
        }

        const blob = await response.blob();
        this.currentObjectUrl = URL.createObjectURL(blob);
        return this.currentObjectUrl;
    }

    async switchImage(targetIndex) {
        if (targetIndex < 0 || targetIndex >= this.images.length) {
            return;
        }
        await this.saveCurrentImage();
        this.currentIndex = targetIndex;
        await this.loadCurrentImage();
    }

    updateStatusText() {
        this.el.statusText.textContent = `模式: ${this.getModeLabel(this.mode)} | 第 ${this.currentIndex + 1}/${this.images.length} 张`;
    }

    renderFileList() {
        if (!this.images.length) {
            this.el.fileList.innerHTML = '<p>暂无数据</p>';
            return;
        }

        const keyword = (this.el.fileSearch.value || '').trim().toLowerCase();
        const filtered = this.images.filter((image) => {
            if (!keyword) {
                return true;
            }
            const text = String(image.original_filename || image.filename || '').toLowerCase();
            return text.includes(keyword);
        });

        if (!filtered.length) {
            this.el.fileList.innerHTML = '<p>未匹配到文件</p>';
            return;
        }

        this.el.fileList.innerHTML = filtered.map((image) => {
            const index = this.images.findIndex((it) => it.id === image.id);
            const activeClass = index === this.currentIndex ? ' active' : '';
            const checkedAttr = index === this.currentIndex ? 'checked' : '';
            const displayText = image.original_filename || image.filename;
            return `
                <button class="ann-file-item${activeClass}" data-file-index="${index}" type="button">
                    <input class="ann-list-checkbox" type="checkbox" ${checkedAttr}>
                    <span>${this.escapeHtml(displayText)}</span>
                </button>
            `;
        }).join('');

        this.el.fileList.querySelectorAll('[data-file-index]').forEach((button) => {
            const checkbox = button.querySelector('.ann-list-checkbox');
            if (checkbox) {
                checkbox.addEventListener('click', (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                });
            }
            button.addEventListener('click', () => this.switchImage(Number(button.dataset.fileIndex)));
        });
    }

    renderCategoryList() {
        if (!this.categories.length) {
            this.el.categoryList.innerHTML = '<p>暂无类别</p>';
            this.syncLabelFilterOptions();
            return;
        }

        this.el.categoryList.innerHTML = this.categories.map((name) => `
            ${this.renderCategoryChip(name)}
        `).join('');

        this.el.categoryList.querySelectorAll('[data-category-delete]').forEach((button) => {
            button.addEventListener('click', async (event) => {
                event.preventDefault();
                event.stopPropagation();
                const targetName = button.getAttribute('data-category-delete') || '';
                await this.removeCategory(targetName);
            });
        });

        this.syncLabelFilterOptions();
    }

    renderCategoryChip(name) {
        const color = this.getCategoryColor(name);
        const textColor = this.getContrastingTextColor(color);
        return `
            <div class="ann-category-chip" style="--category-color:${color}; --category-text:${textColor};">
                <span class="ann-category-name">${this.escapeHtml(name)}</span>
                <button class="ann-cat-remove" data-category-delete="${this.escapeHtml(name)}" type="button" title="删除类别">删除</button>
            </div>
        `;
    }

    async removeCategory(name) {
        const targetName = String(name || '').trim();
        if (!targetName || !this.datasetId) {
            return;
        }

        if (!window.confirm(`确定删除类别「${targetName}」吗？`)) {
            return;
        }

        try {
            const payload = await this.api(
                SeedAI.api.route('DELETE_API_DATASETS_BY_DATASET_ID_LABEL_CATEGORIES', { dataset_id: this.datasetId }),
                {
                    method: 'DELETE',
                    body: JSON.stringify({ name: targetName })
                }
            );

            const categories = payload && payload.data && Array.isArray(payload.data.categories)
                ? payload.data.categories
                : [];

            this.categories = categories;

            if (this.selectedBoxId) {
                const selected = this.boxes.find((item) => item.localId === this.selectedBoxId);
                if (selected && selected.label === targetName) {
                    this.selectedBoxId = null;
                }
            }

            this.renderCategoryList();
            this.renderLabelList();
            this.draw();
        } catch (error) {
            alert(`删除标签失败: ${error.message}`);
        }
    }

    async loadCategoriesFromServer(datasetId) {
        try {
            const payload = await this.api(
                SeedAI.api.route('GET_API_DATASETS_BY_DATASET_ID_LABEL_CATEGORIES', { dataset_id: datasetId })
            );
            const categories = payload && payload.data && Array.isArray(payload.data.categories)
                ? payload.data.categories
                : [];
            return categories;
        } catch (error) {
            return [];
        }
    }

    openAddCategoryModal() {
        this.el.addCategoryInput.value = '';
        this.el.addCategoryModal.style.display = 'flex';
        this.el.addCategoryInput.focus();
    }

    closeAddCategoryModal() {
        this.el.addCategoryModal.style.display = 'none';
    }

    async addCategory() {
        const name = this.el.addCategoryInput.value.trim();
        if (!name) {
            alert('请输入标签名称');
            return;
        }

        if (!this.datasetId) {
            alert('请先选择数据集');
            return;
        }

        try {
            const payload = await this.api(
                SeedAI.api.route('POST_API_DATASETS_BY_DATASET_ID_LABEL_CATEGORIES', { dataset_id: this.datasetId }),
                {
                    method: 'POST',
                    body: JSON.stringify({ name })
                }
            );

            const categories = payload && payload.data && Array.isArray(payload.data.categories)
                ? payload.data.categories
                : [];
            this.categories = categories;
            this.renderCategoryList();
            this.closeAddCategoryModal();
        } catch (error) {
            alert(`新增标签失败: ${error.message}`);
        }
    }

    renderLabelList() {
        const visibleBoxes = this.getFilteredBoxes();
        const editable = this.mode === 'edit';

        const boxRows = visibleBoxes.map((box) => {
            const color = this.getCategoryColor(box.label);
            const textColor = this.getContrastingTextColor(color);
            const selected = this.selectedBoxId === box.localId;
            const checkedAttr = selected ? 'checked' : '';
            const activeClass = selected ? ' active' : '';
            const editableClass = editable ? ' editable' : '';
            return `
            <div class="ann-label-row ann-label-box-row${activeClass}${editableClass}" data-label-box-select="${this.escapeHtml(box.localId)}" style="--category-color:${color}; --category-text:${textColor};">
                <input class="ann-list-checkbox" type="checkbox" ${checkedAttr} ${editable ? '' : 'disabled'}>
                <span class="ann-category-name">${this.escapeHtml(box.label)}</span>
                <button class="ann-cat-remove" data-label-box-delete="${this.escapeHtml(box.localId)}" type="button" title="删除标注">删除</button>
            </div>
        `;
        }).join('');

        const classRows = this.classes.filter((name) => this.matchesFilterCategory(name)).map((name) => {
            const color = this.getCategoryColor(name);
            const textColor = this.getContrastingTextColor(color);
            return `
            <div class="ann-label-row" style="--category-color:${color}; --category-text:${textColor};">
                <span class="ann-category-name">${this.escapeHtml(name)}</span>
                <button class="ann-cat-remove" data-label-class-delete="${this.escapeHtml(name)}" type="button" title="删除分类标签">删除</button>
            </div>
        `;
        }).join('');

        this.el.labelList.innerHTML = boxRows || classRows ? `${boxRows}${classRows}` : '<p>暂无标注</p>';

        this.el.labelList.querySelectorAll('[data-label-box-delete]').forEach((button) => {
            button.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopPropagation();
                const localId = button.getAttribute('data-label-box-delete') || '';
                this.removeBoxByLocalId(localId);
            });
        });

        this.el.labelList.querySelectorAll('[data-label-box-select]').forEach((row) => {
            const checkbox = row.querySelector('.ann-list-checkbox');
            if (checkbox) {
                checkbox.addEventListener('click', (event) => {
                    event.preventDefault();
                    event.stopPropagation();
                });
            }

            row.addEventListener('click', () => {
                if (this.mode !== 'edit') {
                    return;
                }
                this.selectedBoxId = row.getAttribute('data-label-box-select');
                this.renderLabelList();
                this.draw();
            });
        });

        this.el.labelList.querySelectorAll('[data-label-class-delete]').forEach((button) => {
            button.addEventListener('click', (event) => {
                event.preventDefault();
                event.stopPropagation();
                const className = button.getAttribute('data-label-class-delete') || '';
                this.removeClassLabel(className);
            });
        });
    }

    removeBoxByLocalId(localId) {
        const target = String(localId || '').trim();
        if (!target) {
            return;
        }

        this.boxes = this.boxes.filter((box) => box.localId !== target);
        if (this.selectedBoxId === target) {
            this.selectedBoxId = null;
        }

        this.dirty = true;
        this.renderLabelList();
        this.draw();
    }

    removeClassLabel(name) {
        const target = String(name || '').trim();
        if (!target) {
            return;
        }

        this.classes = this.classes.filter((item) => item !== target);
        this.dirty = true;
        this.renderLabelList();
        this.draw();
    }

    syncLabelFilterOptions() {
        const current = this.el.labelFilter.value || 'all';
        const categoryOptions = this.categories.map((name) => `
            <option value="category:${this.escapeHtml(name)}">${this.escapeHtml(name)}</option>
        `).join('');

        this.el.labelFilter.innerHTML = `
            <option value="all">all</option>
            ${categoryOptions}
        `;

        const exists = current === 'all' || this.categories.includes(current.replace(/^category:/, ''));
        this.el.labelFilter.value = exists ? current : 'all';
    }

    getFilterCategoryName() {
        const value = this.el.labelFilter.value || 'all';
        if (!value.startsWith('category:')) {
            return null;
        }
        return value.slice('category:'.length);
    }

    matchesFilterCategory(label) {
        const category = this.getFilterCategoryName();
        if (!category) {
            return true;
        }
        return String(label || '') === category;
    }

    getFilteredBoxes() {
        return this.boxes.filter((box) => this.matchesFilterCategory(box.label));
    }

    handleMouseDown(event) {
        if (!this.images[this.currentIndex]) {
            return;
        }

        if (event.button === 1 || event.button === 2 || (event.button === 0 && this.spacePressed)) {
            this.startPan(event);
            return;
        }

        if (event.button !== 0) {
            return;
        }

        const point = this.getCanvasPoint(event);

        if (this.mode === 'bbox') {
            if (!this.drawingStart) {
                this.drawingStart = point;
                this.mousePoint = point;
                this.draw();
                return;
            }

            const box = this.normalizeBox(this.drawingStart, point);
            this.drawingStart = null;
            this.mousePoint = null;

            if (box.widthNorm < 0.002 || box.heightNorm < 0.002) {
                this.draw();
                return;
            }

            this.pendingBox = box;
            this.openCategoryModal('bbox');
            return;
        }

        if (this.mode === 'edit') {
            if (this.selectedBoxId) {
                const selected = this.boxes.find((item) => item.localId === this.selectedBoxId);
                const handleName = selected ? this.findHandleByPoint(selected, point) : null;
                if (handleName) {
                    this.activeHandle = handleName;
                    this.isDraggingHandle = true;
                    this.draw();
                    return;
                }
            }

            const hit = this.findBoxByPoint(point);
            this.selectedBoxId = hit ? hit.localId : null;
            this.renderLabelList();
            this.draw();
        }
    }

    handleMouseMove(event) {
        if (!this.images[this.currentIndex]) {
            return;
        }

        if (this.isPanning) {
            this.updatePan(event);
            return;
        }

        if (this.mode === 'edit' && this.isDraggingHandle) {
            const point = this.getCanvasPoint(event);
            this.updateSelectedBoxByHandle(point);
            this.draw();
            return;
        }

        if (this.mode === 'bbox') {
            this.mousePoint = this.getCanvasPoint(event);
            this.draw();
        }
    }

    handleMouseLeave() {
        if (this.mode !== 'bbox' || !this.images[this.currentIndex]) {
            return;
        }

        this.mousePoint = null;
        this.draw();
    }

    handleMouseUp(event) {
        if (this.isPanning) {
            this.finishPan(event);
            return;
        }

        if (this.isDraggingHandle) {
            this.isDraggingHandle = false;
            this.activeHandle = null;
            this.renderLabelList();
            this.draw();
        }
    }

    handleContextMenu(event) {
        if (!this.images[this.currentIndex]) {
            return;
        }

        if (this.spacePressed) {
            event.preventDefault();
            return;
        }

        event.preventDefault();

        if (this.panMoved) {
            this.panMoved = false;
            return;
        }

        if (this.mode === 'bbox') {
            this.drawingStart = null;
            this.mousePoint = null;
            this.draw();
            return;
        }

        if (this.mode === 'classify') {
            this.openCategoryModal('classify');
            return;
        }

        if (this.mode === 'edit') {
            const point = this.getCanvasPoint(event);
            const hit = this.findBoxByPoint(point);
            if (!hit) {
                this.hideContextMenu();
                return;
            }
            this.selectedBoxId = hit.localId;
            this.draw();
            this.showContextMenu(event.clientX, event.clientY);
        }
    }

    showContextMenu(x, y) {
        this.el.contextMenu.style.display = 'flex';
        this.el.contextMenu.style.left = `${x}px`;
        this.el.contextMenu.style.top = `${y}px`;
    }

    hideContextMenu() {
        this.el.contextMenu.style.display = 'none';
    }

    startPan(event) {
        event.preventDefault();
        this.isPanning = true;
        this.panMoved = false;
        this.panStartX = event.clientX;
        this.panStartY = event.clientY;
        this.panStartScrollLeft = this.el.canvasWrap.scrollLeft;
        this.panStartScrollTop = this.el.canvasWrap.scrollTop;
        this.el.canvas.style.cursor = 'grabbing';
    }

    updatePan(event) {
        const deltaX = event.clientX - this.panStartX;
        const deltaY = event.clientY - this.panStartY;

        if (Math.abs(deltaX) > 3 || Math.abs(deltaY) > 3) {
            this.panMoved = true;
        }

        // Drag direction follows standard image viewer behavior.
        this.el.canvasWrap.scrollLeft = this.panStartScrollLeft - deltaX;
        this.el.canvasWrap.scrollTop = this.panStartScrollTop - deltaY;
    }

    finishPan(event) {
        const moved = this.panMoved;
        this.isPanning = false;
        this.el.canvas.style.cursor = 'crosshair';

        // Keep right-click context menu behavior when there was no drag.
        if (!moved && event && event.button === 2) {
            return;
        }

        window.setTimeout(() => {
            this.panMoved = false;
        }, 0);
    }

    handleKeyDown(event) {
        if (event.code === 'Space') {
            if (this.isTypingTarget(event.target)) {
                return;
            }
            event.preventDefault();
            this.spacePressed = true;
            this.el.canvas.style.cursor = 'grab';
        }
    }

    handleKeyUp(event) {
        if (event.code === 'Space') {
            if (this.isTypingTarget(event.target)) {
                return;
            }
            this.spacePressed = false;
            if (!this.isPanning) {
                this.el.canvas.style.cursor = 'crosshair';
            }
        }
    }

    isTypingTarget(target) {
        if (!target) {
            return false;
        }
        const tag = (target.tagName || '').toUpperCase();
        return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT' || Boolean(target.isContentEditable);
    }

    deleteSelectedBox() {
        if (!this.selectedBoxId) {
            return;
        }
        this.boxes = this.boxes.filter((box) => box.localId !== this.selectedBoxId);
        this.selectedBoxId = null;
        this.dirty = true;
        this.hideContextMenu();
        this.renderLabelList();
        this.draw();
    }

    openChangeCategoryForSelectedBox() {
        if (!this.selectedBoxId) {
            return;
        }
        this.hideContextMenu();
        this.openCategoryModal('change-box-category');
    }

    openCategoryModal(action) {
        if (!this.categories.length) {
            alert('暂无类别，请先新增标签');
            return;
        }

        this.modalAction = action;
        this.el.categoryModalTitle.textContent = action === 'classify' ? '选择分类类别' : '选择目标框类别';
        this.el.categorySelect.innerHTML = this.categories.map((name) => `<option value="${this.escapeHtml(name)}">${this.escapeHtml(name)}</option>`).join('');
        this.el.categoryModal.style.display = 'flex';
    }

    closeCategoryModal() {
        this.modalAction = null;
        this.pendingBox = null;
        this.el.categoryModal.style.display = 'none';
    }

    applyCategoryModal() {
        const category = this.el.categorySelect.value;
        if (!category) {
            return;
        }

        if (this.modalAction === 'bbox' && this.pendingBox) {
            this.boxes.push({
                localId: `local-${Date.now()}`,
                label: category,
                x_min: this.pendingBox.x_min,
                y_min: this.pendingBox.y_min,
                x_max: this.pendingBox.x_max,
                y_max: this.pendingBox.y_max
            });
            this.dirty = true;
        } else if (this.modalAction === 'classify') {
            if (!this.classes.includes(category)) {
                this.classes.push(category);
                this.dirty = true;
            }
        } else if (this.modalAction === 'change-box-category' && this.selectedBoxId) {
            const box = this.boxes.find((item) => item.localId === this.selectedBoxId);
            if (box) {
                box.label = category;
                this.dirty = true;
            }
        }

        this.closeCategoryModal();
        this.renderLabelList();
        this.draw();
    }

    getCanvasPoint(event) {
        const rect = this.el.canvas.getBoundingClientRect();
        const x = (event.clientX - rect.left) * (this.el.canvas.width / rect.width);
        const y = (event.clientY - rect.top) * (this.el.canvas.height / rect.height);
        return { x, y };
    }

    normalizeBox(start, end) {
        const x1 = Math.min(start.x, end.x);
        const y1 = Math.min(start.y, end.y);
        const x2 = Math.max(start.x, end.x);
        const y2 = Math.max(start.y, end.y);

        return {
            x_min: x1 / this.el.canvas.width,
            y_min: y1 / this.el.canvas.height,
            x_max: x2 / this.el.canvas.width,
            y_max: y2 / this.el.canvas.height,
            widthNorm: (x2 - x1) / this.el.canvas.width,
            heightNorm: (y2 - y1) / this.el.canvas.height
        };
    }

    findBoxByPoint(point) {
        return this.boxes.find((box) => {
            const x1 = box.x_min * this.el.canvas.width;
            const y1 = box.y_min * this.el.canvas.height;
            const x2 = box.x_max * this.el.canvas.width;
            const y2 = box.y_max * this.el.canvas.height;
            return point.x >= x1 && point.x <= x2 && point.y >= y1 && point.y <= y2;
        });
    }

    findHandleByPoint(box, point) {
        const x1 = box.x_min * this.el.canvas.width;
        const y1 = box.y_min * this.el.canvas.height;
        const x2 = box.x_max * this.el.canvas.width;
        const y2 = box.y_max * this.el.canvas.height;
        const handles = {
            tl: { x: x1, y: y1 },
            tr: { x: x2, y: y1 },
            bl: { x: x1, y: y2 },
            br: { x: x2, y: y2 }
        };

        const r = this.handleHitSize;
        for (const [name, p] of Object.entries(handles)) {
            if (Math.abs(point.x - p.x) <= r && Math.abs(point.y - p.y) <= r) {
                return name;
            }
        }
        return null;
    }

    updateSelectedBoxByHandle(point) {
        if (!this.selectedBoxId || !this.activeHandle) {
            return;
        }

        const box = this.boxes.find((item) => item.localId === this.selectedBoxId);
        if (!box) {
            return;
        }

        const w = Math.max(1, this.el.canvas.width);
        const h = Math.max(1, this.el.canvas.height);
        const minDx = 2 / w;
        const minDy = 2 / h;

        const nx = Math.max(0, Math.min(1, point.x / w));
        const ny = Math.max(0, Math.min(1, point.y / h));

        if (this.activeHandle === 'tl') {
            box.x_min = Math.min(nx, box.x_max - minDx);
            box.y_min = Math.min(ny, box.y_max - minDy);
        } else if (this.activeHandle === 'tr') {
            box.x_max = Math.max(nx, box.x_min + minDx);
            box.y_min = Math.min(ny, box.y_max - minDy);
        } else if (this.activeHandle === 'bl') {
            box.x_min = Math.min(nx, box.x_max - minDx);
            box.y_max = Math.max(ny, box.y_min + minDy);
        } else if (this.activeHandle === 'br') {
            box.x_max = Math.max(nx, box.x_min + minDx);
            box.y_max = Math.max(ny, box.y_min + minDy);
        }

        box.x_min = Math.max(0, Math.min(1, box.x_min));
        box.y_min = Math.max(0, Math.min(1, box.y_min));
        box.x_max = Math.max(0, Math.min(1, box.x_max));
        box.y_max = Math.max(0, Math.min(1, box.y_max));
        this.dirty = true;
    }

    draw() {
        this.ctx.clearRect(0, 0, this.el.canvas.width, this.el.canvas.height);

        const visibleBoxes = this.getFilteredBoxes();

        if (this.selectedBoxId && !visibleBoxes.some((box) => box.localId === this.selectedBoxId)) {
            this.selectedBoxId = null;
        }

        visibleBoxes.forEach((box) => {
            const x = box.x_min * this.el.canvas.width;
            const y = box.y_min * this.el.canvas.height;
            const w = (box.x_max - box.x_min) * this.el.canvas.width;
            const h = (box.y_max - box.y_min) * this.el.canvas.height;
            const color = this.getCategoryColor(box.label);

            const selected = this.selectedBoxId === box.localId;
            this.ctx.lineWidth = selected ? this.boxStrokeWidth * 2 : this.boxStrokeWidth;
            this.ctx.strokeStyle = color;
            this.ctx.strokeRect(x, y, w, h);

            if (selected && this.mode === 'edit') {
                const hs = 6;
                const handles = [
                    { x, y },
                    { x: x + w, y },
                    { x, y: y + h },
                    { x: x + w, y: y + h }
                ];
                this.ctx.fillStyle = '#ffffff';
                this.ctx.strokeStyle = '#ef4444';
                this.ctx.lineWidth = 2;
                handles.forEach((p) => {
                    this.ctx.fillRect(p.x - hs, p.y - hs, hs * 2, hs * 2);
                    this.ctx.strokeRect(p.x - hs, p.y - hs, hs * 2, hs * 2);
                });
            }

            this.ctx.fillStyle = color;
            const labelFontSize = 30;
            const labelPaddingX = 10;
            const labelPaddingBottom = 10;
            this.ctx.font = `${labelFontSize}px sans-serif`;
            this.ctx.textBaseline = 'top';
            const label = box.label;
            const labelWidth = this.ctx.measureText(label).width + (labelPaddingX * 2);
            const labelHeight = labelFontSize + labelPaddingBottom;
            const labelTop = Math.max(0, y - labelHeight);
            this.ctx.fillRect(x, labelTop, labelWidth, labelHeight);
            this.ctx.fillStyle = '#ffffff';
            this.ctx.fillText(label, x + labelPaddingX, labelTop);
        });

        if (this.mode === 'bbox' && this.mousePoint) {
            this.ctx.save();
            this.ctx.lineWidth = this.previewStrokeWidth;
            this.ctx.strokeStyle = this.previewStrokeColor;
            this.ctx.beginPath();
            this.ctx.moveTo(this.mousePoint.x, 0);
            this.ctx.lineTo(this.mousePoint.x, this.el.canvas.height);
            this.ctx.moveTo(0, this.mousePoint.y);
            this.ctx.lineTo(this.el.canvas.width, this.mousePoint.y);
            this.ctx.stroke();
            this.ctx.restore();
        }

        if (this.mode === 'bbox' && this.drawingStart && this.mousePoint) {
            const x = Math.min(this.drawingStart.x, this.mousePoint.x);
            const y = Math.min(this.drawingStart.y, this.mousePoint.y);
            const w = Math.abs(this.mousePoint.x - this.drawingStart.x);
            const h = Math.abs(this.mousePoint.y - this.drawingStart.y);

            this.ctx.setLineDash([6, 4]);
            this.ctx.lineWidth = this.previewStrokeWidth;
            this.ctx.strokeStyle = this.previewStrokeColor;
            this.ctx.strokeRect(x, y, w, h);
            this.ctx.setLineDash([]);
        }
    }

    getCategoryColor(name) {
        const normalized = String(name || '').trim().toLowerCase();
        if (!normalized) {
            return '#64748b';
        }

        let hash = 0;
        for (let i = 0; i < normalized.length; i += 1) {
            hash = ((hash << 5) - hash) + normalized.charCodeAt(i);
            hash |= 0;
        }

        const index = Math.abs(hash) % this.categoryColorPalette.length;
        return this.categoryColorPalette[index];
    }

    getContrastingTextColor(hexColor) {
        const hex = String(hexColor || '').replace('#', '');
        if (hex.length !== 6) {
            return '#ffffff';
        }
        const r = parseInt(hex.slice(0, 2), 16);
        const g = parseInt(hex.slice(2, 4), 16);
        const b = parseInt(hex.slice(4, 6), 16);
        const luminance = (0.299 * r) + (0.587 * g) + (0.114 * b);
        return luminance > 160 ? '#111827' : '#ffffff';
    }

    changeZoom(value) {
        this.zoom = Math.max(0.2, Math.min(4, value));
        this.applyZoom();
    }

    fitZoom() {
        if (!this.el.image.naturalWidth || !this.el.image.naturalHeight) {
            this.changeZoom(1);
            return;
        }
        const wrap = this.el.canvasWrap.getBoundingClientRect();
        const ratioX = wrap.width / this.el.image.naturalWidth;
        const ratioY = wrap.height / this.el.image.naturalHeight;
        this.zoom = Math.max(0.2, Math.min(1, Math.min(ratioX, ratioY)));
        this.applyZoom();
    }

    applyZoom() {
        this.el.zoomText.textContent = `${Math.round(this.zoom * 100)}%`;
        this.el.image.style.transformOrigin = 'top left';
        this.el.canvas.style.transformOrigin = 'top left';
        this.el.image.style.transform = `scale(${this.zoom})`;
        this.el.canvas.style.transform = `scale(${this.zoom})`;

        this.updateCanvasCentering();
    }

    updateCanvasCentering() {
        const wrapWidth = this.el.canvasWrap.clientWidth;
        const wrapHeight = this.el.canvasWrap.clientHeight;
        const scaledWidth = this.el.canvas.width * this.zoom;
        const scaledHeight = this.el.canvas.height * this.zoom;

        const left = scaledWidth < wrapWidth ? (wrapWidth - scaledWidth) / 2 : 0;
        const top = scaledHeight < wrapHeight ? (wrapHeight - scaledHeight) / 2 : 0;

        this.el.image.style.left = `${Math.max(0, left)}px`;
        this.el.canvas.style.left = `${Math.max(0, left)}px`;
        this.el.image.style.top = `${Math.max(0, top)}px`;
        this.el.canvas.style.top = `${Math.max(0, top)}px`;
    }

    async saveCurrentImage() {
        const image = this.images[this.currentIndex];
        if (!image) {
            return;
        }

        // Do not send requests when the current image has no local changes.
        if (!this.dirty) {
            return;
        }

        try {
            // Overwrite server-side annotations with current canvas state in one request.
            const nextAnnotations = this.boxes.map((box) => ({
                label: box.label,
                x_min: box.x_min,
                y_min: box.y_min,
                x_max: box.x_max,
                y_max: box.y_max,
                confidence: 1
            }));

            // Persist normalized annotations to DB table first.
            await this.api(`/images/${image.id}/annotations`, {
                method: 'PUT',
                body: JSON.stringify({ annotations: nextAnnotations })
            });

            // Persist category labels and bbox annotations to a dataset COCO file.
            this.writeJson(this.getImageClassKey(image.id), this.classes);
            await this.api(`/images/${image.id}/label-file`, {
                method: 'POST',
                body: JSON.stringify({
                    annotations: nextAnnotations,
                    classes: this.classes
                })
            });

            this.dirty = false;
            this.updateStatusText();
        } catch (error) {
            alert(`保存失败: ${error.message}`);
        }
    }

    getDatasetCategoryKey() {
        return `seedai.dataset.categories.${this.datasetId}`;
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

    formatCoord(value) {
        const n = Number(value);
        if (Number.isNaN(n)) {
            return '0';
        }
        return n.toFixed(4).replace(/\.0+$/, '').replace(/(\.\d*?[1-9])0+$/, '$1');
    }

    writeJson(key, value) {
        localStorage.setItem(key, JSON.stringify(value));
    }

    escapeHtml(value) {
        const div = document.createElement('div');
        div.textContent = value || '';
        return div.innerHTML;
    }
}

window.addEventListener('DOMContentLoaded', () => {
    window.manualAnnotationPage = new ManualAnnotationPage();
});
