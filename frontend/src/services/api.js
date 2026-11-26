const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export async function apiFetch(path, options = {}) {
  const res = await fetch(${API_BASE}, options);
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(errText || Request failed: );
  }
  return res.json();
}