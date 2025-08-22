'use client'

import { useState, useEffect } from 'react'
import { Search, RefreshCw, Filter } from 'lucide-react'
import { apiService } from '../lib/api'

interface TaskFiltersProps {
  filters: {
    status: string
    assignee: string
    search: string
    hasMedia: boolean
  }
  setFilters: (filters: any) => void
  onRefresh: () => void
}

export function TaskFilters({ filters, setFilters, onRefresh }: TaskFiltersProps) {
  const [users, setUsers] = useState<any[]>([])
  const [showFilters, setShowFilters] = useState(false)

  useEffect(() => {
    loadUsers()
  }, [])

  const loadUsers = async () => {
    try {
      const userList = await apiService.getUsers()
      setUsers(userList.filter(u => u.active))
    } catch (error) {
      console.error('Failed to load users:', error)
    }
  }

  const statusOptions = [
    { value: '', label: 'All Statuses' },
    { value: 'new', label: 'New' },
    { value: 'in_progress', label: 'In Progress' },
    { value: 'on_hold', label: 'On Hold' },
    { value: 'done_pending_review', label: 'Pending Review' },
    { value: 'done', label: 'Done' },
    { value: 'canceled', label: 'Canceled' }
  ]

  const handleFilterChange = (key: string, value: any) => {
    setFilters({ ...filters, [key]: value })
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <div className="flex-1 max-w-lg">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search tasks by UID, title, or description..."
              value={filters.search}
              onChange={(e) => handleFilterChange('search', e.target.value)}
              className="pl-10 input"
            />
          </div>
        </div>

        <div className="flex items-center space-x-3">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`btn ${showFilters ? 'btn-primary' : 'btn-secondary'}`}
          >
            <Filter className="w-4 h-4 mr-2" />
            Filters
          </button>
          
          <button
            onClick={onRefresh}
            className="btn btn-secondary"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </button>
        </div>
      </div>

      {showFilters && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Status
              </label>
              <select
                value={filters.status}
                onChange={(e) => handleFilterChange('status', e.target.value)}
                className="input"
              >
                {statusOptions.map(option => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Assignee
              </label>
              <select
                value={filters.assignee}
                onChange={(e) => handleFilterChange('assignee', e.target.value)}
                className="input"
              >
                <option value="">All Assignees</option>
                {users.map(user => (
                  <option key={user.telegramId} value={user.telegramId}>
                    {user.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Media Filter
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={filters.hasMedia}
                  onChange={(e) => handleFilterChange('hasMedia', e.target.checked)}
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-gray-600">Has media</span>
              </label>
            </div>

            <div className="flex items-end">
              <button
                onClick={() => setFilters({ status: '', assignee: '', search: '', hasMedia: false })}
                className="btn btn-secondary w-full"
              >
                Clear Filters
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}