// =================================================================================================
// File: TicketTable.jsx — v1.0 (Frontend UI → Table → Row Mapping)
// Description: Renders the full Zendesk Ticket Table for OAPS Directors.
//   - Data Source: Receives a `tickets` array from the backend (via props).
//   - User Sync: Fetches OAPS users once (via /api/users) and injects them into rows.
//   - Layout: Provides the table wrapper, column headers, and maps tickets → TicketRow.
//   - Child: Delegates per-ticket rendering (status, reassignment, notes) to TicketRow.jsx.
//   - Features:
//       • Dynamic status updates (open/pending/on-hold/solved/closed)
//       • Assignee dropdown (restricted to OAPS users)
//       • Age bucket + exact age toggle (frontend-level)
//       • Closed by Meeting flag
//       • Notes editor (public/internal comments)
//
// Props:
//   • tickets (Array)      — list of ticket objects enriched by backend
//   • onStatus (Function)  — callback to update ticket status
//   • onReassign (Function)— callback to reassign ticket (assignee + group sync)
//   • onNote (Function)    — callback to add a comment to ticket
//   • showExactAge (Bool)  — toggles "bucket view" vs "exact days"
//   • authToken (String)   — authentication token for fetching OAPS users
//
// Author: Olivier Lamy
// Version: 1.0.0 | Updated: September 30, 2025
// =================================================================================================

import React, { useEffect, useState } from "react";
import TicketRow from "./TicketRow.jsx";
import { getUsers } from "../services/backendAPI.js";

export default function TicketTable({ tickets, onStatus, onReassign, onNote, showExactAge, authToken }) {
  const [users, setUsers] = useState([]);
  const [loadingUsers, setLoadingUsers] = useState(true);

  // 🔹 Fetch OAPS users once at the table level
  useEffect(() => {
    if (!authToken) return;
    (async () => {
      try {
        const res = await getUsers(authToken);
        setUsers(res.users || []);
      } catch (e) {
        console.error("Failed to load OAPS users:", e);
      } finally {
        setLoadingUsers(false);
      }
    })();
  }, [authToken]);

  return (
    <div>
      <table className="w-full text-sm border">
        <thead>
          <tr className="bg-gray-100 border-b">
            <th className="p-2 text-left">Ticket ID</th>
            <th className="p-2 text-left">Subject</th>
            <th className="p-2 text-left">Group</th>
            <th className="p-2 text-left">Status</th>
            <th className="p-2 text-left">Assignee</th>
            {/* Age column flexibly shows either bucket or days */}
            <th className="p-2 text-left">
              {showExactAge ? "Age (Days)" : "Age Bucket"}
            </th>
            <th className="p-2 text-left">Closed by Meeting?</th>
            <th className="p-2 text-left">Notes</th>
          </tr>
        </thead>
        <tbody>
          {tickets.map((t) => (
            <TicketRow
              key={t.id}
              t={t}
              onStatus={onStatus}
              onReassign={onReassign}
              onNote={onNote}
              showExactAge={showExactAge}
              users={users}              // ✅ inject OAPS users into each row
              loadingUsers={loadingUsers}
            />
          ))}
        </tbody>
      </table>
    </div>
  );
}
