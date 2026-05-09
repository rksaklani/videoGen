import { Link } from 'react-router-dom'
import { FiPlay, FiMic, FiGlobe, FiZap, FiUsers, FiSmile } from 'react-icons/fi'

const features = [
  { icon: <FiMic className="w-6 h-6" />, title: 'Text to Video', desc: 'Type any text and watch your avatar speak it naturally with lip-sync.' },
  { icon: <FiGlobe className="w-6 h-6" />, title: '20+ Languages', desc: '300+ voices across English, Hindi, Chinese, Spanish, French, and more.' },
  { icon: <FiZap className="w-6 h-6" />, title: 'AI-Powered', desc: 'State-of-the-art diffusion model generates realistic human animations.' },
  { icon: <FiUsers className="w-6 h-6" />, title: 'Multi-Character', desc: 'Generate videos with multiple characters talking in the same scene.' },
  { icon: <FiSmile className="w-6 h-6" />, title: 'Emotion Control', desc: 'Control facial expressions and emotions in your generated videos.' },
  { icon: <FiPlay className="w-6 h-6" />, title: 'Any Style', desc: 'Works with photos, cartoons, 3D renders, and anime characters.' },
]

export default function Home() {
  return (
    <div>
      {/* Hero */}
      <section className="max-w-7xl mx-auto px-6 pt-20 pb-16 text-center">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass-card text-sm text-brand-600 font-medium mb-6">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          Powered by VideoGen AI
        </div>
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-gray-900 leading-tight max-w-4xl mx-auto">
          Create Talking Avatar Videos with <span className="gradient-text">AI</span>
        </h1>
        <p className="text-lg text-gray-500 mt-6 max-w-2xl mx-auto">
          Upload a photo, type your script, and generate professional talking avatar videos in minutes. No camera, no studio, no actors needed.
        </p>
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-10">
          <Link to="/signup"
            className="px-8 py-4 bg-gradient-to-r from-brand-500 to-purple-500 text-white rounded-2xl font-semibold text-lg shadow-xl shadow-brand-500/25 hover:shadow-brand-500/40 transition-all hover:scale-105">
            Get Started Free →
          </Link>
          <Link to="/pricing"
            className="px-8 py-4 glass-card rounded-2xl font-semibold text-gray-700 hover:bg-white/80 transition-all">
            View Pricing
          </Link>
        </div>
      </section>

      {/* Demo Video Placeholder */}
      <section className="max-w-4xl mx-auto px-6 pb-20">
        <div className="glass-card rounded-3xl overflow-hidden aspect-video flex items-center justify-center bg-gradient-to-br from-brand-50 to-purple-50">
          <div className="text-center">
            <div className="w-20 h-20 rounded-full bg-white/80 flex items-center justify-center mx-auto shadow-xl mb-4">
              <FiPlay className="w-8 h-8 text-brand-500 ml-1" />
            </div>
            <p className="text-gray-500 font-medium">See Avatar Studio in action</p>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="max-w-7xl mx-auto px-6 pb-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-gray-900">Everything you need</h2>
          <p className="text-gray-500 mt-2">Professional avatar videos in minutes, not hours</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {features.map((f, i) => (
            <div key={i} className="glass-card rounded-2xl p-6 hover:scale-[1.02] transition-all">
              <div className="w-12 h-12 rounded-xl bg-brand-50 flex items-center justify-center text-brand-500 mb-4">{f.icon}</div>
              <h3 className="font-semibold text-gray-800 mb-2">{f.title}</h3>
              <p className="text-sm text-gray-500">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="max-w-4xl mx-auto px-6 pb-20">
        <div className="glass-card rounded-3xl p-12 text-center bg-gradient-to-br from-brand-50 to-purple-50">
          <h2 className="text-3xl font-bold text-gray-900 mb-4">Ready to create?</h2>
          <p className="text-gray-500 mb-8">Start generating talking avatar videos in minutes.</p>
          <Link to="/signup"
            className="inline-block px-8 py-4 bg-gradient-to-r from-brand-500 to-purple-500 text-white rounded-2xl font-semibold shadow-xl shadow-brand-500/25 hover:shadow-brand-500/40 transition-all hover:scale-105">
            Get Started Free →
          </Link>
        </div>
      </section>
    </div>
  )
}
