import { configureStore } from '@reduxjs/toolkit'
import { avatarApi } from './api'

export const store = configureStore({
  reducer: {
    [avatarApi.reducerPath]: avatarApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware().concat(avatarApi.middleware),
})
