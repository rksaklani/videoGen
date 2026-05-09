import { useGetHealthQuery } from '../../store/api'
import { FiArrowRight, FiUser, FiMic, FiMusic, FiUsers } from 'react-icons/fi'
import { Link } from 'react-router-dom'

export default function Create() {
  const { data: health } = useGetHealthQuery()
  const isReady = health?.engine_loaded
  const user = JSON.parse(localStorage.getItem('user') || '{}')

  const cards = [
    { to: '/dashboard/my-avatars', icon: <FiUser className="w-6 h-6" />, title: 'My Avatars', desc: 'Upload once, generate forever. The fastest way to create videos.', color: 'from-brand-500 to-purple-500', tag: 'Recommended' },
    { to: '/dashboard/text-to-video', icon: <FiMic className="w-6 h-6" />, title: 'Text to Video', desc: 'Quick one-off: upload any image and type your script.', color: 'from-cyan-500 to-blue-500' },
    { to: '/dashboard/audio-to-video', icon: <FiMusic className="w-6 h-6" />, title: 'Audio to Video', desc: 'Use your own recorded audio to drive the avatar.', color: 'from-emerald-500 to-teal-500' },
    { to: '/dashboard/dialogue', icon: <FiUsers className="w-6 h-6" />, title: 'Multi-Character', desc: 'Two characters talking — our unique feature no one else has.', color: 'from-pink-500 to-rose-500', tag: 'Unique' },
  ]

  return (
    <div className="animate-fade-up">
      {/* Welcome Header */}
      <div className="glass-card rounded-2xl p-8 mb-8 bg-gradient-to-r from-brand-50 to-purple-50">
        <h1 className="text-3xl font-bold text-gray-800">
          Welcome back{user.name ? `, ${user.name}` : ''} 👋
        </h1>
        <p className="text-gray-500 mt-2 text-lg">What would you like to create today?</p>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
        {cards.map((card) => (
          <Link key={card.to} to={card.to}
            className="glass-card rounded-2xl p-6 hover:scale-[1.02] transition-all group cursor-pointer relative overflow-hidden">
            {card.tag && (
              <span className="absolute top-4 right-4 px-2.5 py-1 bg-gradient-to-r from-brand-500 to-purple-500 text-white text-[10px] font-bold rounded-full uppercase tracking-wider">
                {card.tag}
              </span>
            )}
            <div className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${card.color} flex items-center justify-center text-white mb-5 shadow-lg`}>
              {card.icon}
            </div>
            <h3 className="text-lg font-bold text-gray-800 mb-2">{card.title}</h3>
            <p className="text-sm text-gray-500 mb-5 leading-relaxed">{card.desc}</p>
            <div className="flex items-center gap-1.5 text-sm text-brand-600 font-semibold group-hover:gap-3 transition-all">
              Get started <FiArrowRight className="w-4 h-4" />
            </div>
          </Link>
        ))}
      </div>

      {/* Status Bar */}
      <div className="mt-8 glass-card rounded-2xl p-5 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className={`w-3 h-3 rounded-full ${isReady ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400 animate-pulse'}`} />
          <span className="text-sm text-gray-600">
            {isReady ? 'AI Engine ready — start creating!' : 'AI models loading... (2-3 minutes)'}
          </span>
        </div>
        <span className="text-xs text-gray-400">{health?.gpu?.gpu_name || ''}</span>
      </div>
    </div>
  )
}
