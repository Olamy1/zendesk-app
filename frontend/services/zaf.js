// Minimal helpers around ZAF SDK.
// services/zaf.js
let client;

/**
 * Initialize or return cached ZAFClient.
 * In local dev (no ZAF), returns null.
 */
export function zaf() {
  if (client) return client;

  if (typeof window.ZAFClient === "undefined") {
    console.warn("[ZAF] No ZAFClient detected (likely local dev).");
    return null;
  }

  client = window.ZAFClient.init();
  console.info("[ZAF] Client initialized.");
  return client;
}

/**
 * Fetch app parameters defined in manifest.json.
 * Returns {} in local dev mode.
 */
export async function getAppParams() {
  const c = zaf();
  if (!c) {
    console.warn("[ZAF] Returning empty params (local dev).");
    return {};
  }

  try {
    const { app } = await c.get("app");
    const { BACKEND_BASE_URL } = app?.parameters || {};
    console.info("[ZAF] Loaded params:", { BACKEND_BASE_URL });
    return { BACKEND_BASE_URL };
  } catch (e) {
    console.error("[ZAF] Failed to fetch app params", e);
    throw e;
  }
}
