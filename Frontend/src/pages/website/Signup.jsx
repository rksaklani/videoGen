import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { FiZap, FiMail, FiLock, FiUser } from 'react-icons/fi'

import { apiV1Base } from '../../config/env'

export default function Signup() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    try {
      const res = await fetch(`${apiV1Base}/auth/register`, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password }),
      })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Registration failed')
      localStorage.setItem('token', data.access_token)
      localStorage.setItem('user', JSON.stringify({ name: data.name, email: data.email }))
      // Check if user was trying to subscribe to a plan
      const pendingPlan = localStorage.getItem('pending_plan')
      if (pendingPlan) {
        localStorage.removeItem('pending_plan')
        navigate(`/pricing`)
      } else {
        navigate('/dashboard')
      }
    } catch (err) { setError(err.message) }
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center px-4">
      <div className="glass-card rounded-3xl p-8 w-full max-w-md">
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-brand-500 to-purple-500 flex items-center justify-center mx-auto mb-4 shadow-lg shadow-brand-500/20">
            <FiZap className="w-6 h-6 text-white" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Create your account</h1>
          <p className="text-gray-500 text-sm mt-1">Start creating avatar videos for free</p>
        </div>

        {error && <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-sm text-red-600">{error}</div>}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Name</label>
            <div className="relative">
              <FiUser className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} required placeholder="Your name"
                className="w-full pl-10 pr-4 py-2.5 glass rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
            <div className="relative">
              <FiMail className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="you@example.com"
                className="w-full pl-10 pr-4 py-2.5 glass rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Password</label>
            <div className="relative">
              <FiLock className="absolute left-3 top-3 w-4 h-4 text-gray-400" />
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={6} placeholder="Min 6 characters"
                className="w-full pl-10 pr-4 py-2.5 glass rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
          </div>
          <button type="submit"
            className="w-full py-3 bg-gradient-to-r from-brand-500 to-purple-500 text-white rounded-xl font-semibold shadow-lg shadow-brand-500/25 transition-all hover:shadow-brand-500/40">
            Create Account
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-6">
          Already have an account? <Link to="/login" className="text-brand-600 font-medium hover:underline">Log in</Link>
        </p>
      </div>
    </div>
  )
}
