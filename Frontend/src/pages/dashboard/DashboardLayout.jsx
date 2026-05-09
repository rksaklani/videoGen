import { useState } from 'react'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useGetHealthQuery } from '../../store/api'
import {
  FiZap, FiPlusCircle, FiGrid, FiClock, FiSettings, FiLogOut,
  FiMenu, FiX, FiMic, FiUpload, FiUsers, FiUser, FiVideo,
  FiChevronLeft, FiChevronRight
} from 'react-icons/fi'

const sidebarLinks = [
  { to: '/dashboard', icon: <FiPlusCircle className="w-5 h-5" />, label: 'Create', exact: true },
  { to: '/dashboard/my-avatars', icon: <FiUser className="w-5 h-5" />, label: 'My Avatars' },
  { to: '/dashboard/text-to-video', icon: <FiMic className="w-5 h-5" />, label: 'Text to Video' },
  { to: '/dashboard/audio-to-video', icon: <FiUpload className="w-5 h-5" />, label: 'Audio to Video' },
  { to: '/dashboard/video-reference', icon: <FiVideo className="w-5 h-5" />, label: 'Video Reference' },
  { to: '/dashboard/dialogue', icon: <FiUsers className="w-5 h-5" />, label: 'Dialogue' },
  { to: '/dashboard/templates', icon: <FiGrid className="w-5 h-5" />, label: 'Templates' },
  { to: '/dashboard/history', icon: <FiClock className="w-5 h-5" />, label: 'History' },
  { to: '/dashboard/settings', icon: <FiSettings className="w-5 h-5" />, label: 'Settings' },
]

