'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { authService, User } from '../lib/auth'
import { apiService, Task } from '../lib/api'
import { TaskCard } from '../components/TaskCard'
import { TaskFilters } from '../components/TaskFilters'
import { DataManagement } from '../components/DataManagement'
import { Header } from '../components/Header'
import { LoadingSpinner } from '../components/LoadingSpinner'

export default function Dashboard() {
  const router = useRouter()
  const [user, setUser] = useState<User | null>(null)
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'tasks' | 'data'>('tasks')
  const [filters, setFilters] = useState({
    status: '',
    assignee: '',
    search: '',
    hasMedia: false
  })

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login')
      return
    }

    const userData = authService.getUser()
    setUser(userData)
    loadTasks()
  }, [router])

  const loadTasks = async () => {
    try {
      setLoading(true)
      const params: any = { limit: 100 }
      
      if (filters.status) params.status = filters.status
      if (filters.assignee) params.assignee_id = parseInt(filters.assignee)
      if (filters.search) params.search = filters.search

      const response = await apiService.getTasks(params)
      let filteredTasks = response.tasks

      // Client-side filter for media
      if (filters.hasMedia) {
        filteredTasks = filteredTasks.filter(task => task.media.length > 0)
      }

      setTasks(filteredTasks)
    } catch (error) {
      console.error('Failed to load tasks:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (user) {
      loadTasks()
    }
  }, [filters, user])

  const handleTaskUpdate = async (uid: string) => {
    // Reload tasks after update
    await loadTasks()
  }

  const handleLogout = () => {
    authService.clearAuth()
    router.push('/login')
  }

  if (loading && !user) {
    return <LoadingSpinner />
  }

  if (!user) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header 
        user={user} 
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onLogout={handleLogout}
      />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'tasks' && (
          <>
            <div className="mb-6">
              <h1 className="text-2xl font-bold text-gray-900 mb-4">
                Maintenance Tasks
              </h1>
              <TaskFilters 
                filters={filters}
                setFilters={setFilters}
                onRefresh={loadTasks}
              />
            </div>

            {loading ? (
              <LoadingSpinner />
            ) : (
              <div className="space-y-4">
                {tasks.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-gray-500 text-lg">No tasks found</div>
                    <div className="text-gray-400 text-sm mt-2">
                      Try adjusting your filters or create a new task via Telegram
                    </div>
                  </div>
                ) : (
                  <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                    {tasks.map((task) => (
                      <TaskCard 
                        key={task.uid} 
                        task={task} 
                        user={user}
                        onUpdate={() => handleTaskUpdate(task.uid)}
                      />
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}

        {activeTab === 'data' && user.role === 'admin' && (
          <DataManagement />
        )}
      </main>
    </div>
  )
}