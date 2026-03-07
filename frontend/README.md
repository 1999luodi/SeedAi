# 前端文档

本文档详细介绍SeedAI前端的页面功能、设计架构、API集成和开发指南。

## 📑 目录

- [前端页面详解](#前端页面详解)
- [功能特性](#功能特性)
- [技术架构](#技术架构)
- [API集成说明](#api集成说明)
- [开发指南](#开发指南)
- [部署配置](#部署配置)
- [常见问题](#常见问题)

---

## 前端页面详解

### 1. 首页 (index.html) - 系统欢迎页面

#### 页面功能
- 📱 **导航菜单**: 包含光谱分析、发芽检测、数据集管理、登录/注册
  - 未登录用户点击受保护功能时自动跳转登录页面
  - 登录成功后自动跳转到首页，登录注册的按钮更改为个人用户
- 🌍 **欢迎横幅**: 展示平台名称和宗旨（基于计算机视觉的种子活力研究平台）
- 📊 **统计数据**: 实时显示已检测图片数、数据集数、活跃用户数
- 🎯 **核心功能介绍**: 
  - 发芽检测：基于YOLOv5的实时目标检测
  - 光谱分析：获取种子光谱信息，分析种子活力
  - 数据集管理：组织和管理图片数据
  - 个人用户：查看自己的账号邮箱和密码
- 📸 **检测示例**: 展示种子发芽的不同阶段示例
- 📰 **最新资讯**: 显示国内外种子活力研究的最新资讯

#### 设计说明
- 响应式导航条，支持移动端菜单折叠
- 导航链接集成登录检查，未认证用户点击受保护功能时自动跳转
- 统计数据从 `/api/stats` 实时获取
- 样本和新闻区域采用响应式网格布局，自适应屏幕宽度

#### 关键文件
- **HTML**: `index.html`
- **JavaScript**: `js/main.js`
- **样式**: 由 `style.css` 中的 `.page-header`, `.hero-section`, `.samples-grid`, `.news-grid` 类管理

---

### 2. 登录/注册页面 (login.html) - 用户认证

#### 页面功能
- 🔐 **用户登录**：
  - 用户名或邮箱登录
  - 密码可见性切换
  - 记住我功能（预留）
  - 忘记密码链接（预留）
- ✍️ **用户注册**：
  - 用户名（3-20字符）
  - 邮箱地址（正则验证）
  - 密码设置（至少6位）
  - 密码确认（匹配验证）
  - 表单验证和错误提示
- 🔄 **表单切换**：登录和注册使用同一页面，通过顶部链接切换
- 💾 **令牌管理**：
  - 登录成功后存储JWT令牌到LocalStorage
  - 支持自动登录（页面刷新时检查token）
- 🎨 **侧边栏**：展示平台的三个核心功能设简介

#### 设计说明
- **表单切换机制**：
  ```javascript
  switchForm(formType) // 切换显示的表单，更新表单标题
  ```
- **独立密码可见性切换**：支持3个不同的密码字段分别控制显示/隐藏
- **验证规则**：
  - 邮箱: `/^[^\s@]+@[^\s@]+\.[^\s@]+$/`
  - 密码: 至少6个字符
  - 用户名: 3-20个字符
- **成功登录**：将JWT token存储到localStorage，页面自动重定向到前一页

#### 关键代码
```javascript
// 登录处理
async function handleLogin() {
    const username_or_email = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    
    const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username_or_email, password })
    });
    
    const data = await response.json();
    localStorage.setItem('token', data.token); // 保存token
    window.location.href = document.referrer || 'index.html';
}
```

---

### 3. AI检测结果页面 (detection.html) - 模型检测结果展示 发芽检测

#### 页面功能
展示YOLOv5模型自动生成的检测结果，用户可以查看模型检测到的目标框和置信度

**数据格式要求：RGB图像 (.jpg, .png)** - 此页面专门处理RGB彩色图像，用于YOLOv5目标检测

#### 页面布局：左右分割设计（350px左 | 1fr右）

##### 左侧操作面板 (350px宽)
- 📊 **检测结果列表**：
  - 显示所有检测到的目标框
  - 每项显示：
    - 类别标签
    - 边界框坐标（x_min, y_min, x_max, y_max）
    - 模型置信度百分比
  - 点击可选中对应目标框
  
- 👀 **检测框过滤**（可选）：
  - 按置信度过滤
  - 按类别过滤
  
- 📥 **导出功能**：
  - 导出检测结果为JSON/CSV

- 📈 **统计信息**：
  - 检测目标总数
  - 平均置信度
  - 检测结果占比分析

- ⬅️➡️ **检测**：
  - 一次上传一张，只有单独图片一张检测
##### 右侧可视化区域
- 🖼️ **图片显示器**（500px高）：
  - 显示原始图片
  - Canvas层叠加绘制YOLOv5的检测框
  
- 📍 **检测框标注层**：
  - 实时显示检测框（矩形轮廓）
  - 显示类别标签和置信度分数
  - 高亮选中的目标框
  


#### 核心功能
- 👁️ **模型结果展示**：清晰展示YOLOv5检测框和置信度
- 🔍 **交互检查**：点击目标框查看详细信息
- 📤 **结果导出**：支持导出检测结果供后续使用
- 💾 **保存标注**：将AI检测结果保存到数据库
- 🎯 **原始数据保留**：不修改模型结果，仅作展示用途

#### 关键代码示例
```javascript
// 加载并显示检测结果
async function loadDetectionResults(imageId) {
    const response = await fetch(`/api/images/${imageId}/annotations`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    });
    
    const annotations = await response.json();
    displayDetectionBoxes(annotations); // 在canvas上绘制检测框
}

// Canvas绘制检测框
function drawDetectionBoxes(canvas, annotations) {
    const ctx = canvas.getContext('2d');
    annotations.forEach(ann => {
        const x = ann.x_min * canvas.width;
        const y = ann.y_min * canvas.height;
        const width = (ann.x_max - ann.x_min) * canvas.width;
        const height = (ann.y_max - ann.y_min) * canvas.height;
        
        // 绘制边框
        ctx.strokeStyle = '#ff6b6b';
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, width, height);
        
        // 显示标签和置信度
        ctx.fillStyle = '#ff6b6b';
        ctx.font = '12px Arial';
        ctx.fillText(`${ann.label} (${(ann.confidence * 100).toFixed(1)}%)`, x, y - 5);
    });
}
```

---

### 4. 手工标注页面 (annotate.html) - 数据集图片标注工具

#### 页面功能
提供手工标注工具，允许用户在数据集的图片上创建、编辑和删除标注框

**数据格式要求：RGB图像 (.jpg, .png)** - 此页面专门处理RGB彩色图像，支持交互式标注

#### 页面布局：左右分割设计（350px左 | 1fr右）

##### 左侧操作面板 (350px宽)
- 📤 **数据集选择**：
  - 下拉菜单选择待标注的数据集
  - 显示数据集中的图片列表
  
- 📋 **标注列表**：
  - 显示当前图片的所有标注框
  - 支持点击选中、编辑、删除
  - 显示标注进度（已标注/总数）
  
- ✏️ **标注编辑面板**：
  - 标注类别选择下拉菜单
  - 边界框坐标输入（x_min, y_min, x_max, y_max）
  - 手动输入或边界框工具自动获取
  
- 💾 **操作按钮**：
  - 新建标注
  - 保存修改
  - 删除标注
  - 批量操作（预留）

##### 右侧可视化区域
- 🖼️ **图片编辑器**（500px高）：
  - 显示原始图片
  - 支持拖拽绘制标注框
  - 支持调整已有标注框的大小和位置
  
- 📍 **交互式标注层**：
  - 点击拖拽绘制新的标注框
  - 双击已有标注框进行编辑
  - 右键菜单删除标注框
  - 实时显示鼠标坐标和框大小
  
- ⬅️➡️ **导航和保存**：
  - 保存当前图片标注
  - 上一张/下一张按钮
  - 图片计数器显示（当前/总数）

#### 核心功能
- 🖱️ **交互式绘制**：在图片上直接拖拽绘制标注框
- ✏️ **灵活编辑**：支持修改、删除和调整标注
- 💾 **实时保存**：标注变化即时保存到数据库
- 📊 **进度跟踪**：显示标注完成进度
- 🏷️ **类别管理**：支持自定义标注类别

#### 关键代码示例
```
// 交互式绘制标注框
let isDrawing = false;
let startX, startY;

canvas.addEventListener('mousedown', (e) => {
    isDrawing = true;
    [startX, startY] = getMouseCoords(e);
});

canvas.addEventListener('mousemove', (e) => {
    if (!isDrawing) return;
    
    const [currentX, currentY] = getMouseCoords(e);
    redrawCanvas(); // 清除并重绘
    
    // 绘制预览框
    ctx.strokeStyle = '#4CAF50';
    ctx.lineWidth = 2;
    ctx.strokeRect(startX, startY, currentX - startX, currentY - startY);
});

canvas.addEventListener('mouseup', (e) => {
    isDrawing = false;
    const [endX, endY] = getMouseCoords(e);
    
    // 创建标注
    const annotation = {
        label: document.getElementById('labelSelect').value,
        x_min: Math.min(startX, endX) / canvas.width,
        y_min: Math.min(startY, endY) / canvas.height,
        x_max: Math.max(startX, endX) / canvas.width,
        y_max: Math.max(startY, endY) / canvas.height
    };
    
    createAnnotation(annotation);
});

// 保存标注到数据库
async function createAnnotation(annotation) {
    const response = await fetch(`/api/images/${currentImageId}/annotations`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(annotation)
    });
    
    const result = await response.json();
    annotations.push(result);
    redrawCanvas();
}

// 删除标注
async function deleteAnnotation(annotationId) {
    await fetch(`/api/annotations/${annotationId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
    });
    
    annotations = annotations.filter(a => a.id !== annotationId);
    redrawCanvas();
}
```

#### 样式关键类
- `.annotate-workspace`: 主容器，CSS Grid布局
- `.annotate-panel`: 左侧操作面板
- `.annotation-editor`: 标注编辑区域
- `.image-editor`: 右侧可编辑的图片容器
- `.canvas-layer`: 标注框绘制层
- `.annotation-item`: 标注列表项

---

### 5. 光谱分析页面 (spectrum.html) - 光谱信息分析工具

#### 页面功能
基于MATLAB数据文件(.mat)进行种子光谱分析，计算并可视化种子活力等级

#### 页面布局：左右分割设计（350px左 | 1fr右）

##### 左侧操作面板 (350px宽)
- 📁 **数据上传区域**：
  - 支持MATLAB数据文件(.mat)
  - 拖拽或点击上传
  - 显示上传状态和文件信息

- 📋 **分析结果区域**：
  - 显示光谱分析的结果摘要
  - 关键指标：平均光谱值、活力等级、推荐指数

- 💾 **操作按钮**：
  - 分析光谱：触发光谱分析算法
  - 保存结果：将分析结果导出为CSV

##### 右侧可视化区域
- 📊 **光谱数据展示**：
  - 显示.mat文件中的光谱数据信息
  - 显示数据基本信息（波长范围、数据点数等）

- 📈 **光谱曲线图表**：
  - Canvas绘制的光谱强度曲线
  - X轴：波长（nm，400-700范围）
  - Y轴：光谱强度（相对值）
  - 实时绘制坐标轴网格和曲线
  - 显示平均光谱值指示线

- 📊 **详细分析信息**：
  - 平均光谱值（数值）
  - 种子活力评级（优/良/一般）
  - 推荐指数（百分比）
  - 分析置信度（百分比）

#### 核心功能
- 🔬 **光谱分析**：计算并显示种子光谱信息
- 📉 **数据可视化**：生成光谱曲线图表
- 📥 **结果导出**：支持下载分析结果为CSV格式
- 🎯 **活力评估**：基于光谱数据评估种子活力等级

#### 关键代码
```
// 生成模拟光谱数据
function generateMockSpectrumData() {
    const wavelengths = []; // 400-700nm
    const intensities = [];
    
    for (let i = 400; i <= 700; i += 10) {
        wavelengths.push(i);
        // 高斯分布模拟光谱强度
        const intensity = 100 * Math.exp(-((i - 550) ** 2) / 10000);
        intensities.push(intensity);
    }
    
    return {
        wavelengths,
        intensities,
        avgIntensity: intensities.reduce((a, b) => a + b) / intensities.length,
        vigorRating: '优', // 根据数据计算
        recommendIndex: 0.85,
        confidence: 0.92
    };
}

// Canvas绘制光谱曲线
function drawSpectralCurve(canvas, data) {
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // 绘制网格
    ctx.strokeStyle = '#e0e0e0';
    ctx.beginPath();
    for (let i = 0; i <= 10; i++) {
        const x = (width / 10) * i;
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
    }
    ctx.stroke();
    
    // 绘制曲线
    ctx.strokeStyle = '#2196F3';
    ctx.lineWidth = 2;
    ctx.beginPath();
    data.wavelengths.forEach((w, i) => {
        const x = ((w - 400) / 300) * width;
        const y = height - ((data.intensities[i] / 100) * height);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
    });
    ctx.stroke();
}

// 导出为CSV
function downloadResults(data) {
    const csv = `波长(nm),光谱强度\n${data.wavelengths.map((w, i) => `${w},${data.intensities[i]}`).join('\n')}`;
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'spectrum_results.csv';
    a.click();
}
```

#### 样式关键类
- `.spectrum-workspace`: 主容器，CSS Grid布局
- `.spectrum-panel`: 左侧操作面板
- `.spectrum-section`: 面板内的区域分隔
- `.chart-container`: 图表容器
- `.analysis-details`: 分析结果网格

---

### 6. 数据集管理页面 (dataset.html) - 数据集和图片管理系统

#### 页面功能
- 📂 **数据集列表**：
  - 网格或列表展示所有用户创建的数据集
  - 每个数据集卡片显示：
    - 数据集名称
    - 描述信息
    - 包含的图片数
    - 创建时间
    - 公开/私有状态

- 🔧 **数据集管理功能**：
  - ➕ **创建数据集**：新建数据集容器
  - 📁 **导入数据集**：上传现有数据集
  - 🔍 **搜索功能**：按名称搜索数据集
  - 📊 **排序功能**：
    - 最新创建
    - 最早创建
    - 按名称排序
    - 按大小排序

- 🎯 **数据集操作按钮**（对应每个数据集）：
  - 📤 **上传图片**：添加新图片到数据集（支持混合格式）
  - 🔍 **检查**：查看AI检测结果 (跳转到 detection.html) - **需要RGB图像 (jpg, png)**
  - ✏️ **标注**：手工标注图片 (跳转到 annotate.html) - **需要RGB图像 (jpg, png)**
  - 🧪 **分析**：进行光谱分析 (跳转到 spectrum.html) - **需要MATLAB数据 (.mat)**
  - 🗑️ **删除**：删除整个数据集

- 📋 **图片管理**（展开数据集后）：
  - 图片列表显示（根据操作类型显示相应格式的文件）
  - 图片缩略图预览（RGB图像）
  - 删除单个图片

#### 核心功能
- 📁 **数据组织**：创建和管理多个数据集容器
- 📤 **文件上传**：支持单个或批量上传图片到数据集（混合格式支持）
- 🌉 **功能桥梁**：数据集是连接到三个工具（检测、标注、光谱分析）的入口
- 📊 **统计信息**：显示数据集大小和图片数量
- 🔄 **快速操作**：一键跳转到相关的分析工具
- ⚠️ **格式验证**：根据选择的分析工具自动验证数据格式

#### 数据格式要求
| 操作类型 | 支持的文件格式 | 说明 |
|----------|----------------|------|
| **AI检测** | `.jpg`, `.png` | RGB彩色图像，用于YOLOv5目标检测 |
| **手工标注** | `.jpg`, `.png` | RGB彩色图像，支持交互式标注 |
| **光谱分析** | `.mat` | MATLAB数据文件，包含光谱信息 |

#### 工作流程集成
```
数据集管理 (dataset.html)
├─ 创建数据集 + 上传图片（混合格式）
├─ 点击"检查" → 跳转 detection.html (查看AI结果) - RGB图像
├─ 点击"标注" → 跳转 annotate.html (手工标注) - RGB图像
├─ 点击"标注" → 跳转 annotate.html (手工标注)
└─ 点击"分析" → 跳转 spectrum.html (光谱分析)
```

---

## 功能特性

### 🎨 用户界面
| 特性 | 说明 |
|------|------|
| **响应式设计** | 支持桌面和移动设备 |
| **现代化UI** | 简洁美观的用户界面，采用渐变色和卡片设计 |
| **导航系统** | 统一的顶部导航栏，支持页面间快速切换 |
| **状态反馈** | 实时的操作反馈和加载提示 |
| **左右布局** | AI检测、手工标注和光谱分析页面采用左操作右展示的布局 |

### 🔐 认证管理
| 特性 | 说明 |
|------|------|
| **JWT令牌** | 本地存储和管理用户认证令牌 |
| **自动登录** | 页面刷新保持登录状态（基于LocalStorage） |
| **权限控制** | 基于令牌的API访问，未登录用户自动跳转登录页 |
| **表单验证** | 客户端表单验证和服务端验证 |
| **登出功能** | 页面导航链接支持一键登出 |

### 📁 文件管理
| 特性 | 说明 |
|------|------|
| **拖拽上传** | 支持文件拖拽上传到指定区域 |
| **点击上传** | 点击区域打开文件选择器 |
| **格式验证** | 图片文件类型检查（JPG、PNG等） |
| **进度显示** | 上传进度实时反馈 |
| **多格式支持** | 支持多种图片格式 |

### 🎯 检测和分析工具
| 特性 | 说明 |
|------|------|
| **AI自动检测** | 一键触发YOLOv5模型进行目标检测 |
| **光谱分析** | 计算并可视化种子光谱信息 |
| **实时标注** | 在图片上实时显示检测框和标签 |
| **手动编辑** | 支持修改、删除和调整标注信息 |
| **数据导出** | 支持将分析结果导出为CSV格式 |

### 📊 数据管理
| 特性 | 说明 |
|------|------|
| **数据集组织** | 创建和管理多个数据集容器 |
| **图片列表** | 显示数据集内的所有图片和标注信息 |
| **搜索和排序** | 支持按名称搜索和多种排序方式 |
| **标注统计** | 显示标注完成率和进度 |
| **批量操作** | 支持批量上传、下载等操作（预留） |

### 🏷️ 标注工具
| 特性 | 说明 |
|------|------|
| **可视化标注** | 图片上清晰显示检测框和标签 |
| **标签管理** | 添加/删除/修改标注标签 |
| **统计信息** | 显示标注数量和完成情况 |
| **导航控制** | 上一张/下一张图片切换 |
| **图片预览** | 详细的图片信息和标注信息显示 |

---

## 技术架构

### 文件结构
```
frontend/
├── README.md               # 本文档
├── index.html              # 首页
├── login.html              # 登录/注册页面
├── dataset.html            # 数据集管理页面
├── detection.html          # AI检测结果展示页面 (模型生成的检测框)
├── annotate.html           # 手工标注页面 (手动标注图片)
├── spectrum.html           # 光谱分析页面
├── style.css               # 全局样式表
└── js/                     # JavaScript模块
    ├── main.js             # 首页逻辑和导航控制
    ├── login.js            # 登录/注册逻辑
    ├── dataset.js          # 数据集管理逻辑
    ├── detection.js        # AI检测结果展示逻辑
    ├── annotate.js         # 手工标注工具逻辑
    └── spectrum.js         # 光谱分析工具逻辑
```

### 技术栈
| 技术 | 说明 |
|------|------|
| **HTML5** | 语义化结构和响应式设计 |
| **CSS3** | 现代化样式、Grid/Flexbox布局、动画效果 |
| **Vanilla JavaScript** | 原生ES6+，无框架依赖 |
| **Fetch API** | 现代HTTP请求处理 |
| **LocalStorage** | 客户端数据存储 |
| **Canvas API** | 图表绘制和标注框渲染 |
| **Nginx** | 静态文件服务和API代理 |

### 页面交互流程

```
┌─────────────────────────────────────────────────────────────────┐
│ 入口流程                                                        │
├─────────────────────────────────────────────────────────────────┤
│ index.html (首页)                                              │
│     ↓                                                           │
│ 导航菜单 (检查登录状态)                                          │
│   ├─ 数据集管理 (受保护)                                        │
│   ├─ AI检测 (受保护)                                            │
│   ├─ 手工标注 (受保护)                                          │
│   ├─ 光谱分析 (受保护)                                          │
│   └─ 登录/注册 (公开)                                           │
│     ↓ (未登录且点击受保护功能)                                   │
│ login.html (自动跳转)                                          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 数据集管理流程                                                   │
├─────────────────────────────────────────────────────────────────┤
│ dataset.html 创建新数据集                                       │
│     ↓                                                           │
│ 上传原始图片到数据集（根据分析类型选择格式）                      │
│   ├─ AI检测/手工标注：上传 RGB图像 (.jpg, .png)                 │
│   └─ 光谱分析：上传 MATLAB数据 (.mat)                           │
│     ↓                                                           │
│ 选择后续操作：                                                  │
│   ├─ 点击"检查" → detection.html (AI检测结果) - RGB图像        │
│   ├─ 点击"标注" → annotate.html (手工标注) - RGB图像            │
│   └─ 点击"分析" → spectrum.html (光谱分析) - .mat数据           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ AI检测结果查看流程                                              │
├─────────────────────────────────────────────────────────────────┤
│ detection.html (从数据集点击"检查"进入)                         │
│ 📋 数据要求：RGB图像 (.jpg, .png)                              │
│     ↓                                                           │
│ 显示YOLOv5模型的自动检测框                                      │
│   ├─ 显示检测框位置和置信度                                    │
│   ├─ 可点击检测框查看详细信息                                  │
│   └─ 可导出检测结果为JSON/CSV                                  │
│     ↓                                                           │
│ 如果对结果不满意：                                              │
│   └─ 跳转到 annotate.html 进行手工标注/修正                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 手工标注流程                                                     │
├─────────────────────────────────────────────────────────────────┤
│ annotate.html (从数据集点击"标注"进入)                          │
│ 📋 数据要求：RGB图像 (.jpg, .png)                              │
│     ↓                                                           │
│ 显示数据集中的图片列表                                          │
│     ↓                                                           │
│ 在图片上拖拽绘制标注框                                          │
│   ├─ 选择标注类别                                              │
│   ├─ 鼠标拖拽创建边界框                                        │
│   └─ 双击编辑或右键删除                                        │
│     ↓                                                           │
│ 保存后导航到下一张图片                                          │
│     ↓                                                           │
│ 重复上述步骤，完成数据集标注                                    │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 光谱分析流程                                                     │
├─────────────────────────────────────────────────────────────────┤
│ spectrum.html (从数据集点击"分析"进入)                          │
│ 📋 数据要求：MATLAB数据 (.mat)                                 │
│     ↓                                                           │
│ 上传或选择种子光谱数据文件                                      │
│     ↓                                                           │
│ 点击"分析光谱"按钮                                              │
│     ↓                                                           │
│ 后端计算光谱信息                                                │
│     ↓                                                           │
│ Canvas绘制光谱曲线                                              │
│     ↓                                                           │
│ 显示分析结果 (活力评级、推荐指数等)                              │
│     ↓                                                           │
│ 下载结果为CSV                                                   │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ 完整工作流程概览                                                 │
├─────────────────────────────────────────────────────────────────┤
│ 1️⃣  数据集管理 → 创建数据集 + 上传原始图片                     │
│     📋 数据格式：根据分析类型选择                               │
│        ├─ AI检测/手工标注：RGB图像 (.jpg, .png)                 │
│        └─ 光谱分析：MATLAB数据 (.mat)                           │
│                                                                │
│ 2️⃣  AI检测 (detection.html) → 查看YOLOv5模型的检测结果       │
│     📋 数据要求：RGB图像 (.jpg, .png)                          │
│                                                                │
│ 3️⃣  手工标注 (annotate.html) → 创建/修正标注框                │
│     📋 数据要求：RGB图像 (.jpg, .png)                          │
│                                                                │
│ 4️⃣  光谱分析 (spectrum.html) → 评估种子活力等级               │
│     📋 数据要求：MATLAB数据 (.mat)                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## API集成说明

### 认证接口

#### 用户登录
```javascript
const response = await fetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ 
        username_or_email: 'user@example.com',
        password: 'password123'
    })
});

// 成功响应
{
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
        "id": 1,
        "username": "user",
        "email": "user@example.com"
    }
}
```

#### 用户注册
```javascript
const response = await fetch('/api/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        username: 'newuser',
        email: 'user@example.com',
        password: 'password123'
    })
});

// 成功响应
{
    "message": "注册成功",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 数据集接口

#### 创建数据集
```javascript
const response = await fetch('/api/datasets', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        name: '我的数据集',
        description: '种子发芽检测数据集'
    })
});

// 成功响应
{
    "id": 1,
    "name": "我的数据集",
    "description": "种子发芽检测数据集",
    "created_by": 1,
    "created_at": "2024-01-01T10:00:00",
    "is_public": false
}
```

#### 获取用户的所有数据集
```javascript
const response = await fetch('/api/datasets', {
    method: 'GET',
    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
});

// 成功响应
[
    {
        "id": 1,
        "name": "数据集1",
        "description": "描述",
        "image_count": 50,
        "created_at": "2024-01-01T10:00:00"
    }
]
```

### 图片管理接口

#### 上传图片
```javascript
const formData = new FormData();
formData.append('file', imageFile);

const response = await fetch('/api/datasets/1/upload', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
    body: formData
});

// 成功响应
{
    "id": 100,
    "filename": "seed_001.jpg",
    "original_filename": "seed_001.jpg",
    "dataset_id": 1,
    "uploaded_at": "2024-01-01T10:00:00",
    "file_path": "/uploads/seed_001.jpg"
}
```

#### 获取图片的标注列表
```javascript
const response = await fetch('/api/images/100/annotations', {
    method: 'GET',
    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
});

// 成功响应
[
    {
        "id": 1,
        "label": "发芽种子",
        "x_min": 0.1,
        "y_min": 0.2,
        "x_max": 0.4,
        "y_max": 0.5,
        "confidence": 0.95,
        "created_at": "2024-01-01T10:00:00"
    }
]
```

#### 添加标注
```javascript
const response = await fetch('/api/images/100/annotations', {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        label: '发芽种子',
        x_min: 0.1,
        y_min: 0.2,
        x_max: 0.4,
        y_max: 0.5,
        confidence: 0.95
    })
});

