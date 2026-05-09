import { useState, useEffect } from 'react'
import { useGenerateFromTextMutation, useGetHealthQuery } from '../store/api'
import { getMaxOutputSeconds } from '../lib/generationLimits'
import FileUpload from './FileUpload'
import { FiMic } from 'react-icons/fi'

const VOICES = [
  { key: 'en-male', label: '🇺🇸 English Male' },
  { key: 'en-female', label: '🇺🇸 English Female' },
  { key: 'en-male-uk', label: '🇬🇧 British Male' },
  { key: 'en-female-uk', label: '🇬🇧 British Female' },
  { key: 'hi-male', label: '🇮🇳 Hindi Male' },
  { key: 'hi-female', label: '🇮🇳 Hindi Female' },
  { key: 'zh-male', label: '🇨🇳 Chinese Male' },
  { key: 'zh-female', label: '🇨🇳 Chinese Female' },
  { key: 'es-male', label: '🇪🇸 Spanish Male' },
  { key: 'es-female', label: '🇪🇸 Spanish Female' },
  { key: 'fr-male', label: '🇫🇷 French Male' },
  { key: 'fr-female', label: '🇫🇷 French Female' },
  { key: 'de-male', label: '🇩🇪 German Male' },
  { key: 'ja-female', label: '🇯🇵 Japanese Female' },
  { key: 'ko-female', label: '🇰🇷 Korean Female' },
  { key: 'ar-male', label: '🇸🇦 Arabic Male' },
  { key: 'pt-female', label: '🇧🇷 Portuguese Female' },
]

export default function TTSPanel({ onJobCreated, isReady }) {
  const [image, setImage] = useState(null)
  const [text, setText] = useState('')
  const [voice, setVoice] = useState('en-male')
  const [prompt, setPrompt] = useState('')
  const [duration, setDuration] = useState(0)  // 0 = match audio length
  const [rate, setRate] = useState('+0%')
  const [generate, { isLoading }] = useGenerateFromTextMutation()
  const { data: health } = useGetHealthQuery()
  const maxDurationCap = getMaxOutputSeconds(health)

  useEffect(() => {
    setDuration((d) => (d > maxDurationCap ? maxDurationCap : d))
  }, [maxDurationCap])

  const handleGenerate = async () => {
    if (!image || !text.trim()) return
    try {
      const result = await generate({ image, text, voice, prompt, maxDuration: duration, rate }).unwrap()
      onJobCreated(result.job_id)
    } catch (err) {
      console.error('TTS generation failed:', err)
    }
  }

  return (
    <div className="space-y-4">
      <FileUpload label="Upload Reference Image" accept={{ 'image/*': ['.png', '.jpg', '.jpeg', '.webp'] }} icon="image" file={image} onFile={setImage} />

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">Text to Speak</label>
        <textarea value={text} onChange={(e) => setText(e.target.value)} placeholder="Type what you want the avatar to say..."
          rows={4} className="w-full px-4 py-3 glass-card rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-400 resize-none" />
        <p className="text-xs text-gray-400 mt-1">{text.length}/5000</p>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Voice</label>
          <select value={voice} onChange={(e) => setVoice(e.target.value)}
            className="w-full px-3 py-2.5 glass-card rounded-xl text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-brand-400">
            {VOICES.map(v => <option key={v.key} value={v.key}>{v.label}</option>)}
          </select>
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">Speed</label>
          <select value={rate} onChange={(e) => setRate(e.target.value)}
            className="w-full px-3 py-2.5 glass-card rounded-xl text-sm text-gray-800 focus:outline-none focus:ring-2 focus:ring-brand-400">
            <option value="-20%">Slow</option>
            <option value="+0%">Normal</option>
            <option value="+15%">Fast</option>
          </select>
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">
          Max output length: {duration === 0 ? 'Match TTS audio' : `${duration}s`}
        </label>
        <input type="range" min={0} max={maxDurationCap} step={5} value={duration}
          onChange={(e) => setDuration(Number(e.target.value))}
          className="w-full accent-brand-500" />
        <p className="text-xs text-gray-400 mt-1">0 = full speech length (cap {maxDurationCap}s)</p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1.5">Scene Description <span className="text-gray-400 font-normal">(optional)</span></label>
        <input type="text" value={prompt} onChange={(e) => setPrompt(e.target.value)} placeholder="e.g. A person in a modern studio"
          className="w-full px-4 py-2.5 glass-card rounded-xl text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-400" />
      </div>

      <button onClick={handleGenerate} disabled={!image || !text.trim() || isLoading || !isReady}
        className="w-full py-3.5 bg-gradient-to-r from-brand-500 to-purple-500 hover:from-brand-600 hover:to-purple-600 disabled:from-gray-300 disabled:to-gray-300 text-white rounded-xl font-semibold transition-all shadow-lg shadow-brand-500/25 hover:shadow-brand-500/40 active:scale-[0.98] flex items-center justify-center gap-2">
        <FiMic className="w-4 h-4" />
        {isLoading ? 'Generating Speech...' : 'Generate Talking Avatar'}
      </button>
    </div>
  )
}
