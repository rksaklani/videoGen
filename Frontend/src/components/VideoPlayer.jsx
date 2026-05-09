import { FiDownload, FiShare2 } from 'react-icons/fi'

export default function VideoPlayer({ jobId }) {
  if (!jobId) return null
  const videoUrl = `${import.meta.env.VITE_API_URL || ''}/api/v1/download/${jobId}`

  return (
    <div className="glass-card rounded-2xl overflow-hidden animate-fade-up">
      <video src={videoUrl} controls autoPlay loop className="w-full aspect-video bg-gray-900 rounded-t-2xl" />
      <div className="p-4 flex items-center justify-between">
        <span className="text-sm text-gray-500 font-medium">Generated Video</span>
        <div className="flex gap-2">
          <a href={videoUrl} download={`avatar_${jobId}.mp4`}
            className="flex items-center gap-1.5 px-4 py-2 bg-brand-500 hover:bg-brand-600 text-white rounded-xl text-sm font-medium transition-all shadow-lg shadow-brand-500/20 hover:shadow-brand-500/30">
            <FiDownload className="w-4 h-4" /> Download
          </a>
        </div>
      </div>
    </div>
  )
}
