import { createI18n } from 'vue-i18n'
import en from './en.json'
import zh from './zh.json'

// 获取保存的语言偏好，默认中文
const savedLocale = localStorage.getItem('locale') || 'zh'

const i18n = createI18n({
    legacy: false,
    locale: savedLocale,
    fallbackLocale: 'en',
    messages: {
        en,
        zh
    }
})

export default i18n

// 切换语言的辅助函数
export function setLocale(locale: string) {
    i18n.global.locale.value = locale as 'en' | 'zh'
    localStorage.setItem('locale', locale)
    document.querySelector('html')?.setAttribute('lang', locale)
}

// 获取当前语言
export function getLocale(): string {
    return i18n.global.locale.value
}

// 支持的语言列表
export const supportedLocales = [
    { code: 'zh', name: '中文', flag: '🇨🇳' },
    { code: 'en', name: 'English', flag: '🇺🇸' }
]
