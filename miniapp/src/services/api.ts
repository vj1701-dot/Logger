export interface Task {
  uid: string
  title: string
  description: string
  status: string
  priority: string
  createdBy?: any
  assignees: any[]
  notes: any[]
  media: any[]
  statusHistory: any[]
  onHoldReason?: string
  timestamps: {
    createdAt: string
    updatedAt: string
  }
}

export class ApiService {
  private static baseUrl = window.location.origin
  private static token: string | null = null

  static setToken(token: string) {
    this.token = token
  }

  private static async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}/api${endpoint}`
    const headers = {
      'Content-Type': 'application/json',
      ...(this.token && { Authorization: `Bearer ${this.token}` }),
      ...options.headers,
    }

    const response = await fetch(url, {
      ...options,
      headers,
    })

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`)
    }

    return response.json()
  }

  static async getTasks(params?: {
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

  static async getTask(uid: string): Promise<Task> {
    return this.request<Task>(`/tasks/${uid}`)
  }

  static getMediaUrl(uid: string, filename: string): string {
    return `${this.baseUrl}/api/media/${uid}/${filename}${this.token ? `?token=${this.token}` : ''}`
  }
}