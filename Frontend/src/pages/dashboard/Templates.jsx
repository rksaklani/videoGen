import { useNavigate } from 'react-router-dom'
import TemplatesPage from '../../components/TemplatesPage'

export default function Templates() {
  const navigate = useNavigate()

  const handleSelect = (template) => {
    // Navigate to text-to-video with template info
    navigate('/dashboard/text-to-video', { state: { templateImage: template.id } })
  }

  return (
    <div className="animate-fade-up">
      <TemplatesPage onSelect={handleSelect} />
      <div className="mt-4 p-3 rounded-xl bg-brand-50 border border-brand-200">
        <p className="text-xs text-brand-700">Tip: For repeat use, create a saved avatar in "My Avatars" — upload once, generate forever.</p>
      </div>
    </div>
  )
}
