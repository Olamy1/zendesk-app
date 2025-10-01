// For local dev you can hardcode during testing.
// In Zendesk, read this from app parameters via ZAF.
export const DEFAULT_BACKEND_BASE_URL = import.meta.env.VITE_BACKEND_BASE_URL || "http://localhost:8080";
export const TIMEZONE = "America/New_York";
