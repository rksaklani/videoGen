export default function About() {
  return (
    <div className="max-w-4xl mx-auto px-6 py-20">
      <h1 className="text-4xl font-bold text-gray-900 mb-6">About Avatar Studio</h1>
      <div className="glass-card rounded-3xl p-8 space-y-6 text-gray-600 leading-relaxed">
        <p>Avatar Studio is an AI-powered platform that generates realistic talking avatar videos from a single photo and text or audio input.</p>
        <p>Built on top of HunyuanVideo-Avatar, a state-of-the-art multimodal diffusion transformer model developed by Tencent, our platform brings professional-quality avatar video generation to everyone.</p>
        <h2 className="text-2xl font-bold text-gray-800 pt-4">What makes us different</h2>
        <ul className="space-y-3">
          <li className="flex gap-3"><span className="text-brand-500 font-bold">→</span> Multi-character scenes — generate two people talking in one video</li>
          <li className="flex gap-3"><span className="text-brand-500 font-bold">→</span> Emotion control — fine-grained facial expression control</li>
          <li className="flex gap-3"><span className="text-brand-500 font-bold">→</span> Any style — photos, cartoons, 3D renders, anime</li>
          <li className="flex gap-3"><span className="text-brand-500 font-bold">→</span> 300+ voices in 20+ languages</li>
          <li className="flex gap-3"><span className="text-brand-500 font-bold">→</span> Full data privacy — your data stays on our servers, never shared</li>
        </ul>
        <h2 className="text-2xl font-bold text-gray-800 pt-4">Technology</h2>
        <p>Our AI engine uses 6 neural networks working together: a video diffusion transformer, VAE, LLaVA vision-language model, CLIP text encoder, Whisper audio processor, and face detection — totaling over 40 billion parameters.</p>
      </div>
    </div>
  )
}
