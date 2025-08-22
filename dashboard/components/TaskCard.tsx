'use client'

import { useState } from 'react'
import { format } from 'date-fns'
import { 
  Clock, 
  User, 
  Paperclip, 
  MessageSquare, 
  MoreVertical,
  Edit3,
  UserPlus,
  FileText,
  AlertCircle
} from 'lucide-react'
import { Task } from '../lib/api'
import { User as AuthUser } from '../lib/auth'
import { TaskDetailModal } from './TaskDetailModal'

interface TaskCardProps {
  task: Task
  user: AuthUser
  onUpdate: () => void
}

export function TaskCard({ task, user, onUpdate }: TaskCardProps) {
  const [showDetail, setShowDetail] = useState(false)
  const [showActions, setShowActions] = useState(false)

  const getStatusStyle = (status: string) => {
    const statusMap: Record<string, string> = {
      'new': 'status-new',
      'in_progress': 'status-in-progress',
      'on_hold': 'status-on-hold',
      'done_pending_review': 'status-done-pending-review',
      'done': 'status-done',
      'canceled': 'status-canceled'
    }
    return statusMap[status] || 'status-new'
  }

  const getPriorityColor = (priority: string) => {
    const colorMap: Record<string, string> = {
      'low': 'text-gray-500',
      'medium': 'text-blue-500',
      'high': 'text-orange-500',
      'urgent': 'text-red-500'
    }
    return colorMap[priority] || 'text-gray-500'
  }

  const formatStatus = (status: string) => {
    return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
  }

  const firstMedia = task.media.length > 0 ? task.media[0] : null

  return (
    <>
      <div className="card p-4 hover:shadow-md transition-shadow cursor-pointer">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-xs font-mono bg-gray-100 text-gray-700 px-2 py-1 rounded">
                {task.uid}
              </span>
              <span className={`priority-indicator ${getPriorityColor(task.priority)}`}>
                <AlertCircle className="w-3 h-3" />
              </span>
            </div>
            <h3 
              className="font-medium text-gray-900 line-clamp-2 mb-2"
              onClick={() => setShowDetail(true)}
            >
              {task.title}
            </h3>
            <p 
              className="text-sm text-gray-600 line-clamp-2 mb-3"
              onClick={() => setShowDetail(true)}
            >
              {task.description}
            </p>
          </div>
          
          {user.role === 'admin' && (
            <div className="relative">
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  setShowActions(!showActions)
                }}
                className="p-1 text-gray-400 hover:text-gray-600 rounded"
              >
                <MoreVertical className="w-4 h-4" />
              </button>
              
              {showActions && (
                <div className="absolute right-0 top-8 bg-white shadow-lg border border-gray-200 rounded-lg py-1 z-10 min-w-32">
                  <button
                    onClick={() => {
                      setShowDetail(true)
                      setShowActions(false)
                    }}
                    className="w-full text-left px-3 py-2 text-sm text-gray-700 hover:bg-gray-50 flex items-center"
                  >
                    <Edit3 className="w-4 h-4 mr-2" />
                    Edit
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        <div className="flex items-center justify-between mb-3">
          <span className={getStatusStyle(task.status)}>
            {formatStatus(task.status)}
          </span>
          <div className="flex items-center space-x-3 text-xs text-gray-500">
            {task.assignees.length > 0 && (
              <div className="flex items-center">
                <User className="w-3 h-3 mr-1" />
                <span>{task.assignees.length}</span>
              </div>
            )}
            {task.media.length > 0 && (
              <div className="flex items-center">
                <Paperclip className="w-3 h-3 mr-1" />
                <span>{task.media.length}</span>
              </div>
            )}
            {task.notes.length > 0 && (
              <div className="flex items-center">
                <MessageSquare className="w-3 h-3 mr-1" />
                <span>{task.notes.length}</span>
              </div>
            )}
          </div>
        </div>

        {firstMedia && firstMedia.type === 'photo' && (
          <div className="mb-3">
            <img
              src={`/api/media/${task.uid}/${firstMedia.metadata.filename}`}
              alt="Task media"
              className="w-full h-32 object-cover rounded-lg"
              onClick={() => setShowDetail(true)}
            />
          </div>
        )}

        {task.assignees.length > 0 && (
          <div className="mb-3">
            <div className="text-xs text-gray-500 mb-1">Assignees:</div>
            <div className="flex flex-wrap gap-1">
              {task.assignees.slice(0, 3).map((assignee, index) => (
                <span
                  key={assignee.telegramId}
                  className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded-full"
                >
                  {assignee.name}
                </span>
              ))}
              {task.assignees.length > 3 && (
                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                  +{task.assignees.length - 3} more
                </span>
              )}
            </div>
          </div>
        )}

        <div className="flex items-center justify-between text-xs text-gray-500">
          <div className="flex items-center">
            <Clock className="w-3 h-3 mr-1" />
            <span>{format(new Date(task.timestamps.updatedAt), 'MMM d, HH:mm')}</span>
          </div>
          
          {task.createdBy && (
            <span>by {task.createdBy.name}</span>
          )}
        </div>
      </div>

      {showDetail && (
        <TaskDetailModal
          task={task}
          user={user}
          onClose={() => setShowDetail(false)}
          onUpdate={onUpdate}
        />
      )}
    </>
  )
}