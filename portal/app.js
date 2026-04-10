// Logicapt Portal - Role-based Frontend
class PortalApp {
    constructor() {
        this.currentRole = null;
        this.currentUser = null;
        this.currentPage = 'dashboard';
        this.apiBase = '/api';
        this.init();
    }

    init() {
        this.bindEvents();
        this.showRoleSelector();
        this.loadTheme();
    }

    bindEvents() {
        // Role selection
        document.querySelectorAll('.role-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                this.selectRole(e.currentTarget.dataset.role);
            });
        });

        // Login form
        document.getElementById('loginForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleLogin();
        });

        // Test mode
        document.getElementById('testModeLink').addEventListener('click', (e) => {
            e.preventDefault();
            this.showTestModeLogin();
        });

        // Logout
        document.getElementById('logoutBtn').addEventListener('click', () => {
            this.logout();
        });

        // Mobile menu
        document.getElementById('mobileMenuBtn').addEventListener('click', () => {
            document.querySelector('.sidebar').classList.toggle('open');
        });

        // Settings
        document.getElementById('settingsBtn').addEventListener('click', () => {
            this.showSettings();
        });

        // Theme change
        document.getElementById('themeSelect').addEventListener('change', (e) => {
            this.setTheme(e.target.value);
        });

        // Modal close
        document.querySelectorAll('.close-btn').forEach(btn => {
            btn.addEventListener('click', this.hideModals.bind(this));
        });
        
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.hideModals();
            }
        });
    }

    // Role Selection
    selectRole(role) {
        this.currentRole = role;
        document.getElementById('role-selector').classList.add('hidden');
        document.getElementById('login-form').classList.remove('hidden');
        document.querySelector('.current-role').textContent = role.toUpperCase();
        document.getElementById('login-title').textContent = `Welcome, ${role.charAt(0).toUpperCase() + role.slice(1)}`;
    }

    async handleLogin() {
        const email = document.getElementById('loginEmail').value.trim();
        const password = document.getElementById('loginPassword').value;
        
        if (!email || !password) return this.showError('Please fill all fields');

        const loginEndpoint = `/api/auth/${this.currentRole}-login.php`;
        try {
            const response = await fetch(loginEndpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                body: new URLSearchParams({ email, password })
            });

            const data = await response.json();

            if (data.success) {
                this.currentUser = {
                    id: sessionStorage.getItem('user_id') || 1,
                    name: data.user?.name || sessionStorage.getItem('name') || 'User',
                    email,
                    type: this.currentRole
                };
                sessionStorage.setItem('userRole', this.currentRole);
                this.showApp();
            } else {
                this.showError(data.message || 'Login failed');
            }
        } catch (error) {
            this.showError('Connection error. Please try again.');
        }
    }

    showTestModeLogin() {
        const testEndpoint = '/api/auth/test-mode-login.php';
        const role = this.currentRole;
        
        fetch(`${testEndpoint}?type=${role}`)
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    this.currentUser = data.user;
                    sessionStorage.setItem('userRole', role);
                    this.showApp();
                } else {
                    this.showError('Test mode failed');
                }
            })
            .catch(() => this.showError('Connection error'));
    }

    showApp() {
        document.getElementById('login-form').classList.add('hidden');
        document.getElementById('app-shell').classList.remove('hidden');
        document.querySelector('.loading-screen').classList.add('hidden');
        
        this.updateUserUI();
        this.renderNav();
        this.navigateTo(this.currentPage);
    }

    updateUserUI() {
        document.getElementById('userName').textContent = this.currentUser.name;
        document.getElementById('userRole').textContent = this.currentUser.type.toUpperCase();
    }

    renderNav() {
        const nav = document.getElementById('sidebarNav');
        const navItems = this.getNavItems();
        
        nav.innerHTML = navItems.map(item => `
            <a href="#" class="nav-item ${this.currentPage === item.id ? 'active' : ''}" data-page="${item.id}">
                <span class="nav-icon">${item.icon}</span>
                <span>${item.title}</span>
            </a>
        `).join('');

        // Bind navigation
        nav.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                this.navigateTo(page);
            });
        });
    }

    getNavItems() {
        const common = [
            { id: 'dashboard', title: 'Dashboard', icon: '📊' },
            { id: 'projects', title: 'Projects', icon: '📁' },
            { id: 'settings', title: 'Settings', icon: '⚙️' }
        ];

        const admin = [
            ...common,
            { id: 'employees', title: 'Employees', icon: '👥' },
            { id: 'clients', title: 'Clients', icon: '🏢' },
            { id: 'client-ids', title: 'Client IDs', icon: '🆔' }
        ];

        const employee = [
            ...common,
            { id: 'create-project', title: 'Create Project', icon: '➕' },
            { id: 'my-projects', title: 'My Projects', icon: '📋' },
            { id: 'upload-file', title: 'Upload File', icon: '📎' },
            { id: 'chat-test', title: 'Chat Test', icon: '💬' }
        ];

        const client = [
            ...common,
            { id: 'chat', title: 'Chat', icon: '💬' }
        ];

        const navMap = {
            'admin': admin,
            'employee': employee,
            'client': client
        };

        return navMap[this.currentRole] || common;
    }

    async navigateTo(page) {
        this.currentPage = page;
        document.getElementById('pageTitle').textContent = this.getPageTitle(page);
        
        // Update nav active state
        document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
        document.querySelector(`[data-page="${page}"]`)?.classList.add('active');

        const content = document.getElementById('pageContent');
        content.innerHTML = '<div class="loading">Loading...</div>';

        try {
            const pageContent = await this.loadPageContent(page);
            content.innerHTML = pageContent;
            this.bindPageEvents(page);
        } catch (error) {
            content.innerHTML = this.renderError('Failed to load page');
        }
    }

    getPageTitle(page) {
        const titles = {
            dashboard: 'Dashboard',
            employees: 'Employees',
            clients: 'Clients',
            'client-ids': 'Client IDs',
            projects: 'Projects',
            'create-project': 'Create Project',
            'my-projects': 'My Projects',
            'project-detail': 'Project Detail',
            'upload-file': 'Upload File',
            'chat-test': 'Chat Test',
            chat: 'Chat',
            settings: 'Settings'
        };
        return titles[page] || page;
    }

    async loadPageContent(page) {
        const pageHandlers = {
            dashboard: () => this.renderDashboard(),
            employees: () => this.renderEmployees(),
            clients: () => this.renderClients(),
            'client-ids': () => this.renderClientIds(),
            projects: () => this.renderProjects(),
            'create-project': () => this.renderCreateProject(),
            'my-projects': () => this.renderMyProjects(),
            'upload-file': () => this.renderUploadFile(),
            'chat-test': () => this.renderChatTest(),
            chat: () => this.renderChat(),
            settings: () => this.renderSettings()
        };

        if (pageHandlers[page]) {
            return await pageHandlers[page]();
        }

        return this.renderError('Page not found');
    }

    bindPageEvents(page) {
        // Dynamic event binding based on page
        if (page === 'create-project') {
            document.getElementById('createProjectForm')?.addEventListener('submit', this.handleCreateProject.bind(this));
        }
        // Add more as needed
    }

    // API Helper
    async apiCall(endpoint, options = {}) {
        const config = {
            headers: {
                'Content-Type': 'application/json'
            },
            ...options
        };

        const response = await fetch(`${this.apiBase}${endpoint}`, config);
        const data = await response.json();

        if (!data.success) {
            throw new Error(data.message || 'API error');
        }

        return data;
    }

    showError(message) {
        document.getElementById('login-error')?.classList.remove('hidden');
        document.getElementById('login-error').textContent = message;
    }

    showNotification(message, type = 'success') {
        // Simple toast notification
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 4000);
    }

    logout() {
        sessionStorage.clear();
        this.showRoleSelector();
    }

    showSettings() {
        document.getElementById('settingsModal').classList.remove('hidden');
    }

    hideModals() {
        document.querySelectorAll('.modal').forEach(modal => modal.classList.add('hidden'));
    }

    loadTheme() {
        const savedTheme = localStorage.getItem('theme') || 'light';
        this.setTheme(savedTheme);
    }

    setTheme(theme) {
        document.body.dataset.theme = theme;
        localStorage.setItem('theme', theme);
    }

    // Page Renderers (placeholders - implement based on APIs)
    async renderDashboard() {
        // Load dashboard stats from API
        return `
            <div class="page-section">
                <div class="card-grid">
                    <div class="card">
                        <div class="card-header">
                            <h4>Total Projects</h4>
                            <div class="card-stats">12</div>
                        </div>
                    </div>
                    <div class="card">
                        <div class="card-header">
                            <h4>Active Employees</h4>
                            <div class="card-stats">8</div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    }

    // Add more render methods...
}

// Initialize app
const app = new PortalApp();

