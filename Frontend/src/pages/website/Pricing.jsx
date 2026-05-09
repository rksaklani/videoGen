import { Link } from 'react-router-dom'
import { FiCheck } from 'react-icons/fi'

const plans = [
  {
    id: 'free', name: 'Free', price: '$0', period: '/month', desc: 'Try it out',
    features: ['5 videos per month', '5 second max', '1 avatar', 'Watermark', '10+ voices'],
    cta: 'Get Started', ctaStyle: 'glass-card text-gray-700 hover:bg-white/80', ctaLink: '/signup',
  },
  {
    id: 'creator', name: 'Creator', price: '$29', period: '/month', desc: 'For content creators', popular: true,
    features: ['100 videos per month', '30 second max', '5 avatars', 'No watermark', '300+ voices', 'Multi-character'],
    cta: 'Start Creator', ctaStyle: 'bg-gradient-to-r from-brand-500 to-purple-500 text-white shadow-lg shadow-brand-500/25',
  },
  {
    id: 'pro', name: 'Pro', price: '$79', period: '/month', desc: 'For professionals',
    features: ['500 videos per month', '2 minute max', '20 avatars', 'No watermark', 'Priority queue', 'Voice cloning', 'API access'],
    cta: 'Start Pro', ctaStyle: 'glass-card text-gray-700 hover:bg-white/80',
  },
  {
    id: 'enterprise', name: 'Enterprise', price: '$299', period: '/month', desc: 'For teams',
    features: ['Unlimited videos', '5 minute max', '100 avatars', 'Dedicated GPU', 'Custom branding', 'SLA support', 'On-premise option'],
    cta: 'Contact Sales', ctaStyle: 'glass-card text-gray-700 hover:bg-white/80', ctaLink: '/contact',
  },
]

export default function Pricing() {
  const handleSubscribe = async (planId) => {
    const token = localStorage.getItem('token')
    if (!token) {
      localStorage.setItem('pending_plan', planId)
      window.location.href = '/signup'
      return
    }

    // Demo mode — simulate plan activation without real Stripe
    const confirmed = window.confirm(
      `Subscribe to ${planId.charAt(0).toUpperCase() + planId.slice(1)} plan?\n\n` +
      `This is demo mode. In production, this opens Stripe Checkout.\n\n` +
      `Click OK to activate the plan.`
    )
    if (confirmed) {
      localStorage.setItem('user_plan', planId)
      alert(`✅ ${planId.charAt(0).toUpperCase() + planId.slice(1)} plan activated!\n\nGo to Dashboard → Settings to see your plan.`)
      window.location.href = '/dashboard/settings'
    }
  }

  return (
    <div className="max-w-7xl mx-auto px-6 py-20">
      <div className="text-center mb-16">
        <h1 className="text-4xl font-bold text-gray-900">Simple, transparent pricing</h1>
        <p className="text-gray-500 mt-3 text-lg">Start free, upgrade when you need more</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 max-w-6xl mx-auto">
        {plans.map((plan) => (
          <div key={plan.id} className={`glass-card rounded-3xl p-6 relative flex flex-col ${plan.popular ? 'ring-2 ring-brand-500 scale-105' : ''}`}>
            {plan.popular && (
              <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-4 py-1 bg-gradient-to-r from-brand-500 to-purple-500 text-white text-xs font-semibold rounded-full">
                Most Popular
              </div>
            )}
            <h3 className="text-lg font-bold text-gray-800">{plan.name}</h3>
            <p className="text-sm text-gray-500 mt-1">{plan.desc}</p>
            <div className="mt-4 mb-6">
              <span className="text-3xl font-bold text-gray-900">{plan.price}</span>
              <span className="text-gray-400">{plan.period}</span>
            </div>
            <ul className="space-y-2.5 mb-6 flex-1">
              {plan.features.map((f) => (
                <li key={f} className="flex items-start gap-2 text-sm text-gray-600">
                  <FiCheck className="w-4 h-4 text-emerald-500 flex-shrink-0 mt-0.5" /> {f}
                </li>
              ))}
            </ul>
            {plan.ctaLink ? (
              <Link to={plan.ctaLink} className={`block text-center px-6 py-3 rounded-xl font-semibold transition-all ${plan.ctaStyle}`}>
                {plan.cta}
              </Link>
            ) : (
              <button onClick={() => handleSubscribe(plan.id)}
                className={`w-full px-6 py-3 rounded-xl font-semibold transition-all ${plan.ctaStyle}`}>
                {plan.cta}
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
