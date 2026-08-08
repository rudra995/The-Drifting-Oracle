/**
 * Centralized API utility for The Drifting Oracle frontend.
 * All backend calls go through fetchApi().
 */

export const API_BASE = 'http://localhost:8000';

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

  if (!response.ok) {
    throw new Error(`Missing endpoint: ${endpoint}`);
  }

  return response.json();
}
