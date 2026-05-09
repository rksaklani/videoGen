import { useState } from 'react'
import JobHistory from '../../components/JobHistory'
import VideoPlayer from '../../components/VideoPlayer'
import { FiClock } from 'react-icons/fi'

export default function History() {
  const [selectedJob, setSelectedJob] = useState(null)

  return (
    <div className="animate-fade-up">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-500 to-orange-500 flex items-center justify-center text-white shadow-lg">
          <FiClock className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Generation History</h1>
          <p className="text-gray-500 text-sm">All your generated videos in one place</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        <div className="lg:col-span-2 glass-card rounded-2xl p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Recent Jobs</h3>
          <JobHistory onSelect={setSelectedJob} />
        </div>
        <div className="lg:col-span-3 glass-card rounded-2xl p-6 min-h-[500px] flex flex-col">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Preview</h3>
          <div className="flex-1">
            {selectedJob ? (
              <VideoPlayer jobId={selectedJob} />
            ) : (
              <div className="rounded-2xl border-2 border-dashed border-gray-200 h-full min-h-[300px] flex items-center justify-center bg-gray-50/50">
                <div className="text-center">
                  <p className="text-5xl mb-3">📋</p>
                  <p className="text-gray-400 font-medium">Select a video to preview</p>
                  <p className="text-gray-300 text-xs mt-1">Click any completed job on the left</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
