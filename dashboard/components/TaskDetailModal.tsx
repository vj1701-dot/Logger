'use client'

import { useState } from 'react'
import { format } from 'date-fns'
import { 
  X, 
  User, 
  Clock, 
  MessageSquare, 
  Paperclip,
  Edit3,
  Save,
  Plus,
  Trash2
} from 'lucide-react'
import { Task, apiService } from '../lib/api'
import { User as AuthUser } from '../lib/auth'

interface TaskDetailModalProps {
  task: Task
  user: AuthUser
  onClose: () => void
  onUpdate: () => void
}

export function TaskDetailModal({ task, user, onClose, onUpdate }: TaskDetailModalProps) {
  const [editing, setEditing] = useState(false)
  const [loading, setLoading] = useState(false)
  const [editData, setEditData] = useState({
    title: task.title,
    description: task.description,
    priority: task.priority
  })
  const [newNote, setNewNote] = useState('')

  const isAdmin = user.role === 'admin'

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

  const handleSave = async () => {
    if (!isAdmin) return

    try {
      setLoading(true)
      await apiService.updateTask(task.uid, editData)
      setEditing(false)
      onUpdate()
    } catch (error) {
      console.error('Failed to update task:', error)
      alert('Failed to update task')
    } finally {
      setLoading(false)
    }
  }

  const handleStatusChange = async (newStatus: string) => {
    if (!isAdmin) return

    try {
      setLoading(true)
      let reason
      if (newStatus === 'on_hold') {
        reason = prompt('Please provide a reason for putting this task on hold:')
        if (!reason) return
      }
      
      await apiService.changeTaskStatus(task.uid, newStatus, reason)
      onUpdate()
    } catch (error) {
      console.error('Failed to change status:', error)
      alert('Failed to change status')
    } finally {
      setLoading(false)
    }
  }

  const handleAddNote = async () => {
    if (!newNote.trim() || !isAdmin) return

    try {
      setLoading(true)
      await apiService.addTaskNote(task.uid, newNote)
      setNewNote('')
      onUpdate()
    } catch (error) {
      console.error('Failed to add note:', error)
      alert('Failed to add note')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center space-x-3">
            <span className="text-sm font-mono bg-gray-100 text-gray-700 px-2 py-1 rounded">
              {task.uid}
            </span>
            <span className={getStatusStyle(task.status)}>
              {formatStatus(task.status)}
            </span>
          </div>
          
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* Title and Description */}
          <div>
            {editing ? (
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Title
                  </label>
                  <input
                    type="text"
                    value={editData.title}
                    onChange={(e) => setEditData({...editData, title: e.target.value})}
                    className="input"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Description
                  </label>
                  <textarea
                    value={editData.description}
                    onChange={(e) => setEditData({...editData, description: e.target.value})}
                    rows={4}
                    className="input"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Priority
                  </label>
                  <select
                    value={editData.priority}
                    onChange={(e) => setEditData({...editData, priority: e.target.value as any})}
                    className="input"
                  >
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="urgent">Urgent</option>
                  </select>
                </div>
                
                <div className="flex space-x-2">
                  <button
                    onClick={handleSave}
                    disabled={loading}
                    className="btn btn-primary"
                  >
                    <Save className="w-4 h-4 mr-2" />
                    Save Changes
                  </button>
                  <button
                    onClick={() => setEditing(false)}
                    className="btn btn-secondary"
                  >
                    Cancel
                  </button>
                </div>
              </div>
            ) : (
              <div>
                <div className="flex items-center justify-between mb-2">
                  <h2 className="text-xl font-semibold text-gray-900">
                    {task.title}
                  </h2>
                  {isAdmin && (
                    <button
                      onClick={() => setEditing(true)}
                      className="btn btn-secondary btn-sm"
                    >
                      <Edit3 className="w-4 h-4 mr-1" />
                      Edit
                    </button>
                  )}
                </div>
                <p className="text-gray-600 mb-4">{task.description}</p>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Priority:</span>
                    <div className={`capitalize font-medium ${
                      task.priority === 'urgent' ? 'text-red-600' :
                      task.priority === 'high' ? 'text-orange-600' :
                      task.priority === 'medium' ? 'text-blue-600' : 'text-gray-600'
                    }`}>
                      {task.priority}
                    </div>
                  </div>
                  <div>
                    <span className="text-gray-500">Created:</span>
                    <div>{format(new Date(task.timestamps.createdAt), 'MMM d, yyyy')}</div>
                  </div>
                  <div>
                    <span className="text-gray-500">Updated:</span>
                    <div>{format(new Date(task.timestamps.updatedAt), 'MMM d, HH:mm')}</div>
                  </div>
                  <div>
                    <span className="text-gray-500">Created by:</span>
                    <div>{task.createdBy?.name || 'Unknown'}</div>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Status Actions */}
          {isAdmin && !editing && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Change Status</h3>
              <div className="flex flex-wrap gap-2">
                {['new', 'in_progress', 'on_hold', 'done_pending_review', 'done', 'canceled'].map(status => (
                  <button
                    key={status}
                    onClick={() => handleStatusChange(status)}
                    disabled={loading || status === task.status}
                    className={`btn btn-sm ${
                      status === task.status ? 'btn-primary' : 'btn-secondary'
                    }`}
                  >
                    {formatStatus(status)}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Assignees */}
          {task.assignees.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Assignees</h3>
              <div className="flex flex-wrap gap-2">
                {task.assignees.map(assignee => (
                  <div
                    key={assignee.telegramId}
                    className="flex items-center space-x-2 bg-blue-50 text-blue-800 px-3 py-1 rounded-full text-sm"
                  >
                    <User className="w-3 h-3" />
                    <span>{assignee.name}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Media */}
          {task.media.length > 0 && (
            <div>
              <h3 className="text-sm font-medium text-gray-700 mb-2">Media Files</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                {task.media.map((media, index) => (
                  <div key={index} className="border border-gray-200 rounded-lg p-2">
                    {media.type === 'photo' ? (
                      <img
                        src={`/api/media/${task.uid}/${media.metadata.filename}`}
                        alt="Task media"
                        className="w-full h-32 object-cover rounded"
                      />
                    ) : (
                      <div className="flex items-center justify-center h-32 bg-gray-50 rounded">
                        <Paperclip className="w-8 h-8 text-gray-400" />
                      </div>
                    )}
                    <div className="mt-2 text-xs text-gray-600 truncate">
                      {media.metadata.filename}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Notes */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-700">
                Notes ({task.notes.length})
              </h3>
            </div>
            
            {/* Add Note (Admin only) */}
            {isAdmin && (
              <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                <textarea
                  value={newNote}
                  onChange={(e) => setNewNote(e.target.value)}
                  placeholder="Add a note..."
                  rows={2}
                  className="input mb-2"
                />
                <button
                  onClick={handleAddNote}
                  disabled={loading || !newNote.trim()}
                  className="btn btn-primary btn-sm"
                >
                  <Plus className="w-4 h-4 mr-1" />
                  Add Note
                </button>
              </div>
            )}
            
            {/* Notes List */}
            <div className="space-y-3">
              {task.notes.length === 0 ? (
                <div className="text-gray-500 text-sm">No notes yet</div>
              ) : (
                task.notes.map(note => (
                  <div key={note.id} className="border border-gray-200 rounded-lg p-3">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <User className="w-4 h-4 text-gray-400" />
                        <span className="text-sm font-medium">{note.author.name}</span>
                      </div>
                      <div className="flex items-center text-xs text-gray-500">
                        <Clock className="w-3 h-3 mr-1" />
                        {format(new Date(note.createdAt), 'MMM d, HH:mm')}
                      </div>
                    </div>
                    <p className="text-sm text-gray-600">{note.content}</p>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}