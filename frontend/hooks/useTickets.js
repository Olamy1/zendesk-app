// hooks/useTickets.js
// ============================================================================
// Hook: useTickets
// Purpose: Manage lifecycle of Zendesk tickets for Directors Reporting app.
//
// Features:
// - Fetch meeting window + tickets in parallel.
// - Supports ticket updates (status, reassignment).
// - Supports adding internal/public notes.
// - Provides state: rows, meeting window, loading, error.
// - Ensures structured error handling + resilience.
//
// Dependencies:
// - backendAPI.js (getMeetingWindow, getTickets, patchTicket, addComment)
//
// Usage:
// const { rows, meetingWindow, loading, err, refresh, updateStatus, reassign, addNote } = useTickets(authToken);
// ============================================================================

import { useCallback, useEffect, useState } from "react";
import {
  getMeetingWindow,
  getTickets,
  patchTicket,
  addComment,
} from "../services/backendAPI";

export default function useTickets(authToken) {
  const [meetingWindow, setMeetingWindow] = useState(null);
  const [rows, setRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");

  /**
   * Refresh tickets + meeting window in parallel.
   * @param {object} params - Extra query params (e.g., { bucketed: true })
   */
  const refresh = useCallback(
    async (params = {}) => {
      setLoading(true);
      setErr("");
      try {
        const [mw, data] = await Promise.all([
          getMeetingWindow(authToken),
          getTickets(authToken, params),
        ]);
        setMeetingWindow(mw || null);
        setRows(data?.rows || []);
      } catch (e) {
        console.error("[useTickets] refresh failed:", e);
        setErr(
          e?.status
            ? `Error ${e.status}: ${e.message || "Unknown error"}`
            : e.message || String(e)
        );
      } finally {
        setLoading(false);
      }
    },
    [authToken]
  );

  // Auto-load once on mount
  useEffect(() => {
    refresh();
  }, [refresh]);

  /**
   * Update ticket status.
   */
  async function updateStatus(id, status) {
    try {
      await patchTicket(authToken, id, { status });
      await refresh();
    } catch (e) {
      console.error("[useTickets] updateStatus failed:", e);
      setErr(e.message || "Failed to update status");
    }
  }

  /**
   * Reassign a ticket to a different user.
   */
  async function reassign(id, assignee_id) {
    try {
      await patchTicket(authToken, id, { assignee_id });
      await refresh();
    } catch (e) {
      console.error("[useTickets] reassign failed:", e);
      setErr(e.message || "Failed to reassign ticket");
    }
  }

  /**
   * Add an internal or public note to a ticket.
   */
  async function addNote(id, body, isPublic = false) {
    try {
      await addComment(authToken, id, body, isPublic);
      await refresh();
    } catch (e) {
      console.error("[useTickets] addNote failed:", e);
      setErr(e.message || "Failed to add note");
    }
  }

  return {
    meetingWindow,
    rows,
    loading,
    err,
    refresh,
    updateStatus,
    reassign,
    addNote,
  };
}
