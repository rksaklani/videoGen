import { FiZap, FiMenu, FiX } from 'react-icons/fi'
import { useState } from 'react'

export default function Navbar({ activePage, onNavigate, health }) {
  const [mobileOpen, setMobileOpen] = useState(false)
  const isReady = health?.engine_loaded
  const isBusy = health?.gpu?.gpu_busy

  const links = [
    { id: 'create', label: 'Create', icon: '🎬' },
    { id: 'templates', label: 'Templates', icon: '🖼️' },
    { id: 'history', label: 'History', icon: '📋' },
  ]

  return (
    <nav className="glass-strong sticky top-0 z-50 border-b border-white/40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center gap-2.5 cursor-pointer" onClick={() => onNavigate('create')}>
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-purple-500 flex items-center justify-center shadow-lg shadow-brand-500/20">
              <FiZap className="w-5 h-5 text-white" />
            </div>
            <span className="text-lg font-bold gradient-text">videoGen</span>
          </div>

          {/* Desktop Nav */}
          <div className="hidden md:flex items-center gap-1">
            {links.map((link) => (
              <button
                key={link.id}
                onClick={() => onNavigate(link.id)}
                className={`px-4 py-2 rounded-xl text-sm font-medium transition-all
                  ${activePage === link.id
                    ? 'bg-brand-500 text-white shadow-lg shadow-brand-500/25'
                    : 'text-gray-600 hover:bg-white/60 hover:text-gray-900'}`}
              >
                <span className="mr-1.5">{link.icon}</span>
                {link.label}
              </button>
            ))}
          </div>

          {/* Status + Mobile Toggle */}
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2 px-3 py-1.5 rounded-full glass-card text-xs font-medium">
              <span className={`w-2 h-2 rounded-full ${isReady ? (isBusy ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400 animate-pulse-ring') : 'bg-red-400'}`} />
              <span className={isReady ? (isBusy ? 'text-amber-700' : 'text-emerald-700') : 'text-red-600'}>
                {isReady ? (isBusy ? 'Processing' : 'Ready') : 'Loading...'}
              </span>
            </div>
            <button className="md:hidden p-2" onClick={() => setMobileOpen(!mobileOpen)}>
              {mobileOpen ? <FiX className="w-5 h-5" /> : <FiMenu className="w-5 h-5" />}
            </button>
          </div>
        </div>

        {/* Mobile Nav */}
        {mobileOpen && (
          <div className="md:hidden pb-4 space-y-1 animate-fade-up">
            {links.map((link) => (
              <button
                key={link.id}
                onClick={() => { onNavigate(link.id); setMobileOpen(false); }}
                className={`w-full text-left px-4 py-2.5 rounded-xl text-sm font-medium transition-all
                  ${activePage === link.id ? 'bg-brand-500 text-white' : 'text-gray-600 hover:bg-white/60'}`}
              >
                <span className="mr-2">{link.icon}</span>{link.label}
              </button>
            ))}
          </div>
        )}
      </div>
    </nav>
  )
}
