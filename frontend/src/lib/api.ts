export const API_URL: string =
  (import.meta as any).env.VITE_API_URL || 'https://pillpulse-backend.onrender.com';

/** The patient this device acts for: the patient's own code, or the code a caregiver linked to. */
export function getPatientId(): string {
  try {
    return localStorage.getItem('pillpulse_patient_code') || 'GUEST-0000';
  } catch {
    return 'GUEST-0000';
  }
}

export async function apiJson<T = any>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, init);
  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    const message = body?.error || body?.detail || `Request failed (${res.status})`;
    throw new Error(typeof message === 'string' ? message : JSON.stringify(message));
  }
  return body as T;
}

export function postJson<T = any>(path: string, data: unknown): Promise<T> {
  return apiJson<T>(path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
}

/** "08:00" -> "8:00 AM" */
export function to12h(hhmm: string): string {
  const [h, m] = hhmm.split(':').map(Number);
  if (Number.isNaN(h)) return hhmm;
  return `${h % 12 || 12}:${String(m).padStart(2, '0')} ${h < 12 ? 'AM' : 'PM'}`;
}
