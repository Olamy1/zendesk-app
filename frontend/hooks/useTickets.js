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

  const refresh = useCallback(
    async (params = {}) => {
      setLoading(true);
      setErr("");
      try {
        const [mw, data] = await Promise.all([
          getMeetingWindow(authToken),
          getTickets(authToken, params), // respects bucketed toggle
        ]);
        setMeetingWindow(mw);
        setRows(data.rows || []);
      } catch (e) {
        // Structured error handling
        if (e?.status) {
          setErr(`Error ${e.status}: ${e.message || "Unknown error"}`);
        } else {
          setErr(e.message || String(e));
        }
      } finally {
        setLoading(false);
      }
    },
    [authToken]
  );

  useEffect(() => {
    refresh();
  }, [refresh]);

  async function updateStatus(id, status) {
    try {
      await patchTicket(authToken, id, { status });
      await refresh();
    } catch (e) {
      setErr(e.message || "Failed to update status");
    }
  }

  async function reassign(id, assignee_id) {
    try {
      await patchTicket(authToken, id, { assignee_id });
      await refresh();
    } catch (e) {
      setErr(e.message || "Failed to reassign ticket");
    }
  }

  async function addNote(id, body, isPublic) {
    try {
      await addComment(authToken, id, body, isPublic);
      await refresh();
    } catch (e) {
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
