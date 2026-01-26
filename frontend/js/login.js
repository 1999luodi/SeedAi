// 导入工具函数（如果在单独的文件中）
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
        window.location.href = 'index.html';
    }

    static showMessage(message, type = 'info', duration = 5000) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type} fade-in`;
        messageDiv.innerHTML = `
            <span class="message-icon">${this.getMessageIcon(type)}</span>
            <span class="message-text">${message}</span>
            <button class="message-close" onclick="this.parentElement.remove()">&times;</button>
        `;

        const container = document.querySelector('.auth-card') || document.body;
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

    static setLoading(button, loading = true) {
        if (loading) {
            button.disabled = true;
            button.innerHTML = '<span class="spinner"></span> 处理中...';
        } else {
            button.disabled = false;
            button.innerHTML = '<span class="btn-icon">🔓</span> 登录';
        }
    }
}

// API请求类
class API {
    static async request(endpoint, options = {}) {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(`/api${endpoint}`, config);
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

    static async post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }
}

// 登录应用类
class LoginApp {
    constructor() {
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkAuthStatus();
    }

    bindEvents() {
        // 登录表单
        const loginForm = document.getElementById('loginForm');
        const loginBtn = document.getElementById('loginBtn');

        loginForm.addEventListener('submit', (e) => this.handleLogin(e));

        // 密码可见性切换
        const passwordToggle = document.getElementById('passwordToggle');
        passwordToggle.addEventListener('click', () => this.togglePasswordVisibility());

        // 注册相关
        const registerLink = document.getElementById('registerLink');
        registerLink.addEventListener('click', (e) => {
            e.preventDefault();
            this.showRegisterModal();
        });

        // 注册模态框
        const closeRegisterModal = document.getElementById('closeRegisterModal');
        const cancelRegister = document.getElementById('cancelRegister');
        const registerForm = document.getElementById('registerForm');

        closeRegisterModal.addEventListener('click', () => this.hideRegisterModal());
        cancelRegister.addEventListener('click', () => this.hideRegisterModal());
        registerForm.addEventListener('submit', (e) => this.handleRegister(e));

        // 点击模态框外部关闭
        document.getElementById('registerModal').addEventListener('click', (e) => {
            if (e.target.id === 'registerModal') {
                this.hideRegisterModal();
            }
        });
    }

    checkAuthStatus() {
        if (Utils.isLoggedIn()) {
            // 如果已经登录，重定向到首页
            window.location.href = 'index.html';
        }
    }

    async handleLogin(e) {
        e.preventDefault();

        const username = document.getElementById('username').value.trim();
        const password = document.getElementById('password').value;
        const rememberMe = document.getElementById('rememberMe').checked;
        const loginBtn = document.getElementById('loginBtn');

        if (!username || !password) {
            Utils.showMessage('请输入用户名和密码', 'warning');
            return;
        }

        Utils.setLoading(loginBtn, true);

        try {
            const response = await API.post('/auth/login', {
                username_or_email: username,
                password: password
            });

            if (response.success) {
                Utils.setToken(response.data.token);

                // 如果选择记住我，设置更长的过期时间（这里简化处理）
                if (rememberMe) {
                    localStorage.setItem('rememberMe', 'true');
                }

                Utils.showMessage('登录成功！正在跳转...', 'success');

                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 1000);
            } else {
                Utils.showMessage(response.message || '登录失败', 'error');
            }
        } catch (error) {
            Utils.showMessage(`登录失败: ${error.message}`, 'error');
        } finally {
            Utils.setLoading(loginBtn, false);
        }
    }

    togglePasswordVisibility() {
        const passwordInput = document.getElementById('password');
        const toggleBtn = document.getElementById('passwordToggle');

        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            toggleBtn.textContent = '🙈';
        } else {
            passwordInput.type = 'password';
            toggleBtn.textContent = '👁️';
        }
    }

    showRegisterModal() {
        document.getElementById('registerModal').style.display = 'flex';
    }

    hideRegisterModal() {
        document.getElementById('registerModal').style.display = 'none';
        document.getElementById('registerForm').reset();
    }

    async handleRegister(e) {
        e.preventDefault();

        const username = document.getElementById('regUsername').value.trim();
        const email = document.getElementById('regEmail').value.trim();
        const password = document.getElementById('regPassword').value;
        const confirmPassword = document.getElementById('regConfirmPassword').value;

        // 表单验证
        if (!username || !email || !password || !confirmPassword) {
            Utils.showMessage('请填写所有必填字段', 'warning');
            return;
        }

        if (password !== confirmPassword) {
            Utils.showMessage('两次输入的密码不一致', 'error');
            return;
        }

        if (password.length < 6) {
            Utils.showMessage('密码长度至少6位', 'warning');
            return;
        }

        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(email)) {
            Utils.showMessage('请输入有效的邮箱地址', 'warning');
            return;
        }

        const submitBtn = e.target.querySelector('button[type="submit"]');
        Utils.setLoading(submitBtn, true);

        try {
            const response = await API.post('/auth/register', {
                username: username,
                email: email,
                password: password
            });

            if (response.success) {
                Utils.showMessage('注册成功！请登录', 'success');
                this.hideRegisterModal();

                // 自动填充登录表单
                document.getElementById('username').value = username;
                document.getElementById('password').value = '';
            } else {
                Utils.showMessage(response.message || '注册失败', 'error');
            }
        } catch (error) {
            Utils.showMessage(`注册失败: ${error.message}`, 'error');
        } finally {
            Utils.setLoading(submitBtn, false);
        }
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    new LoginApp();
});
