declare global {
  interface Window {
    Telegram?: {
      WebApp: {
        ready(): void
        expand(): void
        close(): void
        initData: string
        initDataUnsafe: {
          user?: {
            id: number
            first_name: string
            last_name?: string
            username?: string
            language_code?: string
          }
          auth_date: number
          hash: string
        }
        themeParams: {
          bg_color?: string
          text_color?: string
          hint_color?: string
          link_color?: string
          button_color?: string
          button_text_color?: string
          secondary_bg_color?: string
        }
        colorScheme: 'light' | 'dark'
        isExpanded: boolean
        viewportHeight: number
        viewportStableHeight: number
        MainButton: {
          text: string
          color: string
          textColor: string
          isVisible: boolean
          isActive: boolean
          isProgressVisible: boolean
          setText(text: string): void
          onClick(callback: () => void): void
          offClick(callback: () => void): void
          show(): void
          hide(): void
          enable(): void
          disable(): void
          showProgress(leaveActive?: boolean): void
          hideProgress(): void
          setParams(params: {
            text?: string
            color?: string
            text_color?: string
            is_active?: boolean
            is_visible?: boolean
          }): void
        }
        BackButton: {
          isVisible: boolean
          onClick(callback: () => void): void
          offClick(callback: () => void): void
          show(): void
          hide(): void
        }
      }
    }
  }
}

export class TelegramService {
  static isAvailable(): boolean {
    return typeof window !== 'undefined' && !!window.Telegram?.WebApp
  }

  static getUser() {
    if (!this.isAvailable()) return null
    return window.Telegram!.WebApp.initDataUnsafe.user || null
  }

  static getInitData(): string {
    if (!this.isAvailable()) return ''
    return window.Telegram!.WebApp.initData
  }

  static async authenticate(): Promise<string | null> {
    try {
      const initData = this.getInitData()
      if (!initData) {
        throw new Error('No Telegram init data available')
      }

      // Validate with backend and get JWT
      const response = await fetch('/api/miniapp/validate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ initData })
      })

      if (!response.ok) {
        throw new Error('Authentication failed')
      }

      const data = await response.json()
      return data.access_token
    } catch (error) {
      console.error('Telegram authentication failed:', error)
      return null
    }
  }

  static setMainButton(text: string, onClick: () => void) {
    if (!this.isAvailable()) return

    const mainButton = window.Telegram!.WebApp.MainButton
    mainButton.setText(text)
    mainButton.onClick(onClick)
    mainButton.show()
  }

  static hideMainButton() {
    if (!this.isAvailable()) return
    window.Telegram!.WebApp.MainButton.hide()
  }

  static setBackButton(onClick: () => void) {
    if (!this.isAvailable()) return

    const backButton = window.Telegram!.WebApp.BackButton
    backButton.onClick(onClick)
    backButton.show()
  }

  static hideBackButton() {
    if (!this.isAvailable()) return
    window.Telegram!.WebApp.BackButton.hide()
  }

  static close() {
    if (!this.isAvailable()) return
    window.Telegram!.WebApp.close()
  }

  static getThemeParams() {
    if (!this.isAvailable()) return {}
    return window.Telegram!.WebApp.themeParams
  }

  static getColorScheme(): 'light' | 'dark' {
    if (!this.isAvailable()) return 'light'
    return window.Telegram!.WebApp.colorScheme
  }
}