// 成功响应
{
    "id": 2,
    "image_id": 100,
    "label": "发芽种子",
    "x_min": 0.1,
    "y_min": 0.2,
    "x_max": 0.4,
    "y_max": 0.5,
    "confidence": 0.95
}
```

#### 更新标注
```javascript
const response = await fetch('/api/annotations/1', {
    method: 'PUT',
    headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        label: '高度发芽种子',
        confidence: 0.98
    })
};
```

#### 删除标注
```javascript
const response = await fetch('/api/annotations/1', {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
});
```

---

## 开发指南

### 页面开发规范

#### HTML结构
- 使用语义化标签（`<header>`, `<nav>`, `<main>`, `<footer>` 等）
- 正确的嵌套结构
- 添加适当的ARIA标签以支持无障碍

#### CSS样式
- 遵循BEM命名规范：`.block__element--modifier`
- 使用CSS变量实现主题定制
- Flexbox和Grid布局优先
- 移动优先的响应式设计

#### JavaScript编码规范
```javascript
// 使用ES6+语法
const name = 'value'; // const优先于let
const handleClick = () => {}; // 箭头函数
const { token } = localStorage; // 解构赋值

// 模块化开发
export async function apiRequest(url, options = {}) {
    // 统一的API调用逻辑
}

// 错误处理
try {
    const result = await apiRequest(url);
} catch (error) {
    console.error('操作失败:', error.message);
    showErrorMessage('请重试');
}
```

### 通用工具函数

```javascript
// API请求统一处理
async function apiRequest(url, options = {}) {
    const token = localStorage.getItem('token');
    const defaultOptions = {
        headers: {
            'Authorization': token ? `Bearer ${token}` : '',
            'Content-Type': 'application/json'
        }
    };

    const response = await fetch(url, { ...defaultOptions, ...options });
    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.message || '请求失败');
    }

    return data;
}

