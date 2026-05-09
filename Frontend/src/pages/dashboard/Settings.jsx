import { useState } from 'react'
import { useGetHealthQuery } from '../../store/api'
import { FiUser, FiCreditCard, FiCpu, FiCheck, FiZap, FiStar, FiAward, FiShield } from 'react-icons/fi'

const PLANS = [
  {
    id: 'free', name: 'Free', price: 0, icon: <FiZap />,
    gradient: 'from-gray-400 to-gray-500',
    badge: 'bg-gray-100 text-gray-600 border-gray-200',
    videos: 5, duration: '5s', avatars: 1,
    features: ['5 videos/month', '5 second max', '1 avatar', 'Watermark'],
  },
  {
    id: 'creator', name: 'Creator', price: 29, icon: <FiStar />,
    gradient: 'from-brand-500 to-purple-500',
    badge: 'bg-brand-50 text-brand-700 border-brand-200',
    videos: 100, duration: '30s', avatars: 5, popular: true,
    features: ['100 videos/month', '30 second max', '5 avatars', 'No watermark', '300+ voices'],
  },
  {
    id: 'pro', name: 'Pro', price: 79, icon: <FiAward />,
    gradient: 'from-purple-500 to-pink-500',
    badge: 'bg-purple-50 text-purple-700 border-purple-200',
    videos: 500, duration: '2 min', avatars: 20,
    features: ['500 videos/month', '2 minute max', '20 avatars', 'Priority queue', 'Voice cloning', 'Multi-character'],
  },
  {
    id: 'enterprise', name: 'Enterprise', price: 299, icon: <FiShield />,
    gradient: 'from-amber-500 to-orange-500',
    badge: 'bg-amber-50 text-amber-700 border-amber-200',
    videos: '∞', duration: '5 min', avatars: 100,
    features: ['Unlimited videos', '5 minute max', '100 avatars', 'Dedicated GPU', 'API access', 'SLA support'],
  },
]

