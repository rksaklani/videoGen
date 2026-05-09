import { useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import { FiUploadCloud, FiImage, FiMusic, FiCheck } from 'react-icons/fi'

export default function FileUpload({ label, accept, icon, file, onFile }) {
  const onDrop = useCallback((files) => {
    if (files.length > 0) onFile(files[0])
  }, [onFile])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({ onDrop, accept, maxFiles: 1 })
  const Icon = icon === 'image' ? FiImage : FiMusic

  return (
    <div
      {...getRootProps()}
      className={`relative rounded-2xl p-5 text-center cursor-pointer transition-all duration-200
        ${isDragActive ? 'bg-brand-50 border-2 border-brand-400 scale-[1.02]' :
          file ? 'glass-card border-2 border-emerald-300' : 'glass-card border-2 border-dashed border-gray-200 hover:border-brand-300 hover:bg-white/60'}`}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-2">
        {file ? (
          <>
            <div className="w-10 h-10 rounded-full bg-emerald-100 flex items-center justify-center">
              <FiCheck className="w-5 h-5 text-emerald-600" />
            </div>
            <p className="text-sm font-medium text-gray-800 truncate max-w-full">{file.name}</p>
            <p className="text-xs text-gray-400">{(file.size / 1024 / 1024).toFixed(1)} MB — Click to change</p>
          </>
        ) : (
          <>
            <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center">
              {isDragActive ? <FiUploadCloud className="w-5 h-5 text-brand-500 animate-bounce" /> : <Icon className="w-5 h-5 text-gray-400" />}
            </div>
            <p className="text-sm font-medium text-gray-600">{label}</p>
            <p className="text-xs text-gray-400">Drag & drop or click to browse</p>
          </>
        )}
      </div>
    </div>
  )
}