export default function DashboardLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()
  const navigate = useNavigate()
  const { data: health } = useGetHealthQuery(undefined, { pollingInterval: 10000 })
  const isReady = health?.engine_loaded
  const isBusy = health?.gpu?.gpu_busy
  const user = JSON.parse(localStorage.getItem('user') || '{"name":"User"}')

  const handleLogout = () => {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    localStorage.removeItem('user_plan')
    navigate('/')
  }

  const isActive = (link) => link.exact ? location.pathname === link.to : location.pathname.startsWith(link.to)
  const sidebarWidth = collapsed ? 'w-[72px]' : 'w-64'

  const sidebarContent = (isMobile = false) => (
    <div className="flex flex-col h-full">
      {/* Logo */}
      <div className={`border-b border-white/30 flex items-center ${collapsed && !isMobile ? 'justify-center p-4' : 'justify-between p-4 px-5'}`}>
        <Link to="/dashboard" className="flex items-center gap-2.5" onClick={() => isMobile && setMobileOpen(false)}>
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-brand-500 to-purple-500 flex items-center justify-center shadow-lg shadow-brand-500/20 flex-shrink-0">
            <FiZap className="w-5 h-5 text-white" />
          </div>
          {(!collapsed || isMobile) && <span className="text-lg font-bold gradient-text">Studio</span>}
        </Link>
        {/* Collapse toggle — desktop only */}
        {!isMobile && (
          <button onClick={() => setCollapsed(!collapsed)}
            className="hidden lg:flex w-7 h-7 rounded-lg hover:bg-white/40 items-center justify-center text-gray-400 hover:text-gray-600 transition-colors">
            {collapsed ? <FiChevronRight className="w-4 h-4" /> : <FiChevronLeft className="w-4 h-4" />}
          </button>
        )}
      </div>

      {/* Nav Links */}
      <nav className="flex-1 p-2 space-y-0.5 overflow-y-auto">
        {sidebarLinks.map((link) => (
          <Link key={link.to} to={link.to} onClick={() => isMobile && setMobileOpen(false)}
            title={collapsed && !isMobile ? link.label : undefined}
            className={`flex items-center gap-3 rounded-xl text-sm font-medium transition-all
              ${collapsed && !isMobile ? 'justify-center px-2 py-3' : 'px-4 py-2.5'}
              ${isActive(link)
                ? 'bg-gradient-to-r from-brand-500 to-purple-500 text-white shadow-lg shadow-brand-500/20'
                : 'text-gray-600 hover:bg-white/50 hover:text-gray-900'}`}>
            <span className="flex-shrink-0">{link.icon}</span>
            {(!collapsed || isMobile) && <span>{link.label}</span>}
          </Link>
        ))}
      </nav>

      {/* Bottom: Status + User */}
      <div className="border-t border-white/30 p-3 space-y-2">
        {/* GPU Status */}
        <div className={`flex items-center gap-2 rounded-xl bg-white/40 text-xs font-medium
          ${collapsed && !isMobile ? 'justify-center p-2' : 'px-3 py-2'}`}>
          <span className={`w-2 h-2 rounded-full flex-shrink-0 ${isReady ? (isBusy ? 'bg-amber-400 animate-pulse' : 'bg-emerald-400') : 'bg-red-400 animate-pulse'}`} />
          {(!collapsed || isMobile) && (
            <span className={isReady ? (isBusy ? 'text-amber-700' : 'text-emerald-700') : 'text-red-600'}>
              {isReady ? (isBusy ? 'Processing' : 'GPU Ready') : 'Loading...'}
            </span>
          )}
        </div>

        {/* User */}
        <div className={`flex items-center ${collapsed && !isMobile ? 'justify-center' : 'gap-3 px-2'}`}>
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-brand-400 to-purple-400 flex items-center justify-center text-white text-xs font-bold flex-shrink-0">
            {user.name?.[0]?.toUpperCase() || 'U'}
          </div>
          {(!collapsed || isMobile) && (
            <>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-gray-800 truncate">{user.name}</p>
              </div>
              <button onClick={handleLogout} className="p-1.5 rounded-lg hover:bg-white/50 text-gray-400 hover:text-red-500 transition-colors" title="Logout">
                <FiLogOut className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )

  return (
    <div className="min-h-screen flex">
      {/* Desktop Sidebar */}
      <aside className={`hidden lg:block ${sidebarWidth} glass-strong border-r border-white/40 fixed h-screen transition-all duration-300 z-30`}>
        {sidebarContent(false)}
      </aside>

      {/* Mobile Sidebar Overlay */}
      {mobileOpen && (
        <div className="lg:hidden fixed inset-0 z-50">
          <div className="absolute inset-0 bg-black/30 backdrop-blur-sm" onClick={() => setMobileOpen(false)} />
          <aside className="absolute left-0 top-0 w-72 h-full glass-strong border-r border-white/40 animate-slide-in z-50">
            <div className="absolute top-4 right-4">
              <button onClick={() => setMobileOpen(false)} className="p-2 rounded-lg hover:bg-white/40 text-gray-500">
                <FiX className="w-5 h-5" />
              </button>
            </div>
            {sidebarContent(true)}
          </aside>
        </div>
      )}

      {/* Main Content */}
      <div className={`flex-1 transition-all duration-300 ${collapsed ? 'lg:ml-[72px]' : 'lg:ml-64'}`}>
        {/* Top Bar */}
        <header className="glass-strong sticky top-0 z-20 border-b border-white/40 px-4 sm:px-6 h-14 flex items-center justify-between">
          <button className="lg:hidden p-2 -ml-2 rounded-lg hover:bg-white/40" onClick={() => setMobileOpen(true)}>
            <FiMenu className="w-5 h-5 text-gray-600" />
          </button>

          {/* Breadcrumb */}
          <div className="hidden sm:flex items-center gap-2 text-sm text-gray-400">
            <Link to="/dashboard" className="hover:text-gray-600">Dashboard</Link>
            {location.pathname !== '/dashboard' && (
              <>
                <span>/</span>
                <span className="text-gray-700 font-medium capitalize">
                  {location.pathname.split('/').pop().replace(/-/g, ' ')}
                </span>
              </>
            )}
          </div>

          <div className="flex-1" />

          {/* Right side */}
          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 text-xs font-medium text-gray-500 glass-card px-3 py-1.5 rounded-full">
              <span className={`w-2 h-2 rounded-full ${isReady ? 'bg-emerald-400' : 'bg-red-400 animate-pulse'}`} />
              {isReady ? 'Online' : 'Loading...'}
            </div>
            {/* Mobile user avatar */}
            <div className="lg:hidden w-8 h-8 rounded-full bg-gradient-to-br from-brand-400 to-purple-400 flex items-center justify-center text-white text-xs font-bold">
              {user.name?.[0]?.toUpperCase() || 'U'}
            </div>
          </div>
        </header>

        {/* Page Content — full width with responsive padding */}
        <main className="p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
