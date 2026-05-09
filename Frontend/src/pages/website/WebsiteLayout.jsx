import { Link, Outlet, useLocation } from 'react-router-dom'
import { FiZap } from 'react-icons/fi'
import { useState } from 'react'
import { FiMenu, FiX } from 'react-icons/fi'

export default function WebsiteLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const location = useLocation()

  const navLink = (to, label) => (
    <Link key={to} to={to}
      className={`px-4 py-2 rounded-xl text-sm font-medium transition-all
        ${location.pathname === to ? 'text-brand-600 bg-brand-50' : 'text-gray-600 hover:text-gray-900 hover:bg-white/50'}`}>
      {label}
    </Link>
  )

  return (
    <div className="min-h-screen">
      {/* Navbar */}
      <nav className="glass-strong sticky top-0 z-50 border-b border-white/40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-purple-500 flex items-center justify-center shadow-lg shadow-brand-500/20">
                <FiZap className="w-5 h-5 text-white" />
              </div>
              <span className="text-lg font-bold gradient-text">Avatar Studio</span>
            </Link>

            <div className="hidden md:flex items-center gap-1">
              {navLink('/', 'Home')}
              {navLink('/pricing', 'Pricing')}
              {navLink('/about', 'About')}
              {navLink('/contact', 'Contact')}
            </div>

            <div className="hidden md:flex items-center gap-2">
              <Link to="/login" className="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900 rounded-xl hover:bg-white/50 transition-all">
                Log in
              </Link>
              <Link to="/signup" className="px-5 py-2.5 text-sm font-medium text-white bg-gradient-to-r from-brand-500 to-purple-500 rounded-xl shadow-lg shadow-brand-500/25 hover:shadow-brand-500/40 transition-all">
                Sign up free
              </Link>
            </div>

            <button className="md:hidden p-2" onClick={() => setMobileOpen(!mobileOpen)}>
              {mobileOpen ? <FiX className="w-5 h-5" /> : <FiMenu className="w-5 h-5" />}
            </button>
          </div>

          {mobileOpen && (
            <div className="md:hidden pb-4 space-y-1 animate-fade-up">
              {[['/', 'Home'], ['/pricing', 'Pricing'], ['/about', 'About'], ['/contact', 'Contact']].map(([to, label]) => (
                <Link key={to} to={to} onClick={() => setMobileOpen(false)}
                  className="block px-4 py-2.5 rounded-xl text-sm font-medium text-gray-600 hover:bg-white/50">{label}</Link>
              ))}
              <div className="flex gap-2 pt-2">
                <Link to="/login" className="flex-1 text-center px-4 py-2.5 rounded-xl text-sm font-medium text-gray-600 glass-card">Log in</Link>
                <Link to="/signup" className="flex-1 text-center px-4 py-2.5 rounded-xl text-sm font-medium text-white bg-brand-500">Sign up</Link>
              </div>
            </div>
          )}
        </div>
      </nav>

      <Outlet />

      {/* Footer */}
      <footer className="border-t border-white/40 mt-20">
        <div className="max-w-7xl mx-auto px-6 py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-brand-500 to-purple-500 flex items-center justify-center">
                  <FiZap className="w-4 h-4 text-white" />
                </div>
                <span className="font-bold gradient-text">Avatar Studio</span>
              </div>
              <p className="text-sm text-gray-500">AI-powered talking avatar videos.</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-800 mb-3 text-sm">Product</h4>
              <div className="space-y-2 text-sm text-gray-500">
                <p className="hover:text-gray-700 cursor-pointer">Features</p>
                <p className="hover:text-gray-700 cursor-pointer">Pricing</p>
                <p className="hover:text-gray-700 cursor-pointer">API</p>
              </div>
            </div>
            <div>
              <h4 className="font-semibold text-gray-800 mb-3 text-sm">Company</h4>
              <div className="space-y-2 text-sm text-gray-500">
                <p className="hover:text-gray-700 cursor-pointer">About</p>
                <p className="hover:text-gray-700 cursor-pointer">Blog</p>
                <p className="hover:text-gray-700 cursor-pointer">Careers</p>
              </div>
            </div>
            <div>
              <h4 className="font-semibold text-gray-800 mb-3 text-sm">Legal</h4>
              <div className="space-y-2 text-sm text-gray-500">
                <p className="hover:text-gray-700 cursor-pointer">Privacy</p>
                <p className="hover:text-gray-700 cursor-pointer">Terms</p>
              </div>
            </div>
          </div>
          <div className="border-t border-gray-200 mt-8 pt-8 text-center text-sm text-gray-400">
            © 2026 Avatar Studio. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  )
}
