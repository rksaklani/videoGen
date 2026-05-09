import { useState } from 'react'
import { useGenerateAvatarMutation, useGetHealthQuery } from '../../store/api'
import FileUpload from '../../components/FileUpload'
import JobStatus from '../../components/JobStatus'
import VideoPlayer from '../../components/VideoPlayer'
import { FiMusic } from 'react-icons/fi'

export default function AudioToVideo() {
  const [image, setImage] = useState(null)
  const [audio, setAudio] = useState(null)
  const [prompt, setPrompt] = useState('')
  const [duration, setDuration] = useState(0)
  const [jobId, setJobId] = useState(null)
  const [completedJobId, setCompletedJobId] = useState(null)
  const { data: health } = useGetHealthQuery()
  const [generate, { isLoading }] = useGenerateAvatarMutation()

  const handleGenerate = async () => {
    if (!image || !audio) return
    try {
      const result = await generate({ image, audio, prompt, maxDuration: duration }).unwrap()
      setJobId(result.job_id); setCompletedJobId(null)
    } catch (err) { console.error(err) }
  }

  return (
    <div className="animate-fade-up">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-500 flex items-center justify-center text-white shadow-lg">
          <FiMusic className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Audio to Video</h1>
          <p className="text-gray-500 text-sm">Upload a reference image and your own audio file</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="glass-card rounded-2xl p-6 space-y-5">
          <FileUpload label="Reference Image" accept={{ 'image/*': ['.png', '.jpg', '.jpeg', '.webp'] }} icon="image" file={image} onFile={setImage} />
          <FileUpload label="Audio File (WAV, MP3)" accept={{ 'audio/*': ['.wav', '.mp3', '.flac'] }} icon="audio" file={audio} onFile={setAudio} />

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">Scene Description <span className="text-gray-400 font-normal">(optional)</span></label>
            <input type="text" value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="e.g. A person presenting in a modern studio"
              className="w-full px-4 py-2.5 glass-card rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Duration: {duration === 0 ? 'Match audio length' : `${duration}s`}
            </label>
            <input type="range" min={0} max={120} step={5} value={duration} onChange={(e) => setDuration(Number(e.target.value))} className="w-full accent-brand-500" />
            <p className="text-xs text-gray-400 mt-1">0 = auto-match your audio length</p>
          </div>

          <button onClick={handleGenerate} disabled={!image || !audio || isLoading || !health?.engine_loaded}
            className="w-full py-3.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 disabled:from-gray-300 disabled:to-gray-300 text-white rounded-xl font-semibold transition-all shadow-lg shadow-emerald-500/25 active:scale-[0.98]">
            {isLoading ? 'Submitting...' : '🎬 Generate Avatar Video'}
          </button>
        </div>

        <div className="glass-card rounded-2xl p-6 min-h-[500px] flex flex-col">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Output</h3>
          <div className="flex-1">
            {completedJobId && <VideoPlayer jobId={completedJobId} />}
            {jobId && <JobStatus jobId={jobId} onComplete={(job) => setCompletedJobId(job.job_id)} />}
            {!jobId && !completedJobId && (
              <div className="rounded-2xl border-2 border-dashed border-gray-200 h-full min-h-[300px] flex items-center justify-center bg-gray-50/50">
                <div className="text-center">
                  <p className="text-5xl mb-3">🎵</p>
                  <p className="text-gray-400 font-medium">Your video will appear here</p>
                  <p className="text-gray-300 text-xs mt-1">Upload image + audio → click generate</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
