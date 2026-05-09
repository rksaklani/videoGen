import { useState } from 'react'
import { useGetHealthQuery } from '../../store/api'
import TTSPanel from '../../components/TTSPanel'
import JobStatus from '../../components/JobStatus'
import VideoPlayer from '../../components/VideoPlayer'
import { FiMic, FiInfo } from 'react-icons/fi'

export default function TextToVideo() {
  const [jobId, setJobId] = useState(null)
  const [completedJobId, setCompletedJobId] = useState(null)
  const { data: health } = useGetHealthQuery()

  return (
    <div className="animate-fade-up">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-500 to-blue-500 flex items-center justify-center text-white shadow-lg">
          <FiMic className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Text to Video</h1>
          <p className="text-gray-500 text-sm">Upload an image, type your script, and generate a talking avatar</p>
        </div>
      </div>

      {/* Tip */}
      <div className="flex items-start gap-2 p-3 rounded-xl bg-brand-50 border border-brand-200 mb-6">
        <FiInfo className="w-4 h-4 text-brand-500 mt-0.5 flex-shrink-0" />
        <p className="text-xs text-brand-700">For repeat use, save your image as an avatar in "My Avatars" — upload once, generate forever.</p>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card rounded-2xl p-6">
          <TTSPanel
            onJobCreated={(id) => { setJobId(id); setCompletedJobId(null) }}
            isReady={health?.engine_loaded}
          />
        </div>

        <div className="glass-card rounded-2xl p-6 min-h-[500px] flex flex-col">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Output</h3>
          <div className="flex-1">
            {completedJobId && <VideoPlayer jobId={completedJobId} />}
            {jobId && <JobStatus jobId={jobId} onComplete={(job) => setCompletedJobId(job.job_id)} />}
            {!jobId && !completedJobId && (
              <div className="rounded-2xl border-2 border-dashed border-gray-200 h-full min-h-[300px] flex items-center justify-center bg-gray-50/50">
                <div className="text-center">
                  <p className="text-5xl mb-3">🎬</p>
                  <p className="text-gray-400 font-medium">Your video will appear here</p>
                  <p className="text-gray-300 text-xs mt-1">Upload image → type text → click generate</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
