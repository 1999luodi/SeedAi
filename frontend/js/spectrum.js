// 光谱分析应用类
class SpectrumApp {
    constructor() {
        this.currentImage = null;
        this.analysisData = null;
        this.init();
    }

    init() {
        this.checkAuth();
        this.bindEvents();
    }

    checkAuth() {
        const token = localStorage.getItem('token');
        if (!token) {
            window.location.href = 'login.html';
        }
    }

    bindEvents() {
        // 上传区域
        const uploadArea = document.getElementById('spectrumUploadArea');
        const fileInput = document.getElementById('spectrumImageInput');

        uploadArea.addEventListener('click', () => fileInput.click());

        fileInput.addEventListener('change', (e) => {
            this.handleImageUpload(e.target.files[0]);
        });

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
            this.handleImageUpload(e.dataTransfer.files[0]);
        });

        // 分析按钮
        document.getElementById('analyzeBtn').addEventListener('click', () => this.analyzeImage());

        // 保存按钮
        document.getElementById('downloadBtn').addEventListener('click', () => this.downloadResults());
    }

    handleImageUpload(file) {
        if (!file) return;

        // 验证文件类型
        if (!file.type.startsWith('image/')) {
            alert('请选择图片文件');
            return;
        }

        // 读取文件
        const reader = new FileReader();
        reader.onload = (e) => {
            this.currentImage = {
                file: file,
                data: e.target.result
            };

            // 显示图片
            const img = document.getElementById('spectrumImage');
            img.src = e.target.result;
            img.style.display = 'block';

            // 隐藏占位符
            document.querySelector('.image-placeholder').style.display = 'none';

            // 启用分析按钮
            document.getElementById('analyzeBtn').disabled = false;
        };

        reader.readAsDataURL(file);
    }

    async analyzeImage() {
        if (!this.currentImage) {
            alert('请先上传图片');
            return;
        }

        const analyzeBtn = document.getElementById('analyzeBtn');
        analyzeBtn.disabled = true;
        analyzeBtn.innerHTML = '<span class="spinner"></span> 分析中...';

        try {
            // 模拟光谱分析
            // 实际应该调用后端API进行分析
            const mockData = this.generateMockSpectrumData();

            // 等待1秒来模拟分析时间
            await new Promise(resolve => setTimeout(resolve, 1000));

            this.analysisData = mockData;
            this.displayResults(mockData);
            this.displayChart(mockData);

            // 启用保存按钮
            document.getElementById('downloadBtn').disabled = false;
        } catch (error) {
            console.error('分析失败:', error);
            alert('分析失败: ' + error.message);
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.innerHTML = '<span class="btn-icon">⚙️</span> 分析光谱';
        }
    }

    generateMockSpectrumData() {
        // 生成模拟光谱数据
        const wavelengths = [];
        const intensity = [];

        for (let i = 400; i <= 700; i += 5) {
            wavelengths.push(i);
            // 生成类似高斯分布的光谱强度
            const center = 550;
            const sigma = 100;
            const value = 100 * Math.exp(-Math.pow((i - center) / sigma, 2)) + Math.random() * 5;
            intensity.push(Math.max(0, Math.min(100, value)));
        }

        return {
            wavelengths: wavelengths,
            intensity: intensity,
            avgIntensity: intensity.reduce((a, b) => a + b) / intensity.length,
            vigorRating: '优',
            recommendIndex: 0.85,
            confidence: 0.92
        };
    }

    displayResults(data) {
        const resultsDiv = document.getElementById('analysisResults');
        const detailsDiv = document.getElementById('analysisDetails');

        // 更新详细信息
        document.getElementById('avgSpectrum').textContent = data.avgIntensity.toFixed(2);
        document.getElementById('vigorRating').textContent = data.vigorRating;
        document.getElementById('recommendIndex').textContent = (data.recommendIndex * 100).toFixed(1) + '%';
        document.getElementById('confidence').textContent = (data.confidence * 100).toFixed(1) + '%';

        detailsDiv.style.display = 'block';

        resultsDiv.innerHTML = `
            <div class="result-summary">
                <div class="result-item">
                    <span class="result-label">种子活力评级:</span>
                    <span class="result-value ${data.vigorRating === '优' ? 'excellent' : 'good'}">${data.vigorRating}</span>
                </div>
                <div class="result-item">
                    <span class="result-label">推荐指数:</span>
                    <span class="result-value">${(data.recommendIndex * 100).toFixed(1)}%</span>
                </div>
                <div class="result-item">
                    <span class="result-label">置信度:</span>
                    <span class="result-value">${(data.confidence * 100).toFixed(1)}%</span>
                </div>
            </div>
        `;
    }

    displayChart(data) {
        const chartContainer = document.getElementById('chartContainer');
        const canvas = document.getElementById('spectrumChart');

        if (!canvas) return;

        chartContainer.style.display = 'block';

        // 使用简单的Canvas绘制光谱曲线
        const ctx = canvas.getContext('2d');
        const width = canvas.width = chartContainer.offsetWidth - 40;
        const height = canvas.height = 300;

        ctx.fillStyle = 'white';
        ctx.fillRect(0, 0, width, height);

        // 绘制网格
        ctx.strokeStyle = '#e2e8f0';
        ctx.lineWidth = 1;

        for (let i = 0; i <= 10; i++) {
            const y = (height / 10) * i;
            ctx.beginPath();
            ctx.moveTo(50, y);
            ctx.lineTo(width, y);
            ctx.stroke();
        }

        // 绘制光谱曲线
        ctx.strokeStyle = '#2563eb';
        ctx.lineWidth = 2;
        ctx.beginPath();

        const pointWidth = (width - 100) / (data.wavelengths.length - 1);
        const maxIntensity = Math.max(...data.intensity);

        for (let i = 0; i < data.wavelengths.length; i++) {
            const x = 50 + pointWidth * i;
            const y = height - 30 - (data.intensity[i] / maxIntensity) * (height - 80);

            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }

        ctx.stroke();

        // 绘制坐标轴标签
        ctx.fillStyle = '#64748b';
        ctx.font = '12px Arial';
        ctx.textAlign = 'center';

        // X轴标签（波长）
        for (let i = 0; i < data.wavelengths.length; i += Math.floor(data.wavelengths.length / 5)) {
            const x = 50 + pointWidth * i;
            ctx.fillText(data.wavelengths[i], x, height - 5);
        }

        // Y轴标签
        ctx.textAlign = 'right';
        for (let i = 0; i <= 100; i += 25) {
            const y = height - 30 - (i / 100) * (height - 80);
            ctx.fillText(i, 45, y + 4);
        }
    }

    downloadResults() {
        if (!this.analysisData) return;

        // 生成CSV内容
        let csvContent = '波长(nm),强度\n';
        for (let i = 0; i < this.analysisData.wavelengths.length; i++) {
            csvContent += `${this.analysisData.wavelengths[i]},${this.analysisData.intensity[i].toFixed(2)}\n`;
        }

        // 创建下载链接
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `spectrum_${new Date().getTime()}.csv`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new SpectrumApp();
});
