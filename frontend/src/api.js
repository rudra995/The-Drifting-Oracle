/**
 * Centralized API utility for The Drifting Oracle frontend.
 * All backend calls go through fetchApi().
 */

// VITE_API_BASE lets a build target a non-local backend (e.g. a real
// multi-host Kubernetes deployment); falls back to localhost:8000 for local
// dev, which is unaffected when the env var isn't set.
export const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

/**
 * Fetch data from the backend API.
 * @param {string} endpoint - The API endpoint path (e.g. '/api/v1/models')
 * @param {RequestInit} options - Optional fetch options (method, body, headers)
 * @returns {Promise<any>} Parsed JSON response
 * @throws {Error} With message "Missing endpoint: <endpoint>" on failure
 */
export async function fetchApi(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;

  const defaultHeaders = {
    'Content-Type': 'application/json',
  };

  const config = {
    ...options,
    headers: {
      ...defaultHeaders,
      ...options.headers,
    },
  };

  // Don't set Content-Type for FormData (file uploads)
  if (options.body instanceof FormData) {
    delete config.headers['Content-Type'];
  }

  let response;
  try {
    response = await fetch(url, config);
  } catch {
    throw new Error(`Missing endpoint: ${endpoint}`);
  }

  // The backend now returns real 4xx/5xx status codes for request failures
  // (bad CSV, model not loaded, etc.), with the same
  // {status: "failed", error: "..."} body it always sent. Parse that body
  // instead of discarding it, so callers that already check
  // `result.status !== 'success'` still get the specific error message.
  // Only fall back to a generic error if the body itself isn't valid JSON
  // (a truly unexpected failure, e.g. a proxy error page).
  if (!response.ok) {
    try {
      return await response.json();
    } catch {
      throw new Error(`Missing endpoint: ${endpoint}`);
    }
  }

  return response.json();
}
