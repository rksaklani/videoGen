import { useState, useEffect } from 'react'
import { FiCheckCircle, FiXCircle, FiInfo, FiX } from 'react-icons/fi'

const STYLES = {
  success: { icon: FiCheckCircle, iconColor: 'text-emerald-500', bg: 'bg-emerald-50 border-emerald-200' },
  error: { icon: FiXCircle, iconColor: 'text-red-500', bg: 'bg-red-50 border-red-200' },
  info: { icon: FiInfo, iconColor: 'text-brand-500', bg: 'bg-brand-50 border-brand-200' },
}

export function Toast({ message, type = 'info', onClose, duration = 5000 }) {
  useEffect(() => {
    if (duration > 0) { const t = setTimeout(onClose, duration); return () => clearTimeout(t) }
  }, [duration, onClose])

  const s = STYLES[type] || STYLES.info
  const Icon = s.icon

  return (
    <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border shadow-lg ${s.bg} animate-slide-in`}>
      <Icon className={`w-5 h-5 ${s.iconColor} flex-shrink-0`} />
      <p className="text-sm text-gray-700 flex-1">{message}</p>
      <button onClick={onClose} className="text-gray-400 hover:text-gray-600"><FiX className="w-4 h-4" /></button>
    </div>
  )
}

export function ToastContainer({ toasts, removeToast }) {
  return (
    <div className="fixed top-20 right-4 z-50 space-y-2 w-80">
      {toasts.map((t) => <Toast key={t.id} {...t} onClose={() => removeToast(t.id)} />)}
    </div>
  )
}

let toastId = 0
export function useToasts() {
  const [toasts, setToasts] = useState([])
  const addToast = (message, type = 'info') => { const id = ++toastId; setToasts(p => [...p, { id, message, type }]) }
  const removeToast = (id) => setToasts(p => p.filter(t => t.id !== id))
  return { toasts, addToast, removeToast }
}