// 认证状态管理
const AuthManager = {
    getToken() {
        return localStorage.getItem('token');
    },
    
    setToken(token) {
        localStorage.setItem('token', token);
    },
    
    isLoggedIn() {
        return !!this.getToken();
    },
    
    logout() {
        localStorage.removeItem('token');
        window.location.href = 'login.html';
    }
};

// 用户界面提示
function showSuccessMessage(message) {
    // 显示成功提示
}

function showErrorMessage(message) {
    // 显示错误提示
}

function showLoadingState(isLoading) {
    // 显示加载状态
}
```

### 页面增删的步骤

#### 1. 创建新页面
```bash
# 创建HTML文件
touch frontend/newpage.html

# 创建对应的JavaScript模块
touch frontend/js/newpage.js
```

#### 2. HTML基本结构
```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>新页面 - SeedAI</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <!-- 内容 -->
    </div>
    <script src="js/newpage.js"></script>
</body>
</html>
```

#### 3. JavaScript模块
```javascript
// 初始化页面
document.addEventListener('DOMContentLoaded', () => {
    initializePage();
    setupEventListeners();
});

function initializePage() {
    // 页面初始化逻辑
}

function setupEventListeners() {
    // 绑定事件监听器
    document.getElementById('button').addEventListener('click', handleClick);
}

