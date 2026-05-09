/**
 * Server max output length (seconds) from GET /api/v1/health → generation_limits.
 * Fallback matches Backend/config.yaml inference.max_duration_seconds default.
 */
export function getMaxOutputSeconds(health) {
  return health?.generation_limits?.max_output_duration_seconds ?? 300
}
