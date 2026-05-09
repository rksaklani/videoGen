import { FiImage } from 'react-icons/fi'

const TEMPLATES = [
  { id: 'sample-1', name: 'Campfire Person', category: 'samples', desc: 'Person by a campfire in forest' },
  { id: 'sample-2', name: 'Forest Portrait', category: 'samples', desc: 'Person in a forested area' },
  { id: 'sample-3', name: 'Guitar Player', category: 'samples', desc: 'Person playing guitar' },
  { id: 'sample-4', name: 'Sunlit Forest', category: 'samples', desc: 'Person in sunlit forest' },
  { id: 'sample-src1', name: 'Source Portrait 1', category: 'source', desc: 'Reference portrait' },
  { id: 'sample-src2', name: 'Source Portrait 2', category: 'source', desc: 'Reference portrait' },
  { id: 'sample-src3', name: 'Source Portrait 3', category: 'source', desc: 'Reference portrait' },
  { id: 'sample-src4', name: 'Source Portrait 4', category: 'source', desc: 'Reference portrait' },
]

export default function TemplatesPage({ onSelect }) {
  const apiUrl = import.meta.env.VITE_API_URL || ''

  return (
    <div className="animate-fade-up">
      <div className="mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Template Gallery</h2>
        <p className="text-gray-500 text-sm mt-1">Pick a pre-made avatar to get started quickly</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {TEMPLATES.map((t) => (
          <div key={t.id} onClick={() => onSelect(t)}
            className="glass-card rounded-2xl overflow-hidden cursor-pointer transition-all hover:scale-[1.03] hover:shadow-xl group">
            <div className="aspect-square bg-gradient-to-br from-gray-100 to-gray-200 flex items-center justify-center overflow-hidden">
              <img
                src={`${apiUrl}/api/v1/templates/${t.id}/image`}
                alt={t.name}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform"
                onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex' }}
              />
              <div className="hidden items-center justify-center w-full h-full">
                <FiImage className="w-8 h-8 text-gray-300" />
              </div>
            </div>
            <div className="p-3">
              <p className="text-sm font-semibold text-gray-800">{t.name}</p>
              <p className="text-xs text-gray-400">{t.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
