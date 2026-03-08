class LoginApp {
    constructor() {
        this.currentForm = 'login';
        this.init();
    }

    init() {
        this.bindEvents();
        if (SeedAI.auth.isLoggedIn()) {
            window.location.href = 'index.html';
        }
    }

    bindEvents() {
        document.getElementById('loginForm').addEventListener('submit', (event) => this.handleLogin(event));
        document.getElementById('registerForm').addEventListener('submit', (event) => this.handleRegister(event));

        this.bindSwitchLinks();

        const toggles = [
            ['loginPasswordToggle', 'loginPassword'],
            ['regPasswordToggle', 'regPassword'],
            ['regConfirmPasswordToggle', 'regConfirmPassword']
        ];

        toggles.forEach(([btnId, inputId]) => {
            const button = document.getElementById(btnId);
            if (!button) {
                return;
            }
            button.addEventListener('click', () => this.togglePasswordVisibility(inputId));
        });
    }

    bindSwitchLinks() {
        const toRegister = document.getElementById('switchToRegister');
        if (toRegister) {
            toRegister.onclick = (event) => {
                event.preventDefault();
                this.switchForm('register');
            };
        }

        const toLogin = document.getElementById('switchToLogin');
        if (toLogin) {
            toLogin.onclick = (event) => {
                event.preventDefault();
                this.switchForm('login');
            };
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
            registerForm.style.display = 'block';
            authTitle.textContent = '创建账户';
            authSubtitle.textContent = '加入SeedAI，开始您的种子研究之旅';
            switchFormText.innerHTML = '已有账户？<a href="#" id="switchToLogin">返回登录</a>';
        } else {
            registerForm.style.display = 'none';
            loginForm.style.display = 'block';
            authTitle.textContent = '欢迎回来';
            authSubtitle.textContent = '登录您的SeedAI账户';
            switchFormText.innerHTML = '还没有账户？<a href="#" id="switchToRegister">立即注册</a>';
        }

        this.currentForm = formType;
        this.bindSwitchLinks();
    }

    setLoading(button, loading, text) {
        if (loading) {
            button.disabled = true;
            button.dataset.origin = button.innerHTML;
            button.innerHTML = text;
        } else {
            button.disabled = false;
            button.innerHTML = button.dataset.origin || button.innerHTML;
        }
    }

    showMessage(message, type) {
        const div = document.createElement('div');
        div.className = `message ${type || 'info'} fade-in`;
        div.innerHTML = `<span class="message-text">${message}</span><button class="message-close" onclick="this.parentElement.remove()">&times;</button>`;
        const container = document.querySelector('.auth-card') || document.body;
        container.insertBefore(div, container.firstChild);
        setTimeout(() => {
            if (div.parentElement) {
                div.remove();
            }
        }, 4000);
    }

    async handleLogin(event) {
        event.preventDefault();

        const usernameOrEmail = document.getElementById('loginUsername').value.trim();
        const password = document.getElementById('loginPassword').value;
        const loginBtn = document.getElementById('loginBtn');

        if (!usernameOrEmail || !password) {
            this.showMessage('请输入用户名和密码', 'warning');
            return;
        }

        this.setLoading(loginBtn, true, '<span class="btn-icon">...</span> 登录中...');

        try {
            const endpoint = SeedAI.api.route('POST_API_AUTH_LOGIN');
            const response = await SeedAI.api.post(endpoint, {
                username_or_email: usernameOrEmail,
                password: password
            });

            if (response.success && response.data && response.data.token) {
                SeedAI.token.set(response.data.token);
                this.showMessage('登录成功，正在跳转...', 'success');
                setTimeout(() => {
                    window.location.href = 'index.html';
                }, 800);
                return;
            }

            this.showMessage(response.message || '登录失败', 'error');
        } catch (error) {
            this.showMessage(`登录失败: ${error.message}`, 'error');
        } finally {
            this.setLoading(loginBtn, false);
        }
    }

    async handleRegister(event) {
        event.preventDefault();

        const username = document.getElementById('regUsername').value.trim();
        const email = document.getElementById('regEmail').value.trim();
        const password = document.getElementById('regPassword').value;
        const confirm = document.getElementById('regConfirmPassword').value;
        const registerBtn = document.getElementById('registerBtn');

        if (!username || !email || !password || !confirm) {
            this.showMessage('请填写所有字段', 'warning');
            return;
        }

        if (password !== confirm) {
            this.showMessage('两次输入的密码不一致', 'error');
            return;
        }

        this.setLoading(registerBtn, true, '<span class="btn-icon">...</span> 注册中...');

        try {
            const endpoint = SeedAI.api.route('POST_API_AUTH_REGISTER');
            const response = await SeedAI.api.post(endpoint, {
                username,
                email,
                password
            });

            if (response.success) {
                this.showMessage('注册成功，请登录', 'success');
                document.getElementById('registerForm').reset();
                this.switchForm('login');
                document.getElementById('loginUsername').value = username;
                return;
            }

            this.showMessage(response.message || '注册失败', 'error');
        } catch (error) {
            this.showMessage(`注册失败: ${error.message}`, 'error');
        } finally {
            this.setLoading(registerBtn, false);
        }
    }

    togglePasswordVisibility(inputId) {
        const input = document.getElementById(inputId);
        const button = input.parentNode.querySelector('.password-toggle');
        if (input.type === 'password') {
            input.type = 'text';
            button.textContent = 'HIDE';
        } else {
            input.type = 'password';
            button.textContent = 'SHOW';
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new LoginApp();
});
