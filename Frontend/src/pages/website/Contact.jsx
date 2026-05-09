import { useState } from 'react'
import { FiMail, FiMessageSquare, FiSend } from 'react-icons/fi'

export default function Contact() {
  const [sent, setSent] = useState(false)

  const handleSubmit = (e) => { e.preventDefault(); setSent(true) }

  return (
    <div className="max-w-4xl mx-auto px-6 py-20">
      <h1 className="text-4xl font-bold text-gray-900 mb-6">Contact Us</h1>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        <div className="glass-card rounded-3xl p-8">
          <h2 className="text-xl font-bold text-gray-800 mb-4">Get in touch</h2>
          <div className="space-y-4 text-gray-600">
            <div className="flex items-center gap-3">
              <FiMail className="w-5 h-5 text-brand-500" />
              <span>support@videogen.app</span>
            </div>
            <div className="flex items-center gap-3">
              <FiMessageSquare className="w-5 h-5 text-brand-500" />
              <span>Live chat available 9am-6pm IST</span>
            </div>
          </div>
          <div className="mt-8 p-4 rounded-xl bg-brand-50 border border-brand-200">
            <p className="text-sm text-brand-700">For enterprise inquiries, API access, or custom solutions, reach out and we'll get back within 24 hours.</p>
          </div>
        </div>

        <div className="glass-card rounded-3xl p-8">
          {sent ? (
            <div className="text-center py-8">
              <p className="text-4xl mb-4">✅</p>
              <h3 className="text-xl font-bold text-gray-800">Message sent!</h3>
              <p className="text-gray-500 mt-2">We'll get back to you within 24 hours.</p>
            </div>
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Name</label>
                <input type="text" required placeholder="Your name"
                  className="w-full px-4 py-2.5 glass rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Email</label>
                <input type="email" required placeholder="you@example.com"
                  className="w-full px-4 py-2.5 glass rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-400" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1.5">Message</label>
                <textarea required rows={4} placeholder="How can we help?"
                  className="w-full px-4 py-2.5 glass rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-400 resize-none" />
              </div>
              <button type="submit"
                className="w-full py-3 bg-gradient-to-r from-brand-500 to-purple-500 text-white rounded-xl font-semibold shadow-lg shadow-brand-500/25 flex items-center justify-center gap-2">
                <FiSend className="w-4 h-4" /> Send Message
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
