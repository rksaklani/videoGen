import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react'

export const avatarApi = createApi({
  reducerPath: 'avatarApi',
  baseQuery: fetchBaseQuery({ baseUrl: `${import.meta.env.VITE_API_URL || ''}/api/v1` }),
  tagTypes: ['Jobs'],
  endpoints: (builder) => ({
    // Health check
    getHealth: builder.query({
      query: () => '/health',
    }),

    // Generate avatar video
    generateAvatar: builder.mutation({
      query: ({ image, audio, prompt, maxDuration }) => {
        const formData = new FormData()
        formData.append('image', image)
        formData.append('audio', audio)
        formData.append('prompt', prompt || '')
        // Use ?? so 0 ("match full audio") is sent; `||` wrongly turned 0 into 5.
        formData.append('max_duration', String(maxDuration ?? 5))
        return { url: '/generate', method: 'POST', body: formData }
      },
      invalidatesTags: ['Jobs'],
    }),

    // Get job status (stops polling on error)
    getJobStatus: builder.query({
      query: (jobId) => `/status/${jobId}`,
      transformErrorResponse: (response) => {
        return { status: response.status, message: 'Job not found' }
      },
    }),

    // List all jobs
    getJobs: builder.query({
      query: () => '/jobs',
      providesTags: ['Jobs'],
    }),

    // Generate avatar from TEXT (TTS + avatar)
    generateFromText: builder.mutation({
      query: ({ image, text, voice, prompt, maxDuration, rate }) => {
        const formData = new FormData()
        formData.append('image', image)
        formData.append('text', text)
        formData.append('voice', voice || 'en-male')
        formData.append('prompt', prompt || '')
        formData.append('max_duration', String(maxDuration ?? 5))
        formData.append('rate', rate || '+0%')
        return { url: '/generate-from-text', method: 'POST', body: formData }
      },
      invalidatesTags: ['Jobs'],
    }),

    // Get TTS voice presets
    getTTSVoices: builder.query({
      query: () => '/tts/voices',
    }),
  }),
})

export const {
  useGetHealthQuery,
  useGenerateAvatarMutation,
  useGenerateFromTextMutation,
  useGetTTSVoicesQuery,
  useGetJobStatusQuery,
  useGetJobsQuery,
} = avatarApi
