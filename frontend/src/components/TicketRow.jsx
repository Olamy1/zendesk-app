// =================================================================================================
// File: TicketRow.jsx — v1.0 (Frontend UI → Row → Interactive Controls)
// Description: Renders a single Zendesk ticket row within the TicketTable.
//   - Data Source: Receives a single `ticket` object (t) enriched by backend.
//   - State: Tracks status, assignee, and group live for real-time updates.
//   - User Sync: Fetches OAPS users (restricted) to populate dropdown.
//   - Features:
//       • Status dropdown with backend patch sync
//       • Assignee dropdown (OAPS only), auto-syncs group_id on change
//       • Group column reacts instantly when reassigned
//       • Age column toggles between bucket or exact days
//       • Closed by Meeting flag indicator
//       • Notes editor for public/internal comments
//
// Props:
//   • t (Object)           — ticket object (id, subject, group, assignee, status, etc.)
//   • onStatus (Function)  — callback to update ticket status
//   • onReassign (Function)— callback to reassign ticket (assignee + group sync)
//   • onNote (Function)    — callback to add comment to ticket
//   • showExactAge (Bool)  — toggles "bucket view" vs "exact days"
//   • authToken (String)   — authentication token for fetching OAPS users
//
// Author: Olivier Lamy
// Version: 1.0.0 | Updated: September 30, 2025
// =================================================================================================

import React, { useState, useEffect } from "react";
import StatusBadge from "./StatusBadge.jsx";
import ClosedByMeetingFlag from "./ClosedByMeetingFlag.jsx";
import NotesEditor from "./NotesEditor.jsx";
import { getUsers } from "../services/backendAPI.js";

export default function TicketRow({ t, onStatus, onReassign, onNote, showExactAge, authToken }) {
  const [status, setStatus] = useState(t.status);
  const [assignee, setAssignee] = useState(t.assignee_id || "");
  const [group, setGroup] = useState(t.group || ""); // 🔹 track live group state
  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(true);

  // 🔹 Fetch OAPS users for dropdown
  useEffect(() => {
    if (!authToken) return;
    (async () => {
      try {
        const res = await getUsers(authToken);
        setUsers(res.users || []);
      } catch (e) {
        console.error("Failed to load users:", e);
      } finally {
        setLoadingUsers(false);
      }
    })();
  }, [authToken]);

  // 🔹 Age bucket → color mapping
  const ageColor =
    t.ageBucket === "Over 30 Days"
      ? "bg-red-200"
      : t.ageBucket === "Over 20 Days"
      ? "bg-orange-200"
      : t.ageBucket === "Over 10 Days"
      ? "bg-yellow-100"
      : "bg-green-100";

  return (
    <tr className="border-b">
      <td className="p-2">{t.id}</td>
      <td className="p-2">{t.subject}</td>

      {/* Group column (reactive to reassignment) */}
      <td className="p-2">{group}</td>

      {/* Status column */}
      <td className="p-2">
        <div className="flex items-center gap-2">
          <StatusBadge status={status} />
          <select
            className="border rounded px-2 py-1"
            value={status}
            onChange={async (e) => {
              const s = e.target.value;
              setStatus(s);
              await onStatus(t.id, s);
            }}
          >
            <option value="open">open</option>
            <option value="pending">pending</option>
            <option value="on-hold">on-hold</option>
            <option value="solved">solved</option>
            <option value="closed">closed</option>
          </select>
        </div>
      </td>

      {/* Assignee dropdown (dynamic, OAPS users only) */}
      <td className="p-2">
        <div className="flex items-center gap-2">
          <span className="text-xs text-gray-600">{t.assignee_name || "-"}</span>
          <select
            className="border rounded px-2 py-1 w-44"
            value={assignee}
            disabled={loadingUsers}
            onChange={async (e) => {
              const newAssignee = e.target.value;
              setAssignee(newAssignee);

              if (newAssignee) {
                // 🔹 Find selected user → update group immediately
                const selected = users.find((u) => String(u.id) === newAssignee);
                if (selected) {
                  setGroup(selected.group_id); // optimistic UI update
                  await onReassign(t.id, {
                    assignee_id: Number(selected.id),
                    group_id: selected.group_id,
                  });
                } else {
                  await onReassign(t.id, { assignee_id: Number(newAssignee) });
                }
              }
            }}
          >
            <option value="">
              {loadingUsers ? "Loading..." : "-- Select Assignee --"}
            </option>
            {!loadingUsers &&
              users.map((u) => (
                <option key={u.id} value={u.id}>
                  {u.name}
                </option>
              ))}
          </select>
        </div>
      </td>

      {/* Age column: bucket or exact days */}
      <td className={`p-2 ${ageColor}`}>
        {showExactAge ? (t.ageDays ?? "-") : t.ageBucket}
      </td>

      <td className="p-2">
        <ClosedByMeetingFlag value={t.closedByMeeting} />
      </td>

      <td className="p-2">
        <NotesEditor
          onSubmit={(body, isPublic) => onNote(t.id, body, isPublic)}
        />
      </td>
    </tr>
  );
}