export default function Settings() {
  const { data: health } = useGetHealthQuery()
  const user = JSON.parse(localStorage.getItem('user') || '{}')
  const [currentPlan, setCurrentPlan] = useState(localStorage.getItem('user_plan') || 'free')
  const [showPlans, setShowPlans] = useState(false)

  const activePlan = PLANS.find(p => p.id === currentPlan) || PLANS[0]

  const handleUpgrade = (planId) => {
    if (planId === currentPlan) return
    const plan = PLANS.find(p => p.id === planId)
    if (confirm(`${planId === 'free' ? 'Downgrade' : 'Upgrade'} to ${plan.name} ($${plan.price}/mo)?\n\nDemo mode — in production this opens Stripe Checkout.`)) {
      localStorage.setItem('user_plan', planId)
      setCurrentPlan(planId)
      setShowPlans(false)
    }
  }

  return (
    <div className="animate-fade-up">
      <h1 className="text-2xl font-bold text-gray-800 mb-2">Settings</h1>
      <p className="text-gray-500 mb-8">Manage your account, subscription, and system</p>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column */}
        <div className="space-y-6">

        {/* Profile Card */}
        <div className="glass-card rounded-2xl overflow-hidden">
          <div className="bg-gradient-to-r from-brand-500 to-purple-500 px-6 py-4">
            <div className="flex items-center gap-4">
              <div className="w-14 h-14 rounded-full bg-white/20 backdrop-blur flex items-center justify-center text-white text-xl font-bold">
                {user.name?.[0]?.toUpperCase() || 'U'}
              </div>
              <div>
                <h3 className="text-white font-bold text-lg">{user.name || 'Anonymous'}</h3>
                <p className="text-white/70 text-sm">{user.email || 'Not set'}</p>
              </div>
            </div>
          </div>
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FiUser className="w-4 h-4 text-gray-400" />
                <span className="text-sm text-gray-500">Account Type</span>
              </div>
              <span className={`px-3 py-1 rounded-full text-xs font-semibold border ${activePlan.badge}`}>
                {activePlan.name}
              </span>
            </div>
          </div>
        </div>

        {/* Subscription Card */}
        <div className="glass-card rounded-2xl p-6">
          <div className="flex items-center justify-between mb-5">
            <div className="flex items-center gap-2">
              <FiCreditCard className="w-5 h-5 text-gray-600" />
              <h3 className="font-semibold text-gray-800">Subscription</h3>
            </div>
            <button onClick={() => setShowPlans(!showPlans)}
              className="px-4 py-1.5 text-sm font-medium text-brand-600 bg-brand-50 rounded-lg hover:bg-brand-100 transition-colors">
              {showPlans ? 'Hide Plans' : currentPlan === 'free' ? 'Upgrade' : 'Change Plan'}
            </button>
          </div>

          {/* Current Plan Summary */}
          <div className={`rounded-xl p-4 bg-gradient-to-r ${activePlan.gradient} mb-4`}>
            <div className="flex items-center justify-between text-white">
              <div>
                <p className="text-white/70 text-xs uppercase tracking-wider">Current Plan</p>
                <p className="text-2xl font-bold mt-1">{activePlan.name}</p>
              </div>
              <div className="text-right">
                <p className="text-3xl font-bold">${activePlan.price}</p>
                <p className="text-white/70 text-xs">/month</p>
              </div>
            </div>
            <div className="flex gap-4 mt-4 pt-3 border-t border-white/20">
              <div>
                <p className="text-white/60 text-xs">Videos</p>
                <p className="text-white font-semibold">{activePlan.videos}/mo</p>
              </div>
              <div>
                <p className="text-white/60 text-xs">Duration</p>
                <p className="text-white font-semibold">{activePlan.duration}</p>
              </div>
              <div>
                <p className="text-white/60 text-xs">Avatars</p>
                <p className="text-white font-semibold">{activePlan.avatars}</p>
              </div>
            </div>
          </div>

          {/* Plan Selection */}
          {showPlans && (
            <div className="space-y-3 animate-fade-up">
              <p className="text-sm text-gray-500 mb-3">Select a plan:</p>
              {PLANS.map((plan) => (
                <div key={plan.id}
                  onClick={() => handleUpgrade(plan.id)}
                  className={`relative rounded-xl p-4 cursor-pointer transition-all hover:scale-[1.01]
                    ${plan.id === currentPlan
                      ? 'ring-2 ring-brand-500 bg-brand-50/50'
                      : 'glass-card hover:bg-white/60'}`}>
                  {plan.popular && (
                    <span className="absolute -top-2 right-3 px-2 py-0.5 bg-gradient-to-r from-brand-500 to-purple-500 text-white text-[10px] font-bold rounded-full">
                      POPULAR
                    </span>
                  )}
                  <div className="flex items-center gap-4">
                    <div className={`w-10 h-10 rounded-xl bg-gradient-to-br ${plan.gradient} flex items-center justify-center text-white shadow-lg`}>
                      {plan.icon}
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="font-semibold text-gray-800">{plan.name}</span>
                        {plan.id === currentPlan && (
                          <span className="px-2 py-0.5 bg-emerald-100 text-emerald-700 text-[10px] font-semibold rounded-full">CURRENT</span>
                        )}
                      </div>
                      <p className="text-xs text-gray-400 mt-0.5">{plan.features.slice(0, 3).join(' · ')}</p>
                    </div>
                    <div className="text-right">
                      <p className="text-lg font-bold text-gray-800">${plan.price}</p>
                      <p className="text-xs text-gray-400">/month</p>
                    </div>
                  </div>
                  {plan.id === currentPlan && (
                    <div className="mt-3 pt-3 border-t border-gray-100">
                      <div className="flex flex-wrap gap-2">
                        {plan.features.map((f) => (
                          <span key={f} className="flex items-center gap-1 text-xs text-gray-500">
                            <FiCheck className="w-3 h-3 text-emerald-500" /> {f}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}

          {currentPlan !== 'free' && !showPlans && (
            <button onClick={() => handleUpgrade('free')}
              className="w-full py-2 text-sm text-gray-400 hover:text-red-500 transition-colors">
              Cancel Subscription (Demo)
            </button>
          )}
        </div>
        </div>

        {/* Right Column */}
        <div className="space-y-6">

        {/* System Status */}
        <div className="glass-card rounded-2xl p-6">
          <div className="flex items-center gap-2 mb-5">
            <FiCpu className="w-5 h-5 text-gray-600" />
            <h3 className="font-semibold text-gray-800">System Status</h3>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="rounded-xl bg-gray-50 p-4">
              <p className="text-xs text-gray-400 uppercase tracking-wider">GPU</p>
              <p className="text-sm font-semibold text-gray-800 mt-1">{health?.gpu?.gpu_name || 'N/A'}</p>
            </div>
            <div className="rounded-xl bg-gray-50 p-4">
              <p className="text-xs text-gray-400 uppercase tracking-wider">VRAM</p>
              <p className="text-sm font-semibold text-gray-800 mt-1">{health?.gpu?.gpu_memory_total || 'N/A'}</p>
            </div>
            <div className="rounded-xl bg-gray-50 p-4">
              <p className="text-xs text-gray-400 uppercase tracking-wider">Engine</p>
              <p className={`text-sm font-semibold mt-1 ${health?.engine_loaded ? 'text-emerald-600' : 'text-red-500'}`}>
                {health?.engine_loaded ? '● Online' : '○ Loading...'}
              </p>
            </div>
            <div className="rounded-xl bg-gray-50 p-4">
              <p className="text-xs text-gray-400 uppercase tracking-wider">Queue</p>
              <p className="text-sm font-semibold text-gray-800 mt-1">{health?.gpu?.queue_pending || 0} pending</p>
            </div>
          </div>
        </div>
        </div>
      </div>
    </div>
  )
}