async function handleClick() {
    try {
        const result = await apiRequest('/api/endpoint');
        // 处理结果
    } catch (error) {
        console.error('错误:', error);
    }
}
```

#### 4. 添加导航菜单链接
在 `index.html` 的导航栏中添加链接：
```html
<a href="newpage.html" class="nav-link" data-action="checkLogin">
    新功能
</a>
```

#### 5. 添加样式
在 `style.css` 中添加新页面的样式：
```css
.newpage-container {
    display: grid;
    grid-template-columns: 1fr;
    gap: 20px;
    padding: 20px;
}

@media (max-width: 768px) {
    .newpage-container {
        padding: 15px;
    }
}
```

### 调试技巧

#### 浏览器开发工具
- **F12** 打开开发工具
- **Network** 标签检查API请求
- **Console** 标签编写测试代码
- **Application** 标签查看LocalStorage

#### 常见问题排查
```javascript
// 检查token是否存在
console.log('Token:', localStorage.getItem('token'));

// 检查API响应
fetch('/api/datasets')
    .then(r => r.json())
    .then(d => console.log('API响应:', d))
    .catch(e => console.error('API错误:', e));

// 检查DOM元素
console.log('元素:', document.getElementById('myElement'));
```

---

## 部署配置

### Nginx配置
```
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # SPA路由处理
    location / {
        try_files $uri $uri/ /index.html;
    }

    # API代理到后端
    location /api/ {
        proxy_pass http://backend:5000/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 缓存配置
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # 不缓存HTML
    location ~* \.html?$ {
        expires -1;
        add_header Cache-Control "no-cache, no-store, must-revalidate";
    }
}
```

### Docker配置
```
# 构建前端镜像
FROM nginx:alpine
COPY frontend/ /usr/share/nginx/html/
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### 启动服务
```bash
# 构建并启动
docker-compose up -d --build

# 查看服务状态
docker-compose ps

# 查看前端日志
docker-compose logs frontend
```

