// hooks/useUsers.js
// ============================================================================
// Hook: useUsers
// Purpose: Manage fetching of OAPS-only Zendesk users for dropdowns.
//
// Features:
// - Fetches list of users once or on-demand.
// - Returns state: users, loading, error.
// - Provides refresh() to re-fetch if needed.
// - Structured error handling with safe defaults.
//
// Dependencies:
// - backendAPI.js (getUsers)
//
// Usage:
// const { users, loading, err, refresh } = useUsers(authToken);
// ============================================================================

import { useEffect, useState, useCallback } from "react";
import { getUsers } from "../services/backendAPI";

export default function useUsers(authToken) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  /**
   * Fetch users from backend.
   */
  const refresh = useCallback(async () => {
    setLoading(true);
    setErr("");
    try {
      const data = await getUsers(authToken);
      setUsers(data?.users || []);
    } catch (e) {
      console.error("[useUsers] fetch failed:", e);
      setErr(e.message || "Failed to fetch users.");
    } finally {
      setLoading(false);
    }
  }, [authToken]);

  // Auto-fetch on mount
  useEffect(() => {
    refresh();
  }, [refresh]);

  return { users, loading, err, refresh };
}
