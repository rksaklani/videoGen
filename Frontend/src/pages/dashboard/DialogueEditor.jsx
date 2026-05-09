import { useState } from 'react'
import { useGetHealthQuery } from '../../store/api'
import FileUpload from '../../components/FileUpload'
import JobStatus from '../../components/JobStatus'
import VideoPlayer from '../../components/VideoPlayer'
import { FiPlus, FiTrash2, FiUsers, FiPlay } from 'react-icons/fi'

const VOICES = [
  { key: 'en-male', label: '🇺🇸 Male' }, { key: 'en-female', label: '🇺🇸 Female' },
  { key: 'en-male-uk', label: '🇬🇧 Male' }, { key: 'en-female-uk', label: '🇬🇧 Female' },
  { key: 'hi-male', label: '🇮🇳 Male' }, { key: 'hi-female', label: '🇮🇳 Female' },
  { key: 'zh-male', label: '🇨🇳 Male' }, { key: 'zh-female', label: '🇨🇳 Female' },
  { key: 'es-male', label: '🇪🇸 Male' }, { key: 'fr-female', label: '🇫🇷 Female' },
  { key: 'ja-female', label: '🇯🇵 Female' }, { key: 'ko-female', label: '🇰🇷 Female' },
]

const COLORS = ['bg-brand-100 border-brand-300', 'bg-purple-100 border-purple-300', 'bg-emerald-100 border-emerald-300', 'bg-amber-100 border-amber-300']

