import { authService } from './auth'

export interface Task {
  uid: string
  title: string
  description: string
  status: 'new' | 'in_progress' | 'on_hold' | 'canceled' | 'done_pending_review' | 'done'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  createdBy?: {
    telegramId: number
    name: string
    username?: string
  }
  assignees: Array<{
    telegramId: number
    name: string
    username?: string
  }>
  notes: Array<{
    id: string
    content: string
    author: {
      telegramId: number
      name: string
      username?: string
    }
    createdAt: string
    media?: any
  }>
  media: Array<{
    type: string
    path: string
    metadata: any
    deleteAfter?: string
  }>
  statusHistory: Array<{
    fromStatus?: string
    toStatus: string
    changedBy: {
      telegramId: number
      name: string
      username?: string
    }
    changedAt: string
    reason?: string
  }>
  onHoldReason?: string
  timestamps: {
    createdAt: string
    updatedAt: string
  }
}

export interface User {
  telegramId: number
  name: string
  username?: string
  role: 'user' | 'admin'
  active: boolean
  lastSeenAt?: string
  createdAt: string
}

class ApiService {
  private baseUrl = process.env.API_BASE_URL || ''

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}/api${endpoint}`
    const headers = {
      'Content-Type': 'application/json',
      ...authService.getAuthHeaders(),
      ...options.headers,
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      if (response.status === 401) {
        authService.clearAuth()
        window.location.href = '/login'
        throw new Error('Unauthorized')
      }
      throw new Error(`API Error: ${response.statusText}`)
    }

    return response.json()
  }

  // Task endpoints
  async getTasks(params?: {
    status?: string
    assignee_id?: number
    search?: string
    limit?: number
  }): Promise<{ tasks: Task[]; total: number }> {
    const searchParams = new URLSearchParams()
    if (params?.status) searchParams.set('status', params.status)
    if (params?.assignee_id) searchParams.set('assignee_id', params.assignee_id.toString())
    if (params?.search) searchParams.set('search', params.search)
    if (params?.limit) searchParams.set('limit', params.limit.toString())

    const endpoint = `/tasks${searchParams.toString() ? `?${searchParams.toString()}` : ''}`
    return this.request<{ tasks: Task[]; total: number }>(endpoint)
  }

  async getTask(uid: string): Promise<Task> {
    return this.request<Task>(`/tasks/${uid}`)
  }

  async updateTask(uid: string, updates: Partial<Task>): Promise<Task> {
    return this.request<Task>(`/tasks/${uid}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    })
  }

  async changeTaskStatus(uid: string, status: string, reason?: string): Promise<void> {
    await this.request(`/tasks/${uid}/status`, {
      method: 'POST',
      body: JSON.stringify({ status, reason }),
    })
  }

  async manageAssignee(uid: string, telegramId: number, action: 'add' | 'remove'): Promise<void> {
    await this.request(`/tasks/${uid}/assignees`, {
      method: 'POST',
      body: JSON.stringify({ telegram_id: telegramId, action }),
    })
  }

  async addTaskNote(uid: string, content: string): Promise<void> {
    await this.request(`/tasks/${uid}/note`, {
      method: 'POST',
      body: JSON.stringify({ content }),
    })
  }

  // User endpoints
  async getUsers(): Promise<User[]> {
    return this.request<User[]>('/users')
  }

  async updateUser(telegramId: number, updates: Partial<User>): Promise<User> {
    return this.request<User>(`/users/${telegramId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    })
  }

  async createUser(userData: {
    telegram_id: number
    name: string
    username?: string
    role?: string
  }): Promise<User> {
    return this.request<User>('/users', {
      method: 'POST',
      body: JSON.stringify(userData),
    })
  }

  async exportUsers(): Promise<Blob> {
    const response = await fetch(`${this.baseUrl}/api/users/export`, {
      headers: authService.getAuthHeaders(),
    })

    if (!response.ok) {
      throw new Error('Export failed')
    }

    return response.blob()
  }

  // Media endpoints
  getMediaUrl(uid: string, filename: string): string {
    const token = authService.getToken()
    return `${this.baseUrl}/api/media/${uid}/${filename}?token=${token}`
  }

  async deleteMedia(uid: string, filename: string): Promise<void> {
    await this.request(`/media/${uid}/${filename}`, {
      method: 'DELETE',
    })
  }
}

export const apiService = new ApiService()