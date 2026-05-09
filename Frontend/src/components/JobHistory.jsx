import { useGetJobsQuery } from '../store/api'
import { FiCheckCircle, FiXCircle, FiLoader, FiClock, FiPlay } from 'react-icons/fi'

const icons = {
  completed: <FiCheckCircle className="w-4 h-4 text-emerald-500" />,
  failed: <FiXCircle className="w-4 h-4 text-red-500" />,
  processing: <FiLoader className="w-4 h-4 text-brand-500 animate-spin" />,
  queued: <FiClock className="w-4 h-4 text-amber-500" />,
}

export default function JobHistory({ onSelect }) {
  const { data: jobs } = useGetJobsQuery(undefined, { pollingInterval: 5000 })

  if (!jobs?.length) {
    return (
      <div className="glass-card rounded-2xl p-8 text-center">
        <p className="text-gray-400 text-sm">No generations yet</p>
        <p className="text-gray-300 text-xs mt-1">Your videos will appear here</p>
      </div>
    )
  }

  return (
    <div className="space-y-2">
      {jobs.map((job) => (
        <button
          key={job.job_id}
          onClick={() => job.status === 'completed' && onSelect(job.job_id)}
          className={`w-full glass-card rounded-xl p-3 flex items-center gap-3 transition-all text-left
            ${job.status === 'completed' ? 'hover:scale-[1.01] cursor-pointer' : 'opacity-70 cursor-default'}`}
        >
          {icons[job.status]}
          <div className="flex-1 min-w-0">
            <p className="text-xs font-mono text-gray-600 truncate">{job.job_id}</p>
            <p className="text-xs text-gray-400 truncate">{job.message}</p>
          </div>
          {job.status === 'completed' && (
            <FiPlay className="w-4 h-4 text-brand-500 flex-shrink-0" />
          )}
        </button>
      ))}
    </div>
  )
}
