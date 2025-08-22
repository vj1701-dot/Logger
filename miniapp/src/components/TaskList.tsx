import { useState } from 'react'
import { RefreshCw, Search, Filter } from 'lucide-react'
import { Task } from '../App'
import { TaskCard } from './TaskCard'

interface TaskListProps {
  tasks: Task[]
  onTaskSelect: (task: Task) => void
  onRefresh: () => void
  user: any
}

export function TaskList({ tasks, onTaskSelect, onRefresh, user }: TaskListProps) {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [showFilters, setShowFilters] = useState(false)

  const filteredTasks = tasks.filter(task => {
    const matchesSearch = !searchTerm || 
      task.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      task.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
      task.uid.toLowerCase().includes(searchTerm.toLowerCase())
    
    const matchesStatus = !statusFilter || task.status === statusFilter
    
    return matchesSearch && matchesStatus
  })

  const statusOptions = [
    { value: '', label: 'All' },
    { value: 'new', label: 'New' },
    { value: 'in_progress', label: 'In Progress' },
    { value: 'on_hold', label: 'On Hold' },
    { value: 'done_pending_review', label: 'Pending Review' },
    { value: 'done', label: 'Done' },
    { value: 'canceled', label: 'Canceled' }
  ]

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--tg-theme-bg-color, #ffffff)' }}>
      {/* Header */}
      <div className="sticky top-0 z-10 p-4 border-b" style={{ 
        backgroundColor: 'var(--tg-theme-bg-color, #ffffff)',
        borderColor: 'var(--tg-theme-hint-color, #e5e7eb)'
      }}>
        <div className="flex items-center justify-between mb-3">
          <h1 className="text-lg font-semibold" style={{ color: 'var(--tg-theme-text-color, #000000)' }}>
            My Tasks
          </h1>
          <button
            onClick={onRefresh}
            className="p-2 rounded-lg tg-button"
          >
            <RefreshCw className="w-4 h-4" />
          </button>
        </div>

        {/* Search */}
        <div className="relative mb-3">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 tg-hint" />
          <input
            type="text"
            placeholder="Search tasks..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 rounded-lg border"
            style={{
              backgroundColor: 'var(--tg-theme-secondary-bg-color, #f8f9fa)',
              borderColor: 'var(--tg-theme-hint-color, #e5e7eb)',
              color: 'var(--tg-theme-text-color, #000000)'
            }}
          />
        </div>

        {/* Filter Toggle */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`flex items-center space-x-1 px-3 py-1 rounded-lg text-sm ${
              showFilters ? 'tg-button' : ''
            }`}
            style={!showFilters ? {
              backgroundColor: 'var(--tg-theme-secondary-bg-color, #f8f9fa)',
              color: 'var(--tg-theme-text-color, #000000)'
            } : {}}
          >
            <Filter className="w-3 h-3" />
            <span>Filter</span>
          </button>
          
          {statusFilter && (
            <span className="text-xs px-2 py-1 rounded-full" style={{
              backgroundColor: 'var(--tg-theme-button-color, #3b82f6)',
              color: 'var(--tg-theme-button-text-color, #ffffff)'
            }}>
              {statusOptions.find(opt => opt.value === statusFilter)?.label}
            </span>
          )}
        </div>

        {/* Status Filter */}
        {showFilters && (
          <div className="mt-3">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full px-3 py-2 rounded-lg border"
              style={{
                backgroundColor: 'var(--tg-theme-secondary-bg-color, #f8f9fa)',
                borderColor: 'var(--tg-theme-hint-color, #e5e7eb)',
                color: 'var(--tg-theme-text-color, #000000)'
              }}
            >
              {statusOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>

      {/* Task List */}
      <div className="p-4 space-y-3">
        {filteredTasks.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-lg tg-hint mb-2">No tasks found</div>
            <div className="text-sm tg-hint">
              {searchTerm || statusFilter ? 'Try adjusting your filters' : 'You have no assigned tasks'}
            </div>
          </div>
        ) : (
          filteredTasks.map((task) => (
            <TaskCard
              key={task.uid}
              task={task}
              onClick={() => onTaskSelect(task)}
            />
          ))
        )}
      </div>
    </div>
  )
}