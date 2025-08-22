'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { authService } from '../../lib/auth'
import { LoadingSpinner } from '../../components/LoadingSpinner'

export default function LoginPage() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [telegramId, setTelegramId] = useState('')
  const [loading, setLoading] = useState(false)
  const [message, setMessage] = useState('')

  useEffect(() => {
    // Check if already authenticated
    if (authService.isAuthenticated()) {
      router.push('/')
      return
    }

    // Check for magic link token
    const token = searchParams.get('token')
    if (token) {
      handleMagicLinkVerification(token)
    }
  }, [router, searchParams])

  const handleMagicLinkVerification = async (token: string) => {
    try {
      setLoading(true)
      await authService.verifyMagicLink(token)
      router.push('/')
    } catch (error) {
      setMessage('Invalid or expired magic link. Please request a new one.')
    } finally {
      setLoading(false)
    }
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!telegramId) {
      setMessage('Please enter your Telegram ID')
      return
    }

    try {
      setLoading(true)
      setMessage('')
      
      const response = await authService.requestLogin(parseInt(telegramId))
      setMessage(
        `Magic link sent! Please check your Telegram for a login link. ` +
        `The link will expire in ${10} minutes.`
      )
      
      // For development, you could show the magic link
      if (process.env.NODE_ENV === 'development') {
        console.log('Magic link:', response.magic_link)
      }
      
    } catch (error) {
      setMessage('Failed to send magic link. Please check your Telegram ID and try again.')
    } finally {
      setLoading(false)
    }
  }

  if (loading && !message) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <LoadingSpinner />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Maintenance Task System
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Sign in with your Telegram account
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleLogin}>
          <div>
            <label htmlFor="telegram-id" className="block text-sm font-medium text-gray-700">
              Telegram ID
            </label>
            <input
              id="telegram-id"
              name="telegram-id"
              type="number"
              required
              value={telegramId}
              onChange={(e) => setTelegramId(e.target.value)}
              className="mt-1 input"
              placeholder="Enter your Telegram ID"
            />
            <p className="mt-1 text-xs text-gray-500">
              You can find your Telegram ID by messaging @userinfobot
            </p>
          </div>

          {message && (
            <div className={`p-3 rounded-md text-sm ${
              message.includes('Failed') || message.includes('Invalid') 
                ? 'bg-red-50 text-red-700' 
                : 'bg-green-50 text-green-700'
            }`}>
              {message}
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={loading}
              className="w-full btn btn-primary"
            >
              {loading ? 'Sending...' : 'Send Magic Link'}
            </button>
          </div>
        </form>

        <div className="text-center">
          <div className="text-sm text-gray-600">
            <p>How it works:</p>
            <ol className="mt-2 text-xs text-gray-500 space-y-1">
              <li>1. Enter your Telegram ID</li>
              <li>2. Check your Telegram for a login link</li>
              <li>3. Click the link to access the dashboard</li>
            </ol>
          </div>
        </div>
      </div>
    </div>
  )
}