import { DEFAULT_BACKEND_BASE_URL } from "../config";

// backendAPI.js
export const getUsers = (token) => req("/api/users", { token });

let BASE = DEFAULT_BACKEND_BASE_URL;
export function setBackendBaseUrl(url) {
  BASE = url || BASE;
}



// Internal request helper
async function req(path, { method = "GET", body, token, retries = 1 } = {}) {
  const headers = { "Content-Type": "application/json" };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30000); // 30s timeout

  try {
    const res = await fetch(`${BASE}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
      signal: controller.signal,
    });

    clearTimeout(timeout);

    if (!res.ok) {
      let detail = "";
      try {
        detail = await res.text();
      } catch (_) {
        detail = res.statusText;
      }
      throw { status: res.status, message: detail || "Request failed" };
    }

    return res.json();
  } catch (err) {
    clearTimeout(timeout);

    // Retry transient errors once
    if (
      retries > 0 &&
      (err?.status === 502 || err?.status === 503 || err?.status === 504)
    ) {
      console.warn(`Retrying ${path} after transient error:`, err);
      return req(path, { method, body, token, retries: retries - 1 });
    }

    console.error("API request failed:", err);
    throw err;
  }
}

// Meeting window / Tickets
export const getMeetingWindow = (token) =>
  req("/api/meeting-window", { token });

export const getTickets = (token, params = {}) => {
  const q = new URLSearchParams({
    ...params,
    bucketed: params.bucketed !== undefined ? String(params.bucketed) : "true",
  }).toString();
  return req(`/api/tickets?${q}`, { token });
};

// Mutations (write-back)
export const patchTicket = (token, id, fields) =>
  req(`/api/tickets/${id}`, { method: "PATCH", token, body: fields });

export const addComment = (token, id, body, isPublic) =>
  req(`/api/tickets/${id}/comments`, {
    method: "POST",
    token,
    body: { body, public: !!isPublic },
  });

// Export
export const runExport = (token) =>
  req("/api/export", { method: "POST", token });

// Token endpoint (MVP: no-op; replace if backend issues JWTs)
export const fetchFrontendToken = async () => {
  try {
    // For setups where backend returns a session token:
    // return req("/api/frontend-token", { method: "POST" });
    return { token: "" }; // No-op for now
  } catch (err) {
    console.warn("Token fetch skipped/failed:", err);
    return { token: "" };
  }
};
