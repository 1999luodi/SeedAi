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
            button.dataset.originalContent = button.innerHTML;
            button.innerHTML = '<span class="spinner"></span> 处理中...';
        } else {
            button.disabled = false;
            button.innerHTML = button.dataset.originalContent || button.innerHTML;
        }
    }
}

// API请求类
class API {
    static async request(endpoint, options = {}) {
        // 如果访问端口是80或为空（默认），则使用相对路径（nginx代理）
        // 否则直接连接到后端5000端口
        const port = window.location.port;
        const baseUrl = (port === '' || port === '80') ? '' : `http://localhost:5000`;
        const url = `${baseUrl}/api${endpoint}`;
        
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json'
            }
        };

        const config = { ...defaultOptions, ...options };

        try {
            const response = await fetch(url, config);
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
        this.currentForm = 'login'; // 'login' or 'register'
        this.init();
    }

    init() {
        this.bindEvents();
        this.checkAuthStatus();
    }

    bindEvents() {
        // 登录表单
        const loginForm = document.getElementById('loginForm');
        loginForm.addEventListener('submit', (e) => this.handleLogin(e));

        // 注册表单
        const registerForm = document.getElementById('registerForm');
        registerForm.addEventListener('submit', (e) => this.handleRegister(e));

        // 密码可见性切换
        const loginPasswordToggle = document.getElementById('loginPasswordToggle');
        const regPasswordToggle = document.getElementById('regPasswordToggle');
        const regConfirmPasswordToggle = document.getElementById('regConfirmPasswordToggle');

        if (loginPasswordToggle) {
            loginPasswordToggle.addEventListener('click', () => this.togglePasswordVisibility('loginPassword'));
        }
        if (regPasswordToggle) {
            regPasswordToggle.addEventListener('click', () => this.togglePasswordVisibility('regPassword'));
        }
        if (regConfirmPasswordToggle) {
            regConfirmPasswordToggle.addEventListener('click', () => this.togglePasswordVisibility('regConfirmPassword'));
        }

        // 表单切换
        const switchToRegister = document.getElementById('switchToRegister');
        if (switchToRegister) {
            switchToRegister.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchForm('register');
            });
        }

        // 返回登录链接的事件绑定
        this.bindSwitchToLogin();
    }

    bindSwitchToLogin() {
        const switchToLogin = document.getElementById('switchToLogin');
        if (switchToLogin) {
            switchToLogin.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchForm('login');
            });
        }
    }

    checkAuthStatus() {
        if (Utils.isLoggedIn()) {
            // 如果已经登录，重定向到首页
            window.location.href = 'index.html';
        }
    }

    switchForm(formType) {
        const loginForm = document.getElementById('loginForm');
        const registerForm = document.getElementById('registerForm');
        const authTitle = document.getElementById('authTitle');
        const authSubtitle = document.getElementById('authSubtitle');
        const switchFormText = document.getElementById('switchFormText');

        if (formType === 'register') {
            loginForm.style.display = 'none';
            loginForm.classList.remove('active-form');
            registerForm.style.display = 'block';
            registerForm.classList.add('active-form');
            authTitle.textContent = '创建账户';
            authSubtitle.textContent = '加入SeedAI，开始您的种子研究之旅';
            switchFormText.innerHTML = '已有账户？<a href="#" id="switchToLogin">返回登录</a>';

            // 重新绑定返回登录的事件
            this.bindSwitchToLogin();
        } else {
            registerForm.style.display = 'none';
            registerForm.classList.remove('active-form');
            loginForm.style.display = 'block';
            loginForm.classList.add('active-form');
            authTitle.textContent = '欢迎回来';
            authSubtitle.textContent = '登录您的SeedAI账户';
            switchFormText.innerHTML = '还没有账户？<a href="#" id="switchToRegister">立即注册</a>';
        }

        this.currentForm = formType;
    }

    async handleLogin(e) {
        e.preventDefault();

        const username = document.getElementById('loginUsername').value.trim();
        const password = document.getElementById('loginPassword').value;
        const rememberMe = document.getElementById('rememberMe').checked;
        const loginBtn = document.querySelector('#loginForm button[type="submit"]');

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

    togglePasswordVisibility(inputId) {
        const passwordInput = document.getElementById(inputId);
        const inputGroup = passwordInput.parentNode; // 获取父元素，即.password-input容器
        const toggleBtn = inputGroup.querySelector('.password-toggle'); // 在父元素中查找toggle按钮

        if (passwordInput.type === 'password') {
            passwordInput.type = 'text';
            toggleBtn.textContent = '🙈';
        } else {
            passwordInput.type = 'password';
            toggleBtn.textContent = '👁️';
        }
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

        const submitBtn = document.querySelector('#registerForm button[type="submit"]');
        Utils.setLoading(submitBtn, true);

        try {
            const response = await API.post('/auth/register', {
                username: username,
                email: email,
                password: password
            });

            if (response.success) {
                Utils.showMessage('注册成功！请登录', 'success');

                // 清空注册表单
                document.getElementById('registerForm').reset();

                // 延迟后切换回登录表单
                setTimeout(() => {
                    this.switchForm('login');
                    // 自动填充登录表单
                    document.getElementById('loginUsername').value = username;
                }, 1000);
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

// 处理登录
async function handleLogin(event) {
    event.preventDefault(); // 阻止表单默认提交行为

    const usernameOrEmail = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;

    // 禁用登录按钮，防止重复提交
    const loginButton = document.getElementById('loginBtn');
    const originalButtonText = loginButton.innerHTML;
    loginButton.disabled = true;
    loginButton.innerHTML = '<span class="btn-icon">⏳</span> 登录中...';

    try {
        // 发送登录请求
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username_or_email: usernameOrEmail, password })
        });

        const result = await response.json();

        if (response.ok && result.success) {
            // 存储令牌
            localStorage.setItem('token', result.data.token);
            
            // 显示成功消息
            showMessage('登录成功！', 'success');
            
            // 跳转到首页
            setTimeout(() => {
                window.location.href = 'index.html';
            }, 1000);
        } else {
            // 显示错误消息
            showMessage(result.message || '登录失败', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    } finally {
        // 恢复登录按钮状态
        loginButton.disabled = false;
        loginButton.innerHTML = originalButtonText;
    }
}

// 处理注册
async function handleRegister(event) {
    event.preventDefault(); // 阻止表单默认提交行为

    // 获取表单数据
    const username = document.getElementById('regUsername').value;
    const email = document.getElementById('regEmail').value;
    const password = document.getElementById('regPassword').value;
    const confirmPassword = document.getElementById('regConfirmPassword').value;

    // 验证密码一致性
    if (password !== confirmPassword) {
        showMessage('两次输入的密码不一致', 'error');
        return;
    }

    // 验证密码强度
    if (password.length < 6) {
        showMessage('密码长度至少为6位', 'error');
        return;
    }

    // 禁用注册按钮，防止重复提交
    const registerButton = document.getElementById('registerBtn');
    const originalButtonText = registerButton.innerHTML;
    registerButton.disabled = true;
    registerButton.innerHTML = '<span class="btn-icon">⏳</span> 注册中...';

    try {
        // 发送注册请求
        const response = await fetch('/api/auth/register', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, email, password })
        });

        const result = await response.json();

        if (response.status === 201 && result.success) {
            // 显示成功消息
            showMessage('注册成功！请登录', 'success');
            
            // 注册成功后切换到登录表单
            setTimeout(() => {
                switchForm('login');
            }, 2000);
        } else {
            // 显示错误消息
            showMessage(result.message || '注册失败', 'error');
        }
    } catch (error) {
        console.error('Registration error:', error);
        showMessage('网络错误，请稍后重试', 'error');
    } finally {
        // 恢复注册按钮状态
        registerButton.disabled = false;
        registerButton.innerHTML = originalButtonText;
    }
}
