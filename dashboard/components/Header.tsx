'use client'

import { User } from '../lib/auth'
import { Settings, LogOut, User as UserIcon } from 'lucide-react'

interface HeaderProps {
  user: User
  activeTab: 'tasks' | 'data'
  setActiveTab: (tab: 'tasks' | 'data') => void
  onLogout: () => void
}

export function Header({ user, activeTab, setActiveTab, onLogout }: HeaderProps) {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex items-center space-x-8">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-900">
                Maintenance System
              </h1>
            </div>
            
            <nav className="flex space-x-4">
              <button
                onClick={() => setActiveTab('tasks')}
                className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                  activeTab === 'tasks'
                    ? 'bg-primary-100 text-primary-700'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                }`}
              >
                Tasks
              </button>
              
              {user.role === 'admin' && (
                <button
                  onClick={() => setActiveTab('data')}
                  className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    activeTab === 'data'
                      ? 'bg-primary-100 text-primary-700'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                  }`}
                >
                  <Settings className="w-4 h-4 inline mr-1" />
                  Data Management
                </button>
              )}
            </nav>
          </div>

          <div className="flex items-center space-x-4">
            <div className="flex items-center space-x-2 text-sm text-gray-600">
              <UserIcon className="w-4 h-4" />
              <span>{user.name}</span>
              {user.role === 'admin' && (
                <span className="bg-primary-100 text-primary-800 px-2 py-1 rounded-full text-xs font-medium">
                  Admin
                </span>
              )}
            </div>
            
            <button
              onClick={onLogout}
              className="flex items-center space-x-1 text-gray-500 hover:text-gray-700 transition-colors"
              title="Logout"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>
    </header>
  )
}