---

## 常见问题

### Q: 如何快速开发调试前端？
**A:** 在本地使用Live Server插件在VS Code中打开前端文件夹，可以实时预览修改。

### Q: 为什么登录后还是被重定向到登录页面？
**A:** 检查浏览器的LocalStorage是否正确保存了token，检查Network标签中的API响应是否包含token。

### Q: 为什么点击"分析"按钮时提示文件格式错误？
**A:** 光谱分析功能需要MATLAB数据文件(.mat)，请确保上传的是.mat格式的光谱数据文件，而不是RGB图像。

### Q: AI检测和手工标注功能为什么不能处理.mat文件？
**A:** AI检测和手工标注功能专门处理RGB图像(.jpg, .png)，用于目标检测和标注。光谱分析功能则需要.mat格式的MATLAB数据文件。

### Q: 如何准备适合不同分析类型的数据？
**A:** 
- **AI检测/手工标注**：准备RGB彩色图像(.jpg, .png)，种子发芽的照片
- **光谱分析**：准备MATLAB数据文件(.mat)，包含种子光谱信息的数据

### Q: 修改页面的颜色方案？
**A:** 编辑 `style.css` 中的 `:root` CSS变量，修改 `--primary-color` 等变量值。

### Q: 如何实现AI检测功能（detection.html）？
**A:** 修改 `detection.js` 中的检测结果加载逻辑，调用真实的 `/api/detect` 端点获取YOLOv5模型的检测结果。

