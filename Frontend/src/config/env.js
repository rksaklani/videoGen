/**
 * Browser-exposed configuration from Vite (`import.meta.env.VITE_*`).
 * Copy `Frontend/.env.example` → `Frontend/.env` and adjust.
 */
function stripTrailingSlash(url) {
  if (!url) return ''
  return String(url).replace(/\/$/, '')
}

/** Backend origin without trailing slash (empty string = same origin / dev proxy). */
export const apiOrigin = stripTrailingSlash(import.meta.env.VITE_API_URL)

/** RTK Query base path for `/api/v1`. */
export const apiV1Base = `${apiOrigin}/api/v1`

export const appName = import.meta.env.VITE_APP_NAME || 'videoGen'
export const appVersion = import.meta.env.VITE_APP_VERSION || ''
