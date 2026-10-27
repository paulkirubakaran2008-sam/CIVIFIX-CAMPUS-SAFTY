const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
// Report images may be an absolute URL (Cloudinary, in production) or a
// relative /uploads/... path served by the backend (local dev fallback).
export function resolveImageUrl(imageUrl) {
  if (!imageUrl) return null
  return imageUrl.startsWith('http') ? imageUrl : `${BASE_URL}${imageUrl}`
}
export async function api(path, options = {}) {
  const token = localStorage.getItem('civicfix_token')
  const headers = { ...(options.body instanceof FormData ? {} : { 'Content-Type': 'application/json' }), ...options.headers }
  if (token) headers.Authorization = `Bearer ${token}`
  const response = await fetch(`${BASE_URL}${path}`, { ...options, headers })
  if (!response.ok) { const body = await response.json().catch(() => ({})); throw new Error(body.detail || 'Something went wrong') }
  return response.json()
}