### Q: 如何实现手工标注功能（annotate.html）？
**A:** 修改 `annotate.js` 中的Canvas交互逻辑，实现在图片上拖拽绘制标注框的功能，并调用 `/api/images/{id}/annotations` 端点保存标注。

### Q: 光谱分析的模拟数据如何替换为真实数据？
**A:** 修改 `spectrum.js` 中的 `generateMockSpectrumData()` 函数，改为调用真实的 `/api/spectrum/analyze` 端点。

### Q: 如何在特定设备上测试响应式设计？
**A:** 在浏览器开发工具的Device Mode中选择特定设备，或使用媒体查询预览不同分辨率。

### Q: 如何处理图片上传超时？
**A:** 在 `apiRequest()` 函数中添加timeout配置，或在upload处理中显示进度提示给用户。

---

## 扩展建议

### 性能优化
- [ ] 实现图片懒加载
- [ ] 压缩CSS和JavaScript文件
- [ ] 使用WebP格式的图片
- [ ] 实现Service Worker离线支持

### 功能扩展
- [ ] 暗色主题支持
- [ ] 多语言支持（国际化）
- [ ] 高级搜索和过滤
- [ ] 数据导出为Excel格式
- [ ] 批量处理功能
- [ ] 实时协作功能

### 用户体验改进
- [ ] 键盘快捷键支持
- [ ] 拖拽排序功能
- [ ] 自定义布局保存
- [ ] 操作历史和撤销功能
- [ ] 搜索建议和自动完成

---

**最后更新**: 2024年1月
**维护者**: SeedAI开发团队
