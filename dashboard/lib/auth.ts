import Cookies from 'js-cookie'

export interface User {
  telegram_id: number
  name: string
  username?: string
  role: 'user' | 'admin'
}

export interface AuthResponse {
  access_token: string
  token_type: string
  expires_in: number
  user: User
}

class AuthService {
  private tokenKey = 'auth_token'
  private userKey = 'user_data'

  getToken(): string | null {
    return Cookies.get(this.tokenKey) || null
  }

  getUser(): User | null {
    const userData = Cookies.get(this.userKey)
    return userData ? JSON.parse(userData) : null
  }

  setAuth(authData: AuthResponse) {
    // Set token cookie with expiration
    const expiresIn = new Date(Date.now() + authData.expires_in * 1000)
    Cookies.set(this.tokenKey, authData.access_token, { expires: expiresIn })
    Cookies.set(this.userKey, JSON.stringify(authData.user), { expires: expiresIn })
  }

  clearAuth() {
    Cookies.remove(this.tokenKey)
    Cookies.remove(this.userKey)
  }

  isAuthenticated(): boolean {
    return !!this.getToken()
  }

  isAdmin(): boolean {
    const user = this.getUser()
    return user?.role === 'admin'
  }

  async requestLogin(telegramId: number): Promise<{ magic_link: string }> {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ telegram_id: telegramId }),
    })

    if (!response.ok) {
      throw new Error('Login request failed')
    }

    return response.json()
  }

  async verifyMagicLink(token: string): Promise<AuthResponse> {
    const response = await fetch(`/api/auth/magic-link?token=${token}`)

    if (!response.ok) {
      throw new Error('Magic link verification failed')
    }

    const authData: AuthResponse = await response.json()
    this.setAuth(authData)
    return authData
  }

  getAuthHeaders(): HeadersInit {
    const token = this.getToken()
    return token ? { Authorization: `Bearer ${token}` } : {}
  }
}

export const authService = new AuthService()