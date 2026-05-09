import { useEffect } from 'react'
import { useGetJobStatusQuery } from '../store/api'
import { FiLoader, FiCheckCircle, FiXCircle, FiClock, FiAlertTriangle } from 'react-icons/fi'

export default function JobStatus({ jobId, onComplete }) {
  const { data: job, isLoading, isError } = useGetJobStatusQuery(jobId, {
    pollingInterval: 3000,
    skip: !jobId,
  })

  useEffect(() => {
    if (job?.status === 'completed') onComplete?.(job)
  }, [job?.status])

  if (!jobId) return null
  if (isLoading && !job) return null

  if (isError) {
    return (
      <div className="glass-card rounded-2xl p-4 border-red-200">
        <div className="flex items-center gap-3">
          <FiAlertTriangle className="w-5 h-5 text-red-500" />
          <div>
            <p className="text-sm font-medium text-red-600">Job Not Found</p>
            <p className="text-xs text-gray-500">Submit a new generation</p>
          </div>
        </div>
      </div>
    )
  }

  const configs = {
    queued: { icon: FiClock, color: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200', bar: 'bg-amber-400' },
    processing: { icon: FiLoader, color: 'text-brand-600', bg: 'bg-brand-50', border: 'border-brand-200', bar: 'bg-brand-500' },
    completed: { icon: FiCheckCircle, color: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-200', bar: 'bg-emerald-500' },
    failed: { icon: FiXCircle, color: 'text-red-600', bg: 'bg-red-50', border: 'border-red-200', bar: 'bg-red-500' },
  }

  const c = configs[job?.status] || configs.queued
  const Icon = c.icon

  return (
    <div className={`rounded-2xl p-4 ${c.bg} border ${c.border} animate-fade-up`}>
      <div className="flex items-center gap-3">
        <Icon className={`w-5 h-5 ${c.color} ${job?.status === 'processing' ? 'animate-spin' : ''}`} />
        <div className="flex-1">
          <p className={`text-sm font-semibold ${c.color}`}>{job?.status?.toUpperCase()}</p>
          <p className="text-xs text-gray-500 mt-0.5">{job?.message}</p>
        </div>
      </div>
      {(job?.status === 'processing' || job?.status === 'queued') && (
        <div className="mt-3 w-full bg-white/60 rounded-full h-2 overflow-hidden">
          <div className={`${c.bar} h-2 rounded-full transition-all duration-700 ease-out`}
            style={{ width: `${Math.max((job?.progress || 0) * 100, 3)}%` }} />
        </div>
      )}
    </div>
  )
}
