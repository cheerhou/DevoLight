import type { RouterRequestPayload, RouterResponse } from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

export async function routeRequest(payload: RouterRequestPayload): Promise<RouterResponse> {
  const response = await fetch(`${API_BASE_URL}/route?session_id=${encodeURIComponent(payload.session_id)}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload.payload),
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `请求失败，状态码 ${response.status}`);
  }

  return (await response.json()) as RouterResponse;
}
