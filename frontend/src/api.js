const BASE = ''  // proxied to backend via vite

async function request(path, opts = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) {
    const text = await res.text()
    throw new Error(`${res.status} ${res.statusText}: ${text}`)
  }
  if (res.status === 204) return null
  return res.json()
}

export const api = {
  // profile
  setup: (data) => request('/api/setup', { method: 'POST', body: JSON.stringify(data) }),
  getProfile: () => request('/api/profile'),
  patchProfile: (data) => request('/api/profile', { method: 'PATCH', body: JSON.stringify(data) }),

  // chat
  sendChat: (message, image_b64 = null) =>
    request('/api/chat', { method: 'POST', body: JSON.stringify({ message, image_b64 }) }),
  chatHistory: () => request('/api/chat/history'),
  clearChat: () => request('/api/chat/history', { method: 'DELETE' }),

  // food
  addFood: (data) => request('/api/food', { method: 'POST', body: JSON.stringify(data) }),
  listFood: (date) => request(`/api/food${date ? `?date=${date}` : ''}`),
  deleteFood: (id) => request(`/api/food/${id}`, { method: 'DELETE' }),

  // weight
  addWeight: (data) => request('/api/weight', { method: 'POST', body: JSON.stringify(data) }),
  listWeight: () => request('/api/weight'),
  patchWeight: (id, data) => request(`/api/weight/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteWeight: (id) => request(`/api/weight/${id}`, { method: 'DELETE' }),

  // measurements
  addMeasurement: (data) => request('/api/measurements', { method: 'POST', body: JSON.stringify(data) }),
  listMeasurements: () => request('/api/measurements'),
  patchMeasurement: (id, data) => request(`/api/measurements/${id}`, { method: 'PATCH', body: JSON.stringify(data) }),
  deleteMeasurement: (id) => request(`/api/measurements/${id}`, { method: 'DELETE' }),
}

export function todayIso() {
  const d = new Date()
  const yyyy = d.getFullYear()
  const mm = String(d.getMonth() + 1).padStart(2, '0')
  const dd = String(d.getDate()).padStart(2, '0')
  return `${yyyy}-${mm}-${dd}`
}
