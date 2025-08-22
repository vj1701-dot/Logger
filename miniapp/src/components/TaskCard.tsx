import { format } from 'date-fns'
import { Clock, User, Paperclip, MessageSquare, AlertCircle } from 'lucide-react'
import { Task } from '../App'

interface TaskCardProps {
  task: Task
  onClick: () => void
}

export function TaskCard({ task, onClick }: TaskCardProps) {
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
    <div 
      className="tg-card cursor-pointer active:opacity-80 transition-opacity"
      onClick={onClick}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="flex items-center space-x-2 mb-2">
            <span 
              className="text-xs font-mono px-2 py-1 rounded"
              style={{
                backgroundColor: 'var(--tg-theme-hint-color, #e5e7eb)',
                color: 'var(--tg-theme-text-color, #000000)'
              }}
            >
              {task.uid}
            </span>
            <span className={`priority-indicator ${getPriorityColor(task.priority)}`}>
              <AlertCircle className="w-3 h-3" />
            </span>
          </div>
          <h3 className="font-medium mb-2 line-clamp-2" style={{ color: 'var(--tg-theme-text-color, #000000)' }}>
            {task.title}
          </h3>
          <p className="text-sm tg-hint line-clamp-2 mb-3">
            {task.description}
          </p>
        </div>
      </div>

      <div className="flex items-center justify-between mb-3">
        <span className={getStatusStyle(task.status)}>
          {formatStatus(task.status)}
        </span>
        <div className="flex items-center space-x-3 text-xs tg-hint">
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
            loading="lazy"
          />
        </div>
      )}

      {task.assignees.length > 0 && (
        <div className="mb-3">
          <div className="text-xs tg-hint mb-1">Assignees:</div>
          <div className="flex flex-wrap gap-1">
            {task.assignees.slice(0, 3).map((assignee, index) => (
              <span
                key={assignee.telegramId}
                className="text-xs px-2 py-1 rounded-full"
                style={{
                  backgroundColor: 'var(--tg-theme-button-color, #3b82f6)',
                  color: 'var(--tg-theme-button-text-color, #ffffff)'
                }}
              >
                {assignee.name}
              </span>
            ))}
            {task.assignees.length > 3 && (
              <span 
                className="text-xs px-2 py-1 rounded-full"
                style={{
                  backgroundColor: 'var(--tg-theme-hint-color, #e5e7eb)',
                  color: 'var(--tg-theme-text-color, #000000)'
                }}
              >
                +{task.assignees.length - 3} more
              </span>
            )}
          </div>
        </div>
      )}

      <div className="flex items-center justify-between text-xs tg-hint">
        <div className="flex items-center">
          <Clock className="w-3 h-3 mr-1" />
          <span>{format(new Date(task.timestamps.updatedAt), 'MMM d, HH:mm')}</span>
        </div>
        
        {task.createdBy && (
          <span>by {task.createdBy.name}</span>
        )}
      </div>
    </div>
  )
}