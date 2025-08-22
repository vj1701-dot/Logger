import { useState, useEffect } from 'react'
import { TaskList } from './components/TaskList'
import { TaskDetail } from './components/TaskDetail'
import { TelegramService } from './services/telegram'
import { ApiService } from './services/api'

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

function App() {
  const [tasks, setTasks] = useState<Task[]>([])
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    initializeApp()
  }, [])

  const initializeApp = async () => {
    try {
      // Authenticate with Telegram
      const telegramUser = TelegramService.getUser()
      if (!telegramUser) {
        setError('Telegram authentication required')
        return
      }

      // Get JWT token
      const token = await TelegramService.authenticate()
      if (!token) {
        setError('Authentication failed')
        return
      }

      // Set up API service
      ApiService.setToken(token)
      setUser(telegramUser)

      // Load tasks
      await loadTasks()
    } catch (err) {
      setError('Failed to initialize app')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const loadTasks = async () => {
    try {
      // Load tasks assigned to current user by default
      const response = await ApiService.getTasks({ 
        assignee_id: user?.id,
        limit: 50 
      })
      setTasks(response.tasks)
    } catch (err) {
      console.error('Failed to load tasks:', err)
      setError('Failed to load tasks')
    }
  }

  const handleTaskSelect = (task: Task) => {
    setSelectedTask(task)
  }

  const handleBack = () => {
    setSelectedTask(null)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: 'var(--tg-theme-bg-color, #ffffff)' }}>
        <div className="animate-spin rounded-full h-8 w-8 border-b-2" style={{ borderColor: 'var(--tg-theme-button-color, #3b82f6)' }}></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4" style={{ backgroundColor: 'var(--tg-theme-bg-color, #ffffff)' }}>
        <div className="text-center">
          <div className="text-red-600 mb-2">⚠️ Error</div>
          <div style={{ color: 'var(--tg-theme-text-color, #000000)' }}>{error}</div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--tg-theme-bg-color, #ffffff)', color: 'var(--tg-theme-text-color, #000000)' }}>
      {selectedTask ? (
        <TaskDetail task={selectedTask} onBack={handleBack} />
      ) : (
        <TaskList 
          tasks={tasks} 
          onTaskSelect={handleTaskSelect}
          onRefresh={loadTasks}
          user={user}
        />
      )}
    </div>
  )
}

export default App