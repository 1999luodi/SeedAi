(function (window) {
    const API_BASE = '/api';
    const hasContract = Boolean(window.SeedAIContract && window.SeedAIContract.routes);

    function getToken() {
        return localStorage.getItem('token');
    }

    function setToken(token) {
        localStorage.setItem('token', token);
    }

    function clearToken() {
        localStorage.removeItem('token');
    }

    function isLoggedIn() {
        return Boolean(getToken());
    }

    function buildUrl(path) {
        if (path.startsWith('http://') || path.startsWith('https://')) {
            return path;
        }
        const cleanPath = path.startsWith('/') ? path : `/${path}`;
        return `${API_BASE}${cleanPath}`;
    }

    function route(routeKey, params) {
        if (!hasContract) {
            throw new Error('SeedAIContract is not loaded');
        }
        return window.SeedAIContract.buildRoute(routeKey, params || {});
    }

    async function request(path, options) {
        const opt = options || {};
        const headers = Object.assign({}, opt.headers || {});

        if (!(opt.body instanceof FormData) && !headers['Content-Type']) {
            headers['Content-Type'] = 'application/json';
        }

        const token = getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(buildUrl(path), Object.assign({}, opt, { headers }));

        let payload = null;
        try {
            payload = await response.json();
        } catch (error) {
            payload = null;
        }

        if (!response.ok) {
            const message = payload && payload.message ? payload.message : `HTTP ${response.status}`;
            throw new Error(message);
        }

        return payload;
    }

    async function upload(path, formData, onProgress) {
        const token = getToken();
        const xhr = new XMLHttpRequest();

        return new Promise((resolve, reject) => {
            xhr.open('POST', buildUrl(path));

            if (token) {
                xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            }

            xhr.upload.addEventListener('progress', function (event) {
                if (event.lengthComputable && typeof onProgress === 'function') {
                    onProgress((event.loaded / event.total) * 100);
                }
            });

            xhr.onload = function () {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        resolve(JSON.parse(xhr.responseText));
                    } catch (error) {
                        resolve({ success: true });
                    }
                } else {
                    try {
                        const err = JSON.parse(xhr.responseText);
                        reject(new Error(err.message || `HTTP ${xhr.status}`));
                    } catch (error) {
                        reject(new Error(`HTTP ${xhr.status}`));
                    }
                }
            };

            xhr.onerror = function () {
                reject(new Error('网络错误'));
            };

            xhr.send(formData);
        });
    }

    async function applyUserNav(opts) {
        const options = opts || {};
        const loginLink = document.getElementById(options.loginLinkId || 'loginLink');
        const profileLink = document.getElementById(options.profileLinkId || 'profileLink');
        const usernameNode = document.getElementById(options.usernameId || 'usernameDisplay');
        const logoutNode = document.getElementById(options.logoutId || 'logoutLink');
        const loginHref = options.loginHref || 'login.html';
        const logoutHref = options.logoutHref || 'index.html';

        if (!loginLink) {
            return;
        }

        if (!isLoggedIn()) {
            loginLink.style.display = '';
            loginLink.textContent = options.loginText || '登录/注册';
            loginLink.href = loginHref;
            if (profileLink) {
                profileLink.style.display = 'none';
            }
            return;
        }

        if (profileLink) {
            loginLink.style.display = 'none';
            profileLink.style.display = '';

            if (usernameNode) {
                try {
                    const profile = await request('/users/profile');
                    if (profile && profile.success && profile.data) {
                        usernameNode.textContent = profile.data.username || '用户';
                    }
                } catch (error) {
                    usernameNode.textContent = '用户';
                }
            }

            if (logoutNode) {
                logoutNode.onclick = function (event) {
                    event.preventDefault();
                    clearToken();
                    window.location.href = logoutHref;
                };
            }
            return;
        }

        loginLink.textContent = options.logoutText || '登出';
        loginLink.href = '#';
        loginLink.onclick = function (event) {
            event.preventDefault();
            clearToken();
            window.location.href = logoutHref;
        };
    }

    window.SeedAI = {
        token: {
            get: getToken,
            set: setToken,
            clear: clearToken
        },
        auth: {
            isLoggedIn,
            requireLogin: function (redirectTo) {
                if (!isLoggedIn()) {
                    window.location.href = redirectTo || 'login.html';
                    return false;
                }
                return true;
            },
            logout: function (redirectTo) {
                clearToken();
                window.location.href = redirectTo || 'login.html';
            },
            applyUserNav
        },
        api: {
            route,
            request,
            get: function (path) {
                return request(path);
            },
            post: function (path, data) {
                return request(path, {
                    method: 'POST',
                    body: JSON.stringify(data)
                });
            },
            put: function (path, data) {
                return request(path, {
                    method: 'PUT',
                    body: JSON.stringify(data)
                });
            },
            delete: function (path) {
                return request(path, { method: 'DELETE' });
            },
            upload
        }
    };
})(window);