export default function DialogueEditor() {
  const [charA, setCharA] = useState({ name: 'Alice', voice: 'en-female', image: null })
  const [charB, setCharB] = useState({ name: 'Bob', voice: 'en-male', image: null })
  const [lines, setLines] = useState([
    { character: 'Alice', text: '' },
    { character: 'Bob', text: '' },
  ])
  const [scene, setScene] = useState('Two people having a conversation in a studio')
  const [layout, setLayout] = useState('side-by-side')
  const [jobId, setJobId] = useState(null)
  const [completedJobId, setCompletedJobId] = useState(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const { data: health } = useGetHealthQuery()

  const addLine = () => {
    const lastChar = lines.length > 0 ? lines[lines.length - 1].character : 'Alice'
    const nextChar = lastChar === charA.name ? charB.name : charA.name
    setLines([...lines, { character: nextChar, text: '' }])
  }

  const removeLine = (idx) => {
    if (lines.length > 1) setLines(lines.filter((_, i) => i !== idx))
  }

  const updateLine = (idx, field, value) => {
    const updated = [...lines]
    updated[idx] = { ...updated[idx], [field]: value }
    setLines(updated)
  }

  const handleGenerate = async () => {
    if (!charA.image || lines.every(l => !l.text.trim())) return
    setIsSubmitting(true)

    const formData = new FormData()
    formData.append('char_a_image', charA.image)
    if (charB.image) formData.append('char_b_image', charB.image)
    formData.append('char_a_name', charA.name)
    formData.append('char_b_name', charB.name)
    formData.append('char_a_voice', charA.voice)
    formData.append('char_b_voice', charB.voice)
    formData.append('scene_prompt', scene)
    formData.append('layout', layout)

    const dialogueText = lines.filter(l => l.text.trim()).map(l => `${l.character}: ${l.text}`).join('\n')
    formData.append('dialogue_text', dialogueText)

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || ''}/api/v1/generate-dialogue-simple`, {
        method: 'POST', body: formData,
      })
      const data = await res.json()
      if (data.job_id) {
        setJobId(data.job_id)
        setCompletedJobId(null)
      }
    } catch (err) {
      console.error('Dialogue generation failed:', err)
    }
    setIsSubmitting(false)
  }

  const charColor = (name) => name === charA.name ? COLORS[0] : COLORS[1]

  return (
    <div className="animate-fade-up">
      <div className="flex items-center gap-3 mb-6">
        <FiUsers className="w-6 h-6 text-brand-500" />
        <div>
          <h1 className="text-2xl font-bold text-gray-800">Multi-Character Dialogue</h1>
          <p className="text-gray-500 text-sm">Create conversations between two or more characters</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Characters + Script */}
        <div className="lg:col-span-5 space-y-4">
          {/* Character Setup */}
          <div className="glass-card rounded-2xl p-5">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Characters</h3>
            <div className="grid grid-cols-2 gap-4">
              {/* Character A */}
              <div className={`rounded-xl p-3 border-2 ${COLORS[0]}`}>
                <input type="text" value={charA.name} onChange={(e) => setCharA({...charA, name: e.target.value})}
                  className="w-full px-2 py-1 bg-white/60 rounded-lg text-sm font-semibold mb-2 focus:outline-none" />
                <select value={charA.voice} onChange={(e) => setCharA({...charA, voice: e.target.value})}
                  className="w-full px-2 py-1 bg-white/60 rounded-lg text-xs mb-2">
                  {VOICES.map(v => <option key={v.key} value={v.key}>{v.label}</option>)}
                </select>
                <FileUpload label="Photo" accept={{ 'image/*': ['.png', '.jpg', '.jpeg'] }} icon="image"
                  file={charA.image} onFile={(f) => setCharA({...charA, image: f})} />
              </div>
              {/* Character B */}
              <div className={`rounded-xl p-3 border-2 ${COLORS[1]}`}>
                <input type="text" value={charB.name} onChange={(e) => setCharB({...charB, name: e.target.value})}
                  className="w-full px-2 py-1 bg-white/60 rounded-lg text-sm font-semibold mb-2 focus:outline-none" />
                <select value={charB.voice} onChange={(e) => setCharB({...charB, voice: e.target.value})}
                  className="w-full px-2 py-1 bg-white/60 rounded-lg text-xs mb-2">
                  {VOICES.map(v => <option key={v.key} value={v.key}>{v.label}</option>)}
                </select>
                <FileUpload label="Photo" accept={{ 'image/*': ['.png', '.jpg', '.jpeg'] }} icon="image"
                  file={charB.image} onFile={(f) => setCharB({...charB, image: f})} />
              </div>
            </div>
          </div>

          {/* Dialogue Script */}
          <div className="glass-card rounded-2xl p-5">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-semibold text-gray-700">Script</h3>
              <button onClick={addLine} className="flex items-center gap-1 px-3 py-1.5 bg-brand-50 text-brand-600 rounded-lg text-xs font-medium hover:bg-brand-100">
                <FiPlus className="w-3 h-3" /> Add Line
              </button>
            </div>
            <div className="space-y-2 max-h-[400px] overflow-y-auto">
              {lines.map((line, idx) => (
                <div key={idx} className={`flex gap-2 items-start p-2 rounded-xl border-2 ${charColor(line.character)} transition-all`}>
                  <select value={line.character} onChange={(e) => updateLine(idx, 'character', e.target.value)}
                    className="px-2 py-1.5 bg-white/60 rounded-lg text-xs font-semibold min-w-[80px]">
                    <option value={charA.name}>{charA.name}</option>
                    <option value={charB.name}>{charB.name}</option>
                  </select>
                  <input type="text" value={line.text} onChange={(e) => updateLine(idx, 'text', e.target.value)}
                    placeholder={`${line.character} says...`}
                    className="flex-1 px-3 py-1.5 bg-white/60 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
                  <button onClick={() => removeLine(idx)} className="p-1.5 text-gray-400 hover:text-red-500">
                    <FiTrash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Settings */}
          <div className="glass-card rounded-2xl p-5 space-y-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Scene Description</label>
              <input type="text" value={scene} onChange={(e) => setScene(e.target.value)}
                className="w-full px-4 py-2.5 glass-card rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Layout</label>
              <div className="flex gap-2">
                {['side-by-side', 'interview'].map(l => (
                  <button key={l} onClick={() => setLayout(l)}
                    className={`flex-1 py-2 rounded-xl text-sm font-medium transition-all
                      ${layout === l ? 'bg-brand-500 text-white' : 'glass-card text-gray-600 hover:bg-white/60'}`}>
                    {l === 'side-by-side' ? '👥 Side by Side' : '🎤 Interview'}
                  </button>
                ))}
              </div>
            </div>
            <button onClick={handleGenerate}
              disabled={!charA.image || lines.every(l => !l.text.trim()) || isSubmitting || !health?.engine_loaded}
              className="w-full py-3.5 bg-gradient-to-r from-brand-500 to-purple-500 hover:from-brand-600 hover:to-purple-600 disabled:from-gray-300 disabled:to-gray-300 text-white rounded-xl font-semibold transition-all shadow-lg shadow-brand-500/25 active:scale-[0.98] flex items-center justify-center gap-2">
              <FiPlay className="w-4 h-4" />
              {isSubmitting ? 'Submitting...' : 'Generate Dialogue Video'}
            </button>
          </div>
        </div>

        {/* Right: Output */}
        <div className="lg:col-span-7 space-y-4">
          <div className="glass-card rounded-2xl p-6 min-h-[500px]">
            <h3 className="text-sm font-semibold text-gray-700 mb-4">Output</h3>
            {completedJobId && <VideoPlayer jobId={completedJobId} />}
            {jobId && <JobStatus jobId={jobId} onComplete={(job) => setCompletedJobId(job.job_id)} />}
            {!jobId && !completedJobId && (
              <div className="rounded-2xl border-2 border-dashed border-gray-200 aspect-video flex items-center justify-center bg-gray-50/50">
                <div className="text-center">
                  <p className="text-4xl mb-2">👥</p>
                  <p className="text-gray-400 text-sm">Your dialogue video will appear here</p>
                  <p className="text-gray-300 text-xs mt-1">Upload character images and write a script to get started</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
