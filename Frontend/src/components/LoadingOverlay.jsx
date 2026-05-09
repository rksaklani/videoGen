export default function LoadingOverlay({ show, message = "Loading..." }) {
  if (!show) return null

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 flex items-center justify-center">
      <div className="bg-dark-800 rounded-2xl p-8 flex flex-col items-center gap-4 border border-gray-700">
        <div className="w-12 h-12 border-4 border-primary-500 border-t-transparent rounded-full animate-spin" />
        <p className="text-sm text-gray-300">{message}</p>
      </div>
    </div>
  )
}
