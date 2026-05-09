import { useState, useEffect } from 'react'
import { useGetHealthQuery } from '../../store/api'
import FileUpload from '../../components/FileUpload'
import JobStatus from '../../components/JobStatus'
import VideoPlayer from '../../components/VideoPlayer'
import { FiVideo, FiMic, FiType, FiArrowRight } from 'react-icons/fi'

const VOICES = [
  { key: '', label: '🔊 Auto-detect from video' },
  { key: 'en-male', label: '🇺🇸 English Male' },
  { key: 'en-female', label: '🇺🇸 English Female' },
  { key: 'en-male-uk', label: '🇬🇧 British Male' },
  { key: 'hi-male', label: '🇮🇳 Hindi Male' },
  { key: 'hi-female', label: '🇮🇳 Hindi Female' },
  { key: 'zh-male', label: '🇨🇳 Chinese Male' },
  { key: 'es-female', label: '🇪🇸 Spanish Female' },
  { key: 'fr-male', label: '🇫🇷 French Male' },
  { key: 'ja-female', label: '🇯🇵 Japanese Female' },
]

export default function VideoReference() {
  const [video, setVideo] = useState(null)
  const [mode, setMode] = useState('reanimate') // 'reanimate' or 'new-script'
  const [text, setText] = useState('')
  const [voice, setVoice] = useState('')
  const [prompt, setPrompt] = useState('')
  const [duration, setDuration] = useState(0)
  const [jobId, setJobId] = useState(null)
  const [completedJobId, setCompletedJobId] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { data: health } = useGetHealthQuery()

  const maxDurationCap =
    health?.generation_limits?.max_output_duration_seconds ?? 300

  useEffect(() => {
    setDuration((d) => (d > maxDurationCap ? maxDurationCap : d))
  }, [maxDurationCap])

  const handleGenerate = async () => {
    if (!video) return
    if (mode === 'new-script' && !text.trim()) return
    setIsSubmitting(true)

    const formData = new FormData()
    formData.append('video', video)
    formData.append('mode', mode)
    formData.append('prompt', prompt)
    formData.append('max_duration', String(duration))
    if (mode === 'new-script') {
      formData.append('text', text)
      formData.append('voice', voice)
    }

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/create-avatar-from-video`, {
        method: 'POST', body: formData,
      })
      const data = await res.json()
      if (data.job_id) {
        setJobId(data.job_id)
        setCompletedJobId(null)
      }
    } catch (err) {
      console.error('Generation failed:', err)
    }
    setIsSubmitting(false)
  }

  return (
    <div className="animate-fade-up">
      <div className="flex items-center gap-3 mb-6">
        <FiVideo className="w-6 h-6 text-brand-500" />
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Video Reference</h1>
          <p className="text-gray-500 text-sm">Upload a video of someone talking — we'll extract their face and re-animate it</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left: Input */}
        <div className="space-y-4">
          <div className="glass-card rounded-2xl p-6 space-y-4">
            {/* Step 1: Upload Video */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="w-6 h-6 rounded-full bg-brand-500 text-white text-xs flex items-center justify-center font-bold">1</span>
                <h3 className="text-sm font-semibold text-gray-700">Upload Reference Video</h3>
              </div>
              <FileUpload
                label="Upload a video of someone talking (MP4, MOV)"
                accept={{ 'video/*': ['.mp4', '.mov', '.avi', '.mkv', '.webm'] }}
                icon="image"
                file={video}
                onFile={setVideo}
              />
            </div>

            {/* Step 2: Choose Mode */}
            <div>
              <div className="flex items-center gap-2 mb-3">
                <span className="w-6 h-6 rounded-full bg-brand-500 text-white text-xs flex items-center justify-center font-bold">2</span>
                <h3 className="text-sm font-semibold text-gray-700">What should the avatar do?</h3>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <button onClick={() => setMode('reanimate')}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${mode === 'reanimate'
                    ? 'border-brand-500 bg-brand-50' : 'border-gray-200 hover:border-gray-300'}`}>
                  <FiMic className={`w-5 h-5 mb-2 ${mode === 'reanimate' ? 'text-brand-500' : 'text-gray-400'}`} />
                  <p className="text-sm font-semibold text-gray-800">Re-animate</p>
                  <p className="text-xs text-gray-500 mt-1">Use the video's original audio</p>
                </button>
                <button onClick={() => setMode('new-script')}
                  className={`p-4 rounded-xl border-2 text-left transition-all ${mode === 'new-script'
                    ? 'border-brand-500 bg-brand-50' : 'border-gray-200 hover:border-gray-300'}`}>
                  <FiType className={`w-5 h-5 mb-2 ${mode === 'new-script' ? 'text-brand-500' : 'text-gray-400'}`} />
                  <p className="text-sm font-semibold text-gray-800">New Script</p>
                  <p className="text-xs text-gray-500 mt-1">Type new text for the avatar to speak</p>
                </button>
              </div>
            </div>

            {/* Step 3: New Script Options (if selected) */}
            {mode === 'new-script' && (
              <div className="space-y-3 animate-fade-up">
                <div className="flex items-center gap-2 mb-1">
                  <span className="w-6 h-6 rounded-full bg-brand-500 text-white text-xs flex items-center justify-center font-bold">3</span>
                  <h3 className="text-sm font-semibold text-gray-700">Write your script</h3>
                </div>
                <textarea value={text} onChange={(e) => setText(e.target.value)}
                  placeholder="Type what you want the avatar to say..."
                  rows={4}
                  className="w-full px-4 py-3 glass-card rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-400 resize-none" />
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Voice</label>
                    <select value={voice} onChange={(e) => setVoice(e.target.value)}
                      className="w-full px-3 py-2 glass-card rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-400">
                      {VOICES.map(v => <option key={v.key} value={v.key}>{v.label}</option>)}
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-medium text-gray-600 mb-1">Duration: {duration === 0 ? 'Auto' : `${duration}s`}</label>
                    <input type="range" min={0} max={maxDurationCap} step={5} value={duration}
                      onChange={(e) => setDuration(Number(e.target.value))}
                      className="w-full accent-brand-500 mt-2" />
                  </div>
                </div>
              </div>
            )}

            {/* Scene Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Scene Description <span className="text-gray-400 font-normal">(optional)</span></label>
              <input type="text" value={prompt} onChange={(e) => setPrompt(e.target.value)}
                placeholder="e.g. A person speaking in a modern studio"
                className="w-full px-4 py-2.5 glass-card rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>

            {/* Generate Button */}
            <button onClick={handleGenerate}
              disabled={!video || (mode === 'new-script' && !text.trim()) || isSubmitting || !health?.engine_loaded}
              className="w-full py-3.5 bg-gradient-to-r from-brand-500 to-purple-500 hover:from-brand-600 hover:to-purple-600 disabled:from-gray-300 disabled:to-gray-300 text-white rounded-xl font-semibold transition-all shadow-lg shadow-brand-500/25 active:scale-[0.98] flex items-center justify-center gap-2">
              <FiArrowRight className="w-4 h-4" />
              {isSubmitting ? 'Processing...' : mode === 'reanimate' ? 'Re-animate Video' : 'Generate with New Script'}
            </button>
          </div>

          {/* How it works */}
          <div className="glass-card rounded-2xl p-5">
            <h4 className="text-sm font-semibold text-gray-700 mb-3">How it works</h4>
            <div className="space-y-2 text-xs text-gray-500">
              <div className="flex gap-2"><span className="text-brand-500 font-bold">1.</span> Upload a video of someone talking</div>
              <div className="flex gap-2"><span className="text-brand-500 font-bold">2.</span> We extract the best frame as face reference</div>
              <div className="flex gap-2"><span className="text-brand-500 font-bold">3.</span> Choose: re-animate with original audio OR type new text</div>
              <div className="flex gap-2"><span className="text-brand-500 font-bold">4.</span> AI generates a new video with lip-sync</div>
            </div>
          </div>
        </div>

        {/* Right: Output */}
        <div className="glass-card rounded-2xl p-6 min-h-[500px]">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Output</h3>
          {completedJobId && <VideoPlayer jobId={completedJobId} />}
          {jobId && <JobStatus jobId={jobId} onComplete={(job) => setCompletedJobId(job.job_id)} />}
          {!jobId && !completedJobId && (
            <div className="rounded-2xl border-2 border-dashed border-gray-200 aspect-video flex items-center justify-center bg-gray-50/50">
              <div className="text-center">
                <p className="text-4xl mb-2">🎬</p>
                <p className="text-gray-400 text-sm">Upload a reference video to get started</p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
