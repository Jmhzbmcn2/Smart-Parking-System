import { clearSession, getSession } from './auth'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  headers.set('Accept', 'application/json')
  if (typeof init?.body === 'string' && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const session = getSession()
  if (session) headers.set('Authorization', `Bearer ${session.token}`)

  let response: Response
  try {
    response = await fetch(`/api${path}`, { ...init, headers })
  } catch (error) {
    throw new ApiError(0, error instanceof Error ? error.message : 'Network request failed')
  }

  if (response.status === 401) {
    clearSession()
    window.dispatchEvent(new Event('spms:logout'))
  }

  if (!response.ok) {
    let message = response.statusText || `Request failed (${response.status})`
    try {
      const body: { message?: unknown; detail?: unknown } = await response.json()
      const detail = body.message ?? body.detail
      if (typeof detail === 'string') message = detail
    } catch {
      // Error responses from the proxy may have no JSON body.
    }
    throw new ApiError(response.status, message)
  }

  try {
    return (await response.json()) as T
  } catch {
    throw new ApiError(response.status, 'Invalid JSON response')
  }
}
