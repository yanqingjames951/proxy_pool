import { createApp } from 'vue'
import { createPinia } from 'pinia'
import Antd from 'ant-design-vue';
import 'ant-design-vue/dist/reset.css';
import App from './App.vue'
import router from './router'
import i18n from './locales'

import axios from 'axios'
import { message } from 'ant-design-vue'

const app = createApp(App)

// Axios Configuration
axios.defaults.baseURL = '' // Use relative path
axios.interceptors.request.use(config => {
    const apiKey = localStorage.getItem('api_key')
    if (apiKey) {
        config.headers['X-API-Key'] = apiKey
    }
    return config
})

axios.interceptors.response.use(
    response => response,
    error => {
        if (error.response && error.response.status === 401) {
            if (window.location.hash !== '#/login') { // Vue Router uses hash mode or history, assuming history but checking path
                // Actually better to rely on router guard, but force redirect if needed
                localStorage.removeItem('api_key')
                localStorage.removeItem('user_info')
                // window.location.href = '/login' // might cause reload loop if not careful
            }
        }
        return Promise.reject(error)
    }
)

app.use(createPinia())
app.use(router)
app.use(Antd)
app.use(i18n)

app.mount('#app')
