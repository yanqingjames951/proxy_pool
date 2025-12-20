import { createRouter, createWebHistory } from 'vue-router'
import axios from 'axios'

const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/login',
            name: 'login',
            component: () => import('../views/LoginView.vue'),
            meta: { requiresAuth: false }
        },
        {
            path: '/',
            name: 'dashboard',
            component: () => import('../views/DashboardView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/proxies',
            name: 'proxies',
            component: () => import('../views/ProxyList.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/sources',
            name: 'sources',
            component: () => import('../views/SourcesView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/tools',
            name: 'tools',
            component: () => import('../views/ToolsView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/docs',
            name: 'docs',
            component: () => import('../views/IntegrationView.vue'),
            meta: { requiresAuth: true }
        },
        {
            path: '/admin',
            name: 'admin',
            component: () => import('../views/AdminView.vue'),
            meta: { requiresAuth: true }
        }
    ]
})

// Navigation guard for authentication
router.beforeEach((to, _from, next) => {
    const apiKey = localStorage.getItem('api_key')

    // Set axios header if key exists
    if (apiKey) {
        axios.defaults.headers.common['X-API-Key'] = apiKey
    }

    // Check if route requires auth
    if (to.meta.requiresAuth !== false && !apiKey) {
        next('/login')
    } else if (to.path === '/login' && apiKey) {
        next('/')
    } else {
        next()
    }
})

export default router
