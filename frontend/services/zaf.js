// services/zaf.js
// ============================================================================
// Zendesk App Framework (ZAF) SDK helper utilities
// Provides safe initialization of the ZAFClient and app parameter retrieval.
// ============================================================================

let client = null;
let cachedParams = null;

/**
 * Initialize or return a cached ZAFClient instance.
 *
 * - In production, this wraps window.ZAFClient.init().
 * - In local dev (when ZAF is not present), returns null
 *   to allow graceful fallback without breaking.
 *
 * @returns {object|null} ZAFClient instance or null if unavailable
 */
export function zaf() {
  if (client) return client;

  if (typeof window === "undefined" || typeof window.ZAFClient === "undefined") {
    console.warn("[ZAF] No ZAFClient detected (likely local dev).");
    return null;
  }

  try {
    client = window.ZAFClient.init();
    console.info("[ZAF] Client initialized.");
    return client;
  } catch (e) {
    console.error("[ZAF] Failed to initialize client:", e);
    return null;
  }
}

/**
 * Fetch app parameters defined in manifest.json.
 *
 * Caches the values to avoid repeated lookups.
 * In local dev mode (no ZAF), returns {}.
 *
 * @returns {Promise<object>} Parameters object (e.g., { BACKEND_BASE_URL: string })
 */
export async function getAppParams() {
  if (cachedParams) return cachedParams;

  const c = zaf();
  if (!c) {
    console.warn("[ZAF] Returning empty params (local dev).");
    cachedParams = {};
    return cachedParams;
  }

  try {
    const { app } = await c.get("app");
    const params = app?.parameters || {};
    cachedParams = params;

    console.info("[ZAF] Loaded params:", params);
    return params;
  } catch (e) {
    console.error("[ZAF] Failed to fetch app params:", e);
    cachedParams = {};
    return cachedParams; // fail safe: never throw in production
  }
}

/**
 * Utility: clear cached client + params (for testing / hot reloads).
 */
export function resetZafCache() {
  client = null;
  cachedParams = null;
  console.info("[ZAF] Cache reset.");
}
