import { useEffect, useState } from 'react'
import { format } from 'date-fns'
import { 
  ArrowLeft, 
  User, 
  Clock, 
  MessageSquare, 
  Paperclip,
  AlertCircle 
} from 'lucide-react'
import { Task } from '../App'
import { TelegramService } from '../services/telegram'
import { ApiService } from '../services/api'

interface TaskDetailProps {
  task: Task
  onBack: () => void
}

export function TaskDetail({ task, onBack }: TaskDetailProps) {
  const [fullTask, setFullTask] = useState<Task>(task)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    TelegramService.setBackButton(onBack)
    loadFullTask()

    return () => {
      TelegramService.hideBackButton()
    }
  }, [onBack])

  const loadFullTask = async () => {
    try {
      setLoading(true)
      const taskData = await ApiService.getTask(task.uid)
      setFullTask(taskData)
    } catch (error) {
      console.error('Failed to load full task:', error)
    } finally {
      setLoading(false)
    }
  }

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

  const formatStatus = (status: string) => {
    return status.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
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

  return (
    <div className="min-h-screen" style={{ backgroundColor: 'var(--tg-theme-bg-color, #ffffff)' }}>
      {/* Header */}
      <div className="sticky top-0 z-10 p-4 border-b" style={{ 
        backgroundColor: 'var(--tg-theme-bg-color, #ffffff)',
        borderColor: 'var(--tg-theme-hint-color, #e5e7eb)'
      }}>
        <div className="flex items-center space-x-3">
          <button
            onClick={onBack}
            className="p-2 rounded-lg"
            style={{
              backgroundColor: 'var(--tg-theme-secondary-bg-color, #f8f9fa)',
              color: 'var(--tg-theme-text-color, #000000)'
            }}
          >
            <ArrowLeft className="w-4 h-4" />
          </button>
          
          <div className="flex items-center space-x-2">
            <span 
              className="text-sm font-mono px-2 py-1 rounded"
              style={{
                backgroundColor: 'var(--tg-theme-hint-color, #e5e7eb)',
                color: 'var(--tg-theme-text-color, #000000)'
              }}
            >
              {fullTask.uid}
            </span>
            <span className={getStatusStyle(fullTask.status)}>
              {formatStatus(fullTask.status)}
            </span>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-6">
        {/* Title and Description */}
        <div>
          <div className="flex items-center space-x-2 mb-2">
            <h1 className="text-xl font-semibold" style={{ color: 'var(--tg-theme-text-color, #000000)' }}>
              {fullTask.title}
            </h1>
            <span className={`${getPriorityColor(fullTask.priority)}`}>
              <AlertCircle className="w-4 h-4" />
            </span>
          </div>
          <p className="tg-hint mb-4">{fullTask.description}</p>
          
          <div className="grid grid-cols-2 gap-4 text-sm">
            <div>
              <span className="tg-hint">Priority:</span>
              <div className={`capitalize font-medium ${getPriorityColor(fullTask.priority)}`}>
                {fullTask.priority}
              </div>
            </div>
            <div>
              <span className="tg-hint">Created:</span>
              <div style={{ color: 'var(--tg-theme-text-color, #000000)' }}>
                {format(new Date(fullTask.timestamps.createdAt), 'MMM d, yyyy')}
              </div>
            </div>
            <div>
              <span className="tg-hint">Updated:</span>
              <div style={{ color: 'var(--tg-theme-text-color, #000000)' }}>
                {format(new Date(fullTask.timestamps.updatedAt), 'MMM d, HH:mm')}
              </div>
            </div>
            <div>
              <span className="tg-hint">Created by:</span>
              <div style={{ color: 'var(--tg-theme-text-color, #000000)' }}>
                {fullTask.createdBy?.name || 'Unknown'}
              </div>
            </div>
          </div>
        </div>

        {/* On Hold Reason */}
        {fullTask.onHoldReason && (
          <div className="tg-card">
            <div className="flex items-center space-x-2 mb-2">
              <AlertCircle className="w-4 h-4 text-yellow-600" />
              <span className="font-medium" style={{ color: 'var(--tg-theme-text-color, #000000)' }}>
                On Hold Reason
              </span>
            </div>
            <p className="tg-hint">{fullTask.onHoldReason}</p>
          </div>
        )}

        {/* Assignees */}
        {fullTask.assignees.length > 0 && (
          <div>
            <h3 className="text-sm font-medium mb-2" style={{ color: 'var(--tg-theme-text-color, #000000)' }}>
              Assignees
            </h3>
            <div className="flex flex-wrap gap-2">
              {fullTask.assignees.map(assignee => (
                <div
                  key={assignee.telegramId}
                  className="flex items-center space-x-2 px-3 py-1 rounded-full text-sm"
                  style={{
                    backgroundColor: 'var(--tg-theme-button-color, #3b82f6)',
                    color: 'var(--tg-theme-button-text-color, #ffffff)'
                  }}
                >
                  <User className="w-3 h-3" />
                  <span>{assignee.name}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Media */}
        {fullTask.media.length > 0 && (
          <div>
            <h3 className="text-sm font-medium mb-2" style={{ color: 'var(--tg-theme-text-color, #000000)' }}>
              Media Files ({fullTask.media.length})
            </h3>
            <div className="grid grid-cols-2 gap-2">
              {fullTask.media.map((media, index) => (
                <div key={index} className="tg-card">
                  {media.type === 'photo' ? (
                    <img
                      src={ApiService.getMediaUrl(fullTask.uid, media.metadata.filename)}
                      alt="Task media"
                      className="w-full h-32 object-cover rounded"
                      loading="lazy"
                    />
                  ) : (
                    <div className="flex items-center justify-center h-32 rounded" style={{
                      backgroundColor: 'var(--tg-theme-hint-color, #e5e7eb)'
                    }}>
                      <Paperclip className="w-8 h-8 tg-hint" />
                    </div>
                  )}
                  <div className="mt-2 text-xs tg-hint truncate">
                    {media.metadata.filename}
                  </div>
                  {media.deleteAfter && (
                    <div className="text-xs text-red-500 mt-1">
                      Deletes: {format(new Date(media.deleteAfter), 'MMM d, yyyy')}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Notes */}
        <div>
          <h3 className="text-sm font-medium mb-2" style={{ color: 'var(--tg-theme-text-color, #000000)' }}>
            Notes ({fullTask.notes.length})
          </h3>
          
          {fullTask.notes.length === 0 ? (
            <div className="tg-hint text-sm">No notes yet</div>
          ) : (
            <div className="space-y-3">
              {fullTask.notes.map(note => (
                <div key={note.id} className="tg-card">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <User className="w-4 h-4 tg-hint" />
                      <span className="text-sm font-medium" style={{ color: 'var(--tg-theme-text-color, #000000)' }}>
                        {note.author.name}
                      </span>
                    </div>
                    <div className="flex items-center text-xs tg-hint">
                      <Clock className="w-3 h-3 mr-1" />
                      {format(new Date(note.createdAt), 'MMM d, HH:mm')}
                    </div>
                  </div>
                  <p className="text-sm tg-hint">{note.content}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Status History */}
        {fullTask.statusHistory.length > 0 && (
          <div>
            <h3 className="text-sm font-medium mb-2" style={{ color: 'var(--tg-theme-text-color, #000000)' }}>
              Status History
            </h3>
            <div className="space-y-2">
              {fullTask.statusHistory.slice(0, 5).map((entry, index) => (
                <div key={index} className="flex items-center justify-between text-sm">
                  <div>
                    <span className="tg-hint">
                      {entry.fromStatus ? formatStatus(entry.fromStatus) : 'Created'} → {formatStatus(entry.toStatus)}
                    </span>
                    <div className="text-xs tg-hint">by {entry.changedBy.name}</div>
                  </div>
                  <div className="text-xs tg-hint">
                    {format(new Date(entry.changedAt), 'MMM d, HH:mm')}
                  </div>
                </div>
              ))}
              {fullTask.statusHistory.length > 5 && (
                <div className="text-xs tg-hint text-center">
                  +{fullTask.statusHistory.length - 5} more entries
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}