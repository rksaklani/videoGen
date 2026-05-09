import { useState, useEffect } from 'react'
import { useGetHealthQuery } from '../../store/api'
import FileUpload from '../../components/FileUpload'
import JobStatus from '../../components/JobStatus'
import VideoPlayer from '../../components/VideoPlayer'
import { FiPlus, FiTrash2, FiPlay, FiUser, FiVideo, FiImage, FiMic } from 'react-icons/fi'

const API = import.meta.env.VITE_API_URL || ''
const VOICES = [
  { key: 'en-male', label: '🇺🇸 Male' }, { key: 'en-female', label: '🇺🇸 Female' },
  { key: 'en-male-uk', label: '🇬🇧 Male' }, { key: 'hi-male', label: '🇮🇳 Male' },
  { key: 'hi-female', label: '🇮🇳 Female' }, { key: 'zh-male', label: '🇨🇳 Male' },
  { key: 'es-male', label: '🇪🇸 Male' }, { key: 'fr-female', label: '🇫🇷 Female' },
  { key: 'ja-female', label: '🇯🇵 Female' }, { key: 'ko-female', label: '🇰🇷 Female' },
]

export default function MyAvatars() {
  const [avatars, setAvatars] = useState([])
  const [selectedAvatar, setSelectedAvatar] = useState(null)
  const [showCreate, setShowCreate] = useState(false)
  const [createMode, setCreateMode] = useState('video') // 'video' or 'image'
  const [file, setFile] = useState(null)
  const [name, setName] = useState('')
  const [voice, setVoice] = useState('en-male')
  const [creating, setCreating] = useState(false)

  // Generate state
  const [text, setText] = useState('')
  const [genVoice, setGenVoice] = useState('')
  const [jobId, setJobId] = useState(null)
  const [completedJobId, setCompletedJobId] = useState(null)
  const [generating, setGenerating] = useState(false)

  const { data: health } = useGetHealthQuery()

  const authHeaders = () => {
    const t = localStorage.getItem('token')
    return t ? { Authorization: `Bearer ${t}` } : {}
  }

  const fetchAvatars = async () => {
    try {
      let res = await fetch(`${API}/api/v1/avatars/list`, { headers: authHeaders() })
      if (res.status === 401) {
        localStorage.removeItem('token')
        res = await fetch(`${API}/api/v1/avatars/list`, { headers: {} })
      }
      const data = await res.json()
      setAvatars(data.avatars || [])
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => { fetchAvatars() }, [])

  const handleCreate = async () => {
    if (!file || !name.trim()) return
    setCreating(true)
    const formData = new FormData()
    formData.append(createMode === 'video' ? 'video' : 'image', file)
    formData.append('name', name)
    if (createMode === 'image') formData.append('voice', voice)

    try {
      const endpoint = createMode === 'video' ? 'create-from-video' : 'create-from-image'
      const res = await fetch(`${API}/api/v1/avatars/${endpoint}`, {
        method: 'POST', body: formData, headers: authHeaders(),
      })
      if (res.ok) {
        setShowCreate(false); setFile(null); setName('')
        fetchAvatars()
      }
    } catch (e) { console.error(e) }
    setCreating(false)
  }

  const handleDelete = async (id) => {
    if (!confirm('Delete this avatar?')) return
    await fetch(`${API}/api/v1/avatars/${id}`, { method: 'DELETE', headers: authHeaders() })
    fetchAvatars()
    if (selectedAvatar?.avatar_id === id) setSelectedAvatar(null)
  }

  const handleGenerate = async () => {
    if (!selectedAvatar || !text.trim()) return
    setGenerating(true)
    const formData = new FormData()
    formData.append('text', text)
    if (genVoice) formData.append('voice', genVoice)
    formData.append('max_duration', '0')

    try {
      const res = await fetch(`${API}/api/v1/avatars/${selectedAvatar.avatar_id}/generate`, {
        method: 'POST', body: formData, headers: authHeaders(),
      })
      const data = await res.json()
      if (data.job_id) { setJobId(data.job_id); setCompletedJobId(null) }
    } catch (e) { console.error(e) }
    setGenerating(false)
  }

  return (
    <div className="animate-fade-up">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-800">My Avatars</h1>
          <p className="text-gray-500 text-sm">Create once, generate videos forever</p>
        </div>
        <button onClick={() => setShowCreate(!showCreate)}
          className="flex items-center gap-2 px-4 py-2.5 bg-gradient-to-r from-brand-500 to-purple-500 text-white rounded-xl font-medium shadow-lg shadow-brand-500/25 hover:shadow-brand-500/40 transition-all">
          <FiPlus className="w-4 h-4" /> New Avatar
        </button>
      </div>

      {/* Create Avatar Modal */}
      {showCreate && (
        <div className="glass-card rounded-2xl p-6 mb-6 animate-fade-up">
          <h3 className="font-semibold text-gray-800 mb-4">Create New Avatar</h3>
          <div className="flex gap-2 mb-4">
            <button onClick={() => setCreateMode('video')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium transition-all
                ${createMode === 'video' ? 'bg-brand-500 text-white' : 'glass-card text-gray-600'}`}>
              <FiVideo className="w-4 h-4" /> From Video
            </button>
            <button onClick={() => setCreateMode('image')}
              className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-xl text-sm font-medium transition-all
                ${createMode === 'image' ? 'bg-brand-500 text-white' : 'glass-card text-gray-600'}`}>
              <FiImage className="w-4 h-4" /> From Image
            </button>
          </div>

          {createMode === 'video' ? (
            <FileUpload label="Upload video of yourself talking (10s-2min)" accept={{ 'video/*': ['.mp4', '.mov', '.avi'] }} icon="image" file={file} onFile={setFile} />
          ) : (
            <FileUpload label="Upload face photo" accept={{ 'image/*': ['.png', '.jpg', '.jpeg'] }} icon="image" file={file} onFile={setFile} />
          )}

          <div className="grid grid-cols-2 gap-3 mt-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Avatar Name</label>
              <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. My Avatar"
                className="w-full px-3 py-2.5 glass-card rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
            </div>
            {createMode === 'image' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Voice</label>
                <select value={voice} onChange={(e) => setVoice(e.target.value)}
                  className="w-full px-3 py-2.5 glass-card rounded-xl text-sm">
                  {VOICES.map(v => <option key={v.key} value={v.key}>{v.label}</option>)}
                </select>
              </div>
            )}
          </div>

          {createMode === 'video' && (
            <div className="mt-3 p-3 rounded-xl bg-brand-50 border border-brand-200">
              <p className="text-xs text-brand-700">We'll automatically extract the best face frame and analyze your voice from the video.</p>
            </div>
          )}

          <div className="flex gap-2 mt-4">
            <button onClick={() => setShowCreate(false)} className="flex-1 py-2.5 glass-card rounded-xl text-sm font-medium text-gray-600">Cancel</button>
            <button onClick={handleCreate} disabled={!file || !name.trim() || creating}
              className="flex-1 py-2.5 bg-brand-500 hover:bg-brand-600 disabled:bg-gray-300 text-white rounded-xl text-sm font-medium transition-all">
              {creating ? 'Creating...' : 'Create Avatar'}
            </button>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left: Avatar List */}
        <div className="lg:col-span-4 space-y-3">
          {avatars.length === 0 && !showCreate && (
            <div className="glass-card rounded-2xl p-8 text-center">
              <FiUser className="w-12 h-12 text-gray-300 mx-auto mb-3" />
              <p className="text-gray-500 text-sm">No avatars yet</p>
              <p className="text-gray-400 text-xs mt-1">Click "New Avatar" to create one</p>
            </div>
          )}

          {avatars.map((a) => (
            <div key={a.avatar_id}
              onClick={() => { setSelectedAvatar(a); setGenVoice(a.voice_analysis?.matched_voice || '') }}
              className={`glass-card rounded-2xl p-4 flex items-center gap-3 cursor-pointer transition-all hover:scale-[1.01]
                ${selectedAvatar?.avatar_id === a.avatar_id ? 'ring-2 ring-brand-500 bg-brand-50/50' : ''}`}>
              <img src={`${API}/api/v1/avatars/${a.avatar_id}/image`} alt={a.name}
                className="w-14 h-14 rounded-xl object-cover bg-gray-100"
                onError={(e) => { e.target.style.display = 'none' }} />
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-gray-800 text-sm truncate">{a.name}</p>
                <p className="text-xs text-gray-400">{a.voice_analysis?.gender || 'unknown'} voice</p>
              </div>
              <button onClick={(e) => { e.stopPropagation(); handleDelete(a.avatar_id) }}
                className="p-1.5 text-gray-300 hover:text-red-500 transition-colors">
                <FiTrash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>

        {/* Right: Generate with selected avatar */}
        <div className="lg:col-span-8">
          {selectedAvatar ? (
            <div className="space-y-4">
              <div className="glass-card rounded-2xl p-6">
                <div className="flex items-center gap-4 mb-4">
                  <img src={`${API}/api/v1/avatars/${selectedAvatar.avatar_id}/image`} alt=""
                    className="w-16 h-16 rounded-xl object-cover" />
                  <div>
                    <h3 className="font-bold text-gray-800">{selectedAvatar.name}</h3>
                    <p className="text-xs text-gray-400">Type text below and generate a video</p>
                  </div>
                </div>

                <textarea value={text} onChange={(e) => setText(e.target.value)}
                  placeholder="Type what you want this avatar to say..."
                  rows={4} className="w-full px-4 py-3 glass-card rounded-xl text-sm placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-400 resize-none" />

                <div className="flex gap-3 mt-3">
                  <select value={genVoice} onChange={(e) => setGenVoice(e.target.value)}
                    className="flex-1 px-3 py-2.5 glass-card rounded-xl text-sm">
                    <option value="">Auto (matched voice)</option>
                    {VOICES.map(v => <option key={v.key} value={v.key}>{v.label}</option>)}
                  </select>
                  <button onClick={handleGenerate}
                    disabled={!text.trim() || generating || !health?.engine_loaded}
                    className="px-6 py-2.5 bg-gradient-to-r from-brand-500 to-purple-500 hover:from-brand-600 hover:to-purple-600 disabled:from-gray-300 disabled:to-gray-300 text-white rounded-xl font-medium transition-all shadow-lg shadow-brand-500/25 flex items-center gap-2">
                    <FiPlay className="w-4 h-4" />
                    {generating ? 'Submitting...' : 'Generate'}
                  </button>
                </div>
              </div>

              {/* Output */}
              <div className="glass-card rounded-2xl p-6 min-h-[300px]">
                <h3 className="text-sm font-semibold text-gray-700 mb-4">Output</h3>
                {completedJobId && <VideoPlayer jobId={completedJobId} />}
                {jobId && <JobStatus jobId={jobId} onComplete={(job) => setCompletedJobId(job.job_id)} />}
                {!jobId && !completedJobId && (
                  <div className="rounded-2xl border-2 border-dashed border-gray-200 aspect-video flex items-center justify-center bg-gray-50/50">
                    <div className="text-center">
                      <p className="text-4xl mb-2">🎬</p>
                      <p className="text-gray-400 text-sm">Type text and click Generate</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="glass-card rounded-2xl p-12 text-center">
              <FiUser className="w-16 h-16 text-gray-200 mx-auto mb-4" />
              <p className="text-gray-500">Select an avatar to start generating</p>
              <p className="text-gray-400 text-xs mt-1">Or create a new one with the button above</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
